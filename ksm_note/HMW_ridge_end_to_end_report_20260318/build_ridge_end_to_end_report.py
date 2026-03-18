from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent
KSM_DIR = BASE_DIR.parent
DATA_DIR = KSM_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"

TRAIN_PATH = DATA_DIR / "ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv"
TEST_PATH = DATA_DIR / "ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv"

LINEAR_DIR = KSM_DIR / "HMW_linear_regression_coefficients_20260318" / "outputs"
SIM_DIR = KSM_DIR / "feature_weight" / "outputs"
CLUSTER_DIR = KSM_DIR / "HMW_cluster_ridge_regression_20260318" / "outputs"
AUDIT_DIR = KSM_DIR / "lightgbm_reason" / "outputs"
LGBM_COMPARE_DIR = KSM_DIR / "lightgbm_reason_1" / "outputs"
CORR_DIR = KSM_DIR / "feature_hitmap" / "outputs"

REMOVED_COLS = [
    "rental_count_deseasonalized",
    "bike_change_trend_1_24",
    "bike_change_trend_24_168",
    "mapped_dong_code",
    "seasonal_mean_2023",
    "bike_change_lag_24",
    "bike_change_lag_168",
    "bike_change_deseasonalized",
]

COL_MEANINGS = [
    ("station_id", "대여소 고유 ID"),
    ("hour", "시간대(0~23시)"),
    ("rental_count", "해당 시점 대여 건수"),
    ("weekday", "요일 정보(월~일 인코딩)"),
    ("month", "월 정보"),
    ("holiday", "공휴일 여부"),
    ("temperature", "기온"),
    ("humidity", "습도"),
    ("precipitation", "강수량"),
    ("wind_speed", "풍속"),
    ("cluster", "대여소 군집 번호"),
    ("bike_change_raw", "예측 대상인 자전거 수요 변화량"),
    ("bike_change_lag_1", "직전 시점의 bike_change_raw"),
    ("bike_change_rollmean_24", "직전 24시간 bike_change_raw 평균"),
    ("bike_change_rollstd_24", "직전 24시간 bike_change_raw 표준편차"),
    ("bike_change_rollmean_168", "직전 168시간 bike_change_raw 평균"),
    ("bike_change_rollstd_168", "직전 168시간 bike_change_raw 표준편차"),
    ("sample_weight", "월별 유사패턴을 반영해 학습 시 곱해준 행 가중치"),
]

WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]


def setup_plot_style() -> None:
    plt.rcParams["font.family"] = ["Malgun Gothic"]
    plt.rcParams["font.sans-serif"] = ["Malgun Gothic"]
    plt.rcParams["axes.unicode_minus"] = False
    sns.set_theme(style="whitegrid", font="Malgun Gothic")


def rel(path: Path) -> str:
    import os

    path = Path(path)
    if path.is_relative_to(OUT_DIR):
        return path.relative_to(OUT_DIR).as_posix()
    return os.path.relpath(path, OUT_DIR).replace("\\", "/")


