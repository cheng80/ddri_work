from pathlib import Path

import koreanize_matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path("/Users/cheng80/Desktop/ddri_work")
DATA_DIR = BASE_DIR / "works" / "03_prediction" / "02_data"
IMG_DIR = BASE_DIR / "works" / "03_prediction" / "03_images"
IMG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False
sns.set_theme(style="whitegrid", font="AppleGothic")


def load_labeled_frames():
    frames = []
    for dataset_name, path in [
        ("학습(2023~2024)", DATA_DIR / "ddri_station_day_train_baseline_dataset.csv"),
        ("테스트(2025)", DATA_DIR / "ddri_station_day_test_baseline_dataset.csv"),
    ]:
        df = pd.read_csv(path)
        df["dataset"] = dataset_name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def build_summary_chart(df: pd.DataFrame) -> None:
    summary = (
        df.groupby("dataset")
        .agg(
            평균_대여량=("rental_count", "mean"),
            평균_반납량=("return_count", "mean"),
            평균_self_return_비율=("same_station_return_ratio", "mean"),
            평균_순유출입=("net_flow", "mean"),
        )
        .reset_index()
    )
    long_summary = summary.melt(id_vars="dataset", var_name="지표", value_name="값")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=160)

    sns.barplot(data=long_summary, x="지표", y="값", hue="dataset", ax=axes[0])
    axes[0].set_title("학습/테스트 운영 보조 지표 평균 비교")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("평균값")
    axes[0].tick_params(axis="x", rotation=15)
    axes[0].legend(title="데이터셋")

    flow_df = df.copy()
    flow_df["net_flow_clipped"] = flow_df["net_flow"].clip(-20, 20)
    sns.histplot(
        data=flow_df,
        x="net_flow_clipped",
        hue="dataset",
        bins=41,
        stat="density",
        common_norm=False,
        alpha=0.45,
        ax=axes[1],
    )
    axes[1].set_title("순유출입(net flow) 분포 비교")
    axes[1].set_xlabel("순유출입 (20 이하/이상 구간 절단)")
    axes[1].set_ylabel("밀도")

    plt.tight_layout()
    fig.savefig(IMG_DIR / "ddri_flow_metrics_summary.png", bbox_inches="tight")
    plt.close(fig)


def build_ratio_boxplot(df: pd.DataFrame) -> None:
    plot_df = df.copy()
    plot_df["same_station_return_ratio_capped"] = plot_df["same_station_return_ratio"].clip(upper=0.6)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=160)
    sns.boxplot(
        data=plot_df,
        x="dataset",
        y="same_station_return_ratio_capped",
        hue="dataset",
        palette=["#4e79a7", "#e15759"],
        legend=False,
        ax=ax,
    )
    ax.set_title("동일 대여소 반납 비율 분포")
    ax.set_xlabel("")
    ax.set_ylabel("same_station_return_ratio (0.6 상한 표시)")
    plt.tight_layout()
    fig.savefig(IMG_DIR / "ddri_same_station_return_ratio_boxplot.png", bbox_inches="tight")
    plt.close(fig)


def build_correlation_heatmap(df: pd.DataFrame) -> None:
    corr_cols = [
        "rental_count",
        "return_count",
        "same_station_return_ratio",
        "net_flow",
        "temperature_mean",
        "humidity_mean",
        "precipitation_sum",
    ]
    label_map = {
        "rental_count": "대여량",
        "return_count": "반납량",
        "same_station_return_ratio": "self-return 비율",
        "net_flow": "순유출입",
        "temperature_mean": "평균 기온",
        "humidity_mean": "평균 습도",
        "precipitation_sum": "강수량 합",
    }
    corr_df = df[corr_cols].corr().round(2).rename(index=label_map, columns=label_map)

    fig, ax = plt.subplots(figsize=(8, 6), dpi=160)
    sns.heatmap(corr_df, annot=True, cmap="YlGnBu", fmt=".2f", linewidths=0.5, ax=ax)
    ax.set_title("예측 입력/운영 지표 상관관계 히트맵")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.tight_layout()
    fig.savefig(IMG_DIR / "ddri_prediction_feature_correlation_heatmap.png", bbox_inches="tight")
    plt.close(fig)


def build_holiday_weekend_comparison(df: pd.DataFrame) -> None:
    holiday_df = (
        df.groupby("is_holiday")["rental_count"]
        .mean()
        .reset_index()
        .replace({"is_holiday": {0: "비공휴일", 1: "공휴일"}})
        .rename(columns={"is_holiday": "구분", "rental_count": "평균 대여량"})
    )
    weekend_df = (
        df.groupby("is_weekend")["rental_count"]
        .mean()
        .reset_index()
        .replace({"is_weekend": {0: "평일", 1: "주말"}})
        .rename(columns={"is_weekend": "구분", "rental_count": "평균 대여량"})
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), dpi=160)
    sns.barplot(data=holiday_df, x="구분", y="평균 대여량", hue="구분", palette="Set2", legend=False, ax=axes[0])
    axes[0].set_title("공휴일/비공휴일 평균 대여량")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("평균 대여량")
    sns.barplot(data=weekend_df, x="구분", y="평균 대여량", hue="구분", palette="Set3", legend=False, ax=axes[1])
    axes[1].set_title("평일/주말 평균 대여량")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("평균 대여량")
    plt.tight_layout()
    fig.savefig(IMG_DIR / "ddri_holiday_weekend_rental_comparison.png", bbox_inches="tight")
    plt.close(fig)


def build_monthly_target_trend(df: pd.DataFrame) -> None:
    plot_df = df.copy()
    plot_df["date"] = pd.to_datetime(plot_df["date"])
    plot_df["month"] = plot_df["date"].dt.to_period("M").astype(str)
    monthly = (
        plot_df.groupby(["dataset", "month"])["rental_count"]
        .mean()
        .reset_index(name="avg_rental_count")
    )

    fig, ax = plt.subplots(figsize=(14, 4.5), dpi=160)
    sns.lineplot(data=monthly, x="month", y="avg_rental_count", hue="dataset", marker="o", ax=ax)
    ax.set_title("월별 평균 대여량 추이")
    ax.set_xlabel("월")
    ax.set_ylabel("평균 대여량")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="데이터셋")
    plt.tight_layout()
    fig.savefig(IMG_DIR / "ddri_monthly_avg_rental_trend.png", bbox_inches="tight")
    plt.close(fig)


def main():
    df = load_labeled_frames()
    build_summary_chart(df)
    build_ratio_boxplot(df)
    build_correlation_heatmap(df)
    build_holiday_weekend_comparison(df)
    build_monthly_target_trend(df)


if __name__ == "__main__":
    main()
