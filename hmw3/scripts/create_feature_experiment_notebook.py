from __future__ import annotations

import json
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


ROOT = Path(__file__).resolve().parents[2]
HMW3_DIR = ROOT / "hmw3"
DATA_DIR = HMW3_DIR / "Data"
FEATURE_DIR = HMW3_DIR / "feature"
NOTEBOOK_PATH = FEATURE_DIR / "hmw_feature.ipynb"
SUMMARY_DIR = DATA_DIR / "summaries"

TOP6_PATH = SUMMARY_DIR / "top20_station_combined_test_r2_ranking.csv"
RAW_DIR = DATA_DIR / "station_raw"
FORMULA_DIR = DATA_DIR / "formulas"
WEIGHTS_DIR = DATA_DIR / "weights"

METRICS_OUTPUT = SUMMARY_DIR / "feature_top6_experiment_metrics.csv"
BEST_TARGET_OUTPUT = SUMMARY_DIR / "feature_top6_best_by_target.csv"
BEST_STATION_OUTPUT = SUMMARY_DIR / "feature_top6_best_by_station.csv"
BEST_SUMMARY_OUTPUT = SUMMARY_DIR / "feature_top6_station_optimal_summary.csv"
INTERPRETATION_OUTPUT = SUMMARY_DIR / "feature_top6_station_interpretation.csv"
SUMMARY_MD_PATH = FEATURE_DIR / "hmw_feature_summary.md"


ALPHAS = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
TARGETS = ["rental_count", "return_count"]
SPLIT_ORDER = ["train", "valid", "test"]


def season_from_month(month: int) -> str:
    if month in [12, 1, 2]:
        return "winter"
    if month in [3, 4, 5]:
        return "spring"
    if month in [6, 7, 8]:
        return "summer"
    return "autumn"


def rush_bucket(hour: int) -> str:
    if hour in [7, 8, 9]:
        return "morning_peak"
    if hour in [17, 18, 19]:
        return "evening_peak"
    return "other"


def resolve_weight(weight_map: dict[str, float], key: str | int) -> float:
    key_str = str(key)
    if key_str in weight_map:
        return float(weight_map[key_str])
    return 1.0


def compute_base_value(formula_params: dict[str, float], hour: int) -> float:
    angle = 2 * np.pi * hour / 24.0
    return (
        formula_params["intercept"]
        + formula_params["sin_hour_coef"] * np.sin(angle)
        + formula_params["cos_hour_coef"] * np.cos(angle)
    )


def build_train_weight_map(df: pd.DataFrame, group_cols: list[str], target: str) -> dict[str, float]:
    overall_mean = df[target].mean()
    if overall_mean <= 0:
        return {}
    grouped = df.groupby(group_cols, as_index=False)[target].mean()
    weight_map: dict[str, float] = {}
    for _, row in grouped.iterrows():
        key = "__".join(str(row[col]) for col in group_cols)
        weight_map[key] = float(row[target] / overall_mean)
    return weight_map


