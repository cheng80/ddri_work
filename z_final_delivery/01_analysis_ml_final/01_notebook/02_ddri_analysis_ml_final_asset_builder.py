from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = BASE_DIR / "02_input_data"
OUTPUT_DIR = BASE_DIR / "03_output_data"
FONT_PATH = BASE_DIR / "05_fonts" / "AppleGothic.ttf"


def configure_font() -> None:
    if FONT_PATH.exists():
        fm.fontManager.addfont(str(FONT_PATH))
        plt.rcParams["font.family"] = "AppleGothic"
    plt.rcParams["axes.unicode_minus"] = False


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def normalize_bilingual_label(text: str) -> str:
    if " / " not in text:
        return text
    ko, en = text.split(" / ", 1)
    ko = ko.strip()
    en = en.strip()
    if not en or ko == en:
        return ko
    return f"{ko}\n({en})"


def wrap_label(text: str) -> str:
    return normalize_bilingual_label(text)


def save_delta_chart(
    df: pd.DataFrame,
    output_path: Path,
    title_ko: str,
    title_en: str,
    delta_col: str = "최선 대비 차이 x1000(delta_x1000)",
    colors: Iterable[str] | None = None,
) -> None:
    labels = [wrap_label(x) for x in df["표시명(label)"]]
    plot_colors = list(colors) if colors is not None else ["#94a3b8"] * len(df)

    fig, ax_chart = plt.subplots(figsize=(15.5, 6.8))
    y = np.arange(len(df))
    delta_values = df[delta_col].astype(float).to_numpy()
    ax_chart.barh(y, delta_values, color=plot_colors, height=0.68)
    ax_chart.set_yticks(y)
    ax_chart.set_yticklabels(labels, fontsize=13)
    ax_chart.invert_yaxis()
    ax_chart.set_xlabel("최선 대비 차이 x1000(delta_x1000)")
    ax_chart.set_title(f"{title_ko}\n{title_en}", fontsize=22)
    ax_chart.grid(axis="x", color="#cbd5e1", linewidth=1, alpha=0.9)
    ax_chart.set_axisbelow(True)
    max_delta = max(delta_values.max(), 0.1)
    ax_chart.set_xlim(0, max_delta * 1.18)
    for i, v in enumerate(delta_values):
        ax_chart.text(v + max_delta * 0.02, i, f"Δ={v:.1f}", va="center", fontsize=13, color="#334155")

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_rmse_chart(
    df: pd.DataFrame,
    output_path: Path,
    title_ko: str,
    title_en: str,
    rmse_col: str = "테스트 RMSE(test_rmse)",
    label_col: str = "표시명(label)",
    colors: Iterable[str] | None = None,
) -> None:
    """RMSE 값을 0.01 단위 눈금으로 표시하는 차트."""
    labels = [wrap_label(x) for x in df[label_col]]
    rmse_values = df[rmse_col].astype(float).to_numpy()
    plot_colors = list(colors) if colors is not None else ["#94a3b8"] * len(df)

    fig, ax = plt.subplots(figsize=(15.5, 6.8))
    y = np.arange(len(df))
    ax.barh(y, rmse_values, color=plot_colors, height=0.68)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=13)
    ax.invert_yaxis()
    ax.set_xlabel("테스트 오차 RMSE", fontsize=14)
    ax.set_title(f"{title_ko}\n{title_en}", fontsize=22)
    ax.grid(axis="x", color="#cbd5e1", linewidth=1, alpha=0.9)
    ax.set_axisbelow(True)

    # RMSE 0.01 단위 눈금 (범위가 크면 0.05)
    v_min, v_max = rmse_values.min(), rmse_values.max()
    rng = v_max - v_min
    tick = 0.01 if rng <= 0.05 else (0.05 if rng <= 0.3 else 0.1)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(tick))
    pad = max(0.02, rng * 0.15)
    ax.set_xlim(max(0, v_min - pad), v_max + pad * 2)

    for i, v in enumerate(rmse_values):
        fmt = ".4f" if v < 0.1 else ".3f"
        ax.text(v + pad * 0.3, i, f"{v:{fmt}}", va="center", fontsize=13, color="#334155")

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_rep15_chart() -> None:
    df = read_csv(OUTPUT_DIR / "ddri_analysis_ml_final_rep15_metrics.csv")
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"]
    save_rmse_chart(
        df,
        OUTPUT_DIR / "ddri_analysis_ml_final_rep15_test_rmse.png",
        "대표 15개 테스트 오차",
        "Representative 15 Test RMSE",
        colors=colors,
    )