def load_inputs() -> dict[str, pd.DataFrame]:
    train = pd.read_csv(TRAIN_PATH, parse_dates=["date"])
    test = pd.read_csv(TEST_PATH, parse_dates=["date"])
    scores = pd.read_csv(LINEAR_DIR / "linear_regression_scores.csv")
    coefs = pd.read_csv(LINEAR_DIR / "linear_regression_coefficients.csv")
    month_weights = pd.read_csv(SIM_DIR / "overall_month_weight_suggestions.csv")
    similarity = pd.read_csv(SIM_DIR / "feature_adjacent_month_similarity.csv")
    profiles = pd.read_csv(SIM_DIR / "feature_hourly_profiles_by_year_month.csv")
    cluster_scores = pd.read_csv(CLUSTER_DIR / "cluster_ridge_scores.csv")
    target_audit = pd.read_csv(AUDIT_DIR / "target_like_feature_audit.csv")
    future_audit = pd.read_csv(AUDIT_DIR / "future_information_audit.csv")
    split_ranges = pd.read_csv(AUDIT_DIR / "split_date_ranges.csv")
    split_overlap = pd.read_csv(AUDIT_DIR / "split_key_overlap_audit.csv")
    lgbm_compare = pd.read_csv(LGBM_COMPARE_DIR / "lightgbm_without_history_comparison.csv")
    high_corr_pairs = pd.read_csv(CORR_DIR / "high_correlation_pairs_over_0_7.csv")
    return {
        "train": train,
        "test": test,
        "scores": scores,
        "coefs": coefs,
        "month_weights": month_weights,
        "similarity": similarity,
        "profiles": profiles,
        "cluster_scores": cluster_scores,
        "target_audit": target_audit,
        "future_audit": future_audit,
        "split_ranges": split_ranges,
        "split_overlap": split_overlap,
        "lgbm_compare": lgbm_compare,
        "high_corr_pairs": high_corr_pairs,
    }


def split_counts(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"split": "train", "period": "2023", "rows": int(train[train["date"].dt.year.eq(2023)].shape[0])},
            {"split": "valid", "period": "2024", "rows": int(train[train["date"].dt.year.eq(2024)].shape[0])},
            {"split": "test", "period": "2025", "rows": int(test.shape[0])},
        ]
    )