def load_station_components(station_id: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw_df = pd.read_csv(RAW_DIR / f"station_{station_id}.csv")
    formula_df = pd.read_csv(FORMULA_DIR / f"station_{station_id}_offday_hour_formulas.csv")
    weight_df = pd.read_csv(WEIGHTS_DIR / f"station_{station_id}_month_weights.csv")
    return raw_df, formula_df, weight_df


def prepare_station_frame(station_id: int) -> pd.DataFrame:
    raw_df, formula_df, weight_df = load_station_components(station_id)
    raw_df["time"] = pd.to_datetime(raw_df["time"])
    raw_df["date"] = raw_df["time"].dt.strftime("%Y-%m-%d")
    raw_df["split"] = raw_df["year"].map({2023: "train", 2024: "valid", 2025: "test"})
    raw_df["is_weekend"] = raw_df["weekday"] >= 5

    holiday_df = pd.read_csv(DATA_DIR / "holiday_reference" / f"station_{station_id}_holiday_reference.csv")
    holiday_dates = set(pd.to_datetime(holiday_df["date"]).dt.strftime("%Y-%m-%d").tolist())
    raw_df["is_holiday"] = raw_df["date"].isin(holiday_dates)
    raw_df["day_type"] = np.where(raw_df["is_weekend"] | raw_df["is_holiday"], "offday", "weekday")
    raw_df["quarter"] = ((raw_df["month"] - 1) // 3 + 1).astype(int)
    raw_df["season"] = raw_df["month"].apply(season_from_month)
    raw_df["rush_bucket"] = raw_df["hour"].apply(rush_bucket)
    raw_df["month_day_type_key"] = raw_df["month"].astype(str) + "__" + raw_df["day_type"]
    raw_df["weekday_key"] = raw_df["weekday"].astype(str)
    raw_df["season_key"] = raw_df["season"]
    raw_df["quarter_key"] = raw_df["quarter"].astype(str)
    raw_df["rush_bucket_key"] = raw_df["rush_bucket"]

    formula_map: dict[str, dict[str, dict[str, float]]] = {}
    for target in TARGETS:
        formula_map[target] = {}
        sub = formula_df[formula_df["target"] == target].copy()
        for _, row in sub.iterrows():
            formula_map[target][row["day_type"]] = {
                "intercept": float(row["intercept"]),
                "sin_hour_coef": float(row["sin_hour_coef"]),
                "cos_hour_coef": float(row["cos_hour_coef"]),
            }

    weight_maps: dict[str, dict[str, dict[str, float]]] = {"month_weight": {}, "year_weight": {}, "hour_weight": {}}
    for target in TARGETS:
        sub = weight_df[weight_df["target"] == target].copy()
        for weight_type in ["month_weight", "year_weight", "hour_weight"]:
            target_sub = sub[sub["weight_type"] == weight_type]
            weight_maps[weight_type][target] = {str(row["key"]): float(row["value"]) for _, row in target_sub.iterrows()}

    for target in TARGETS:
        raw_df[f"{target}_base_value"] = raw_df.apply(
            lambda row: compute_base_value(formula_map[target][row["day_type"]], int(row["hour"])),
            axis=1,
        )
        raw_df[f"{target}_month_weight"] = raw_df["month"].apply(
            lambda x: resolve_weight(weight_maps["month_weight"][target], int(x))
        )
        raw_df[f"{target}_year_weight"] = raw_df["year"].apply(
            lambda x: resolve_weight(weight_maps["year_weight"][target], int(x))
        )
        raw_df[f"{target}_hour_weight"] = raw_df["hour"].apply(
            lambda x: resolve_weight(weight_maps["hour_weight"][target], int(x))
        )
        raw_df[f"{target}_pattern_prior"] = (
            raw_df[f"{target}_base_value"]
            * raw_df[f"{target}_month_weight"]
            * raw_df[f"{target}_year_weight"]
        )
        raw_df[f"{target}_corrected_pattern_prior"] = (
            raw_df[f"{target}_pattern_prior"] * raw_df[f"{target}_hour_weight"]
        )

        train_df = raw_df[raw_df["split"] == "train"].copy()
        weekday_weight_map = build_train_weight_map(train_df, ["weekday_key"], target)
        season_weight_map = build_train_weight_map(train_df, ["season_key"], target)
        quarter_weight_map = build_train_weight_map(train_df, ["quarter_key"], target)
        rush_weight_map = build_train_weight_map(train_df, ["rush_bucket_key"], target)
        month_day_type_map = build_train_weight_map(train_df, ["month_day_type_key"], target)

        raw_df[f"{target}_weekday_weight"] = raw_df["weekday_key"].apply(lambda x: resolve_weight(weekday_weight_map, x))
        raw_df[f"{target}_season_weight"] = raw_df["season_key"].apply(lambda x: resolve_weight(season_weight_map, x))
        raw_df[f"{target}_quarter_weight"] = raw_df["quarter_key"].apply(lambda x: resolve_weight(quarter_weight_map, x))
        raw_df[f"{target}_rush_hour_weight"] = raw_df["rush_bucket_key"].apply(lambda x: resolve_weight(rush_weight_map, x))
        raw_df[f"{target}_month_day_type_weight"] = raw_df["month_day_type_key"].apply(lambda x: resolve_weight(month_day_type_map, x))

        raw_df[f"{target}_weekday_adjusted_prior"] = raw_df[f"{target}_corrected_pattern_prior"] * raw_df[f"{target}_weekday_weight"]
        raw_df[f"{target}_season_adjusted_prior"] = raw_df[f"{target}_corrected_pattern_prior"] * raw_df[f"{target}_season_weight"]
        raw_df[f"{target}_quarter_adjusted_prior"] = raw_df[f"{target}_corrected_pattern_prior"] * raw_df[f"{target}_quarter_weight"]
        raw_df[f"{target}_rush_hour_adjusted_prior"] = raw_df[f"{target}_corrected_pattern_prior"] * raw_df[f"{target}_rush_hour_weight"]
        raw_df[f"{target}_month_day_type_adjusted_prior"] = raw_df[f"{target}_corrected_pattern_prior"] * raw_df[f"{target}_month_day_type_weight"]

    raw_df["day_type_weekday"] = (raw_df["day_type"] == "weekday").astype(float)
    raw_df["day_type_offday"] = (raw_df["day_type"] == "offday").astype(float)
    return raw_df


def get_feature_sets(target: str) -> dict[str, list[str]]:
    prefix = f"{target}_"
    baseline = [
        prefix + "base_value",
        prefix + "month_weight",
        prefix + "year_weight",
        prefix + "hour_weight",
        prefix + "pattern_prior",
        prefix + "corrected_pattern_prior",
        "day_type_weekday",
        "day_type_offday",
    ]
    return {
        "baseline": baseline,
        "baseline_plus_weekday": baseline + [prefix + "weekday_weight", prefix + "weekday_adjusted_prior"],
        "baseline_plus_season": baseline + [prefix + "season_weight", prefix + "season_adjusted_prior"],
        "baseline_plus_quarter": baseline + [prefix + "quarter_weight", prefix + "quarter_adjusted_prior"],
        "baseline_plus_rush_hour": baseline + [prefix + "rush_hour_weight", prefix + "rush_hour_adjusted_prior"],
        "baseline_plus_month_day_type": baseline + [prefix + "month_day_type_weight", prefix + "month_day_type_adjusted_prior"],
        "all_extended": baseline
        + [
            prefix + "weekday_weight",
            prefix + "weekday_adjusted_prior",
            prefix + "season_weight",
            prefix + "season_adjusted_prior",
            prefix + "quarter_weight",
            prefix + "quarter_adjusted_prior",
            prefix + "rush_hour_weight",
            prefix + "rush_hour_adjusted_prior",
            prefix + "month_day_type_weight",
            prefix + "month_day_type_adjusted_prior",
        ],
    }


def evaluate_predictions(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    clipped = np.clip(y_pred, 0.0, None)
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, clipped))),
        "mae": float(mean_absolute_error(y_true, clipped)),
        "r2": float(r2_score(y_true, clipped)),
    }


