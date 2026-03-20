from __future__ import annotations

import json
import os
import warnings
from contextlib import contextmanager
from pathlib import Path

import nbformat
import pandas as pd
from IPython.display import display

os.environ.setdefault("MPLBACKEND", "Agg")
warnings.filterwarnings("ignore", message="FigureCanvasAgg is non-interactive")


ROOT = Path(__file__).resolve().parents[2]
HMW3_DIR = ROOT / "hmw3"
DATA_DIR = HMW3_DIR / "Data"
STATION_RAW_DIR = DATA_DIR / "station_raw"
HOLIDAY_DIR = DATA_DIR / "holiday_reference"
FORMULA_DIR = DATA_DIR / "formulas"
WEIGHTS_DIR = DATA_DIR / "weights"
TUNING_DIR = DATA_DIR / "tuning"
METRICS_DIR = DATA_DIR / "metrics"
PREDICTIONS_DIR = DATA_DIR / "predictions"
FEATURE_DIR = DATA_DIR / "feature_analysis"
COMPARISON_DIR = DATA_DIR / "comparisons"
SUMMARY_DIR = DATA_DIR / "summaries"
NOTE_DIR = HMW3_DIR / "Note"
SOURCE_PATH = ROOT / "3조 공유폴더" / "station_hour_bike_flow_2023_2025.csv"
TEMPLATE_NOTEBOOK = NOTE_DIR / "hmw2340.ipynb"


def load_top20_station_ids() -> list[int]:
    if SOURCE_PATH.exists():
        df = pd.read_csv(SOURCE_PATH)
        usage = (
            df.assign(total=df["rental_count"].fillna(0) + df["return_count"].fillna(0))
            .groupby("station_id", as_index=False)["total"]
            .sum()
            .sort_values("total", ascending=False)
            .head(20)
        )
        return usage["station_id"].astype(int).tolist()

    metric_summary_path = SUMMARY_DIR / "top20_station_metrics_summary.csv"
    if metric_summary_path.exists():
        metric_df = pd.read_csv(metric_summary_path)
        return sorted(metric_df["station_id"].dropna().astype(int).unique().tolist())

    station_ids = []
    for path in sorted(STATION_RAW_DIR.glob("station_*.csv")):
        station_name = path.stem.replace("station_", "")
        if station_name.isdigit():
            station_ids.append(int(station_name))
    return station_ids[:20]


def extract_station_csv(source_df: pd.DataFrame, station_id: int) -> Path:
    output_path = STATION_RAW_DIR / f"station_{station_id}.csv"
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
        metric_path = METRICS_DIR / f"station_{station_id}_offday_month_ridge_metrics.csv"
        metric_df = pd.read_csv(metric_path)
        metric_df.insert(0, "station_id", station_id)
        frames.append(metric_df)
    summary_df = pd.concat(frames, ignore_index=True)
    summary_df.to_csv(SUMMARY_DIR / "top20_station_metrics_summary.csv", index=False, encoding="utf-8-sig")
    return summary_df