def current_feature_corr(train: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_cols = [c for c in train.columns if c not in ["date", "bike_change_raw", "sample_weight"]]
    corr = train[feature_cols].corr(numeric_only=True)
    pairs = []
    cols = corr.columns.tolist()
    for i, left in enumerate(cols):
        for right in cols[i + 1 :]:
            value = corr.loc[left, right]
            pairs.append({"feature_a": left, "feature_b": right, "correlation": value, "abs_correlation": abs(value)})
    pair_df = pd.DataFrame(pairs).sort_values("abs_correlation", ascending=False).reset_index(drop=True)
    return corr, pair_df


def save_process_flow() -> Path:
    path = OUT_DIR / "analysis_process_flow.png"
    fig, ax = plt.subplots(figsize=(13, 3.2))
    ax.axis("off")
    steps = [
        ("1. 원본 점검", "컬럼 구조 확인\n타깃 정의"),
        ("2. 공선성 정리", "고상관 변수 제거\n중복 파생변수 축소"),
        ("3. 누수 점검", "미래정보 확인\n시간축 분할 검증"),
        ("4. 패턴 진단", "월·요일·시간 패턴 비교\nsample_weight 설계"),
        ("5. Ridge 학습", "2023 학습\n2024 검증"),
        ("6. 성능 평가", "2025 테스트\n클러스터별 비교"),
    ]
    x_positions = [0.06, 0.24, 0.42, 0.60, 0.78, 0.94]
    for idx, ((title, subtitle), x) in enumerate(zip(steps, x_positions)):
        ax.text(
            x,
            0.5,
            f"{title}\n{subtitle}",
            ha="center",
            va="center",
            fontsize=11,
            bbox={"boxstyle": "round,pad=0.45", "facecolor": "#f4f1ea", "edgecolor": "#3b5b75", "linewidth": 1.5},
        )
        if idx < len(steps) - 1:
            ax.annotate("", xy=(x_positions[idx + 1] - 0.07, 0.5), xytext=(x + 0.07, 0.5), arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#3b5b75"})
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_feature_count_bar(before_count: int, after_count: int, removed_count: int) -> Path:
    path = OUT_DIR / "feature_count_summary.png"
    df = pd.DataFrame({"단계": ["원본 컬럼 수", "제거 컬럼 수", "최종 입력 변수 수"], "개수": [before_count, removed_count, after_count]})
    plt.figure(figsize=(8, 4.8))
    ax = sns.barplot(data=df, x="단계", y="개수", hue="단계", dodge=False, palette=["#5d8aa8", "#c26a2e", "#4f7942"])
    if ax.legend_ is not None:
        ax.legend_.remove()
    ax.set_title("전처리 단계별 변수 개수")
    ax.set_xlabel("")
    ax.set_ylabel("개수")
    for idx, row in df.reset_index(drop=True).iterrows():
        ax.text(idx, row["개수"], str(int(row["개수"])), ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_split_bar(counts: pd.DataFrame) -> Path:
    path = OUT_DIR / "split_row_counts.png"
    plot_df = counts.copy()
    plot_df["split"] = plot_df["split"].map({"train": "학습", "valid": "검증", "test": "테스트"})
    plt.figure(figsize=(8, 4.8))
    ax = sns.barplot(data=plot_df, x="split", y="rows", hue="split", dodge=False, palette=["#1f4e79", "#4f7942", "#c26a2e"])
    if ax.legend_ is not None:
        ax.legend_.remove()
    ax.set_title("학습·검증·테스트 데이터 행 수")
    ax.set_xlabel("")
    ax.set_ylabel("행 수")
    for idx, row in plot_df.reset_index(drop=True).iterrows():
        ax.text(idx, row["rows"], f"{row['rows']:,}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_score_bar(scores: pd.DataFrame) -> Path:
    path = OUT_DIR / "ridge_scores.png"
    score_long = scores.melt(id_vars=["split"], value_vars=["rmse", "mae", "r2"], var_name="metric", value_name="value")
    score_long["split"] = score_long["split"].map({"train": "학습", "valid": "검증", "test": "테스트"})
    score_long["metric"] = score_long["metric"].map({"rmse": "RMSE", "mae": "MAE", "r2": "R2"})
    plt.figure(figsize=(9, 5.2))
    ax = sns.barplot(data=score_long, x="split", y="value", hue="metric", palette=["#c26a2e", "#5d8aa8", "#4f7942"])
    ax.set_title("Ridge 회귀모델 분할별 성능")
    ax.set_xlabel("")
    ax.set_ylabel("점수")
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
    ax.set_title("표준화 회귀계수 상위 변수")
    ax.set_xlabel("계수값")
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
    ax.set_title("월별 제안 가중치")
    ax.set_xlabel("연월")
    ax.set_ylabel("가중치")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_current_corr_heatmap(corr: pd.DataFrame) -> Path:
    path = OUT_DIR / "current_feature_correlation_heatmap.png"
    plt.figure(figsize=(11, 9))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, cmap="RdBu_r", center=0, vmin=-1, vmax=1, square=True, linewidths=0.4)
    plt.title("최종 입력 변수 상관계수 히트맵")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_high_corr_bar(high_corr_pairs: pd.DataFrame) -> Path:
    path = OUT_DIR / "high_correlation_pairs_bar.png"
    plot_df = high_corr_pairs.copy().sort_values("abs_correlation", ascending=True)
    labels = plot_df["feature_a"] + " ↔ " + plot_df["feature_b"]
    colors = ["#b22222" if v >= 0.9 else "#c26a2e" for v in plot_df["abs_correlation"]]
    plt.figure(figsize=(10, 4.8))
    plt.barh(labels, plot_df["abs_correlation"], color=colors)
    plt.axvline(0.9, color="#1f4e79", linestyle="--", linewidth=1.5, label="0.9 기준")
    plt.title("초기 공선성 점검: 높은 상관계수 쌍")
    plt.xlabel("절대 상관계수")
    plt.ylabel("")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_similarity_heatmap(similarity: pd.DataFrame) -> Path:
    path = OUT_DIR / "adjacent_month_similarity_heatmap.png"
    plot_df = similarity[~similarity["feature"].str.startswith("bike_change")].copy()
    top_features = (
        plot_df.groupby("feature", as_index=False)["similarity_score"].max().sort_values("similarity_score", ascending=False).head(8)["feature"].tolist()
    )
    plot_df = plot_df[plot_df["feature"].isin(top_features)].copy()
    plot_df["month_pair"] = plot_df["year_month_left"] + "→" + plot_df["year_month_right"]
    pivot = plot_df.pivot(index="feature", columns="month_pair", values="similarity_score")
    plt.figure(figsize=(14, 5.5))
    sns.heatmap(pivot, cmap="YlGnBu", vmin=0, vmax=1, linewidths=0.3)
    plt.title("인접 월 시간 평균선 유사도 히트맵")
    plt.xlabel("인접 월 쌍")
    plt.ylabel("변수")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_hourly_profile_compare(profiles: pd.DataFrame, similarity: pd.DataFrame, feature: str = "rental_count", left: str = "2023-05", right: str = "2023-06") -> Path:
    path = OUT_DIR / "hourly_profile_compare_rental_count.png"
    plot_df = profiles[(profiles["feature"].eq(feature)) & (profiles["year_month"].isin([left, right]))].copy()
    sim_row = similarity[(similarity["feature"].eq(feature)) & (similarity["year_month_left"].eq(left)) & (similarity["year_month_right"].eq(right))].iloc[0]
    plt.figure(figsize=(10, 4.8))
    sns.lineplot(data=plot_df, x="hour", y="hourly_mean", hue="year_month", marker="o", palette=["#1f4e79", "#c26a2e"])
    plt.title(f"시간별 평균선 비교: {feature} ({left} vs {right})")
    plt.xlabel("시간")
    plt.ylabel("평균값")
    plt.text(0.01, 0.02, f"corr={sim_row['corr']:.3f}, NRMSE={sim_row['nrmse']:.3f}, similarity={sim_row['similarity_score']:.3f}", transform=plt.gca().transAxes)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_weekday_profile_compare(train: pd.DataFrame, feature: str = "rental_count", left: str = "2023-05", right: str = "2023-06") -> Path:
    path = OUT_DIR / "weekday_profile_compare_rental_count.png"
    work = train.copy()
    work["year_month"] = work["date"].dt.to_period("M").astype(str)
    plot_df = (
        work[work["year_month"].isin([left, right])]
        .groupby(["year_month", "weekday"], as_index=False)[feature]
        .mean()
        .sort_values(["year_month", "weekday"])
    )
    plot_df["weekday_label"] = plot_df["weekday"].map(dict(enumerate(WEEKDAY_LABELS)))
    plt.figure(figsize=(8, 4.8))
    sns.lineplot(data=plot_df, x="weekday_label", y=feature, hue="year_month", marker="o", palette=["#1f4e79", "#c26a2e"])
    plt.title(f"요일별 평균 패턴 비교: {feature} ({left} vs {right})")
    plt.xlabel("요일")
    plt.ylabel("평균값")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def make_removed_feature_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"제거 컬럼": "bike_change_deseasonalized", "원인": "bike_change_raw와 상관계수 0.9349로 매우 높음", "조치": "중복 타깃 계열 변수 제거"},
            {"제거 컬럼": "rental_count_deseasonalized", "원인": "원 변수와 계절조정 변수가 함께 존재", "조치": "설명력이 겹치는 파생변수 제거"},
            {"제거 컬럼": "bike_change_trend_1_24 / bike_change_trend_24_168", "원인": "bike_change 계열 추세 파생변수 중복", "조치": "공선성 완화를 위해 제거"},
            {"제거 컬럼": "bike_change_lag_24 / bike_change_lag_168", "원인": "다중 시차 변수 과다로 공선성 우려", "조치": "대표 lag만 남기고 제거"},
            {"제거 컬럼": "seasonal_mean_2023", "원인": "계절성 요약값이 월·시간 변수와 의미 중첩", "조치": "대표성 낮은 요약 변수 제거"},
            {"제거 컬럼": "mapped_dong_code", "원인": "지역 코드형 변수로 군집 변수와 역할 중첩", "조치": "모델 단순화를 위해 제거"},
        ]
    )