def run_feature_experiments() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ranking_df = pd.read_csv(TOP6_PATH).head(6).copy()
    top6_station_ids = ranking_df["station_id"].astype(int).tolist()

    metric_rows: list[dict] = []

    for station_id in top6_station_ids:
        station_name = ranking_df.loc[ranking_df["station_id"] == station_id, "station_name"].iloc[0]
        station_df = prepare_station_frame(station_id)

        for target in TARGETS:
            feature_sets = get_feature_sets(target)
            train_df = station_df[station_df["split"] == "train"].copy()
            valid_df = station_df[station_df["split"] == "valid"].copy()
            test_df = station_df[station_df["split"] == "test"].copy()
            y_train = train_df[target]
            y_valid = valid_df[target]
            y_test = test_df[target]

            for feature_set_name, feature_cols in feature_sets.items():
                X_train = train_df[feature_cols]
                X_valid = valid_df[feature_cols]
                X_test = test_df[feature_cols]

                best_alpha = None
                best_valid_rmse = None
                best_model = None

                for alpha in ALPHAS:
                    model = Ridge(alpha=alpha)
                    model.fit(X_train, y_train)
                    valid_metrics = evaluate_predictions(y_valid, model.predict(X_valid))
                    if best_valid_rmse is None or valid_metrics["rmse"] < best_valid_rmse:
                        best_valid_rmse = valid_metrics["rmse"]
                        best_alpha = alpha
                        best_model = model

                assert best_model is not None

                for split_name, X_split, y_split in [
                    ("train", X_train, y_train),
                    ("valid", X_valid, y_valid),
                    ("test", X_test, y_test),
                ]:
                    metrics = evaluate_predictions(y_split, best_model.predict(X_split))
                    metric_rows.append({
                        "station_id": station_id,
                        "station_name": station_name,
                        "target": target,
                        "feature_set": feature_set_name,
                        "alpha": best_alpha,
                        "split": split_name,
                        **metrics,
                    })

    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(METRICS_OUTPUT, index=False, encoding="utf-8-sig")

    valid_df = metrics_df[metrics_df["split"] == "valid"].copy()
    best_target_df = (
        valid_df.sort_values(["station_id", "target", "r2", "rmse", "mae"], ascending=[True, True, False, True, True])
        .groupby(["station_id", "target"], as_index=False)
        .first()
        .sort_values(["station_id", "target"])
        .reset_index(drop=True)
    )
    best_target_df.to_csv(BEST_TARGET_OUTPUT, index=False, encoding="utf-8-sig")

    station_valid_pivot = (
        valid_df.pivot_table(index=["station_id", "station_name", "feature_set"], columns="target", values=["rmse", "mae", "r2"], aggfunc="mean")
        .reset_index()
    )
    station_valid_pivot.columns = [
        "station_id" if col == ("station_id", "") else
        "station_name" if col == ("station_name", "") else
        "feature_set" if col == ("feature_set", "") else
        f"{col[1]}_{col[0]}" for col in station_valid_pivot.columns
    ]
    station_valid_pivot["combined_valid_r2"] = station_valid_pivot[["rental_count_r2", "return_count_r2"]].mean(axis=1)
    station_valid_pivot["combined_valid_rmse"] = station_valid_pivot[["rental_count_rmse", "return_count_rmse"]].mean(axis=1)
    station_valid_pivot["combined_valid_mae"] = station_valid_pivot[["rental_count_mae", "return_count_mae"]].mean(axis=1)

    best_station_df = (
        station_valid_pivot.sort_values(
            ["station_id", "combined_valid_r2", "combined_valid_rmse", "combined_valid_mae"],
            ascending=[True, False, True, True],
        )
        .groupby("station_id", as_index=False)
        .first()
        .sort_values("station_id")
        .reset_index(drop=True)
    )
    best_station_df.to_csv(BEST_STATION_OUTPUT, index=False, encoding="utf-8-sig")

    rental_best_df = (
        best_target_df[best_target_df["target"] == "rental_count"][
            ["station_id", "feature_set", "alpha", "rmse", "mae", "r2"]
        ]
        .rename(columns={
            "feature_set": "rental_best_feature_set",
            "alpha": "rental_best_alpha",
            "rmse": "rental_valid_rmse",
            "mae": "rental_valid_mae",
            "r2": "rental_valid_r2",
        })
    )
    return_best_df = (
        best_target_df[best_target_df["target"] == "return_count"][
            ["station_id", "feature_set", "alpha", "rmse", "mae", "r2"]
        ]
        .rename(columns={
            "feature_set": "return_best_feature_set",
            "alpha": "return_best_alpha",
            "rmse": "return_valid_rmse",
            "mae": "return_valid_mae",
            "r2": "return_valid_r2",
        })
    )
    combined_best_df = best_station_df[
        [
            "station_id",
            "station_name",
            "feature_set",
            "combined_valid_r2",
            "combined_valid_rmse",
            "combined_valid_mae",
        ]
    ].rename(columns={"feature_set": "combined_best_feature_set"})

    station_summary_df = (
        combined_best_df
        .merge(rental_best_df, on="station_id", how="left")
        .merge(return_best_df, on="station_id", how="left")
        .sort_values("station_id")
        .reset_index(drop=True)
    )
    baseline_valid_df = (
        valid_df[valid_df["feature_set"] == "baseline"][
            ["station_id", "target", "rmse", "mae", "r2"]
        ]
        .rename(columns={
            "rmse": "baseline_valid_rmse",
            "mae": "baseline_valid_mae",
            "r2": "baseline_valid_r2",
        })
    )
    target_compare_df = (
        best_target_df.merge(baseline_valid_df, on=["station_id", "target"], how="left")
        .assign(
            delta_r2=lambda df: df["r2"] - df["baseline_valid_r2"],
            delta_rmse=lambda df: df["rmse"] - df["baseline_valid_rmse"],
            delta_mae=lambda df: df["mae"] - df["baseline_valid_mae"],
        )
    )

    interpretation_rows: list[dict] = []
    for station_id in station_summary_df["station_id"]:
        station_name = station_summary_df.loc[station_summary_df["station_id"] == station_id, "station_name"].iloc[0]
        rental_row = target_compare_df[
            (target_compare_df["station_id"] == station_id) & (target_compare_df["target"] == "rental_count")
        ].iloc[0]
        return_row = target_compare_df[
            (target_compare_df["station_id"] == station_id) & (target_compare_df["target"] == "return_count")
        ].iloc[0]
        combined_row = station_summary_df[station_summary_df["station_id"] == station_id].iloc[0]

        interpretation_rows.append({
            "station_id": station_id,
            "station_name": station_name,
            "rental_best_feature_set": rental_row["feature_set"],
            "rental_valid_r2": rental_row["r2"],
            "rental_baseline_valid_r2": rental_row["baseline_valid_r2"],
            "rental_delta_r2": rental_row["delta_r2"],
            "rental_delta_rmse": rental_row["delta_rmse"],
            "rental_comment": (
                "개선 폭이 뚜렷함" if rental_row["delta_r2"] >= 0.02 else
                "소폭 개선됨" if rental_row["delta_r2"] > 0.005 else
                "거의 변화 없음" if rental_row["delta_r2"] >= -0.005 else
                "baseline보다 악화됨"
            ),
            "return_best_feature_set": return_row["feature_set"],
            "return_valid_r2": return_row["r2"],
            "return_baseline_valid_r2": return_row["baseline_valid_r2"],
            "return_delta_r2": return_row["delta_r2"],
            "return_delta_rmse": return_row["delta_rmse"],
            "return_comment": (
                "개선 폭이 뚜렷함" if return_row["delta_r2"] >= 0.02 else
                "소폭 개선됨" if return_row["delta_r2"] > 0.005 else
                "거의 변화 없음" if return_row["delta_r2"] >= -0.005 else
                "baseline보다 악화됨"
            ),
            "combined_best_feature_set": combined_row["combined_best_feature_set"],
            "combined_valid_r2": combined_row["combined_valid_r2"],
        })

    interpretation_df = pd.DataFrame(interpretation_rows).sort_values("station_id").reset_index(drop=True)
    station_summary_df.to_csv(BEST_SUMMARY_OUTPUT, index=False, encoding="utf-8-sig")
    interpretation_df.to_csv(INTERPRETATION_OUTPUT, index=False, encoding="utf-8-sig")
    return metrics_df, best_target_df, best_station_df, station_summary_df, interpretation_df


