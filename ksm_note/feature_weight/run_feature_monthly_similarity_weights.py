from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3.csv"
OUT_DIR = BASE_DIR / "outputs"


def build_feature_list(df: pd.DataFrame) -> list[str]:
    exclude = {
        "station_id",
        "date",
        "hour",
        "bike_change_raw",
    }
    return [col for col in df.columns if col not in exclude]


def make_hourly_profiles(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"])
    work["year"] = work["date"].dt.year.astype("int16")
    work["year_month"] = work["date"].dt.to_period("M").astype(str)

    profiles = (
        work.groupby(["year", "month", "year_month", "hour"], as_index=False)[features]
        .mean(numeric_only=True)
        .melt(
            id_vars=["year", "month", "year_month", "hour"],
            value_vars=features,
            var_name="feature",
            value_name="hourly_mean",
        )
        .sort_values(["feature", "year", "month", "hour"])
        .reset_index(drop=True)
    )
    return profiles


def calculate_adjacent_similarity(profiles: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str | bool]] = []

    for feature, feature_df in profiles.groupby("feature", sort=True):
        meta = (
            feature_df[["year", "month", "year_month"]]
            .drop_duplicates()
            .sort_values(["year", "month"])
            .reset_index(drop=True)
        )

        for idx in range(len(meta) - 1):
            left = meta.iloc[idx]
            right = meta.iloc[idx + 1]

            if (right["year"] * 12 + right["month"]) - (left["year"] * 12 + left["month"]) != 1:
                continue

            left_vec = (
                feature_df.loc[feature_df["year_month"].eq(left["year_month"]), ["hour", "hourly_mean"]]
                .set_index("hour")["hourly_mean"]
                .reindex(range(24))
            )
            right_vec = (
                feature_df.loc[feature_df["year_month"].eq(right["year_month"]), ["hour", "hourly_mean"]]
                .set_index("hour")["hourly_mean"]
                .reindex(range(24))
            )

            pair = pd.concat([left_vec.rename("left"), right_vec.rename("right")], axis=1).dropna()
            if len(pair) < 12:
                corr = np.nan
                nrmse = np.nan
                mad = np.nan
                similar = False
                score = np.nan
            else:
                left_std = float(pair["left"].std(ddof=0))
                right_std = float(pair["right"].std(ddof=0))
                if left_std == 0 and right_std == 0:
                    corr = 1.0 if np.allclose(pair["left"], pair["right"]) else 0.0
                elif left_std == 0 or right_std == 0:
                    corr = 0.0
                else:
                    corr = float(pair["left"].corr(pair["right"]))
                rmse = float(np.sqrt(np.mean((pair["left"] - pair["right"]) ** 2)))
                scale = left_std
                if scale == 0:
                    scale = right_std
                if scale == 0:
                    scale = 1.0
                nrmse = float(rmse / scale)
                mad = float(np.mean(np.abs(pair["left"] - pair["right"])))

                corr_for_score = 0.0 if np.isnan(corr) else max(corr, 0.0)
                similarity_score = corr_for_score * max(0.0, 1.0 - min(nrmse, 1.0))
                score = float(similarity_score)
                similar = bool((corr_for_score >= 0.95) and (nrmse <= 0.35))

            rows.append(
                {
                    "feature": feature,
                    "year_month_left": left["year_month"],
                    "year_month_right": right["year_month"],
                    "corr": corr,
                    "nrmse": nrmse,
                    "mean_abs_diff": mad,
                    "similarity_score": score,
                    "similar_flag": similar,
                }
            )

    return pd.DataFrame(rows).sort_values(["feature", "year_month_left"]).reset_index(drop=True)


def make_monthly_weights(similarity: pd.DataFrame) -> pd.DataFrame:
    left_view = similarity[
        ["feature", "year_month_left", "similarity_score", "similar_flag"]
    ].rename(columns={"year_month_left": "year_month"})
    right_view = similarity[
        ["feature", "year_month_right", "similarity_score", "similar_flag"]
    ].rename(columns={"year_month_right": "year_month"})
    long_view = pd.concat([left_view, right_view], ignore_index=True)

    monthly = (
        long_view.groupby(["feature", "year_month"], as_index=False)
        .agg(
            adjacent_similarity_mean=("similarity_score", "mean"),
            adjacent_similarity_max=("similarity_score", "max"),
            similar_neighbor_count=("similar_flag", "sum"),
        )
        .fillna({"adjacent_similarity_mean": 0.0, "adjacent_similarity_max": 0.0})
    )

    # Similarity가 높을수록 가중치를 낮추는 보수적 휴리스틱
    monthly["suggested_weight"] = (1.0 - 0.5 * monthly["adjacent_similarity_mean"]).clip(0.5, 1.0)
    monthly["downweight_flag"] = monthly["suggested_weight"] < 0.85
    return monthly.sort_values(["feature", "year_month"]).reset_index(drop=True)


