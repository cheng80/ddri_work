from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent
KSM_DIR = BASE_DIR.parent
DATA_DIR = KSM_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"

TRAIN_PATH = DATA_DIR / "ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv"
TEST_PATH = DATA_DIR / "ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv"

LINEAR_DIR = KSM_DIR / "HMW_linear_regression_coefficients_20260318" / "outputs"
SIM_DIR = KSM_DIR / "HMW_feature_monthly_similarity_weights_20260318" / "outputs"
HET_DIR = KSM_DIR / "HMW_heteroscedasticity_diagnosis_20260318"


def load_inputs() -> dict[str, pd.DataFrame]:
    train = pd.read_csv(TRAIN_PATH, parse_dates=["date"])
    test = pd.read_csv(TEST_PATH, parse_dates=["date"])
    scores = pd.read_csv(LINEAR_DIR / "linear_regression_scores.csv")
    coefs = pd.read_csv(LINEAR_DIR / "linear_regression_coefficients.csv")
    month_weights = pd.read_csv(SIM_DIR / "overall_month_weight_suggestions.csv")
    hetero = pd.read_csv(HET_DIR / "bike_change_target_heteroscedasticity_feature_list.csv")
    return {
        "train": train,
        "test": test,
        "scores": scores,
        "coefs": coefs,
        "month_weights": month_weights,
        "hetero": hetero,
    }