def build_full161_chart() -> None:
    df = read_csv(OUTPUT_DIR / "ddri_analysis_ml_final_full161_metrics.csv")
    colors = ["#10b981"] + ["#94a3b8"] * (len(df) - 1)
    save_rmse_chart(
        df,
        OUTPUT_DIR / "ddri_analysis_ml_final_full161_test_rmse.png",
        "강남구 161개 테스트 오차",
        "Gangnam 161 Test RMSE",
        colors=colors,
    )


def build_routing_chart() -> None:
    df = read_csv(OUTPUT_DIR / "ddri_analysis_ml_final_full161_metrics.csv")
    keep = [
        "full161_static_weather_full",
        "full161_partial_routing",
        "full161_exact_cluster_routing_weather_full",
        "full161_static_routing",
        "full161_exact_cluster_routing",
    ]
    df = df[df["구분(track)"].isin(keep)].copy()
    df = df.sort_values("테스트 RMSE(test_rmse)")
    colors = ["#10b981"] + ["#ef4444"] * (len(df) - 1)
    save_rmse_chart(
        df,
        OUTPUT_DIR / "ddri_analysis_ml_final_routing_vs_single_test_rmse.png",
        "단일 최종안 vs 군집 분기 테스트 오차",
        "Single Best vs Routing Test RMSE",
        colors=colors,
    )


def build_weather_chart() -> None:
    subset_df = read_csv(INPUT_DIR / "ddri_full_weather_interaction_subset_comparison_metrics.csv")
    subset_df = subset_df[subset_df["split"] == "test_2025_refit"].copy()
    subset_df = subset_df.rename(columns={"feature_set": "model_key"})

    weight_df = read_csv(INPUT_DIR / "ddri_full_static_weather_weighting_metrics.csv")
    weight_df = weight_df[weight_df["split"] == "test_2025_refit"].copy()
    weight_df = weight_df.rename(columns={"model": "model_key"})

    rows = [
        ("weather_full", "전체 날씨 상호작용 / weather_full", "weather_full", "대표 개선안"),
        ("weather_time_band_core", "시간대 핵심 조합 / weather_time_band_core", "weather_time_band_core", "시간대 축소안"),
        ("weather_commute_core", "출퇴근 핵심 조합 / weather_commute_core", "weather_commute_core", "출퇴근 축소안"),
        ("weather_precip_intensity_core", "강수 강도 핵심 조합 / weather_precip_intensity_core", "weather_precip_intensity_core", "강수 강도 축소안"),
        ("static_enriched_base", "정적 피처 기준선 / static_enriched_base", "static_enriched_base", "정적 피처 기준선"),
        ("weather_full_weight_simple", "단순 가중치 / weather_full_weight_simple", "weather_full_weight_simple", "단순 가중치"),
        ("weather_full_weight_monthly", "월별 가중치 / weather_full_weight_monthly", "weather_full_weight_monthly", "월별 가중치"),
    ]

    records = []
    for key, label, lookup_key, note in rows:
        if lookup_key.startswith("weather_full_weight"):
            row = weight_df[weight_df["model_key"] == lookup_key].iloc[0]
        else:
            row = subset_df[subset_df["model_key"] == lookup_key].iloc[0]
        records.append(
            {
                "표시명(label)": label,
                "모델(model)": lookup_key,
                "테스트 RMSE(test_rmse)": float(row["rmse"]),
                "비고(note)": note,
            }
        )
    df = pd.DataFrame.from_records(records).sort_values("테스트 RMSE(test_rmse)")
    df["표시명(label)"] = [
        "전체 날씨 상호작용",
        "시간대 핵심 조합",
        "출퇴근 핵심 조합",
        "강수 강도 핵심 조합",
        "정적 피처 기준선",
        "단순 가중치",
        "월별 가중치",
    ]
    colors = ["#10b981"] + ["#94a3b8"] * (len(df) - 1)
    save_rmse_chart(
        df,
        OUTPUT_DIR / "ddri_analysis_ml_final_weather_interaction_test_rmse.png",
        "날씨 상호작용 피처 테스트 오차",
        "Weather Interaction Test RMSE",
        colors=colors,
    )