def create_integrated_notebook(station_ids: list[int]) -> Path:
    notebook_path = NOTE_DIR / "hmw_top20_station_integrated_comparison.ipynb"

    def md(text: str):
        return nbformat.v4.new_markdown_cell(text)

    def code(text: str):
        return nbformat.v4.new_code_cell(text)

    cells = [
        md(
            "# 이용량 상위 20개 station 통합 분석\n\n"
            "이 노트북은 이용량이 많은 station 20개를 대상으로, 원천 데이터 확인부터 전처리, 패턴 feature 생성, "
            "Ridge 학습, station별 성능 비교, 오차 진단, 최종 결론까지 한 흐름으로 정리한 통합 분석 노트입니다.\n\n"
            "## 분석 흐름\n"
            "1. 분석 대상과 사용 데이터 정리\n"
            "2. station 선정 근거 설명\n"
            "3. 원천 데이터 품질 점검\n"
            "4. 전처리 및 데이터 분할 방식 정리\n"
            "5. 패턴 기반 feature 생성 과정 설명\n"
            "6. Ridge 튜닝 및 성능 비교\n"
            "7. 통합 랭킹, 중요 feature, 오차 구간 해석\n"
            "8. 최종 결론 정리"
        ),
        code(
            "from pathlib import Path\n"
            "\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "import matplotlib as mpl\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "import folium\n"
            "from matplotlib.ticker import MaxNLocator\n"
            "\n"
            "plt.style.use('seaborn-v0_8-whitegrid')\n"
            "pd.set_option('display.max_columns', 100)\n"
            "pd.set_option('display.float_format', lambda x: f'{x:,.4f}')\n"
            "sns.set_palette(['#1f4e79', '#2e8b57', '#d97a04', '#9c2f2f', '#6b4c9a'])\n"
            "mpl.rcParams['figure.facecolor'] = 'white'\n"
            "mpl.rcParams['axes.facecolor'] = '#fbfbf8'\n"
            "mpl.rcParams['axes.edgecolor'] = '#c7c7c7'\n"
            "mpl.rcParams['grid.color'] = '#d9d9d9'\n"
            "mpl.rcParams['font.size'] = 11\n"
            "mpl.rcParams['font.family'] = 'Malgun Gothic'\n"
            "mpl.rcParams['axes.unicode_minus'] = False\n"
            "\n"
            "ROOT = Path.cwd().resolve().parents[0]\n"
            "DATA_DIR = ROOT / 'Data'\n"
            "STATION_META_DIR = ROOT.parent / '3조 공유폴더' / '강남구 대여소 정보 (2023~2025)'\n"
            f"TOP20_STATIONS = {station_ids}\n"
            "TARGETS = ['rental_count', 'return_count']\n"
            "SPLIT_ORDER = ['train', 'valid', 'test']\n"
            "YEAR_TO_SPLIT = {2023: 'train', 2024: 'valid', 2025: 'test'}\n"
            "\n"
            "def format_axis(ax, title=None, xlabel=None, ylabel=None, grid_axis='x'):\n"
            "    if title is not None:\n"
            "        ax.set_title(title, fontsize=13, fontweight='bold', pad=12)\n"
            "    if xlabel is not None:\n"
            "        ax.set_xlabel(xlabel)\n"
            "    if ylabel is not None:\n"
            "        ax.set_ylabel(ylabel)\n"
            "    ax.grid(axis=grid_axis, alpha=0.22, linestyle='--')\n"
            "    sns.despine(ax=ax, left=False, bottom=False)\n"
            "    return ax\n"
            "\n"
            "def annotate_barh(ax, fmt='{:.3f}', pad=0.01):\n"
            "    max_width = max((patch.get_width() for patch in ax.patches), default=0)\n"
            "    for patch in ax.patches:\n"
            "        width = patch.get_width()\n"
            "        y = patch.get_y() + patch.get_height() / 2\n"
            "        ax.text(width + max_width * pad, y, fmt.format(width), va='center', ha='left', fontsize=9, color='#333333')\n"
            "\n"
            "def annotate_bar(ax, fmt='{:.0f}', pad=0.02):\n"
            "    max_height = max((patch.get_height() for patch in ax.patches), default=0)\n"
            "    for patch in ax.patches:\n"
            "        height = patch.get_height()\n"
            "        x = patch.get_x() + patch.get_width() / 2\n"
            "        ax.text(x, height + max_height * pad, fmt.format(height), va='bottom', ha='center', fontsize=9, color='#333333')\n"
            "\n"
            "def make_station_label(station_id, station_name, max_len=18):\n"
            "    station_name = str(station_name)\n"
            "    short_name = station_name if len(station_name) <= max_len else station_name[:max_len - 1] + '…'\n"
            "    return f'{int(station_id)} | {short_name}'\n"
        ),
        md(
            "## 1. 분석 대상과 사용 데이터\n\n"
            "통합 노트는 각 station 노트에서 생성한 산출물을 다시 모아 비교합니다. "
            "원천 시계열 데이터, 공휴일 기준표, 시간대 패턴 공식, 가중치 테이블, Ridge 튜닝 로그, "
            "평가 지표, 예측 결과, 중요도 표, 연도별 패턴 비교표, 고오차 시점 표를 함께 사용합니다."
        ),
        code(
            "station_meta_frames = []\n"
            "for year in ['2023', '2024', '2025']:\n"
            "    meta_path = STATION_META_DIR / f'{year}_강남구_대여소.csv'\n"
            "    meta_df = pd.read_csv(meta_path)\n"
            "    meta_df['source_year'] = int(year)\n"
            "    station_meta_frames.append(meta_df[['대여소번호', '대여소명', '위도', '경도', '주소', 'source_year']])\n"
            "station_meta_df = pd.concat(station_meta_frames, ignore_index=True)\n"
            "station_meta_df['station_id'] = station_meta_df['대여소번호'].astype(float).astype(int)\n"
            "station_meta_df = station_meta_df.sort_values(['station_id', 'source_year']).drop_duplicates('station_id', keep='last')\n"
            "station_meta_df = station_meta_df.rename(columns={'대여소명': 'station_name', '위도': 'latitude', '경도': 'longitude', '주소': 'address'})\n"
            "station_meta_df['station_label'] = station_meta_df.apply(lambda row: make_station_label(row['station_id'], row['station_name']), axis=1)\n"
            "\n"
            "raw_frames = []\n"
            "formula_frames = []\n"
            "weight_frames = []\n"
            "tuning_frames = []\n"
            "metric_frames = []\n"
            "importance_frames = []\n"
            "comparison_frames = []\n"
            "error_frames = []\n"
            "prediction_frames = []\n"
            "holiday_frames = []\n"
            "\n"
            "for station_id in TOP20_STATIONS:\n"
            "    raw_df = pd.read_csv(DATA_DIR / 'station_raw' / f'station_{station_id}.csv')\n"
            "    raw_df['station_id'] = station_id\n"
            "    raw_frames.append(raw_df)\n"
            "\n"
            "    formula_df = pd.read_csv(DATA_DIR / 'formulas' / f'station_{station_id}_offday_hour_formulas.csv')\n"
            "    formula_df['station_id'] = station_id\n"
            "    formula_frames.append(formula_df)\n"
            "\n"
            "    weight_df = pd.read_csv(DATA_DIR / 'weights' / f'station_{station_id}_month_weights.csv')\n"
            "    weight_df['station_id'] = station_id\n"
            "    weight_frames.append(weight_df)\n"
            "\n"
            "    tuning_df = pd.read_csv(DATA_DIR / 'tuning' / f'station_{station_id}_offday_month_ridge_tuning.csv')\n"
            "    tuning_df['station_id'] = station_id\n"
            "    tuning_frames.append(tuning_df)\n"
            "\n"
            "    metric_df = pd.read_csv(DATA_DIR / 'metrics' / f'station_{station_id}_offday_month_ridge_metrics.csv')\n"
            "    metric_df['station_id'] = station_id\n"
            "    metric_frames.append(metric_df)\n"
            "\n"
            "    importance_df = pd.read_csv(DATA_DIR / 'feature_analysis' / f'station_{station_id}_feature_importance.csv')\n"
            "    importance_df['station_id'] = station_id\n"
            "    importance_frames.append(importance_df)\n"
            "\n"
            "    comparison_df = pd.read_csv(DATA_DIR / 'comparisons' / f'station_{station_id}_year_actual_vs_regression_vs_ml.csv')\n"
            "    comparison_df['station_id'] = station_id\n"
            "    comparison_frames.append(comparison_df)\n"
            "\n"
            "    error_df = pd.read_csv(DATA_DIR / 'comparisons' / f'station_{station_id}_2025_high_error_points.csv')\n"
            "    error_df['station_id'] = station_id\n"
            "    error_frames.append(error_df)\n"
            "\n"
            "    pred_df = pd.read_csv(DATA_DIR / 'predictions' / f'station_{station_id}_offday_month_ridge_predictions_long.csv')\n"
            "    pred_df['station_id'] = station_id\n"
            "    prediction_frames.append(pred_df)\n"
            "\n"
            "    holiday_df = pd.read_csv(DATA_DIR / 'holiday_reference' / f'station_{station_id}_holiday_reference.csv')\n"
            "    holiday_df['station_id'] = station_id\n"
            "    holiday_frames.append(holiday_df)\n"
            "\n"
            "raw_all_df = pd.concat(raw_frames, ignore_index=True)\n"
            "formula_all_df = pd.concat(formula_frames, ignore_index=True)\n"
            "weight_all_df = pd.concat(weight_frames, ignore_index=True)\n"
            "tuning_all_df = pd.concat(tuning_frames, ignore_index=True)\n"
            "metrics_df = pd.concat(metric_frames, ignore_index=True)\n"
            "importance_all_df = pd.concat(importance_frames, ignore_index=True)\n"
            "comparison_all_df = pd.concat(comparison_frames, ignore_index=True)\n"
            "error_all_df = pd.concat(error_frames, ignore_index=True)\n"
            "prediction_all_df = pd.concat(prediction_frames, ignore_index=True)\n"
            "holiday_all_df = pd.concat(holiday_frames, ignore_index=True)\n"
            "\n"
            "raw_all_df['time'] = pd.to_datetime(raw_all_df['time'])\n"
            "raw_all_df['date'] = raw_all_df['time'].dt.normalize()\n"
            "holiday_all_df['date'] = pd.to_datetime(holiday_all_df['date'])\n"
            "shared_holiday_df = holiday_all_df[['date', 'holiday_name']].drop_duplicates().sort_values('date').reset_index(drop=True)\n"
            "holiday_set = set(shared_holiday_df['date'])\n"
            "raw_all_df['is_holiday'] = raw_all_df['date'].isin(holiday_set).astype(int)\n"
            "raw_all_df['is_offday'] = ((raw_all_df['weekday'] >= 5) | (raw_all_df['is_holiday'] == 1)).astype(int)\n"
            "raw_all_df['day_type'] = np.where(raw_all_df['is_offday'] == 1, 'offday', 'weekday')\n"
            "raw_all_df['split'] = raw_all_df['year'].map(YEAR_TO_SPLIT)\n"
            "raw_all_df = raw_all_df.merge(station_meta_df[['station_id', 'station_name', 'station_label', 'latitude', 'longitude', 'address']], on='station_id', how='left')\n"
        ),
        md(
            "## 2. station 선정 근거\n\n"
            "이번 분석에서는 단순히 이용량이 많은 station만 고른 것이 아니라, "
            "**머신러닝 예측에 적합하도록 이용자가 많은 station들 중에서 2023~2025년 시간별 패턴이 크게 벗어나지 않고 비교적 비슷하게 유지되는 station**을 우선 선정했습니다.\n\n"
            "즉, 선정 기준은 다음 두 가지입니다.\n"
            "1. 이용량이 충분히 많아 패턴이 안정적으로 관측될 것\n"
            "2. 연도별 시간대 패턴이 지나치게 흔들리지 않아 학습한 패턴이 다음 해에도 재현될 것"
        ),
        code(
            "station_usage_df = (\n"
            "    raw_all_df.groupby('station_id', as_index=False)\n"
            "    .agg(\n"
            "        rental_total=('rental_count', 'sum'),\n"
            "        return_total=('return_count', 'sum'),\n"
            "    )\n"
            ")\n"
            "station_usage_df['total_usage'] = station_usage_df['rental_total'] + station_usage_df['return_total']\n"
            "station_usage_df = station_usage_df.sort_values('total_usage', ascending=False).reset_index(drop=True)\n"
            "\n"
            "year_hour_profile_df = (\n"
            "    raw_all_df.groupby(['station_id', 'year', 'hour'], as_index=False)[['rental_count', 'return_count']]\n"
            "    .mean()\n"
            ")\n"
            "year_hour_profile_df['total_flow'] = year_hour_profile_df['rental_count'] + year_hour_profile_df['return_count']\n"
            "pattern_stability_df = (\n"
            "    year_hour_profile_df.groupby(['station_id', 'hour'], as_index=False)['total_flow']\n"
            "    .agg(['mean', 'std'])\n"
            "    .reset_index()\n"
            ")\n"
            "pattern_stability_df['cv'] = np.where(pattern_stability_df['mean'] > 0, pattern_stability_df['std'] / pattern_stability_df['mean'], 0)\n"
            "pattern_stability_df = (\n"
            "    pattern_stability_df.groupby('station_id', as_index=False)\n"
            "    .agg(\n"
            "        mean_hourly_flow=('mean', 'mean'),\n"
            "        mean_hourly_std=('std', 'mean'),\n"
            "        mean_hourly_cv=('cv', 'mean'),\n"
            "    )\n"
            ")\n"
            "selection_basis_df = station_usage_df.merge(pattern_stability_df, on='station_id', how='left')\n"
            "selection_basis_df = selection_basis_df.merge(station_meta_df[['station_id', 'station_name', 'station_label', 'latitude', 'longitude']], on='station_id', how='left')\n"
            "selection_basis_df = selection_basis_df.sort_values(['total_usage', 'mean_hourly_cv'], ascending=[False, True]).reset_index(drop=True)\n"
            "display(selection_basis_df[['station_id', 'station_name', 'total_usage', 'mean_hourly_flow', 'mean_hourly_std', 'mean_hourly_cv']].round(4))\n"
            "\n"
            "fig, axes = plt.subplots(1, 2, figsize=(18, 6))\n"
            "usage_plot_df = selection_basis_df.sort_values('total_usage', ascending=False)\n"
            "sns.barplot(data=usage_plot_df, x='total_usage', y='station_label', ax=axes[0], color='#1f4e79')\n"
            "format_axis(axes[0], '선정된 20개 station의 총 이용량', '2023~2025 총 이용량', 'station')\n"
            "annotate_barh(axes[0], fmt='{:.0f}', pad=0.008)\n"
            "\n"
            "stability_plot_df = selection_basis_df.sort_values('mean_hourly_cv', ascending=True)\n"
            "sns.barplot(data=stability_plot_df, x='mean_hourly_cv', y='station_label', ax=axes[1], color='#2e8b57')\n"
            "format_axis(axes[1], '연도별 시간 패턴 안정성 비교', '시간대 평균 변동계수(CV)', 'station')\n"
            "annotate_barh(axes[1], fmt='{:.3f}', pad=0.02)\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "\n"
            "top20_map = folium.Map(location=[selection_basis_df['latitude'].mean(), selection_basis_df['longitude'].mean()], zoom_start=13, tiles='CartoDB positron')\n"
            "for _, row in selection_basis_df.iterrows():\n"
            "    popup_html = f\"<b>{row['station_name']}</b><br>station_id: {int(row['station_id'])}<br>총 이용량: {row['total_usage']:.0f}<br>평균 CV: {row['mean_hourly_cv']:.3f}\"\n"
            "    folium.CircleMarker(location=[row['latitude'], row['longitude']], radius=6, color='#1f4e79', fill=True, fill_color='#2e8b57', fill_opacity=0.85, popup=popup_html, tooltip=row['station_label']).add_to(top20_map)\n"
            "top20_map\n"
        ),
        code(
            "asset_summary_df = pd.DataFrame([\n"
            "    {'asset': 'station 원천 csv', 'count': len(raw_frames)},\n"
            "    {'asset': '공휴일 기준 csv', 'count': len(holiday_frames)},\n"
            "    {'asset': '패턴 공식 csv', 'count': len(formula_frames)},\n"
            "    {'asset': '가중치 csv', 'count': len(weight_frames)},\n"
            "    {'asset': '튜닝 결과 csv', 'count': len(tuning_frames)},\n"
            "    {'asset': '성능 지표 csv', 'count': len(metric_frames)},\n"
            "    {'asset': 'feature 중요도 csv', 'count': len(importance_frames)},\n"
            "    {'asset': '연도별 비교 csv', 'count': len(comparison_frames)},\n"
            "    {'asset': '고오차 지점 csv', 'count': len(error_frames)},\n"
            "    {'asset': '예측 long csv', 'count': len(prediction_frames)},\n"
            "])\n"
            "display(asset_summary_df)\n"
            "\n"
            "scope_summary_df = pd.DataFrame([\n"
            "    {'item': 'station 개수', 'value': raw_all_df['station_id'].nunique()},\n"
            "    {'item': '전체 row 수', 'value': len(raw_all_df)},\n"
            "    {'item': '시작 시점', 'value': raw_all_df['time'].min()},\n"
            "    {'item': '종료 시점', 'value': raw_all_df['time'].max()},\n"
            "    {'item': '공휴일 개수', 'value': len(shared_holiday_df)},\n"
            "])\n"
            "display(scope_summary_df)\n"
            "\n"
            "station_scope_df = (\n"
            "    raw_all_df.groupby('station_id', as_index=False)\n"
            "    .agg(\n"
            "        rows=('time', 'size'),\n"
            "        rental_sum=('rental_count', 'sum'),\n"
            "        return_sum=('return_count', 'sum'),\n"
            "        start_time=('time', 'min'),\n"
            "        end_time=('time', 'max'),\n"
            "    )\n"
            "    .sort_values('rental_sum', ascending=False)\n"
            ")\n"
            "station_scope_df = station_scope_df.merge(station_meta_df[['station_id', 'station_name', 'station_label']], on='station_id', how='left')\n"
            "station_scope_df.head(10)\n"
        ),
        md(
            "## 3. 원천 데이터 품질 점검\n\n"
            "모델 결과를 해석하기 전에 각 station 시계열이 충분한 길이를 가지는지, "
            "결측이 많은지, 시간 중복이 있는지, 음수처럼 비정상 값이 있는지를 먼저 확인합니다."
        ),
        code(
            "quality_df = (\n"
            "    raw_all_df.groupby('station_id', as_index=False)\n"
            "    .agg(\n"
            "        rows=('time', 'size'),\n"
            "        unique_time=('time', 'nunique'),\n"
            "        rental_missing=('rental_count', lambda s: int(s.isna().sum())),\n"
            "        return_missing=('return_count', lambda s: int(s.isna().sum())),\n"
            "        min_rental=('rental_count', 'min'),\n"
            "        min_return=('return_count', 'min'),\n"
            "    )\n"
            ")\n"
            "quality_df['duplicate_time_rows'] = quality_df['rows'] - quality_df['unique_time']\n"
            "quality_df['negative_rental_exists'] = quality_df['min_rental'] < 0\n"
            "quality_df['negative_return_exists'] = quality_df['min_return'] < 0\n"
            "quality_df = quality_df.merge(station_meta_df[['station_id', 'station_name']], on='station_id', how='left')\n"
            "quality_df.sort_values('station_id')\n"
        ),
        code(
            "fig, axes = plt.subplots(1, 2, figsize=(16, 5))\n"
            "daily_summary = raw_all_df.groupby('day_type', as_index=False)[['rental_count', 'return_count']].mean()\n"
            "daily_summary = daily_summary.melt(id_vars='day_type', var_name='target', value_name='mean_count')\n"
            "sns.barplot(data=daily_summary, x='day_type', y='mean_count', hue='target', ax=axes[0], palette=['#1f4e79', '#d97a04'])\n"
            "format_axis(axes[0], 'top20 station의 day_type별 평균 이용량', 'day_type', '평균 이용량', grid_axis='y')\n"
            "axes[0].legend(title='target', frameon=True, loc='upper right')\n"
            "\n"
            "hourly_profile_df = (\n"
            "    raw_all_df.groupby(['day_type', 'hour'], as_index=False)[['rental_count', 'return_count']]\n"
            "    .mean()\n"
            "    .melt(id_vars=['day_type', 'hour'], var_name='target', value_name='mean_count')\n"
            ")\n"
            "sns.lineplot(data=hourly_profile_df, x='hour', y='mean_count', hue='day_type', style='target', linewidth=2.4, ax=axes[1])\n"
            "format_axis(axes[1], '모델링 이전 시간대 평균 패턴', 'hour', '평균 이용량', grid_axis='y')\n"
            "axes[1].xaxis.set_major_locator(MaxNLocator(integer=True))\n"
            "axes[1].legend(title='day_type / target', frameon=True, loc='upper left')\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
        ),
        md(
            "## 4. 전처리와 데이터 분할 설계\n\n"
            "개별 station 노트는 동일한 전처리 파이프라인을 따릅니다. "
            "시간 변수를 정리하고, 공휴일을 결합하고, 주말과 공휴일을 `offday`로 통합한 뒤, "
            "전체 시계열을 연도 기준으로 train, valid, test로 분할합니다."
        ),
        code(
            "preprocess_example_df = raw_all_df[\n"
            "    ['station_id', 'time', 'date', 'year', 'month', 'day', 'weekday', 'hour', 'is_holiday', 'is_offday', 'day_type', 'split', 'rental_count', 'return_count']\n"
            "].sort_values(['station_id', 'time']).head(12)\n"
            "preprocess_example_df\n"
        ),
        code(
            "split_summary_df = (\n"
            "    raw_all_df.groupby(['split', 'day_type'], as_index=False)\n"
            "    .agg(\n"
            "        rows=('time', 'size'),\n"
            "        station_count=('station_id', 'nunique'),\n"
            "        rental_mean=('rental_count', 'mean'),\n"
            "        return_mean=('return_count', 'mean'),\n"
            "    )\n"
            ")\n"
            "split_summary_df['split'] = pd.Categorical(split_summary_df['split'], categories=SPLIT_ORDER, ordered=True)\n"
            "split_summary_df.sort_values(['split', 'day_type'])\n"
        ),
        md(
            "## 5. 패턴 기반 feature 생성 과정\n\n"
            "이 분석은 원천 count를 바로 Ridge에 넣지 않습니다. "
            "먼저 `day_type`별 시간 패턴을 기본 형태로 만들고, 여기에 month, year, hour 가중치를 얹어 "
            "`base_value`, `pattern_prior`, `corrected_pattern_prior` 같은 패턴 중심 feature를 생성합니다."
        ),
        code(
            "formula_summary_df = (\n"
            "    formula_all_df.groupby(['target', 'day_type'], as_index=False)\n"
            "    .agg(\n"
            "        station_count=('station_id', 'nunique'),\n"
            "        intercept_mean=('intercept', 'mean'),\n"
            "        sin_coef_mean=('sin_hour_coef', 'mean'),\n"
            "        cos_coef_mean=('cos_hour_coef', 'mean'),\n"
            "    )\n"
            ")\n"
            "display(formula_summary_df.round(4))\n"
            "\n"
            "formula_all_df.sort_values(['target', 'day_type', 'station_id']).head(12)\n"
        ),
        code(
            "month_weight_df = weight_all_df[weight_all_df['weight_type'] == 'month_weight'].copy()\n"
            "month_weight_summary_df = (\n"
            "    month_weight_df.groupby(['target', 'key'], as_index=False)\n"
            "    .agg(\n"
            "        mean_weight=('value', 'mean'),\n"
            "        min_weight=('value', 'min'),\n"
            "        max_weight=('value', 'max'),\n"
            "    )\n"
            "    .rename(columns={'key': 'month'})\n"
            ")\n"
            "\n"
            "fig, axes = plt.subplots(1, 2, figsize=(16, 5), sharex=True)\n"
            "for ax, target in zip(axes, TARGETS):\n"
            "    sub = month_weight_summary_df[month_weight_summary_df['target'] == target]\n"
            "    color = '#1f4e79' if target == 'rental_count' else '#d97a04'\n"
            "    ax.plot(sub['month'], sub['mean_weight'], marker='o', linewidth=2.4, color=color)\n"
            "    ax.fill_between(sub['month'], sub['min_weight'], sub['max_weight'], alpha=0.18, color=color)\n"
            "    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1)\n"
            "    format_axis(ax, f'{target}의 월 가중치 범위', 'month', '가중치', grid_axis='y')\n"
            "    ax.xaxis.set_major_locator(MaxNLocator(integer=True))\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "\n"
            "month_weight_summary_df.round(4)\n"
        ),
        md(
            "### year_weight와 hour_weight 해석\n\n"
            "월 가중치와 마찬가지로 실제 모델에는 `year_weight`, `hour_weight`도 함께 사용됩니다.\n\n"
            "- `year_weight`: 특정 연도의 전체적인 수준 차이를 보정하는 값\n"
            "- `hour_weight`: 기본 패턴식만으로 설명되지 않는 세부 시간대 보정을 반영하는 값\n\n"
            "특히 `year_weight`는 **해당 연도의 실제 데이터를 보고 계산되는 값**이기 때문에, "
            "완전히 새로운 연도에 대해 사전에 정확한 값을 알 수 없습니다. "
            "즉, 새로운 연도의 데이터를 일부 확보한 뒤 다시 weight를 갱신하거나 모델을 재학습하는 과정이 필요합니다.\n\n"
            "따라서 현재 구조에서 `year_weight`는 장기 미래를 미리 고정적으로 예측하는 변수라기보다, "
            "해당 연도의 수준 변화를 반영하기 위한 사후적 보정값에 가깝습니다."
        ),
        code(
            "year_weight_df = weight_all_df[weight_all_df['weight_type'] == 'year_weight'].copy()\n"
            "year_weight_summary_df = (\n"
            "    year_weight_df.groupby(['target', 'key'], as_index=False)\n"
            "    .agg(\n"
            "        mean_weight=('value', 'mean'),\n"
            "        min_weight=('value', 'min'),\n"
            "        max_weight=('value', 'max'),\n"
            "    )\n"
            "    .rename(columns={'key': 'year'})\n"
            ")\n"
            "\n"
            "fig, axes = plt.subplots(1, 2, figsize=(15, 5), sharex=True)\n"
            "for ax, target in zip(axes, TARGETS):\n"
            "    sub = year_weight_summary_df[year_weight_summary_df['target'] == target].copy().sort_values('year')\n"
            "    color = '#2e8b57' if target == 'rental_count' else '#9c2f2f'\n"
            "    ax.plot(sub['year'], sub['mean_weight'], marker='o', linewidth=2.6, color=color)\n"
            "    ax.fill_between(sub['year'], sub['min_weight'], sub['max_weight'], alpha=0.18, color=color)\n"
            "    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1)\n"
            "    format_axis(ax, f'{target}의 연도 가중치 범위', 'year', '가중치', grid_axis='y')\n"
            "    ax.xaxis.set_major_locator(MaxNLocator(integer=True))\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "\n"
            "year_weight_summary_df.round(4)\n"
        ),
        code(
            "hour_weight_df = weight_all_df[weight_all_df['weight_type'] == 'hour_weight'].copy()\n"
            "hour_weight_summary_df = (\n"
            "    hour_weight_df.groupby(['target', 'key'], as_index=False)\n"
            "    .agg(\n"
            "        mean_weight=('value', 'mean'),\n"
            "        min_weight=('value', 'min'),\n"
            "        max_weight=('value', 'max'),\n"
            "    )\n"
            "    .rename(columns={'key': 'hour'})\n"
            ")\n"
            "\n"
            "fig, axes = plt.subplots(1, 2, figsize=(16, 5), sharex=True)\n"
            "for ax, target in zip(axes, TARGETS):\n"
            "    sub = hour_weight_summary_df[hour_weight_summary_df['target'] == target].copy().sort_values('hour')\n"
            "    color = '#6b4c9a' if target == 'rental_count' else '#d97a04'\n"
            "    ax.plot(sub['hour'], sub['mean_weight'], marker='o', markersize=4, linewidth=2.0, color=color)\n"
            "    ax.fill_between(sub['hour'], sub['min_weight'], sub['max_weight'], alpha=0.15, color=color)\n"
            "    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1)\n"
            "    format_axis(ax, f'{target}의 시간 가중치 범위', 'hour', '가중치', grid_axis='y')\n"
            "    ax.xaxis.set_major_locator(MaxNLocator(integer=True))\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "\n"
            "hour_weight_summary_df.round(4)\n"
        ),
        md(
            "## 6. 모델 선정 이유\n\n"
            "이번 분석에서는 `pattern feature + Ridge 회귀` 구조를 선택했습니다. "
            "선정 이유는 다음과 같습니다.\n\n"
            "1. **해석 가능성**: 대여/반납량이 어떤 시간 패턴과 가중치에 의해 설명되는지 비교적 명확하게 볼 수 있습니다.\n"
            "2. **데이터 규모 적합성**: station별로 데이터를 나누어 학습할 때, 지나치게 복잡한 모델보다 안정적으로 학습됩니다.\n"
            "3. **과적합 제어**: Ridge의 `alpha`를 통해 feature 계수를 조절할 수 있어 station별 변동에 과하게 맞추는 것을 줄일 수 있습니다.\n"
            "4. **현재 목적과의 적합성**: 이번 단계의 핵심은 `rental_count`, `return_count`를 예측하고 station 간 패턴을 비교하는 것이므로, "
            "고성능 블랙박스 모델보다 구조가 단순하고 비교가 쉬운 모델이 더 적절했습니다.\n\n"
            "즉, 이번 모델은 최고 복잡도의 예측기라기보다, "
            "**시간 패턴을 보존하면서 station별 차이를 해석 가능하게 비교하기 위한 기준 모델**로 선택한 것입니다."
        ),
        md(
            "## 7. Ridge 튜닝과 평가\n\n"
            "station별, target별로 train 구간에서 패턴 구조를 학습하고 valid 구간에서 Ridge alpha를 고른 뒤, "
            "같은 설정을 2025 test 구간에 적용해 최종 성능을 평가합니다."
        ),
        code(
            "best_alpha_df = (\n"
            "    tuning_all_df.sort_values(['station_id', 'target', 'rmse'])\n"
            "    .groupby(['station_id', 'target'], as_index=False)\n"
            "    .first()\n"
            ")\n"
            "display(best_alpha_df[['station_id', 'target', 'alpha', 'rmse', 'mae', 'r2']].round(4))\n"
            "\n"
            "alpha_dist_df = (\n"
            "    best_alpha_df.groupby(['target', 'alpha'], as_index=False)\n"
            "    .size()\n"
            "    .rename(columns={'size': 'station_count'})\n"
            ")\n"
            "alpha_dist_df\n"
        ),
        code(
            "fig, axes = plt.subplots(1, 2, figsize=(15, 5))\n"
            "for ax, target in zip(axes, TARGETS):\n"
            "    sub = alpha_dist_df[alpha_dist_df['target'] == target].copy()\n"
            "    sub['alpha_label'] = sub['alpha'].astype(str)\n"
            "    sns.barplot(data=sub, x='alpha_label', y='station_count', ax=ax, color='#4C78A8')\n"
            "    format_axis(ax, f'{target}의 선택 alpha 분포', 'alpha', 'station 개수', grid_axis='y')\n"
            "    annotate_bar(ax, fmt='{:.0f}', pad=0.04)\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
        ),
        md(
            "## 8. station별 성능 비교\n\n"
            "이 절에서는 split별 RMSE, MAE, R^2를 비교하고, "
            "마지막에는 두 target의 test R^2 평균으로 통합 랭킹을 만듭니다."
        ),
        code(
            "metric_summary_df = (\n"
            "    metrics_df.groupby(['target', 'split'], as_index=False)\n"
            "    .agg(\n"
            "        rmse_mean=('rmse', 'mean'),\n"
            "        mae_mean=('mae', 'mean'),\n"
            "        r2_mean=('r2', 'mean'),\n"
            "        r2_min=('r2', 'min'),\n"
            "        r2_max=('r2', 'max'),\n"
            "    )\n"
            ")\n"
            "metric_summary_df['split'] = pd.Categorical(metric_summary_df['split'], categories=SPLIT_ORDER, ordered=True)\n"
            "metric_summary_df.sort_values(['target', 'split']).round(4)\n"
        ),
        code(
            "for target in TARGETS:\n"
            "    view = metrics_df[metrics_df['target'] == target].copy()\n"
            "    pivot_r2 = view.pivot(index='station_id', columns='split', values='r2').reindex(TOP20_STATIONS)\n"
            "    pivot_rmse = view.pivot(index='station_id', columns='split', values='rmse').reindex(TOP20_STATIONS)\n"
            "    fig, axes = plt.subplots(1, 2, figsize=(18, 6))\n"
            "    pivot_r2[SPLIT_ORDER].plot(kind='bar', ax=axes[0], color=['#1f4e79', '#6b4c9a', '#2e8b57'], width=0.82)\n"
            "    format_axis(axes[0], f'{target}의 split별 R^2', 'station_id', 'R^2', grid_axis='y')\n"
            "    axes[0].tick_params(axis='x', rotation=45)\n"
            "    axes[0].legend(title='split', frameon=True, loc='upper right')\n"
            "    pivot_rmse[SPLIT_ORDER].plot(kind='bar', ax=axes[1], color=['#1f4e79', '#6b4c9a', '#d97a04'], width=0.82)\n"
            "    format_axis(axes[1], f'{target}의 split별 RMSE', 'station_id', 'RMSE', grid_axis='y')\n"
            "    axes[1].tick_params(axis='x', rotation=45)\n"
            "    axes[1].legend(title='split', frameon=True, loc='upper right')\n"
            "    plt.tight_layout()\n"
            "    plt.show()\n"
        ),
        code(
            "test_metric_df = metrics_df[(metrics_df['split'] == 'test') & (metrics_df['target'].isin(TARGETS))].copy()\n"
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
            "ranking_df = ranking_df.merge(station_meta_df[['station_id', 'station_name', 'station_label', 'latitude', 'longitude']], on='station_id', how='left')\n"
            "ranking_df.index = ranking_df.index + 1\n"
            "ranking_df.to_csv(DATA_DIR / 'summaries/top20_station_combined_test_r2_ranking.csv', index_label='rank', encoding='utf-8-sig')\n"
            "ranking_df\n"
        ),
        code(
            "plot_df = ranking_df.reset_index().rename(columns={'index': 'rank'})\n"
            "fig, axes = plt.subplots(1, 3, figsize=(22, 8), sharey=True)\n"
            "sns.barplot(data=plot_df, x='combined_test_r2', y='station_label', ax=axes[0], color='#4C78A8')\n"
            "format_axis(axes[0], '통합 test R^2 랭킹', '평균 test R^2', 'station')\n"
            "annotate_barh(axes[0], fmt='{:.3f}', pad=0.02)\n"
            "\n"
            "sns.barplot(data=plot_df, x='combined_test_rmse', y='station_label', ax=axes[1], color='#F58518')\n"
            "format_axis(axes[1], '통합 test RMSE', '평균 RMSE', 'station')\n"
            "annotate_barh(axes[1], fmt='{:.3f}', pad=0.02)\n"
            "\n"
            "sns.barplot(data=plot_df, x='combined_test_mae', y='station_label', ax=axes[2], color='#54A24B')\n"
            "format_axis(axes[2], '통합 test MAE', '평균 MAE', 'station')\n"
            "annotate_barh(axes[2], fmt='{:.3f}', pad=0.02)\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "\n"
            "plot_df[['rank', 'station_id', 'station_name', 'rental_count', 'return_count', 'combined_test_r2', 'combined_test_rmse', 'combined_test_mae']]\n"
        ),
        md(
            "## 9. 상위 6개 station 심화 분석\n\n"
            "통합 test R^2 기준으로 가장 성능이 좋은 상위 6개 station을 별도로 선정해, "
            "성능 구성, 주요 feature, 연도별 패턴 재현력, 오차 특성을 더 자세히 살펴봅니다."
        ),
        code(
            "top6_station_ids = ranking_df.head(6)['station_id'].astype(int).tolist()\n"
            "top6_summary_df = ranking_df[ranking_df['station_id'].isin(top6_station_ids)].copy()\n"
            "top6_summary_df = top6_summary_df.set_index('station_id').loc[top6_station_ids].reset_index()\n"
            "top6_summary_df\n"
        ),
        code(
            "top6_plot_df = top6_summary_df.copy()\n"
            "fig, axes = plt.subplots(1, 2, figsize=(18, 6))\n"
            "sns.barplot(data=top6_plot_df, x='combined_test_r2', y='station_label', ax=axes[0], color='#1f4e79')\n"
            "format_axis(axes[0], '상위 6개 station의 통합 test R^2', '통합 test R^2', 'station')\n"
            "annotate_barh(axes[0], fmt='{:.3f}', pad=0.02)\n"
            "\n"
            "top6_target_df = top6_plot_df.melt(id_vars=['station_id', 'station_name', 'station_label', 'latitude', 'longitude'], value_vars=['rental_count', 'return_count'], var_name='target', value_name='test_r2')\n"
            "sns.barplot(data=top6_target_df, x='test_r2', y='station_label', hue='target', ax=axes[1], palette=['#1f4e79', '#d97a04'])\n"
            "format_axis(axes[1], '상위 6개 station의 target별 test R^2', 'test R^2', 'station')\n"
            "axes[1].legend(title='target', frameon=True, loc='lower right')\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "\n"
            "top6_map = folium.Map(location=[top6_plot_df['latitude'].mean(), top6_plot_df['longitude'].mean()], zoom_start=13, tiles='CartoDB positron')\n"
            "for _, row in top6_plot_df.iterrows():\n"
            "    popup_html = f\"<b>{row['station_name']}</b><br>station_id: {int(row['station_id'])}<br>통합 test R^2: {row['combined_test_r2']:.3f}\"\n"
            "    folium.Marker(location=[row['latitude'], row['longitude']], popup=popup_html, tooltip=row['station_label'], icon=folium.Icon(color='blue', icon='info-sign')).add_to(top6_map)\n"
            "top6_map\n"
        ),
        code(
            "top6_importance_df = importance_all_df[importance_all_df['station_id'].isin(top6_station_ids)].copy()\n"
            "for target in TARGETS:\n"
            "    target_df = top6_importance_df[top6_importance_df['target'] == target].copy()\n"
            "    target_df = target_df.merge(station_meta_df[['station_id', 'station_label']], on='station_id', how='left')\n"
            "    pivot_df = target_df.pivot(index='feature', columns='station_label', values='importance_ratio')\n"
            "    plt.figure(figsize=(12, 5.5))\n"
            "    sns.heatmap(pivot_df, annot=True, fmt='.2f', cmap='Blues', linewidths=0.4, linecolor='white', cbar_kws={'shrink': 0.8, 'label': '중요도 비율'})\n"
            "    plt.title(f'상위 6개 station feature 중요도 비교: {target}', fontsize=13, fontweight='bold', pad=12)\n"
            "    plt.xlabel('station')\n"
            "    plt.ylabel('feature')\n"
            "    plt.xticks(rotation=20, ha='right', fontsize=8)\n"
            "    plt.yticks(fontsize=9)\n"
            "    plt.tight_layout()\n"
            "    plt.show()\n"
        ),
        code(
            "for target in TARGETS:\n"
            "    target_df = comparison_all_df[(comparison_all_df['target'] == target) & (comparison_all_df['granularity'] == 'hour') & (comparison_all_df['station_id'].isin(top6_station_ids))].copy()\n"
            "    yearly = (\n"
            "        target_df.pivot_table(index=['station_id', 'year', 'key'], columns='series', values='value', aggfunc='mean')\n"
            "        .reset_index()\n"
            "    )\n"
            "    fig, axes = plt.subplots(2, 3, figsize=(18, 9), sharex=True, sharey=True)\n"
            "    axes = axes.flatten()\n"
            "    for ax, station_id in zip(axes, top6_station_ids):\n"
            "        station_df = yearly[yearly['station_id'] == station_id]\n"
            "        for year in sorted(station_df['year'].dropna().unique()):\n"
            "            part = station_df[station_df['year'] == year]\n"
            "            ax.plot(part['key'], part['actual_value'], label=f'{int(year)} 실제', linewidth=2.0)\n"
            "            ax.plot(part['key'], part['prediction'], linestyle='--', label=f'{int(year)} 예측', linewidth=1.8)\n"
            "        ax.set_title(f'Station {station_id}', fontsize=11, fontweight='bold')\n"
            "        ax.grid(axis='y', alpha=0.18, linestyle='--')\n"
            "    handles, labels = axes[0].get_legend_handles_labels()\n"
            "    fig.legend(handles, labels, loc='upper center', ncol=3)\n"
            "    fig.suptitle(f'상위 6개 station의 연도별 시간 패턴 비교: {target}', y=0.995, fontsize=14, fontweight='bold')\n"
            "    plt.tight_layout(rect=[0, 0, 1, 0.95])\n"
            "    plt.show()\n"
        ),
        code(
            "top6_error_df = error_all_df[error_all_df['station_id'].isin(top6_station_ids)].copy()\n"
            "top6_error_summary_df = (\n"
            "    top6_error_df.groupby(['station_id', 'target'], as_index=False)\n"
            "    .agg(\n"
            "        mean_abs_error=('abs_error', 'mean'),\n"
            "        max_abs_error=('abs_error', 'max'),\n"
            "    )\n"
            ")\n"
            "top6_error_summary_df = top6_error_summary_df.merge(station_meta_df[['station_id', 'station_label', 'station_name']], on='station_id', how='left')\n"
            "display(top6_error_summary_df.round(4))\n"
            "\n"
            "plt.figure(figsize=(12, 5.5))\n"
            "sns.barplot(data=top6_error_summary_df, x='mean_abs_error', y='station_label', hue='target', palette=['#9c2f2f', '#d97a04'])\n"
            "format_axis(plt.gca(), '상위 6개 station의 평균 절대오차 비교', '평균 절대오차', 'station')\n"
            "plt.legend(title='target', frameon=True, loc='lower right')\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
        ),
        md(
            "## 10. 중요 feature와 오차 진단\n\n"
            "단순 랭킹만으로는 모델을 설명하기 어렵기 때문에, 여기서는 모델이 반복적으로 의존한 feature와 "
            "2025년에 오차가 많이 발생한 시점을 함께 정리합니다."
        ),
        code(
            "importance_summary_df = (\n"
            "    importance_all_df.groupby(['target', 'feature'], as_index=False)['importance_ratio']\n"
            "    .mean()\n"
            "    .sort_values(['target', 'importance_ratio'], ascending=[True, False])\n"
            ")\n"
            "importance_summary_df.round(4)\n"
        ),
        code(
            "for target in TARGETS:\n"
            "    target_df = importance_summary_df[importance_summary_df['target'] == target].copy()\n"
            "    plt.figure(figsize=(10, 5))\n"
            "    sns.barplot(data=target_df, x='importance_ratio', y='feature', color='#4C78A8')\n"
            "    plt.title(f'top20 station 평균 feature 중요도: {target}')\n"
            "    plt.xlabel('평균 정규화 중요도')\n"
            "    plt.ylabel('feature')\n"
            "    annotate_barh(plt.gca(), fmt='{:.3f}', pad=0.02)\n"
            "    plt.tight_layout()\n"
            "    plt.show()\n"
        ),
        md(
            "## 11. 2025 테스트 오차 hotspot\n\n"
            "각 station에서 추출한 고오차 시점을 합쳐, 현재 feature 구성으로 설명이 어려운 공통 월과 시간대를 확인합니다."
        ),
        code(
            "error_summary_df = (\n"
            "    error_all_df.groupby(['station_id', 'target'], as_index=False)\n"
            "    .agg(\n"
            "        hotspot_count=('abs_error', 'size'),\n"
            "        mean_abs_error=('abs_error', 'mean'),\n"
            "        max_abs_error=('abs_error', 'max'),\n"
            "    )\n"
            "    .sort_values(['mean_abs_error', 'max_abs_error'], ascending=False)\n"
            ")\n"
            "display(error_summary_df.head(12).round(4))\n"
            "\n"
            "hotspot_time_df = (\n"
            "    error_all_df.groupby(['target', 'month', 'hour'], as_index=False)\n"
            "    .agg(\n"
            "        hotspot_count=('abs_error', 'size'),\n"
            "        mean_abs_error=('abs_error', 'mean'),\n"
            "    )\n"
            ")\n"
            "hotspot_time_df.sort_values(['target', 'hotspot_count', 'mean_abs_error'], ascending=[True, False, False]).head(20)\n"
        ),
        code(
            "fig, axes = plt.subplots(1, 2, figsize=(18, 6))\n"
            "for ax, target in zip(axes, TARGETS):\n"
            "    sub = hotspot_time_df[hotspot_time_df['target'] == target]\n"
            "    pivot = sub.pivot(index='month', columns='hour', values='mean_abs_error').sort_index()\n"
            "    sns.heatmap(pivot, cmap='YlOrRd', ax=ax, linewidths=0.4, linecolor='white', cbar_kws={'shrink': 0.8, 'label': '평균 절대오차'})\n"
            "    ax.set_title(f'{target}의 평균 절대오차 hotspot 히트맵')\n"
            "    ax.set_xlabel('hour')\n"
            "    ax.set_ylabel('month')\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
        ),
        md(
            "## 12. 최종 결론\n\n"
            "마지막으로 통합 랭킹, 반복적으로 중요한 feature, test hotspot 결과를 한 번에 묶어 요약합니다."
        ),
        code(
            "top5_df = ranking_df.head(5)[['station_id', 'combined_test_r2', 'combined_test_rmse', 'combined_test_mae']].copy()\n"
            "bottom5_df = ranking_df.tail(5)[['station_id', 'combined_test_r2', 'combined_test_rmse', 'combined_test_mae']].copy()\n"
            "top_feature_df = (\n"
            "    importance_summary_df.sort_values(['target', 'importance_ratio'], ascending=[True, False])\n"
            "    .groupby('target', as_index=False)\n"
            "    .first()[['target', 'feature', 'importance_ratio']]\n"
            ")\n"
            "conclusion_summary_df = pd.DataFrame([\n"
            "    {'item': '통합 test R^2 1위 station', 'value': int(ranking_df.iloc[0]['station_id'])},\n"
            "    {'item': '1위 station의 통합 test R^2', 'value': float(ranking_df.iloc[0]['combined_test_r2'])},\n"
            "    {'item': '통합 test R^2 중앙값', 'value': float(ranking_df['combined_test_r2'].median())},\n"
            "    {'item': '통합 test R^2 최하위 station', 'value': int(ranking_df.iloc[-1]['station_id'])},\n"
            "    {'item': 'rental_count 공통 핵심 feature', 'value': top_feature_df[top_feature_df['target'] == 'rental_count']['feature'].iloc[0]},\n"
            "    {'item': 'return_count 공통 핵심 feature', 'value': top_feature_df[top_feature_df['target'] == 'return_count']['feature'].iloc[0]},\n"
            "])\n"
            "display(conclusion_summary_df)\n"
            "display(top5_df.round(4))\n"
            "display(bottom5_df.round(4))\n"
            "display(top_feature_df.round(4))\n"
            "\n"
            "print('해석 가이드')\n"
            "print('- 통합 점수는 rental_count와 return_count의 test R^2 평균입니다.')\n"
            "print('- 상위 station일수록 시간대 패턴 재현력이 안정적인 경우가 많습니다.')\n"
            "print('- 반복적으로 나타나는 hotspot 월과 시간대는 후속 외생 변수 보강 후보입니다.')\n"
        ),
        md(
            "## 13. 현재 구조에서 재고 예측을 해석하는 방법\n\n"
            "현재 모델은 특정 시점의 **총 보유 대수**를 직접 예측하는 구조가 아니라, "
            "각 시간대의 `rental_count`와 `return_count`를 예측하는 구조입니다.\n\n"
            "따라서 API 등을 통해 **현재 시점의 실제 자전거 수량**을 알고 있다면, 이후 재고는 다음과 같이 누적 계산할 수 있습니다.\n\n"
            "`다음 시점 재고 = 현재 재고 - 예측 rental_count + 예측 return_count`\n\n"
            "이 방식은 몇 시간 뒤 또는 하루 이내처럼 **단기 재고 흐름**을 보는 데는 활용할 수 있지만, "
            "며칠 뒤처럼 예측 구간이 길어질수록 대여/반납 예측 오차가 누적되기 때문에 신뢰도가 빠르게 낮아질 수 있습니다.\n\n"
            "또한 실제 운영에서는 재배치, 거치대 용량, 돌발 이벤트 같은 요소가 재고에 영향을 주므로, "
            "장기 재고 예측까지 안정적으로 수행하려면 이후에는 `총 재고` 자체를 직접 예측하는 모델이나 "
            "재배치/외생 변수까지 포함한 구조로 확장하는 것이 더 적절합니다."
        ),
        code(
            "inventory_note_df = pd.DataFrame([\n"
            "    {'구분': '현재 모델의 직접 예측값', '설명': '시간대별 rental_count, return_count'},\n"
            "    {'구분': '재고 계산 방식', '설명': '현재 재고 - 예측 대여량 + 예측 반납량의 누적 합'},\n"
            "    {'구분': '상대적으로 적합한 범위', '설명': '몇 시간 뒤 ~ 하루 이내의 단기 재고 흐름'},\n"
            "    {'구분': '주의가 필요한 범위', '설명': '며칠 후 재고처럼 누적 오차가 커지는 장기 예측'},\n"
            "    {'구분': '오차 확대 요인', '설명': '재배치, 거치대 한계, 이벤트, 날씨 급변, 시간 누적 오차'},\n"
            "])\n"
            "inventory_note_df\n"
        ),
    ]

    notebook = nbformat.v4.new_notebook(
        cells=cells,
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
    if SOURCE_PATH.exists():
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
