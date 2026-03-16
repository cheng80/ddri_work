from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np


BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "support_assets"
FONT_PATH = Path("/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/05_fonts/AppleGothic.ttf")


def configure_font() -> None:
    ASSET_DIR.mkdir(exist_ok=True)
    if FONT_PATH.exists():
        fm.fontManager.addfont(str(FONT_PATH))
        plt.rcParams["font.family"] = "AppleGothic"
    plt.rcParams["axes.unicode_minus"] = False


def build_rep15_summary() -> None:
    labels = ["주거 도착형 최선", "15개 기준선", "아침 도착 업무"]
    values = [0.799, 0.920, 1.311]
    notes = ["cluster02 + Poisson", "정적 피처 기준", "가장 어려운 군집"]
    colors = ["#16a34a", "#f59e0b", "#2563eb"]

    fig, ax = plt.subplots(figsize=(7.0, 8.8))
    fig.patch.set_facecolor("#f8fafc")
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, height=0.56)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=14)
    ax.invert_yaxis()
    ax.set_title("대표 15개 핵심 결과\nRepresentative 15 Key Results", fontsize=22, pad=14)
    ax.set_xlabel("테스트 오차 RMSE", fontsize=13)
    ax.grid(axis="x", color="#cbd5e1", linewidth=1, alpha=0.9)
    ax.set_axisbelow(True)
    ax.set_xlim(0, 1.45)

    for bar, value, note in zip(bars, values, notes):
        ax.text(value + 0.03, bar.get_y() + bar.get_height() / 2, f"{value:.3f}\n{note}", va="center", fontsize=12, color="#334155")

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    fig.savefig(ASSET_DIR / "ddri_ml_report_2page_rep15_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_final_model_summary() -> None:
    labels = ["최종 채택안", "군집별 정적 강조", "정적 피처만", "원본 기준선", "군집별 분기"]
    values = [0.8604, 0.8615, 0.8620, 0.8624, 0.8677]
    notes = ["정적+날씨×시간대", "소폭 개선", "정적 복원 효과", "원본 기준선", "일반화 실패"]
    colors = ["#16a34a", "#3b82f6", "#94a3b8", "#cbd5e1", "#ef4444"]

    fig, ax = plt.subplots(figsize=(7.0, 8.8))
    fig.patch.set_facecolor("#f8fafc")
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, height=0.52)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=13)
    ax.invert_yaxis()
    ax.set_title("161개 운영 모델 비교\nFinal 161 Model Comparison", fontsize=22, pad=14)
    ax.set_xlabel("테스트 오차 RMSE", fontsize=13)
    ax.grid(axis="x", color="#cbd5e1", linewidth=1, alpha=0.9)
    ax.set_axisbelow(True)
    ax.set_xlim(0.858, 0.8705)

    for bar, value, note in zip(bars, values, notes):
        ax.text(value + 0.00018, bar.get_y() + bar.get_height() / 2, f"{value:.4f}\n{note}", va="center", fontsize=11, color="#334155")

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    fig.savefig(ASSET_DIR / "ddri_ml_report_2page_final_model_summary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    configure_font()
    build_rep15_summary()
    build_final_model_summary()
    print("built 2page summary assets")


if __name__ == "__main__":
    main()