def make_column_table() -> pd.DataFrame:
    return pd.DataFrame(COL_MEANINGS, columns=["컬럼", "의미"])


def write_report(data: dict[str, pd.DataFrame], image_paths: dict[str, Path], corr: pd.DataFrame, current_pairs: pd.DataFrame) -> Path:
    train = data["train"]
    scores = data["scores"]
    coefs = data["coefs"]
    month_weights = data["month_weights"]
    similarity = data["similarity"]
    cluster_scores = data["cluster_scores"]
    target_audit = data["target_audit"]
    future_audit = data["future_audit"]
    split_ranges = data["split_ranges"]
    split_overlap = data["split_overlap"]
    lgbm_compare = data["lgbm_compare"]
    high_corr_pairs = data["high_corr_pairs"]

    feature_cols = [c for c in train.columns if c not in ["date", "bike_change_raw", "sample_weight"]]
    before_count = len(feature_cols) + len(REMOVED_COLS) + 2
    after_count = len(feature_cols)
    current_top = current_pairs.head(10)
    current_max = current_pairs.iloc[0]
    high_corr_09 = high_corr_pairs[high_corr_pairs["abs_correlation"] >= 0.9].copy()
    low_months = month_weights.sort_values("overall_month_weight").head(5)[["year_month", "overall_month_weight", "mean_adjacent_similarity"]]
    top_similar = similarity.sort_values(["similar_flag", "similarity_score"], ascending=[False, False]).head(12)
    valid_best = cluster_scores[cluster_scores["split"].eq("valid")].sort_values("r2", ascending=False).iloc[0]
    test_best = cluster_scores[cluster_scores["split"].eq("test")].sort_values("r2", ascending=False).iloc[0]

    lines: list[str] = []
    lines.append("# Ridge 기반 End-to-End 분석 보고서")
    lines.append("")
    lines.append("## 1. 분석 목적")
    lines.append("- 목표는 `bike_change_raw`를 예측하는 해석 가능한 회귀모델을 만드는 것입니다.")
    lines.append("- 발표에서는 `데이터 정제 -> 공선성 정리 -> 누수 점검 -> 시계열 패턴 진단 -> sample_weight 적용 -> Ridge 학습 -> 성능 검증` 순서로 설명합니다.")
    lines.append("")
    lines.append(f"![process flow]({rel(image_paths['flow'])})")
    lines.append("")
    lines.append("## 2. 데이터 구성")
    lines.append(f"- 학습 데이터: `{TRAIN_PATH.as_posix()}`")
    lines.append(f"- 테스트 데이터: `{TEST_PATH.as_posix()}`")
    lines.append(f"- 원본 canonical 컬럼 수: **{before_count}개**")
    lines.append(f"- 최종 입력 변수 수: **{after_count}개**")
    lines.append(f"- 최종 예측 타깃: `bike_change_raw`")
    lines.append("")
    lines.append(f"![feature counts]({rel(image_paths['feature_count'])})")
    lines.append("")
    lines.append("### 최종 컬럼 의미")
    lines.append(make_column_table().to_markdown(index=False))
    lines.append("")
    lines.append("## 3. 데이터 정제와 공선성 정리")
    lines.append("### 3-1. 왜 정리가 필요했는가")
    lines.append("- 초기 데이터에는 원 변수와 계절조정 변수, 여러 시차·추세 파생변수가 함께 있어 상관관계가 높은 조합이 존재했습니다.")
    lines.append("- 상관이 너무 높은 변수들을 동시에 넣으면 회귀계수 해석이 흔들리고, 학습 안정성이 떨어질 수 있습니다.")
    lines.append("")
    lines.append("### 3-2. 근거 시각화")
    lines.append("- 초기 공선성 점검 결과, `bike_change_raw`와 `bike_change_deseasonalized`의 절대 상관계수는 **0.9349**로 0.9를 넘었습니다.")
    lines.append("- 이 값은 사실상 같은 정보를 두 컬럼이 나눠 들고 있다는 뜻이라 판단했습니다.")
    lines.append("")
    lines.append(high_corr_09.to_markdown(index=False))
    lines.append("")
    lines.append(f"![high corr pairs]({rel(image_paths['high_corr'])})")
    lines.append("")
    lines.append("### 3-3. 어떤 조치를 했는가")
    lines.append(make_removed_feature_table().to_markdown(index=False))
    lines.append("")
    lines.append("### 3-4. 조치 이후 결과")
    lines.append(f"- 최종 입력 변수 기준 최대 절대 상관계수는 `{current_max['feature_a']} ↔ {current_max['feature_b']}`의 **{current_max['abs_correlation']:.4f}**였습니다.")
    lines.append("- 즉, 초기처럼 0.9를 넘는 강한 중복 구조는 최종 입력 변수에서는 남지 않았습니다.")
    lines.append("")
    lines.append(current_top.to_markdown(index=False))
    lines.append("")
    lines.append(f"![current corr heatmap]({rel(image_paths['corr_heatmap'])})")
    lines.append("")
    lines.append("## 4. 누수와 분할 오류 점검")
    lines.append("### 4-1. 무엇을 의심했는가")
    lines.append("- 높은 성능이 나왔을 때 가장 먼저 의심해야 하는 것은 타깃 누수, 미래정보 혼입, 잘못된 train/valid/test 분할입니다.")
    lines.append("- 특히 `bike_change_lag_1`, `bike_change_rollmean_24`, `bike_change_rollstd_24`, `bike_change_rollmean_168`, `bike_change_rollstd_168`는 타깃의 과거값에서 파생된 변수라 생성 로직을 확인할 필요가 있었습니다.")
    lines.append("")
    lines.append("### 4-2. 점검 결과")
    lines.append("- 과거값 기준 재계산 검증 결과, 위 5개 파생변수는 모두 **현재값이나 미래값을 쓰지 않고** 생성된 것으로 확인됐습니다.")
    lines.append("- train/valid/test는 `2023 -> 2024 -> 2025` 시간순으로 분리되어 겹치지 않았습니다.")
    lines.append("")
    lines.append(future_audit.to_markdown(index=False))
    lines.append("")
    lines.append(split_ranges.to_markdown(index=False))
    lines.append("")
    lines.append(split_overlap.to_markdown(index=False))
    lines.append("")
    lines.append(f"![target corr]({rel(AUDIT_DIR / 'target_like_feature_correlation.png')})")
    lines.append("")
    lines.append("## 5. 시계열 패턴 진단과 sample_weight 설계")
    lines.append("### 5-1. 왜 이 단계가 필요했는가")
    lines.append("- 시계열 데이터에서는 누수는 없어도, 서로 너무 비슷한 월 패턴이 반복되면 특정 구간이 학습에 과도하게 반영될 수 있습니다.")
    lines.append("- 그래서 인접한 월끼리 24시간 평균선을 비교해, 패턴이 매우 비슷한 달은 학습 가중치를 낮추는 전략을 적용했습니다.")
    lines.append("")
    lines.append("### 5-2. 월별 유사패턴 근거")
    lines.append("- `rental_count`의 `2023-05`와 `2023-06`은 `corr=0.9947`, `NRMSE=0.1074`로 매우 유사했습니다.")
    lines.append("- 이런 형태는 일부 변수에서 반복적으로 관찰됐고, 이는 같은 패턴을 여러 달이 거의 중복해서 보여준다는 뜻입니다.")
    lines.append("")
    lines.append(top_similar[["feature", "year_month_left", "year_month_right", "corr", "nrmse", "similarity_score", "similar_flag"]].to_markdown(index=False))
    lines.append("")
    lines.append(f"![similarity heatmap]({rel(image_paths['similarity_heatmap'])})")
    lines.append("")
    lines.append("### 5-3. 월별·일별·시간별 패턴 시각화")
    lines.append("- 아래 그림은 대표 예시로 `rental_count`의 두 인접 월을 비교한 것입니다.")
    lines.append("- 월 수준에서는 두 달의 전체 가중치가 비슷하게 낮아지고, 일 수준에서는 요일별 평균 패턴이 유사하며, 시간 수준에서는 24시간 평균선의 모양이 거의 겹칩니다.")
    lines.append("")
    lines.append(f"![month weights]({rel(image_paths['month_weight'])})")
    lines.append("")
    lines.append(f"![weekday compare]({rel(image_paths['weekday_compare'])})")
    lines.append("")
    lines.append(f"![hourly compare]({rel(image_paths['hourly_compare'])})")
    lines.append("")
    lines.append("### 5-4. 어떤 조치를 했는가")
    lines.append(f"- 각 월에 대해 `sample_weight`를 부여했고, 실제 범위는 **{train['sample_weight'].min():.6f} ~ {train['sample_weight'].max():.6f}**였습니다.")
    lines.append("- 패턴 유사도가 높은 달일수록 가중치를 조금 낮춰서, 중복되는 계절·시간 패턴이 학습을 과하게 지배하지 않도록 했습니다.")
    lines.append("")
    lines.append(low_months.to_markdown(index=False))
    lines.append("")
    lines.append("## 6. 데이터 분할과 모델링")
    lines.append("- 분할 방식: `train=2023`, `valid=2024`, `test=2025`")
    lines.append("- 모델: `Ridge(alpha=2.0)`")
    lines.append("- 전처리: median imputation + standardization")
    lines.append("- 학습 시 `sample_weight` 적용")
    lines.append("- 평가 지표: `RMSE`, `MAE`, `R2`")
    lines.append("")
    lines.append(f"![split counts]({rel(image_paths['split'])})")
    lines.append("")
    lines.append("## 7. 전체 Ridge 회귀 성능")
    lines.append(scores.to_markdown(index=False))
    lines.append("")
    lines.append(f"![ridge scores]({rel(image_paths['scores'])})")
    lines.append("")
    lines.append("### 성능 해석")
    train_row = scores[scores["split"].eq("train")].iloc[0]
    valid_row = scores[scores["split"].eq("valid")].iloc[0]
    test_row = scores[scores["split"].eq("test")].iloc[0]
    lines.append(f"- train R2={train_row['r2']:.6f}, valid R2={valid_row['r2']:.6f}, test R2={test_row['r2']:.6f}로 split 간 차이가 크지 않았습니다.")
    lines.append("- 즉, Ridge는 과적합이 심하지 않으면서도 설명 가능한 수준의 안정적인 성능을 보였습니다.")
    lines.append("")
    lines.append("## 8. 회귀계수 해석")
    lines.append("- 표준화 계수 기준 상위 변수는 `rental_count`, `bike_change_lag_1`, `bike_change_rollmean_24`, `bike_change_rollmean_168` 순으로 영향이 컸습니다.")
    lines.append(coefs.head(12).to_markdown(index=False))
    lines.append("")
    lines.append(f"![top coefficients]({rel(image_paths['coef'])})")
    lines.append("")
    lines.append("## 9. LightGBM 고성능에 대한 해석")
    lines.append("- LightGBM은 매우 높은 R2를 보였지만, 타깃 이력 파생변수 제거 후 성능이 크게 하락했습니다.")
    lines.append("- 따라서 LightGBM의 높은 점수는 순수한 일반화 능력만이 아니라 `강한 과거 이력 feature + 반복되는 시계열 패턴`의 영향이 크다고 해석했습니다.")
    lines.append("")
    lines.append(lgbm_compare.to_markdown(index=False))
    lines.append("")
    lines.append(f"![repeat counts]({rel(AUDIT_DIR / 'repeated_pattern_similarity_counts.png')})")
    lines.append("")
    lines.append("## 10. 클러스터별 Ridge 결과")
    lines.append(cluster_scores.sort_values(["cluster", "split"]).to_markdown(index=False))
    lines.append("")
    lines.append(f"![cluster r2]({rel(CLUSTER_DIR / 'cluster_r2_by_split.png')})")
    lines.append("")
    lines.append(f"![cluster rmse]({rel(CLUSTER_DIR / 'cluster_rmse_by_split.png')})")
    lines.append("")
    lines.append(f"- 검증 기준 최고 클러스터는 `cluster {int(valid_best['cluster'])}`로 R2={valid_best['r2']:.6f}였습니다.")
    lines.append(f"- 테스트 기준 최고 클러스터는 `cluster {int(test_best['cluster'])}`로 R2={test_best['r2']:.6f}였습니다.")
    lines.append("- `cluster 1`은 상대적으로 성능이 낮아 군집 특화 feature 보강이 필요한 구간으로 보입니다.")
    lines.append("")
    lines.append("## 11. 결론")
    lines.append("- 공선성 정리 단계에서는 고상관 변수와 중복 파생변수를 제거해 해석 가능한 회귀 구조를 확보했습니다.")
    lines.append("- 누수 점검 단계에서는 미래정보 혼입과 잘못된 분할이 없음을 확인했습니다.")
    lines.append("- 시계열 패턴 진단 단계에서는 월별·요일별·시간별 유사패턴이 반복되는 것을 확인했고, 이를 완화하기 위해 `sample_weight`를 적용했습니다.")
    lines.append("- 그 결과 Ridge는 `R2 약 0.72` 수준의 안정적이고 설명 가능한 기준 모델로 정리할 수 있었습니다.")
    lines.append("")
    lines.append("## 12. 참고 산출물")
    lines.append(f"- 선형회귀 계수: `{(LINEAR_DIR / 'linear_regression_coefficients.csv').as_posix()}`")
    lines.append(f"- 선형회귀 점수: `{(LINEAR_DIR / 'linear_regression_scores.csv').as_posix()}`")
    lines.append(f"- 월 가중치 제안: `{(SIM_DIR / 'overall_month_weight_suggestions.csv').as_posix()}`")
    lines.append(f"- 누수/분할 점검 보고서: `{(AUDIT_DIR / 'lightgbm_high_score_audit_report.md').as_posix()}`")
    lines.append(f"- LightGBM 재실험 보고서: `{(LGBM_COMPARE_DIR / 'lightgbm_without_history_report.md').as_posix()}`")
    lines.append(f"- 클러스터별 Ridge 점수: `{(CLUSTER_DIR / 'cluster_ridge_scores.csv').as_posix()}`")

    report_path = OUT_DIR / "ridge_end_to_end_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    setup_plot_style()

    data = load_inputs()
    counts = split_counts(data["train"], data["test"])
    corr, current_pairs = current_feature_corr(data["train"])

    image_paths = {
        "flow": save_process_flow(),
        "feature_count": save_feature_count_bar(before_count=26, after_count=16, removed_count=8),
        "split": save_split_bar(counts),
        "scores": save_score_bar(data["scores"]),
        "coef": save_coef_bar(data["coefs"]),
        "month_weight": save_month_weight_bar(data["month_weights"]),
        "corr_heatmap": save_current_corr_heatmap(corr),
        "high_corr": save_high_corr_bar(data["high_corr_pairs"]),
        "similarity_heatmap": save_similarity_heatmap(data["similarity"]),
        "weekday_compare": save_weekday_profile_compare(data["train"]),
        "hourly_compare": save_hourly_profile_compare(data["profiles"], data["similarity"]),
    }

    report_path = write_report(data, image_paths, corr, current_pairs)

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
