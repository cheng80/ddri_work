from __future__ import annotations

import json
import os
from pathlib import Path
from contextlib import contextmanager

import nbformat
import pandas as pd
from IPython.display import display


ROOT = Path(__file__).resolve().parents[2]
HMW3_DIR = ROOT / "hmw3"
DATA_DIR = HMW3_DIR / "Data"
NOTE_DIR = HMW3_DIR / "Note"
SOURCE_PATH = ROOT / "3조 공유폴더" / "station_hour_bike_flow_2023_2025.csv"
TEMPLATE_NOTEBOOK = NOTE_DIR / "hmw2340.ipynb"


def load_top20_station_ids() -> list[int]:
    df = pd.read_csv(SOURCE_PATH)
    usage = (
        df.assign(total=df["rental_count"].fillna(0) + df["return_count"].fillna(0))
        .groupby("station_id", as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
        .head(20)
    )
    return usage["station_id"].astype(int).tolist()


def extract_station_csv(source_df: pd.DataFrame, station_id: int) -> Path:
    output_path = DATA_DIR / f"station_{station_id}.csv"
    station_df = source_df.loc[source_df["station_id"] == station_id].copy()
    station_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def create_station_notebook(station_id: int) -> Path:
    output_path = NOTE_DIR / f"hmw{station_id}.ipynb"
    if output_path.exists():
        return output_path

    raw_text = TEMPLATE_NOTEBOOK.read_text(encoding="utf-8")
    raw_text = raw_text.replace("2340", str(station_id))
    output_path.write_text(raw_text, encoding="utf-8")
    return output_path


@contextmanager
def pushd(path: Path):
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def execute_notebook(notebook_path: Path) -> None:
    with notebook_path.open("r", encoding="utf-8") as handle:
        notebook = nbformat.read(handle, as_version=4)

    namespace: dict[str, object] = {"__name__": "__main__", "display": display}
    with pushd(NOTE_DIR):
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            source = cell.source.strip()
            if not source:
                continue
            exec(compile(source, f"{notebook_path.name}", "exec"), namespace)


def collect_metrics(station_ids: list[int]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for station_id in station_ids:
        metric_path = DATA_DIR / f"station_{station_id}_offday_month_ridge_metrics.csv"
        metric_df = pd.read_csv(metric_path)
        metric_df.insert(0, "station_id", station_id)
        frames.append(metric_df)
    summary_df = pd.concat(frames, ignore_index=True)
    summary_df.to_csv(DATA_DIR / "top20_station_metrics_summary.csv", index=False, encoding="utf-8-sig")
    return summary_df


def create_integrated_notebook(station_ids: list[int]) -> Path:
    notebook_path = NOTE_DIR / "hmw_top20_station_integrated_comparison.ipynb"

    intro_md = nbformat.v4.new_markdown_cell(
        "# Top 20 Station Integrated Comparison\n\n"
        "이 노트북은 사용량 상위 20개 station에 대해 동일한 패턴 기반 회귀 모델 결과를 한 번에 비교합니다."
    )

    setup_code = nbformat.v4.new_code_cell(
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "import numpy as np\n"
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n"
        "\n"
        "plt.style.use('seaborn-v0_8-whitegrid')\n"
        "sns.set_palette('Set2')\n"
        "ROOT = Path.cwd().resolve().parents[0]\n"
        "DATA_DIR = ROOT / 'Data'\n"
        f"TOP20_STATIONS = {station_ids}\n"
    )

    metrics_code = nbformat.v4.new_code_cell(
        "metrics_df = pd.read_csv(DATA_DIR / 'top20_station_metrics_summary.csv')\n"
        "metrics_df"
    )

    metric_plot_code = nbformat.v4.new_code_cell(
        "targets = ['rental_count', 'return_count']\n"
        "for target in targets:\n"
        "    view = metrics_df[metrics_df['target'] == target].copy()\n"
        "    pivot_r2 = view.pivot(index='station_id', columns='split', values='r2').reindex(TOP20_STATIONS)\n"
        "    pivot_rmse = view.pivot(index='station_id', columns='split', values='rmse').reindex(TOP20_STATIONS)\n"
        "    fig, axes = plt.subplots(1, 2, figsize=(18, 6))\n"
        "    pivot_r2[['train', 'valid', 'test']].plot(kind='bar', ax=axes[0])\n"
        "    axes[0].set_title(f'{target} R² Comparison')\n"
        "    axes[0].set_xlabel('station_id')\n"
        "    axes[0].set_ylabel('R²')\n"
        "    pivot_rmse[['train', 'valid', 'test']].plot(kind='bar', ax=axes[1])\n"
        "    axes[1].set_title(f'{target} RMSE Comparison')\n"
        "    axes[1].set_xlabel('station_id')\n"
        "    axes[1].set_ylabel('RMSE')\n"
        "    plt.tight_layout()\n"
        "    plt.show()\n"
    )

    importance_code = nbformat.v4.new_code_cell(
        "importance_frames = []\n"
        "for station_id in TOP20_STATIONS:\n"
        "    path = DATA_DIR / f'station_{station_id}_feature_importance.csv'\n"
        "    df = pd.read_csv(path)\n"
        "    df['station_id'] = station_id\n"
        "    importance_frames.append(df)\n"
        "importance_df = pd.concat(importance_frames, ignore_index=True)\n"
        "importance_df.head()"
    )

    importance_plot_code = nbformat.v4.new_code_cell(
        "for target in ['rental_count', 'return_count']:\n"
        "    target_df = importance_df[importance_df['target'] == target].copy()\n"
        "    summary = (\n"
        "        target_df.groupby('feature', as_index=False)['importance_ratio']\n"
        "        .mean()\n"
        "        .sort_values('importance_ratio', ascending=False)\n"
        "    )\n"
        "    plt.figure(figsize=(10, 5))\n"
        "    sns.barplot(data=summary, x='importance_ratio', y='feature')\n"
        "    plt.title(f'Average Feature Importance Across Top 20 Stations: {target}')\n"
        "    plt.xlabel('Average Importance')\n"
        "    plt.ylabel('Feature')\n"
        "    plt.tight_layout()\n"
        "    plt.show()\n"
    )

    test_prediction_code = nbformat.v4.new_code_cell(
        "comparison_frames = []\n"
        "for station_id in TOP20_STATIONS:\n"
        "    path = DATA_DIR / f'station_{station_id}_year_actual_vs_regression_vs_ml.csv'\n"
        "    df = pd.read_csv(path)\n"
        "    df['station_id'] = station_id\n"
        "    comparison_frames.append(df)\n"
        "comparison_df = pd.concat(comparison_frames, ignore_index=True)\n"
        "comparison_df.head()"
    )

    year_pattern_plot_code = nbformat.v4.new_code_cell(
        "for target in ['rental_count', 'return_count']:\n"
        "    target_df = comparison_df[(comparison_df['target'] == target) & (comparison_df['granularity'] == 'hour')].copy()\n"
        "    yearly = (\n"
        "        target_df.pivot_table(index=['station_id', 'year', 'key'], columns='series', values='value', aggfunc='mean')\n"
        "        .reset_index()\n"
        "    )\n"
        "    fig, axes = plt.subplots(4, 5, figsize=(22, 16), sharex=True, sharey=True)\n"
        "    axes = axes.flatten()\n"
        "    for ax, station_id in zip(axes, TOP20_STATIONS):\n"
        "        station_df = yearly[yearly['station_id'] == station_id]\n"
        "        for year in sorted(station_df['year'].dropna().unique()):\n"
        "            part = station_df[station_df['year'] == year]\n"
        "            ax.plot(part['key'], part['actual_value'], label=f'{int(year)} actual')\n"
        "            ax.plot(part['key'], part['prediction'], linestyle='--', label=f'{int(year)} pred')\n"
        "        ax.set_title(f'Station {station_id}')\n"
        "    for ax in axes[len(TOP20_STATIONS):]:\n"
        "        ax.axis('off')\n"
        "    handles, labels = axes[0].get_legend_handles_labels()\n"
        "    fig.legend(handles, labels, loc='upper center', ncol=3)\n"
        "    fig.suptitle(f'Hourly Actual vs Prediction by Year: {target}', y=0.995)\n"
        "    plt.tight_layout(rect=[0, 0, 1, 0.97])\n"
        "    plt.show()\n"
    )

    ranking_md = nbformat.v4.new_markdown_cell(
        "## Test R² Integrated Ranking\n\n"
        "`rental_count`와 `return_count`의 test R²를 평균내어 station별 종합 점수를 계산하고, 높은 순서대로 시각화합니다.\n\n"
        "같은 순서에서 `RMSE`, `MAE`도 함께 정리해서 성능을 한 번에 비교할 수 있도록 구성합니다."
    )

    ranking_code = nbformat.v4.new_code_cell(
        "test_metric_df = metrics_df[(metrics_df['split'] == 'test') & (metrics_df['target'].isin(['rental_count', 'return_count']))].copy()\n"
        "r2_df = (\n"
        "    test_metric_df.pivot_table(index='station_id', columns='target', values='r2', aggfunc='mean')\n"
        "    .reset_index()\n"
        ")\n"
        "rmse_df = (\n"
        "    test_metric_df.pivot_table(index='station_id', columns='target', values='rmse', aggfunc='mean')\n"
        "    .reset_index()\n"
        "    .rename(columns={'rental_count': 'rental_rmse', 'return_count': 'return_rmse'})\n"
        ")\n"
        "mae_df = (\n"
        "    test_metric_df.pivot_table(index='station_id', columns='target', values='mae', aggfunc='mean')\n"
        "    .reset_index()\n"
        "    .rename(columns={'rental_count': 'rental_mae', 'return_count': 'return_mae'})\n"
        ")\n"
        "ranking_df = r2_df.merge(rmse_df, on='station_id').merge(mae_df, on='station_id')\n"
        "ranking_df['combined_test_r2'] = ranking_df[['rental_count', 'return_count']].mean(axis=1)\n"
        "ranking_df['combined_test_rmse'] = ranking_df[['rental_rmse', 'return_rmse']].mean(axis=1)\n"
        "ranking_df['combined_test_mae'] = ranking_df[['rental_mae', 'return_mae']].mean(axis=1)\n"
        "ranking_df = ranking_df.sort_values('combined_test_r2', ascending=False).reset_index(drop=True)\n"
        "ranking_df.index = ranking_df.index + 1\n"
        "ranking_df.to_csv(DATA_DIR / 'top20_station_combined_test_r2_ranking.csv', index_label='rank', encoding='utf-8-sig')\n"
        "ranking_df"
    )

    ranking_plot_code = nbformat.v4.new_code_cell(
        "plot_df = ranking_df.reset_index().rename(columns={'index': 'rank'})\n"
        "plt.figure(figsize=(14, 8))\n"
        "sns.barplot(data=plot_df, x='combined_test_r2', y=plot_df['station_id'].astype(str), palette='viridis')\n"
        "plt.title('Top 20 Stations Ranked By Combined Test R²')\n"
        "plt.xlabel('Average Test R² of rental_count and return_count')\n"
        "plt.ylabel('station_id')\n"
        "plt.tight_layout()\n"
        "plt.show()\n"
        "\n"
        "plt.figure(figsize=(14, 8))\n"
        "rank_melt_df = plot_df.melt(id_vars=['rank', 'station_id'], value_vars=['rental_count', 'return_count'], var_name='target', value_name='test_r2')\n"
        "sns.barplot(data=rank_melt_df, x='test_r2', y=rank_melt_df['station_id'].astype(str), hue='target')\n"
        "plt.title('Test R² By Target In Combined Ranking Order')\n"
        "plt.xlabel('Test R²')\n"
        "plt.ylabel('station_id')\n"
        "plt.tight_layout()\n"
        "plt.show()\n"
    )

    error_metric_plot_code = nbformat.v4.new_code_cell(
        "plot_df = ranking_df.reset_index().rename(columns={'index': 'rank'})\n"
        "fig, axes = plt.subplots(1, 2, figsize=(18, 8), sharey=True)\n"
        "sns.barplot(data=plot_df, x='combined_test_rmse', y=plot_df['station_id'].astype(str), ax=axes[0], color='#4C72B0')\n"
        "axes[0].set_title('Combined Test RMSE')\n"
        "axes[0].set_xlabel('Average RMSE of rental_count and return_count')\n"
        "axes[0].set_ylabel('station_id')\n"
        "sns.barplot(data=plot_df, x='combined_test_mae', y=plot_df['station_id'].astype(str), ax=axes[1], color='#55A868')\n"
        "axes[1].set_title('Combined Test MAE')\n"
        "axes[1].set_xlabel('Average MAE of rental_count and return_count')\n"
        "axes[1].set_ylabel('station_id')\n"
        "plt.tight_layout()\n"
        "plt.show()\n"
        "\n"
        "detail_metric_df = plot_df[['rank', 'station_id', 'rental_rmse', 'return_rmse', 'combined_test_rmse', 'rental_mae', 'return_mae', 'combined_test_mae']]\n"
        "detail_metric_df\n"
    )

    notebook = nbformat.v4.new_notebook(
        cells=[
            intro_md,
            setup_code,
            metrics_code,
            metric_plot_code,
            importance_code,
            importance_plot_code,
            test_prediction_code,
            year_pattern_plot_code,
            ranking_md,
            ranking_code,
            ranking_plot_code,
            error_metric_plot_code,
        ],
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.x"},
        },
    )

    with notebook_path.open("w", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)

    return notebook_path


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)

    top20_station_ids = load_top20_station_ids()
    source_df = pd.read_csv(SOURCE_PATH)

    for station_id in top20_station_ids:
        extract_station_csv(source_df, station_id)
        notebook_path = create_station_notebook(station_id)
        execute_notebook(notebook_path)

    collect_metrics(top20_station_ids)
    integrated_notebook = create_integrated_notebook(top20_station_ids)
    execute_notebook(integrated_notebook)

    print(json.dumps({"top20_station_ids": top20_station_ids, "integrated_notebook": str(integrated_notebook)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
