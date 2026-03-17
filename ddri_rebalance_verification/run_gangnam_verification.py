#!/usr/bin/env python3
"""강남구 재배치 검증 - 데이터 기반 재배치 시간대 추출 후 검증"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "3조 공유폴더" / "서울특별시_대여소별 공공자전거 대여가능 수량(1시간 단위)_20230331"
MAPPING_PATH = ROOT / "cheng80" / "api_output" / "ddri_full161_station_api_mapping_table.csv"
OUTPUT_DIR = ROOT / "ddri_rebalance_verification" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD_INCREASE = 8
THRESHOLD_DECREASE = -8
N_STATIONS = 161
# 출퇴근 시간대: 재배치 후보에서 제외 (7~10시 출근, 15~20시 퇴근·오후피크)
COMMUTE_HOURS = {7, 8, 9, 10, 15, 16, 17, 18, 19, 20}


def load_gangnam_station_ids():
    mapping = pd.read_csv(MAPPING_PATH, encoding="utf-8-sig")
    return set(mapping["station_id"].astype(int))


def load_monthly_data():
    gangnam_ids = load_gangnam_station_ids()
    parts = []
    for m in range(1, 13):
        path = DATA_DIR / f"22.{m:02d}.csv"
        if path.exists():
            df = pd.read_csv(path, encoding="cp949")
            df = df.rename(columns={"일시": "date", "대여소번호": "station_id", "대여소명": "station_name", "시간대": "hour", "거치대수량": "stock"})
            df["station_id"] = pd.to_numeric(df["station_id"], errors="coerce")
            df = df.dropna(subset=["station_id"]).astype({"station_id": int})
            df = df[df["station_id"].isin(gangnam_ids)]
            parts.append(df)
    for fname in ["23.01.csv", "23.02.csv", "23.03.csv"]:
        path = DATA_DIR / fname
        if path.exists():
            df = pd.read_csv(path, encoding="cp949")
            df = df.rename(columns={"일시": "date", "대여소번호": "station_id", "대여소명": "station_name", "시간대": "hour", "거치대수량": "stock"})
            df["station_id"] = pd.to_numeric(df["station_id"], errors="coerce")
            df = df.dropna(subset=["station_id"]).astype({"station_id": int})
            df = df[df["station_id"].isin(gangnam_ids)]
            parts.append(df)
    return pd.concat(parts, ignore_index=True)


def sum_positive(d):
    return d[d > 0].sum()


def sum_negative(d):
    return d[d < 0].sum()


def main():
    plt.rcParams["font.family"] = "AppleGothic"
    plt.rcParams["axes.unicode_minus"] = False

    df = load_monthly_data()
    df = df.sort_values(["station_id", "date", "hour"])
    df["prev_stock"] = df.groupby("station_id")["stock"].shift(1)
    df["delta"] = df["stock"] - df["prev_stock"]
    df = df.dropna(subset=["delta"])
    df["large_increase"] = df["delta"] >= THRESHOLD_INCREASE
    df["large_decrease"] = df["delta"] <= THRESHOLD_DECREASE
    large_events = df[df["large_increase"] | df["large_decrease"]].copy()

    inc = large_events[large_events["large_increase"]].groupby("hour")["delta"].agg(["mean", "count", "median"])
    dec = large_events[large_events["large_decrease"]].groupby("hour")["delta"].agg(["mean", "count", "median"])
    inc.columns = ["inc_mean", "inc_count", "inc_median"]
    dec.columns = ["dec_mean", "dec_count", "dec_median"]
    by_hour = df.groupby("hour").agg(
        large_increase=("large_increase", "sum"),
        large_decrease=("large_decrease", "sum"),
    ).reset_index()
    by_hour["total"] = by_hour["large_increase"] + by_hour["large_decrease"]
    by_hour = by_hour.merge(inc, on="hour", how="left").merge(dec, on="hour", how="left")

    # 데이터 기반 재배치 시간대 추출 (출퇴근 시간대 제외)
    by_hour["ratio"] = by_hour["large_increase"] / by_hour["large_decrease"].clip(lower=1)
    mask = (
        (by_hour["ratio"] >= 0.7) & (by_hour["ratio"] <= 1.3)
        & (by_hour["total"] >= 30)
        & (~by_hour["hour"].isin(COMMUTE_HOURS))
    )
    rebalance_hours = sorted(by_hour[mask]["hour"].tolist())
    print(f"데이터에서 추출한 재배치 의심 시간대: {rebalance_hours} (급증/급감 0.7~1.3, 이벤트≥30, 출퇴근 제외)")

    by_hour.to_csv(OUTPUT_DIR / "ddri_rebalance_by_hour_2022_01_2023_03.csv", index=False, encoding="utf-8-sig")

    by_station = df.groupby("station_id").agg(
        station_name=("station_name", "first"),
        large_increase=("large_increase", "sum"),
        large_decrease=("large_decrease", "sum"),
    ).reset_index()
    by_station["total"] = by_station["large_increase"] + by_station["large_decrease"]
    by_station = by_station.sort_values("total", ascending=False).head(20)
    by_station.to_csv(OUTPUT_DIR / "ddri_rebalance_by_station_top20_2022_01_2023_03.csv", index=False, encoding="utf-8-sig")

    rebal_events_for_date = large_events[
        (large_events["hour"].isin(rebalance_hours)) & (large_events["date"].notna())
    ].copy()
    rebal_events_for_date["date"] = pd.to_datetime(rebal_events_for_date["date"])
    by_date = rebal_events_for_date.groupby("date").agg(
        total_increase=("delta", sum_positive),
        total_decrease=("delta", sum_negative),
        n_increase=("large_increase", "sum"),
        n_decrease=("large_decrease", "sum"),
    ).reset_index()
    by_date["abs_decrease"] = by_date["total_decrease"].abs()
    by_date["balance_ratio"] = by_date["total_increase"] / (by_date["abs_decrease"] + 1e-9)
    by_date["imbalance"] = (by_date["total_increase"] + by_date["total_decrease"]).abs()
    by_date.to_csv(OUTPUT_DIR / "ddri_rebalance_0h_by_date_2022_01_2023_03.csv", index=False, encoding="utf-8-sig")

    # 차트 1: 선정 근거
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    rebalance_hours_set = set(rebalance_hours)
    colors = ["#1565c0" if h in rebalance_hours_set else "#90a4ae" if h in [9, 15] else "#b0bec5" for h in by_hour["hour"]]
    axes[0].bar(by_hour["hour"], by_hour["total"], color=colors, edgecolor="white")
    for h in rebalance_hours_set:
        axes[0].axvspan(h - 0.5, h + 0.5, alpha=0.15, color="#1565c0")
    axes[0].set_xlabel("시간대")
    axes[0].set_ylabel("급격한 증감 횟수")
    axes[0].set_title("강남구 시간대별 급격한 증감 횟수\n(파란색: 데이터 추출 재배치 시간대, 회색: 출퇴근 피크)")
    axes[0].set_xticks(by_hour["hour"])
    for h in rebalance_hours_set:
        row = by_hour[by_hour["hour"] == h]
        if len(row) > 0:
            axes[0].text(h, row["total"].values[0] + 15, f"{h}시", ha="center", fontsize=8, color="#1565c0")
    axes[0].grid(True, alpha=0.3, axis="y")
    ratio = by_hour["large_increase"] / by_hour["large_decrease"].clip(lower=1)
    ratio = ratio.clip(upper=5)
    axes[1].bar(by_hour["hour"], ratio, color=colors, edgecolor="white")
    axes[1].axhline(1.0, color="#2e7d32", linestyle="--", linewidth=1.5, label="1:1 균형 (쌍 이동)")
    axes[1].axhspan(0.7, 1.3, alpha=0.1, color="green")
    axes[1].set_xlabel("시간대")
    axes[1].set_ylabel("급증/급감 비율")
    axes[1].set_title("강남구 시간대별 급증/급감 비율\n(비율≈1: 재배치 의심, 비율>2: 사용자 출퇴근)")
    axes[1].set_xticks(by_hour["hour"])
    axes[1].set_ylim(0, 5)
    axes[1].legend(loc="upper right", fontsize=9)
    axes[1].grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ddri_rebalance_0h_22h_23h_selection_evidence.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 차트 2: 스캐터
    df_chart = by_date.copy()
    df_chart["date"] = pd.to_datetime(df_chart["date"])
    valid = df_chart[(df_chart["abs_decrease"] >= 20) & (df_chart["total_increase"] >= 20) & (df_chart["balance_ratio"] < 10)]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    paired = valid[(valid["balance_ratio"] >= 0.5) & (valid["balance_ratio"] <= 2.0)]
    other = valid[(valid["balance_ratio"] < 0.5) | (valid["balance_ratio"] > 2.0)]
    axes[0].scatter(other["abs_decrease"], other["total_increase"], s=80, alpha=0.7, c="#999999", label="쌍 이동 아님")
    axes[0].scatter(paired["abs_decrease"], paired["total_increase"], s=100, alpha=0.8, c="#2e7d32", label="쌍 이동 가능 (0.5~2.0)")
    if len(valid) > 0:
        lim_max = max(valid["abs_decrease"].max(), valid["total_increase"].max()) * 1.05
        axes[0].plot([0, lim_max], [0, lim_max], "k--", linewidth=1.5, alpha=0.7, label="y=x (급증합=급감합)")
        for _, row in paired.iterrows():
            axes[0].annotate(row["date"].strftime("%m/%d"), (row["abs_decrease"], row["total_increase"]), fontsize=8, xytext=(5, 5), textcoords="offset points")
        axes[0].set_xlim(0, lim_max)
        axes[0].set_ylim(0, lim_max)
    axes[0].set_xlabel("급감합 (절대값, 대)")
    axes[0].set_ylabel("급증합 (대)")
    axes[0].set_title("강남구 재배치 시간대 일별 급증합 vs 급감합\n(y=x에 가까우면 트럭 A→B 쌍 이동)")
    axes[0].legend(loc="upper left", fontsize=9)
    axes[0].set_aspect("equal")
    axes[0].grid(True, alpha=0.3)
    all_valid = df_chart[(df_chart["balance_ratio"] > 0) & (df_chart["balance_ratio"] < 10)].copy()
    all_valid.loc[:, "paired"] = (all_valid["balance_ratio"] >= 0.5) & (all_valid["balance_ratio"] <= 2.0)
    colors = ["#2e7d32" if p else "#999999" for p in all_valid["paired"]]
    axes[1].scatter(all_valid["date"], all_valid["balance_ratio"], s=70, c=colors, alpha=0.8, edgecolor="white", linewidth=0.5)
    axes[1].axhline(1.0, color="#1565c0", linestyle="-", linewidth=1.5, label="balance=1 (완전 쌍 이동)")
    axes[1].axhspan(0.5, 2.0, alpha=0.12, color="green", label="쌍 이동 가능 구간 (0.5~2.0)")
    axes[1].set_xlabel("날짜")
    axes[1].set_ylabel("balance_ratio (급증합/급감합)")
    axes[1].set_title("강남구 재배치 시간대 일별 balance_ratio\n(1에 가까울수록 쌍 이동)")
    axes[1].legend(loc="upper right", fontsize=9)
    axes[1].set_ylim(0, 3.5)
    axes[1].grid(True, alpha=0.3)
    plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=30)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ddri_rebalance_verification_scatter.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 차트 3: 히트맵
    rebal_events = large_events[large_events["hour"].isin(rebalance_hours)].copy()
    rebal_events["date"] = pd.to_datetime(rebal_events["date"])
    rebal_dates = rebal_events.groupby(rebal_events["date"].dt.date).size().reset_index(name="n")
    rebal_dates["date"] = pd.to_datetime(rebal_dates["date"])
    rebal_dates["month"] = rebal_dates["date"].dt.to_period("M")
    rebal_dates["day"] = rebal_dates["date"].dt.day
    months = sorted(rebal_dates["month"].unique())
    heatmap_data = []
    for m in months:
        row = [0] * 31
        for d in rebal_dates[rebal_dates["month"] == m]["day"].tolist():
            row[d - 1] = 1
        heatmap_data.append(row)
    arr = np.array(heatmap_data)
    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(arr, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
    ax.set_yticks(range(len(months)))
    ax.set_yticklabels([str(m) for m in months], fontsize=9)
    ax.set_xticks(range(0, 31, 2))
    ax.set_xticklabels(range(1, 32, 2))
    ax.set_xlabel("일 (1~31)")
    ax.set_ylabel("월")
    ax.set_title("강남구 재배치 발생 날짜 (월별)\n색: 해당 일에 재배치 이벤트 있음")
    ax.set_xlim(-0.5, 30.5)
    plt.colorbar(im, ax=ax, label="이벤트 있음(1)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ddri_rebalance_0h_22h_23h_by_month_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 스테이션별 분포
    rebal = large_events[large_events["hour"].isin(rebalance_hours)]
    by_st_rebal = rebal.groupby("station_id").size().reset_index(name="count")
    st_names = df.groupby("station_id")["station_name"].first().reset_index()
    by_st_rebal = by_st_rebal.merge(st_names, on="station_id", how="left")
    by_st_rebal = by_st_rebal.sort_values("count", ascending=False)
    by_st_rebal.to_csv(OUTPUT_DIR / "ddri_rebalance_0h_22h_23h_by_station.csv", index=False, encoding="utf-8-sig")

    n_st = len(by_st_rebal)
    total_ev = by_st_rebal["count"].sum()
    top10_share = by_st_rebal.head(10)["count"].sum() / total_ev * 100 if total_ev > 0 else 0
    p = by_st_rebal["count"] / total_ev if total_ev > 0 else by_st_rebal["count"] * 0
    hhi = (p ** 2).sum() * 10000 if total_ev > 0 else 0

    # 차트 4: 스테이션 빈도
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    top20 = by_st_rebal.head(20)
    def short_label(row):
        s = str(row["station_name"]).split(". ", 1)[-1] if ". " in str(row["station_name"]) else str(row["station_name"])
        return f"{row['station_id']} {s[:10]}…" if len(s) > 10 else f"{row['station_id']} {s}"
    labels = [short_label(row) for _, row in top20.iterrows()]
    axes[0].barh(range(len(top20)), top20["count"].values, color="#1565c0", alpha=0.85, edgecolor="white")
    axes[0].set_yticks(range(len(top20)))
    axes[0].set_yticklabels(labels, fontsize=8)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("재배치 이벤트 수")
    axes[0].set_title("강남구 상위 20개 스테이션 재배치 빈도")
    axes[0].grid(True, alpha=0.3, axis="x")
    if by_st_rebal["count"].max() >= 1:
        axes[1].hist(by_st_rebal["count"], bins=range(1, int(by_st_rebal["count"].max()) + 2), color="#1565c0", alpha=0.85, edgecolor="white")
    axes[1].set_xlabel("재배치 이벤트 수")
    axes[1].set_ylabel("스테이션 수")
    axes[1].set_title("강남구 이벤트 수 분포 (골고루 정도)\n대부분 1~10회 구간에 분포")
    axes[1].grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ddri_rebalance_station_frequency.png", dpi=150, bbox_inches="tight")
    plt.close()

    print("=== 강남구 재배치 검증 완료 ===")
    print(f"이벤트 있는 스테이션: {n_st} / {N_STATIONS}")
    print(f"총 이벤트: {total_ev}")
    print(f"상위 10개 점유율: {top10_share:.1f}%")
    print(f"HHI: {hhi:.0f}")
    for f in sorted(OUTPUT_DIR.glob("*")):
        if f.is_file():
            print(f"  - {f.name}")


if __name__ == "__main__":
    main()