def make_overall_month_weights(weights: pd.DataFrame) -> pd.DataFrame:
    overall = (
        weights.groupby("year_month", as_index=False)
        .agg(
            feature_count=("feature", "size"),
            mean_feature_weight=("suggested_weight", "mean"),
            min_feature_weight=("suggested_weight", "min"),
            downweight_feature_count=("downweight_flag", "sum"),
            mean_adjacent_similarity=("adjacent_similarity_mean", "mean"),
        )
        .sort_values("year_month")
        .reset_index(drop=True)
    )
    overall["overall_month_weight"] = overall["mean_feature_weight"].clip(0.5, 1.0)
    overall["downweight_flag"] = overall["overall_month_weight"] < 0.85
    return overall


def make_summary_md(
    features: list[str],
    similarity: pd.DataFrame,
    weights: pd.DataFrame,
    overall_weights: pd.DataFrame,
) -> str:
    top_similar = similarity.sort_values(["similar_flag", "similarity_score"], ascending=[False, False]).head(20)
    top_down = weights.sort_values("suggested_weight", ascending=True).head(20)
    top_months = overall_weights.sort_values("overall_month_weight", ascending=True).head(12)

    lines: list[str] = []
    lines.append("# feature별 월간 시간평균선 유사도 및 가중치 제안")
    lines.append("")
    lines.append(f"- 데이터: `{DATA_PATH.as_posix()}`")
    lines.append(f"- 분석 feature 수: **{len(features)}개**")
    lines.append("- 기준: 인접 월(예: 2023-01 vs 2023-02)의 24시간 평균선 비교")
    lines.append("- 지표: `corr`, `NRMSE`, `similarity_score = max(corr,0) * (1 - min(NRMSE,1))`")
    lines.append("- 유사 판정: `corr >= 0.95` 그리고 `NRMSE <= 0.35`")
    lines.append("- 제안 가중치: `1 - 0.5 * 평균 similarity_score`, 범위 `[0.5, 1.0]`")
    lines.append("")
    lines.append("## 유사도 높은 인접 월 상위 20개")
    lines.append("")
    lines.append(top_similar.to_markdown(index=False))
    lines.append("")
    lines.append("## 가중치가 가장 낮게 제안된 feature-월 상위 20개")
    lines.append("")
    lines.append(top_down.to_markdown(index=False))
    lines.append("")
    lines.append("## 월 단위 전체 가중치 제안")
    lines.append("")
    lines.append(top_months.to_markdown(index=False))
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    features = build_feature_list(df)

    profiles = make_hourly_profiles(df, features)
    similarity = calculate_adjacent_similarity(profiles)
    weights = make_monthly_weights(similarity)
    overall_weights = make_overall_month_weights(weights)

    profiles.to_csv(OUT_DIR / "feature_hourly_profiles_by_year_month.csv", index=False, encoding="utf-8-sig")
    similarity.to_csv(OUT_DIR / "feature_adjacent_month_similarity.csv", index=False, encoding="utf-8-sig")
    weights.to_csv(OUT_DIR / "feature_monthly_weight_suggestions.csv", index=False, encoding="utf-8-sig")
    overall_weights.to_csv(OUT_DIR / "overall_month_weight_suggestions.csv", index=False, encoding="utf-8-sig")
    (OUT_DIR / "feature_monthly_similarity_summary.md").write_text(
        make_summary_md(features, similarity, weights, overall_weights),
        encoding="utf-8",
    )

    print("saved:", OUT_DIR.as_posix())
    print("features:", len(features))
    print("similar_pairs:", len(similarity))
    print("downweight_rows:", int(weights["downweight_flag"].sum()))


if __name__ == "__main__":
    main()