def build_peak_chart() -> None:
    df = read_csv(INPUT_DIR / "ddri_full_top5_station_peak_error_hours.csv")
    df["station_name"] = df["station_name"].astype(str).str.strip()
    df = df[df["peak_rank"].astype(int) <= 3].copy()
    df["label"] = df["station_name"] + "\n" + df["hour"].astype(str) + "시"

    mae_df = df.sort_values("mae", ascending=True)
    gap_df = df.sort_values("gap_mean", ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(22, 10.5))

    mae_colors = ["#ef4444" if x < 0 else "#3b82f6" for x in mae_df["gap_mean"]]
    axes[0].barh(mae_df["label"], mae_df["mae"], color=mae_colors)
    axes[0].set_title("상위 오류 스테이션 피크 시간 MAE\nPeak Hour MAE", fontsize=22)
    axes[0].set_xlabel("평균절대오차(mae)")
    axes[0].grid(axis="x", color="#cbd5e1", linewidth=1, alpha=0.9)
    axes[0].set_axisbelow(True)
    for i, v in enumerate(mae_df["mae"]):
        axes[0].text(v + 0.03, i, f"{v:.3f}", va="center", fontsize=12)

    gap_colors = ["#ef4444" if x < 0 else "#3b82f6" for x in gap_df["gap_mean"]]
    axes[1].barh(gap_df["label"], gap_df["gap_mean"], color=gap_colors)
    axes[1].set_title("상위 오류 스테이션 과대/과소 방향\nMean Gap (gap_mean)", fontsize=22)
    axes[1].set_xlabel("평균 차이(gap_mean)")
    axes[1].grid(axis="x", color="#cbd5e1", linewidth=1, alpha=0.9)
    axes[1].set_axisbelow(True)
    axes[1].set_xlim(-0.6, 0.8)
    for i, v in enumerate(gap_df["gap_mean"]):
        if v < 0:
            axes[1].text(v - 0.03, i, f"{v:.3f}", va="center", ha="right", fontsize=12)
        else:
            axes[1].text(v + 0.03, i, f"{v:.3f}", va="center", ha="left", fontsize=12)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "ddri_analysis_ml_final_top5_peak_error_hours.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_role_chart() -> None:
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.axis("off")

    box_style = dict(boxstyle="round,pad=0.6", fc="#f8fafc", ec="#334155", lw=1.5)
    ax.text(0.2, 0.62, "15개 대표 스테이션\n(군집 해석 / 피처 발굴)", ha="center", va="center", fontsize=14, bbox=box_style)
    ax.text(0.5, 0.62, "최종 분석 통합\n(근거 문서 + 정본 노트북)", ha="center", va="center", fontsize=14, bbox=box_style)
    ax.text(0.8, 0.62, "161개 전체 스테이션\n(운영 모델 결정)", ha="center", va="center", fontsize=14, bbox=box_style)
    ax.annotate("", xy=(0.38, 0.62), xytext=(0.28, 0.62), arrowprops=dict(arrowstyle="->", lw=2, color="#64748b"))
    ax.annotate("", xy=(0.62, 0.62), xytext=(0.72, 0.62), arrowprops=dict(arrowstyle="->", lw=2, color="#64748b"))
    ax.text(0.2, 0.32, "역할: 탐색 / 설명", ha="center", fontsize=12, color="#475569")
    ax.text(0.8, 0.32, "역할: 운영 / 서비스", ha="center", fontsize=12, color="#475569")
    ax.text(0.5, 0.16, "최종 운영안: static enriched + weather_full interaction", ha="center", fontsize=13, color="#065f46")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "ddri_analysis_ml_final_role_structure.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    configure_font()
    build_rep15_chart()
    build_full161_chart()
    build_routing_chart()
    build_weather_chart()
    build_peak_chart()
    build_role_chart()
    print("rebuilt all analysis final images")


if __name__ == "__main__":
    main()