def create_notebook() -> None:
    summary_md_text = ""
    if SUMMARY_MD_PATH.exists():
        summary_md_text = SUMMARY_MD_PATH.read_text(encoding="utf-8")

    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell(
            "# Feature Expansion Experiment For Top 6 Stations\n\n"
            "`hmw_station.ipynb`의 baseline 구조를 유지하면서, 추가 feature를 station별로 넣어 봤을 때 "
            "어떤 조합이 가장 좋은 `RMSE`, `MAE`, `R²`를 만드는지 비교하는 노트북입니다."
        ),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "from sklearn.linear_model import Ridge\n"
            "from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score\n"
            "\n"
            "CURRENT_DIR = Path.cwd().resolve()\n"
            "ROOT = next((path for path in [CURRENT_DIR, *CURRENT_DIR.parents] if path.name == 'hmw3' and (path / 'Data').exists()), None)\n"
            "if ROOT is None:\n"
            "    raise FileNotFoundError('hmw3/Data 폴더를 찾지 못했습니다. 노트북 실행 위치를 확인해주세요.')\n"
            "DATA_DIR = ROOT / 'Data'\n"
            "SUMMARY_DIR = DATA_DIR / 'summaries'\n"
            "RAW_DIR = DATA_DIR / 'station_raw'\n"
            "FORMULA_DIR = DATA_DIR / 'formulas'\n"
            "WEIGHTS_DIR = DATA_DIR / 'weights'\n"
            "TOP6_PATH = SUMMARY_DIR / 'top20_station_combined_test_r2_ranking.csv'\n"
            "METRICS_OUTPUT = SUMMARY_DIR / 'feature_top6_experiment_metrics.csv'\n"
            "BEST_TARGET_OUTPUT = SUMMARY_DIR / 'feature_top6_best_by_target.csv'\n"
            "BEST_STATION_OUTPUT = SUMMARY_DIR / 'feature_top6_best_by_station.csv'\n"
            "BEST_SUMMARY_OUTPUT = SUMMARY_DIR / 'feature_top6_station_optimal_summary.csv'\n"
            "INTERPRETATION_OUTPUT = SUMMARY_DIR / 'feature_top6_station_interpretation.csv'\n"
            "TOP6_STATION_IDS = pd.read_csv(TOP6_PATH).head(6)['station_id'].astype(int).tolist()\n"
            "TARGETS = ['rental_count', 'return_count']\n"
            "ALPHAS = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]\n"
            "TOP6_STATION_IDS"
        ),
        nbformat.v4.new_markdown_cell(
            "## 1. 실험 대상 station\n\n"
            "이번 실험은 `hmw_station.ipynb`에서 선정된 상위 6개 station만 대상으로 합니다."
        ),
        nbformat.v4.new_code_cell(
            "top6_df = pd.read_csv(TOP6_PATH).head(6).copy()\n"
            "top6_df[['rank', 'station_id', 'station_name', 'combined_test_r2', 'combined_test_rmse', 'combined_test_mae']]"
        ),
        nbformat.v4.new_markdown_cell(
            "## 2. baseline과 추가 feature 시스템\n\n"
            "baseline은 기존 station 모델이 쓰던 패턴 feature를 유지합니다.\n\n"
            "추가 feature는 모두 `월/시간 보정`과 비슷하게 **가중치(weight) + 보정 prior** 형태로 붙입니다.\n\n"
            "실험하는 추가 feature 세트:\n\n"
            "- `baseline_plus_weekday`\n"
            "- `baseline_plus_season`\n"
            "- `baseline_plus_quarter`\n"
            "- `baseline_plus_rush_hour`\n"
            "- `baseline_plus_month_day_type`\n"
            "- `all_extended`"
        ),
        nbformat.v4.new_code_cell(
            "feature_catalog_df = pd.DataFrame([\n"
            "    {'feature_set': 'baseline', 'description': '기존 base/month/year/hour/day_type 기반 feature'},\n"
            "    {'feature_set': 'baseline_plus_weekday', 'description': '요일 weight와 weekday_adjusted_prior 추가'},\n"
            "    {'feature_set': 'baseline_plus_season', 'description': '계절 weight와 season_adjusted_prior 추가'},\n"
            "    {'feature_set': 'baseline_plus_quarter', 'description': '분기 weight와 quarter_adjusted_prior 추가'},\n"
            "    {'feature_set': 'baseline_plus_rush_hour', 'description': 'rush hour weight와 rush_hour_adjusted_prior 추가'},\n"
            "    {'feature_set': 'baseline_plus_month_day_type', 'description': 'month×day_type weight와 조합 prior 추가'},\n"
            "    {'feature_set': 'all_extended', 'description': '위 추가 feature를 전부 결합'},\n"
            "])\n"
            "feature_catalog_df"
        ),
        nbformat.v4.new_markdown_cell(
            "## 3. 실험 로직 함수\n\n"
            "각 station에 대해 train(2023) 데이터에서 추가 weight를 만들고, valid(2024) 기준으로 alpha와 feature set을 선택합니다."
        ),
        nbformat.v4.new_code_cell(
            "def season_from_month" +
            Path(__file__).read_text(encoding="utf-8").split("def season_from_month", 1)[1].split("def create_notebook", 1)[0].strip()
        ),
        nbformat.v4.new_markdown_cell(
            "## 4. 실험 실행 및 결과 저장\n\n"
            "결과는 summary CSV로도 저장됩니다."
        ),
        nbformat.v4.new_code_cell(
            "metrics_df, best_target_df, best_station_df, station_summary_df, interpretation_df = run_feature_experiments()\n"
            "metrics_df.head()"
        ),
        nbformat.v4.new_markdown_cell(
            "## 5. target별 최적 feature set\n\n"
            "station별로 `rental_count`, `return_count` 각각에 대해 valid 기준 최적 feature set을 고릅니다."
        ),
        nbformat.v4.new_code_cell(
            "best_target_df[['station_id', 'station_name', 'target', 'feature_set', 'alpha', 'rmse', 'mae', 'r2']]"
        ),
        nbformat.v4.new_markdown_cell(
            "## 6. station별 통합 최적 feature set\n\n"
            "`rental_count`, `return_count`의 valid 성능을 함께 보고 station 단위 최적 feature set을 정리합니다."
        ),
        nbformat.v4.new_code_cell(
            "best_station_df[['station_id', 'station_name', 'feature_set', 'combined_valid_r2', 'combined_valid_rmse', 'combined_valid_mae']]"
        ),
        nbformat.v4.new_markdown_cell(
            "## 7. station별 최적 feature 요약\n\n"
            "각 station에 대해 `rental_count`, `return_count`, 그리고 두 target을 함께 봤을 때의 종합 최적 feature set을 한 표로 정리합니다."
        ),
        nbformat.v4.new_code_cell(
            "station_summary_df[[\n"
            "    'station_id', 'station_name',\n"
            "    'rental_best_feature_set', 'rental_valid_r2',\n"
            "    'return_best_feature_set', 'return_valid_r2',\n"
            "    'combined_best_feature_set', 'combined_valid_r2'\n"
            "]]"
        ),
        nbformat.v4.new_code_cell(
            "for _, row in station_summary_df.iterrows():\n"
            "    print(\n"
            "        f\"Station {int(row['station_id'])} ({row['station_name'].strip()}): \"\n"
            "        f\"rental -> {row['rental_best_feature_set']} (R2={row['rental_valid_r2']:.4f}), \"\n"
            "        f\"return -> {row['return_best_feature_set']} (R2={row['return_valid_r2']:.4f}), \"\n"
            "        f\"combined -> {row['combined_best_feature_set']} (R2={row['combined_valid_r2']:.4f})\"\n"
            "    )"
        ),
        nbformat.v4.new_markdown_cell(
            "## 8. Feature 설명\n\n"
            "이번 실험에서 사용한 feature set이 각각 무엇을 추가하는지 정리합니다."
        ),
        nbformat.v4.new_code_cell(
            "feature_explain_df = pd.DataFrame([\n"
            "    {'feature_set': 'baseline', 'used_features': 'base_value, month_weight, year_weight, hour_weight, pattern_prior, corrected_pattern_prior, day_type', 'meaning': '기존 hmw_station 모델에서 쓰던 기본 패턴 feature'},\n"
            "    {'feature_set': 'baseline_plus_weekday', 'used_features': 'baseline + weekday_weight + weekday_adjusted_prior', 'meaning': '요일별 수요 차이를 추가로 반영'},\n"
            "    {'feature_set': 'baseline_plus_season', 'used_features': 'baseline + season_weight + season_adjusted_prior', 'meaning': '계절별 규모 차이를 추가로 반영'},\n"
            "    {'feature_set': 'baseline_plus_quarter', 'used_features': 'baseline + quarter_weight + quarter_adjusted_prior', 'meaning': '분기 단위의 패턴 차이를 추가로 반영'},\n"
            "    {'feature_set': 'baseline_plus_rush_hour', 'used_features': 'baseline + rush_hour_weight + rush_hour_adjusted_prior', 'meaning': '출퇴근 피크 시간대 효과를 추가로 반영'},\n"
            "    {'feature_set': 'baseline_plus_month_day_type', 'used_features': 'baseline + month_day_type_weight + month_day_type_adjusted_prior', 'meaning': '월과 weekday/offday 조합 효과를 추가로 반영'},\n"
            "    {'feature_set': 'all_extended', 'used_features': 'baseline + weekday + season + quarter + rush_hour + month_day_type', 'meaning': '확장 feature를 전부 결합한 조합'},\n"
            "])\n"
            "feature_explain_df"
        ),
        nbformat.v4.new_markdown_cell(
            "## 9. station별 해석\n\n"
            "baseline과 비교했을 때 어떤 feature 조합이 개선을 만들었는지 station별로 정리합니다."
        ),
        nbformat.v4.new_code_cell(
            "interpretation_df[[\n"
            "    'station_id', 'station_name',\n"
            "    'rental_best_feature_set', 'rental_baseline_valid_r2', 'rental_valid_r2', 'rental_delta_r2', 'rental_comment',\n"
            "    'return_best_feature_set', 'return_baseline_valid_r2', 'return_valid_r2', 'return_delta_r2', 'return_comment',\n"
            "    'combined_best_feature_set', 'combined_valid_r2'\n"
            "]]"
        ),
        nbformat.v4.new_code_cell(
            "for _, row in interpretation_df.iterrows():\n"
            "    print(f\"[Station {int(row['station_id'])}] {row['station_name'].strip()}\")\n"
            "    print(\n"
            "        f\"- rental_count: {row['rental_best_feature_set']} 사용 시 baseline R2 {row['rental_baseline_valid_r2']:.4f} -> {row['rental_valid_r2']:.4f} \"\n"
            "        f\"(Δ {row['rental_delta_r2']:+.4f}), {row['rental_comment']}\"\n"
            "    )\n"
            "    print(\n"
            "        f\"- return_count: {row['return_best_feature_set']} 사용 시 baseline R2 {row['return_baseline_valid_r2']:.4f} -> {row['return_valid_r2']:.4f} \"\n"
            "        f\"(Δ {row['return_delta_r2']:+.4f}), {row['return_comment']}\"\n"
            "    )\n"
            "    print(\n"
            "        f\"- 종합: {row['combined_best_feature_set']} 조합이 가장 안정적이었고 combined valid R2는 {row['combined_valid_r2']:.4f}\"\n"
            "    )\n"
            "    print()\n"
        ),
        nbformat.v4.new_markdown_cell(
            "## 10. feature set별 valid/test 비교\n\n"
            "어떤 추가 feature가 실제로 개선에 기여하는지 한눈에 보기 위해 station별 valid/test 성능을 비교합니다."
        ),
        nbformat.v4.new_code_cell(
            "summary_view_df = metrics_df[metrics_df['split'].isin(['valid', 'test'])].copy()\n"
            "pivot_df = summary_view_df.pivot_table(index=['station_id', 'feature_set'], columns=['target', 'split'], values='r2', aggfunc='mean').reset_index()\n"
            "pivot_df.head(20)"
        ),
        nbformat.v4.new_code_cell(
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "plt.style.use('seaborn-v0_8-whitegrid')\n"
            "for station_id in TOP6_STATION_IDS:\n"
            "    station_view = metrics_df[(metrics_df['station_id'] == station_id) & (metrics_df['split'] == 'valid')].copy()\n"
            "    fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n"
            "    sns.barplot(data=station_view, x='r2', y='feature_set', hue='target', ax=axes[0])\n"
            "    axes[0].set_title(f'Station {station_id} valid R²')\n"
            "    sns.barplot(data=station_view, x='rmse', y='feature_set', hue='target', ax=axes[1])\n"
            "    axes[1].set_title(f'Station {station_id} valid RMSE')\n"
            "    sns.barplot(data=station_view, x='mae', y='feature_set', hue='target', ax=axes[2])\n"
            "    axes[2].set_title(f'Station {station_id} valid MAE')\n"
            "    plt.tight_layout()\n"
            "    plt.show()\n"
        ),
        nbformat.v4.new_markdown_cell(
            "## 11. 저장된 결과 파일\n\n"
            "실험 결과는 아래 summary 파일로 저장됩니다."
        ),
        nbformat.v4.new_code_cell(
            "saved_files = pd.DataFrame([\n"
            "    {'file': str(SUMMARY_DIR / 'feature_top6_experiment_metrics.csv')},\n"
            "    {'file': str(SUMMARY_DIR / 'feature_top6_best_by_target.csv')},\n"
            "    {'file': str(SUMMARY_DIR / 'feature_top6_best_by_station.csv')},\n"
            "    {'file': str(SUMMARY_DIR / 'feature_top6_station_optimal_summary.csv')},\n"
            "    {'file': str(SUMMARY_DIR / 'feature_top6_station_interpretation.csv')},\n"
            "])\n"
            "saved_files"
        ),
    ]
    if summary_md_text:
        notebook.cells.extend([
            nbformat.v4.new_markdown_cell("## 12. Markdown Summary"),
            nbformat.v4.new_markdown_cell(summary_md_text),
        ])
    notebook.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"},
    }
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with NOTEBOOK_PATH.open("w", encoding="utf-8") as f:
        nbformat.write(notebook, f)


def main() -> None:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    run_feature_experiments()
    create_notebook()
    print(json.dumps({
        "notebook_path": str(NOTEBOOK_PATH),
        "metrics_output": str(METRICS_OUTPUT),
        "best_target_output": str(BEST_TARGET_OUTPUT),
        "best_station_output": str(BEST_STATION_OUTPUT),
        "best_summary_output": str(BEST_SUMMARY_OUTPUT),
        "interpretation_output": str(INTERPRETATION_OUTPUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