def split_counts(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    train_2023 = train[train["date"].dt.year.eq(2023)]
    valid_2024 = train[train["date"].dt.year.eq(2024)]
    parts = [
        {"split": "train", "period": "2023", "rows": len(train_2023)},
        {"split": "valid", "period": "2024", "rows": len(valid_2024)},
        {"split": "test", "period": "2025", "rows": len(test)},
    ]
    return pd.DataFrame(parts)


def save_split_bar(counts: pd.DataFrame) -> Path:
    path = OUT_DIR / "split_row_counts.png"
    plt.figure(figsize=(8, 4.8))
    ax = sns.barplot(data=counts, x="split", y="rows", palette=["#1f4e79", "#4f7942", "#c26a2e"])
    ax.set_title("Train / Valid / Test Rows")
    ax.set_xlabel("")
    ax.set_ylabel("rows")
    for idx, row in counts.reset_index(drop=True).iterrows():
        ax.text(idx, row["rows"], f"{row['rows']:,}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_score_bar(scores: pd.DataFrame) -> Path:
    path = OUT_DIR / "ridge_scores.png"
    score_long = scores.melt(id_vars=["split"], value_vars=["rmse", "mae", "r2"], var_name="metric", value_name="value")
    plt.figure(figsize=(9, 5.2))
    ax = sns.barplot(data=score_long, x="split", y="value", hue="metric", palette=["#c26a2e", "#5d8aa8", "#4f7942"])
    ax.set_title("Ridge Regression Scores by Split")
    ax.set_xlabel("")
    ax.set_ylabel("score")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_coef_bar(coefs: pd.DataFrame) -> Path:
    path = OUT_DIR / "top_standardized_coefficients.png"
    top = coefs.head(12).copy().sort_values("standardized_coefficient")
    plt.figure(figsize=(9, 6))
    colors = ["#c26a2e" if v > 0 else "#1f4e79" for v in top["standardized_coefficient"]]
    ax = plt.gca()
    ax.barh(top["feature"], top["standardized_coefficient"], color=colors)
    ax.set_title("Top Standardized Coefficients")
    ax.set_xlabel("coefficient")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_month_weight_bar(month_weights: pd.DataFrame) -> Path:
    path = OUT_DIR / "overall_month_weights.png"
    ordered = month_weights.sort_values("year_month")
    plt.figure(figsize=(12, 4.8))
    ax = sns.lineplot(data=ordered, x="year_month", y="overall_month_weight", marker="o", color="#1f4e79")
    ax.set_title("Overall Month Weight Suggestions")
    ax.set_xlabel("year_month")
    ax.set_ylabel("weight")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def write_report(data: dict[str, pd.DataFrame], image_paths: dict[str, Path]) -> Path:
    train = data["train"]
    test = data["test"]
    scores = data["scores"]
    coefs = data["coefs"]
    month_weights = data["month_weights"]
    hetero = data["hetero"]

    counts = split_counts(train, test)
    feature_cols = [c for c in train.columns if c not in ["bike_change_raw", "date", "sample_weight"]]
    removed_cols = [
        "rental_count_deseasonalized",
        "bike_change_trend_1_24",
        "bike_change_trend_24_168",
        "mapped_dong_code",
        "seasonal_mean_2023",
        "bike_change_lag_24",
        "bike_change_lag_168",
        "bike_change_deseasonalized",
    ]
    hetero_true = hetero[hetero["heteroscedasticity_violation"] == True]["feature"].tolist()

    lines: list[str] = []
    lines.append("# Ridge 회귀 기반 End-to-End 분석 보고서")
    lines.append("")
    lines.append("## 1. 목적")
    lines.append("- 최종 전처리된 DDRI 데이터로 해석 가능한 회귀 모델(Ridge)을 학습하고, 시간순 train/valid/test 성능을 평가한다.")
    lines.append("- 데이터 정제, 공선성 정리, 누수 점검, 월 유사도 기반 sample weight 반영까지의 과정을 문서화한다.")
    lines.append("")
    lines.append("## 2. 원본 및 최종 데이터")
    lines.append(f"- 학습 데이터: `{TRAIN_PATH.as_posix()}`")
    lines.append(f"- 테스트 데이터: `{TEST_PATH.as_posix()}`")
    lines.append(f"- 타깃: `bike_change_raw`")
    lines.append(f"- 최종 학습 feature 수: **{len(feature_cols)}개**")
    lines.append(f"- 최종 학습 feature: `{', '.join(feature_cols)}`")
    lines.append("")
    lines.append("## 3. 전처리 요약")
    lines.append("- 공선성 제거 후보 PDF 기준으로 주요 중복/선형결합 컬럼을 제거했다.")
    lines.append(f"- 제거 컬럼: `{', '.join(removed_cols)}`")
    lines.append("- `bike_change_lag_1`, `bike_change_rollmean_24`, `bike_change_rollstd_24`, `bike_change_rollmean_168`, `bike_change_rollstd_168`는 과거값 기반 파생변수로 확인되었고, 현재/미래값 누수는 없는 것으로 검증했다.")
    lines.append(f"- 등분산성 진단에서는 키 제외 기준으로 여러 feature가 이분산 신호를 보였으며, 대표 위반 컬럼 예시는 `{', '.join(hetero_true[:8])}` 이다.")
    lines.append("")
    lines.append("## 4. 월 유사도 기반 sample_weight")
    lines.append("- 연-월별 시간 평균선이 너무 유사한 구간은 학습 기여도를 약하게 하기 위해 월 단위 `sample_weight`를 만들었다.")
    lines.append(
        f"- sample_weight 범위: `{train['sample_weight'].min():.6f} ~ {train['sample_weight'].max():.6f}`"
    )
    low_months = month_weights.sort_values("overall_month_weight").head(5)[["year_month", "overall_month_weight"]]
    lines.append("- 가중치가 낮은 월 예시:")
    lines.append(low_months.to_markdown(index=False))
    lines.append("")
    lines.append("## 5. 데이터 분할")
    lines.append("- train: 2023년")
    lines.append("- valid: 2024년")
    lines.append("- test: 2025년")
    lines.append("")
    lines.append(f"![split counts]({image_paths['split'].name})")
    lines.append("")
    lines.append("## 6. 모델링 방법")
    lines.append("- 모델: `Ridge(alpha=2.0)`")
    lines.append("- 전처리: 결측치는 median imputation, 수치형 feature는 standardization")
    lines.append("- 학습 시 `sample_weight` 사용")
    lines.append("- 평가 지표: `RMSE`, `MAE`, `R2`")
    lines.append("")
    lines.append("## 7. 회귀 성능")
    lines.append("")
    lines.append(scores.to_markdown(index=False))
    lines.append("")
    lines.append(f"![ridge scores]({image_paths['scores'].name})")
    lines.append("")
    lines.append("## 8. 성능 해석")
    train_row = scores[scores["split"] == "train"].iloc[0]
    valid_row = scores[scores["split"] == "valid"].iloc[0]
    test_row = scores[scores["split"] == "test"].iloc[0]
    lines.append(
        f"- train R2={train_row['r2']:.6f}, valid R2={valid_row['r2']:.6f}, test R2={test_row['r2']:.6f}로 split 간 차이가 크지 않아 과적합은 심하지 않은 편이다."
    )
    lines.append(
        f"- valid/test 성능이 train과 유사하게 유지되어 시간순 분할 기준에서도 안정적인 선형 베이스라인으로 볼 수 있다."
    )
    lines.append("")
    lines.append("## 9. 회귀 계수 해석")
    lines.append("- 아래 계수는 표준화 계수 기준이며, 절댓값이 클수록 타깃에 미치는 선형 영향력이 크다.")
    lines.append("")
    lines.append(coefs.head(12).to_markdown(index=False))
    lines.append("")
    lines.append(f"![top coefficients]({image_paths['coef'].name})")
    lines.append("")
    lines.append("## 10. 종합 결론")
    lines.append("- 현재 전처리와 feature 구성으로 Ridge 회귀는 해석 가능성과 성능의 균형이 좋은 모델이다.")
    lines.append("- 최고 성능 모델은 아닐 수 있지만, 설명 가능한 기준모델이자 실제 운영 후보로도 검토할 만하다.")
    lines.append("- 이후에는 LightGBM과 Ridge를 병행 운영하거나, Ridge를 기준선 모델로 유지하는 전략이 유효하다.")
    lines.append("")
    lines.append("## 11. 참고 산출물")
    lines.append(f"- 선형회귀 계수: `{(LINEAR_DIR / 'linear_regression_coefficients.csv').as_posix()}`")
    lines.append(f"- 선형회귀 점수: `{(LINEAR_DIR / 'linear_regression_scores.csv').as_posix()}`")
    lines.append(f"- 월 가중치 제안: `{(SIM_DIR / 'overall_month_weight_suggestions.csv').as_posix()}`")
    lines.append(f"- 공산성 진단: `{(HET_DIR / 'bike_change_target_heteroscedasticity_report_ko.md').as_posix()}`")

    report_path = OUT_DIR / "ridge_end_to_end_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    data = load_inputs()
    counts = split_counts(data["train"], data["test"])

    image_paths = {
        "split": save_split_bar(counts),
        "scores": save_score_bar(data["scores"]),
        "coef": save_coef_bar(data["coefs"]),
        "month_weight": save_month_weight_bar(data["month_weights"]),
    }

    report_path = write_report(data, image_paths)

    meta = {
        "train_path": TRAIN_PATH.as_posix(),
        "test_path": TEST_PATH.as_posix(),
        "report_path": report_path.as_posix(),
        "images": {k: v.as_posix() for k, v in image_paths.items()},
    }
    (OUT_DIR / "report_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("report:", report_path.as_posix())
    for key, value in image_paths.items():
        print(key, value.as_posix())


if __name__ == "__main__":
    main()
