from __future__ import annotations

import json
from pathlib import Path

import h5py
import nbformat
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
HMW3_DIR = ROOT / "hmw3"
DATA_DIR = HMW3_DIR / "Data"
NOTE_DIR = HMW3_DIR / "Note"
H5_RELATED_DIR = HMW3_DIR / "h5_related"
NOTEBOOK_PATH = H5_RELATED_DIR / "hmw_h5_model_store.ipynb"
H5_PATH = H5_RELATED_DIR / "top6_station_model_store.h5"
JSON_EXAMPLE_PATH = H5_RELATED_DIR / "top6_station_prediction_example.json"
WEEKLY_JSON_EXAMPLE_PATH = H5_RELATED_DIR / "top6_station_weekly_recursive_forecast_example.json"
DYNAMIC_YEAR_WEIGHT_JSON_EXAMPLE_PATH = H5_RELATED_DIR / "top6_station_dynamic_year_weight_update_example.json"


def get_top6_station_ids() -> list[int]:
    ranking_df = pd.read_csv(DATA_DIR / "summaries/top20_station_combined_test_r2_ranking.csv")
    return ranking_df.head(6)["station_id"].astype(int).tolist()


def get_holiday_dates() -> list[str]:
    top6_station_ids = get_top6_station_ids()
    holiday_path = DATA_DIR / "holiday_reference" / f"station_{top6_station_ids[0]}_holiday_reference.csv"
    holiday_df = pd.read_csv(holiday_path)
    return sorted(pd.to_datetime(holiday_df["date"]).dt.strftime("%Y-%m-%d").unique().tolist())


def build_station_bundle(station_id: int) -> dict:
    coef_df = pd.read_csv(DATA_DIR / "coefficients" / f"station_{station_id}_offday_month_ridge_coefficients.csv")
    formula_df = pd.read_csv(DATA_DIR / "formulas" / f"station_{station_id}_offday_hour_formulas.csv")
    weight_df = pd.read_csv(DATA_DIR / "weights" / f"station_{station_id}_month_weights.csv")

    bundle: dict[str, object] = {
        "station_id": int(station_id),
        "formula": {},
        "month_weight": {},
        "year_weight": {},
        "hour_weight": {},
        "day_type_map": {"weekday": 1, "offday": 0},
    }

    for target in ["rental_count", "return_count"]:
        target_coef = coef_df[coef_df["target"] == target].copy()
        feature_df = target_coef[target_coef["feature"] != "intercept"].copy()
        intercept = float(target_coef.loc[target_coef["feature"] == "intercept", "coefficient"].iloc[0])

        bundle_key = "rental" if target == "rental_count" else "return"
        bundle[bundle_key] = {
            "coef": feature_df["coefficient"].astype(float).tolist(),
            "intercept": intercept,
            "feature_names": feature_df["feature"].tolist(),
        }

        target_formula = formula_df[formula_df["target"] == target].copy()
        bundle["formula"][target] = {}
        for _, row in target_formula.iterrows():
            bundle["formula"][target][row["day_type"]] = {
                "intercept": float(row["intercept"]),
                "sin_hour_coef": float(row["sin_hour_coef"]),
                "cos_hour_coef": float(row["cos_hour_coef"]),
            }

        target_weights = weight_df[weight_df["target"] == target].copy()
        for weight_type in ["month_weight", "year_weight", "hour_weight"]:
            sub = target_weights[target_weights["weight_type"] == weight_type].copy()
            bundle[weight_type][target] = {
                str(row["key"]): float(row["value"]) for _, row in sub.iterrows()
            }

    return bundle


def save_model_store(h5_path: Path, top6_station_ids: list[int], holiday_dates: list[str]) -> None:
    if h5_path.exists():
        h5_path.unlink()

    ranking_df = pd.read_csv(DATA_DIR / "summaries/top20_station_combined_test_r2_ranking.csv")
    ranking_df = ranking_df[ranking_df["station_id"].isin(top6_station_ids)].copy()

    with h5py.File(h5_path, "w") as f:
        meta_grp = f.require_group("meta")
        meta_grp.attrs["model_type"] = "pattern_weight_ridge"
        meta_grp.attrs["version"] = "v1"
        meta_grp.create_dataset("station_ids", data=np.asarray(top6_station_ids, dtype=int))
        meta_grp.create_dataset("holiday_dates", data=np.asarray(holiday_dates, dtype="S"))

        ranking_grp = f.require_group("ranking")
        ranking_grp.create_dataset("station_id", data=ranking_df["station_id"].astype(int).to_numpy())
        ranking_grp.create_dataset("combined_test_r2", data=ranking_df["combined_test_r2"].astype(float).to_numpy())
        ranking_grp.create_dataset("combined_test_rmse", data=ranking_df["combined_test_rmse"].astype(float).to_numpy())
        ranking_grp.create_dataset("combined_test_mae", data=ranking_df["combined_test_mae"].astype(float).to_numpy())

        stations_grp = f.require_group("stations")
        for station_id in top6_station_ids:
            bundle = build_station_bundle(station_id)
            station_name = ranking_df.loc[ranking_df["station_id"] == station_id, "station_name"].iloc[0]

            st_grp = stations_grp.require_group(str(station_id))
            st_grp.attrs["station_name"] = station_name

            for target_key in ["rental", "return"]:
                target_grp = st_grp.require_group(target_key)
                target_bundle = bundle[target_key]
                target_grp.create_dataset("coef", data=np.asarray(target_bundle["coef"], dtype=float))
                target_grp.create_dataset("intercept", data=np.asarray([target_bundle["intercept"]], dtype=float))
                target_grp.create_dataset(
                    "feature_names",
                    data=np.asarray(target_bundle["feature_names"], dtype="S"),
                )

            formula_grp = st_grp.require_group("formula")
            for target in ["rental_count", "return_count"]:
                target_formula_grp = formula_grp.require_group(target)
                for day_type, params in bundle["formula"][target].items():
                    day_grp = target_formula_grp.require_group(day_type)
                    for key, value in params.items():
                        day_grp.attrs[key] = float(value)

            for weight_type in ["month_weight", "year_weight", "hour_weight"]:
                outer_grp = st_grp.require_group(weight_type)
                for target in ["rental_count", "return_count"]:
                    target_grp = outer_grp.require_group(target)
                    keys = np.asarray(list(bundle[weight_type][target].keys()), dtype="S")
                    values = np.asarray(list(bundle[weight_type][target].values()), dtype=float)
                    target_grp.create_dataset("keys", data=keys)
                    target_grp.create_dataset("values", data=values)


def build_example_json(h5_path: Path) -> dict:
    with h5py.File(h5_path, "r") as f:
        station_ids = [int(x) for x in f["meta"]["station_ids"][:].tolist()]
        holiday_dates = {x.decode("utf-8") for x in f["meta"]["holiday_dates"][:].tolist()}

        def load_station(station_id: int) -> dict:
            st_grp = f["stations"][str(station_id)]
            station_bundle = {
                "station_id": station_id,
                "station_name": st_grp.attrs["station_name"],
                "formula": {},
                "month_weight": {},
                "year_weight": {},
                "hour_weight": {},
            }
            for target_key in ["rental", "return"]:
                t_grp = st_grp[target_key]
                station_bundle[target_key] = {
                    "coef": t_grp["coef"][:],
                    "intercept": float(t_grp["intercept"][0]),
                    "feature_names": [x.decode("utf-8") for x in t_grp["feature_names"][:]],
                }
            for target in ["rental_count", "return_count"]:
                station_bundle["formula"][target] = {}
                for day_type in ["weekday", "offday"]:
                    attrs = f["stations"][str(station_id)]["formula"][target][day_type].attrs
                    station_bundle["formula"][target][day_type] = {
                        key: float(attrs[key]) for key in attrs.keys()
                    }
            for weight_type in ["month_weight", "year_weight", "hour_weight"]:
                station_bundle[weight_type] = {}
                for target in ["rental_count", "return_count"]:
                    grp = st_grp[weight_type][target]
                    keys = [x.decode("utf-8") for x in grp["keys"][:]]
                    values = grp["values"][:].tolist()
                    station_bundle[weight_type][target] = dict(zip(keys, values))
            return station_bundle

        def resolve_weight(weight_map: dict[str, float], key: int) -> float:
            if str(key) in weight_map:
                return float(weight_map[str(key)])
            numeric_keys = sorted(int(k) for k in weight_map.keys())
            fallback = max(numeric_keys)
            return float(weight_map[str(fallback)])

        def compute_base_value(formula_params: dict[str, float], hour: int) -> float:
            angle = 2 * np.pi * hour / 24.0
            return (
                formula_params["intercept"]
                + formula_params["sin_hour_coef"] * np.sin(angle)
                + formula_params["cos_hour_coef"] * np.cos(angle)
            )

        def build_features(bundle: dict, dt: pd.Timestamp, target: str) -> dict[str, float]:
            date_str = dt.strftime("%Y-%m-%d")
            day_type = "offday" if (dt.weekday() >= 5 or date_str in holiday_dates) else "weekday"
            base_value = compute_base_value(bundle["formula"][target][day_type], int(dt.hour))
            month_weight = resolve_weight(bundle["month_weight"][target], int(dt.month))
            year_weight = resolve_weight(bundle["year_weight"][target], int(dt.year))
            hour_weight = resolve_weight(bundle["hour_weight"][target], int(dt.hour))
            pattern_prior = base_value * month_weight * year_weight
            corrected_pattern_prior = pattern_prior * hour_weight
            return {
                "base_value": float(base_value),
                "month_weight": float(month_weight),
                "year_weight": float(year_weight),
                "hour_weight": float(hour_weight),
                "pattern_prior": float(pattern_prior),
                "corrected_pattern_prior": float(corrected_pattern_prior),
                "day_type_weekday": 1.0 if day_type == "weekday" else 0.0,
                "day_type_offday": 1.0 if day_type == "offday" else 0.0,
            }

        def linear_predict(model_info: dict, feature_dict: dict[str, float]) -> float:
            x = np.asarray([feature_dict[name] for name in model_info["feature_names"]], dtype=float)
            return float(model_info["intercept"] + np.dot(model_info["coef"], x))

        dt = pd.Timestamp("2026-04-25 16:00:00")
        station_id = station_ids[0]
        bundle = load_station(station_id)
        rental_features = build_features(bundle, dt, "rental_count")
        return_features = build_features(bundle, dt, "return_count")
        rental_pred = max(linear_predict(bundle["rental"], rental_features), 0.0)
        return_pred = max(linear_predict(bundle["return"], return_features), 0.0)
        bike_change = float(rental_pred - return_pred)

        return {
            "station_id": station_id,
            "station_name": bundle["station_name"],
            "datetime": dt.isoformat(),
            "input": {
                "year": int(dt.year),
                "month": int(dt.month),
                "day": int(dt.day),
                "hour": int(dt.hour),
            },
            "prediction": {
                "rental_count_pred": float(rental_pred),
                "return_count_pred": float(return_pred),
                "bike_change_pred": bike_change,
            },
            "display": {
                "rental_count_pred": int(round(rental_pred)),
                "return_count_pred": int(round(return_pred)),
                "bike_change_pred": int(round(bike_change)),
            },
        }


def build_weekly_recursive_example(h5_path: Path) -> dict:
    with h5py.File(h5_path, "r") as f:
        station_ids = [int(x) for x in f["meta"]["station_ids"][:].tolist()]
        holiday_dates = {x.decode("utf-8") for x in f["meta"]["holiday_dates"][:].tolist()}

        def load_station(station_id: int) -> dict:
            st_grp = f["stations"][str(station_id)]
            station_bundle = {
                "station_id": station_id,
                "station_name": st_grp.attrs["station_name"],
                "formula": {},
                "month_weight": {},
                "year_weight": {},
                "hour_weight": {},
            }
            for target_key in ["rental", "return"]:
                t_grp = st_grp[target_key]
                station_bundle[target_key] = {
                    "coef": t_grp["coef"][:],
                    "intercept": float(t_grp["intercept"][0]),
                    "feature_names": [x.decode("utf-8") for x in t_grp["feature_names"][:]],
                }
            for target in ["rental_count", "return_count"]:
                station_bundle["formula"][target] = {}
                for day_type in ["weekday", "offday"]:
                    attrs = st_grp["formula"][target][day_type].attrs
                    station_bundle["formula"][target][day_type] = {
                        key: float(attrs[key]) for key in attrs.keys()
                    }
            for weight_type in ["month_weight", "year_weight", "hour_weight"]:
                station_bundle[weight_type] = {}
                for target in ["rental_count", "return_count"]:
                    grp = st_grp[weight_type][target]
                    keys = [x.decode("utf-8") for x in grp["keys"][:]]
                    values = grp["values"][:].tolist()
                    station_bundle[weight_type][target] = dict(zip(keys, values))
            return station_bundle

        def resolve_weight(weight_map: dict[str, float], key: int) -> float:
            if str(key) in weight_map:
                return float(weight_map[str(key)])
            numeric_keys = sorted(int(k) for k in weight_map.keys())
            fallback = max(numeric_keys)
            return float(weight_map[str(fallback)])

        def compute_base_value(formula_params: dict[str, float], hour: int) -> float:
            angle = 2 * np.pi * hour / 24.0
            return (
                formula_params["intercept"]
                + formula_params["sin_hour_coef"] * np.sin(angle)
                + formula_params["cos_hour_coef"] * np.cos(angle)
            )

        def build_features(bundle: dict, dt: pd.Timestamp, target: str) -> dict[str, float]:
            date_str = dt.strftime("%Y-%m-%d")
            day_type = "offday" if (dt.weekday() >= 5 or date_str in holiday_dates) else "weekday"
            base_value = compute_base_value(bundle["formula"][target][day_type], int(dt.hour))
            month_weight = resolve_weight(bundle["month_weight"][target], int(dt.month))
            year_weight = resolve_weight(bundle["year_weight"][target], int(dt.year))
            hour_weight = resolve_weight(bundle["hour_weight"][target], int(dt.hour))
            pattern_prior = base_value * month_weight * year_weight
            corrected_pattern_prior = pattern_prior * hour_weight
            return {
                "base_value": float(base_value),
                "month_weight": float(month_weight),
                "year_weight": float(year_weight),
                "hour_weight": float(hour_weight),
                "pattern_prior": float(pattern_prior),
                "corrected_pattern_prior": float(corrected_pattern_prior),
                "day_type_weekday": 1.0 if day_type == "weekday" else 0.0,
                "day_type_offday": 1.0 if day_type == "offday" else 0.0,
            }

        def linear_predict(model_info: dict, feature_dict: dict[str, float]) -> float:
            x = np.asarray([feature_dict[name] for name in model_info["feature_names"]], dtype=float)
            return float(model_info["intercept"] + np.dot(model_info["coef"], x))

        def predict_station_flow(bundle: dict, dt: pd.Timestamp) -> dict:
            rental_features = build_features(bundle, dt, "rental_count")
            return_features = build_features(bundle, dt, "return_count")
            rental_pred = max(linear_predict(bundle["rental"], rental_features), 0.0)
            return_pred = max(linear_predict(bundle["return"], return_features), 0.0)
            bike_change = float(rental_pred - return_pred)
            return {
                "datetime": dt.isoformat(),
                "rental_count_pred": float(rental_pred),
                "return_count_pred": float(return_pred),
                "bike_change_pred": bike_change,
                "display": {
                    "rental_count_pred": int(round(rental_pred)),
                    "return_count_pred": int(round(return_pred)),
                    "bike_change_pred": int(round(bike_change)),
                },
            }

        def recursive_forecast(bundle: dict, start_dt: pd.Timestamp, initial_bike_count: float, horizon_hours: int = 168) -> dict:
            horizon_hours = int(min(max(horizon_hours, 1), 24 * 7))
            records = []
            bike_count = float(initial_bike_count)
            for step in range(1, horizon_hours + 1):
                forecast_dt = start_dt + pd.Timedelta(hours=step)
                pred = predict_station_flow(bundle, forecast_dt)
                next_bike_count = max(bike_count + pred["bike_change_pred"], 0.0)
                records.append({
                    "step": step,
                    "datetime": forecast_dt.isoformat(),
                    "bike_count_from_api_or_prev_step": float(bike_count),
                    "rental_count_pred": pred["rental_count_pred"],
                    "return_count_pred": pred["return_count_pred"],
                    "bike_change_pred": pred["bike_change_pred"],
                    "next_bike_count_pred": float(next_bike_count),
                    "display": {
                        "bike_count_from_api_or_prev_step": int(round(bike_count)),
                        "rental_count_pred": int(round(pred["rental_count_pred"])),
                        "return_count_pred": int(round(pred["return_count_pred"])),
                        "bike_change_pred": int(round(pred["bike_change_pred"])),
                        "next_bike_count_pred": int(round(next_bike_count)),
                    },
                })
                bike_count = next_bike_count
            return {
                "station_id": bundle["station_id"],
                "station_name": bundle["station_name"],
                "start_datetime": start_dt.isoformat(),
                "initial_bike_count_from_api": float(initial_bike_count),
                "horizon_hours": horizon_hours,
                "forecast": records,
            }

        station_id = station_ids[0]
        bundle = load_station(station_id)
        start_dt = pd.Timestamp("2026-03-20 10:00:00")
        return recursive_forecast(bundle, start_dt, initial_bike_count=12.0, horizon_hours=24)


def build_dynamic_year_weight_example(h5_path: Path) -> dict:
    with h5py.File(h5_path, "r") as f:
        station_ids = [int(x) for x in f["meta"]["station_ids"][:].tolist()]
        holiday_dates = {x.decode("utf-8") for x in f["meta"]["holiday_dates"][:].tolist()}

        def load_station(station_id: int) -> dict:
            st_grp = f["stations"][str(station_id)]
            station_bundle = {
                "station_id": station_id,
                "station_name": st_grp.attrs["station_name"],
                "formula": {},
                "month_weight": {},
                "year_weight": {},
                "hour_weight": {},
            }
            for target_key in ["rental", "return"]:
                t_grp = st_grp[target_key]
                station_bundle[target_key] = {
                    "coef": t_grp["coef"][:],
                    "intercept": float(t_grp["intercept"][0]),
                    "feature_names": [x.decode("utf-8") for x in t_grp["feature_names"][:]],
                }
            for target in ["rental_count", "return_count"]:
                station_bundle["formula"][target] = {}
                for day_type in ["weekday", "offday"]:
                    attrs = st_grp["formula"][target][day_type].attrs
                    station_bundle["formula"][target][day_type] = {
                        key: float(attrs[key]) for key in attrs.keys()
                    }
            for weight_type in ["month_weight", "year_weight", "hour_weight"]:
                station_bundle[weight_type] = {}
                for target in ["rental_count", "return_count"]:
                    grp = st_grp[weight_type][target]
                    keys = [x.decode("utf-8") for x in grp["keys"][:]]
                    values = grp["values"][:].tolist()
                    station_bundle[weight_type][target] = dict(zip(keys, values))
            return station_bundle

        def resolve_weight(weight_map: dict[str, float], key: int) -> float:
            if str(key) in weight_map:
                return float(weight_map[str(key)])
            numeric_keys = sorted(int(k) for k in weight_map.keys())
            fallback = max(numeric_keys)
            return float(weight_map[str(fallback)])

        def compute_base_value(formula_params: dict[str, float], hour: int) -> float:
            angle = 2 * np.pi * hour / 24.0
            return (
                formula_params["intercept"]
                + formula_params["sin_hour_coef"] * np.sin(angle)
                + formula_params["cos_hour_coef"] * np.cos(angle)
            )

        def build_features(bundle: dict, dt: pd.Timestamp, target: str) -> dict[str, float]:
            date_str = dt.strftime("%Y-%m-%d")
            day_type = "offday" if (dt.weekday() >= 5 or date_str in holiday_dates) else "weekday"
            base_value = compute_base_value(bundle["formula"][target][day_type], int(dt.hour))
            month_weight = resolve_weight(bundle["month_weight"][target], int(dt.month))
            year_weight = resolve_weight(bundle["year_weight"][target], int(dt.year))
            hour_weight = resolve_weight(bundle["hour_weight"][target], int(dt.hour))
            pattern_prior = base_value * month_weight * year_weight
            corrected_pattern_prior = pattern_prior * hour_weight
            return {
                "base_value": float(base_value),
                "month_weight": float(month_weight),
                "year_weight": float(year_weight),
                "hour_weight": float(hour_weight),
                "pattern_prior": float(pattern_prior),
                "corrected_pattern_prior": float(corrected_pattern_prior),
                "day_type_weekday": 1.0 if day_type == "weekday" else 0.0,
                "day_type_offday": 1.0 if day_type == "offday" else 0.0,
            }

        def linear_predict(model_info: dict, feature_dict: dict[str, float]) -> float:
            x = np.asarray([feature_dict[name] for name in model_info["feature_names"]], dtype=float)
            return float(model_info["intercept"] + np.dot(model_info["coef"], x))

        def predict_station_flow(bundle: dict, dt: pd.Timestamp) -> dict:
            rental_features = build_features(bundle, dt, "rental_count")
            return_features = build_features(bundle, dt, "return_count")
            rental_pred = max(linear_predict(bundle["rental"], rental_features), 0.0)
            return_pred = max(linear_predict(bundle["return"], return_features), 0.0)
            return {
                "station_id": bundle["station_id"],
                "station_name": bundle["station_name"],
                "datetime": dt.isoformat(),
                "prediction": {
                    "rental_count_pred": float(rental_pred),
                    "return_count_pred": float(return_pred),
                    "bike_change_pred": float(rental_pred - return_pred),
                },
            }

        def predict_with_dynamic(bundle: dict, dt: pd.Timestamp, dynamic_state: dict) -> dict:
            base_result = predict_station_flow(bundle, dt)
            rental_base = float(base_result["prediction"]["rental_count_pred"])
            return_base = float(base_result["prediction"]["return_count_pred"])
            rental_adj = max(rental_base * float(dynamic_state["rental_count"]), 0.0)
            return_adj = max(return_base * float(dynamic_state["return_count"]), 0.0)
            base_change = float(rental_base - return_base)
            adjusted_change = float(rental_adj - return_adj)
            return {
                "station_id": bundle["station_id"],
                "station_name": bundle["station_name"],
                "datetime": dt.isoformat(),
                "dynamic_year_weight": {
                    "rental_count": float(dynamic_state["rental_count"]),
                    "return_count": float(dynamic_state["return_count"]),
                },
                "base_prediction": {
                    "rental_count_pred": float(rental_base),
                    "return_count_pred": float(return_base),
                    "bike_change_pred": base_change,
                    "display": {
                        "rental_count_pred": int(round(rental_base)),
                        "return_count_pred": int(round(return_base)),
                        "bike_change_pred": int(round(base_change)),
                    },
                },
                "adjusted_prediction": {
                    "rental_count_pred": float(rental_adj),
                    "return_count_pred": float(return_adj),
                    "bike_change_pred": adjusted_change,
                    "display": {
                        "rental_count_pred": int(round(rental_adj)),
                        "return_count_pred": int(round(return_adj)),
                        "bike_change_pred": int(round(adjusted_change)),
                    },
                },
            }

        def update_dynamic(predicted_result: dict, actual_rental: float, actual_return: float, dynamic_state: dict, alpha: float = 0.2) -> dict:
            pred_rental = max(float(predicted_result["adjusted_prediction"]["rental_count_pred"]), 1e-6)
            pred_return = max(float(predicted_result["adjusted_prediction"]["return_count_pred"]), 1e-6)
            rental_ratio = float(actual_rental) / pred_rental
            return_ratio = float(actual_return) / pred_return
            dynamic_state["rental_count"] = float(dynamic_state["rental_count"] * (1 - alpha) + rental_ratio * alpha)
            dynamic_state["return_count"] = float(dynamic_state["return_count"] * (1 - alpha) + return_ratio * alpha)
            return {
                "alpha": float(alpha),
                "actual_observation": {
                    "rental_count": float(actual_rental),
                    "return_count": float(actual_return),
                },
                "observed_ratio": {
                    "rental_count": float(rental_ratio),
                    "return_count": float(return_ratio),
                },
                "updated_dynamic_year_weight": {
                    "rental_count": float(dynamic_state["rental_count"]),
                    "return_count": float(dynamic_state["return_count"]),
                },
            }

        station_id = station_ids[0]
        bundle = load_station(station_id)
        dynamic_state = {"rental_count": 1.0, "return_count": 1.0}
        predict_dt = pd.Timestamp("2026-03-20 11:00:00")
        before_update = predict_with_dynamic(bundle, predict_dt, dynamic_state)
        update_result = update_dynamic(before_update, actual_rental=3.1, actual_return=1.8, dynamic_state=dynamic_state, alpha=0.2)
        after_update = predict_with_dynamic(bundle, pd.Timestamp("2026-03-20 12:00:00"), dynamic_state)
        return {
            "station_id": station_id,
            "station_name": bundle["station_name"],
            "before_update_prediction": before_update,
            "update_result": update_result,
            "after_update_next_hour_prediction": after_update,
        }


def create_notebook(top6_station_ids: list[int]) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell(
            "# Top 6 Station H5 Model Store\n\n"
            "상위 6개 station 모델을 하나의 `h5` 파일로 통합 저장하고, "
            "실제 서비스에서 로드한 뒤 입력값으로 예측하고 JSON으로 출력하는 전체 과정을 정리한 노트북입니다."
        ),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import json\n"
            "import h5py\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "\n"
            "ROOT = Path.cwd().resolve().parents[0]\n"
            "DATA_DIR = ROOT / 'Data'\n"
            "NOTE_DIR = ROOT / 'Note'\n"
            "H5_PATH = DATA_DIR / 'top6_station_model_store.h5'\n"
            f"TOP6_STATION_IDS = {top6_station_ids}\n"
        ),
        nbformat.v4.new_markdown_cell(
            "## 0. 서비스 입력값과 출력값\n\n"
            "이 모델은 외부에서 많은 feature를 직접 받지 않습니다. 서비스에서 **직접 넣어야 하는 입력값은 아래 3개**입니다.\n\n"
            "- `station_id`: 어떤 대여소 모델을 쓸지 결정\n"
            "- `datetime`: 예측하려는 시점\n"
            "- `current_bike_count_from_api`: 현재 자전거 수량 API 값\n\n"
            "이 중 `station_id`와 `datetime`은 단일 시점 예측에 필요하고, `current_bike_count_from_api`는 재귀형 다중 시간 예측에 필요합니다.\n\n"
            "최종 출력은 JSON입니다. JSON 안에는 보통 아래 값이 들어갑니다.\n\n"
            "- `rental_count_pred`\n"
            "- `return_count_pred`\n"
            "- `bike_change_pred`\n"
            "- `next_bike_count_pred` 또는 이후 시간대 예측 배열"
        ),
        nbformat.v4.new_code_cell(
            "service_io_df = pd.DataFrame([\n"
            "    {'field': 'station_id', 'required': True, 'type': 'int', 'description': '예측에 사용할 station 모델 id'},\n"
            "    {'field': 'datetime', 'required': True, 'type': 'datetime or ISO string', 'description': '예측 대상 시점'},\n"
            "    {'field': 'current_bike_count_from_api', 'required': False, 'type': 'float', 'description': '현재 자전거 수량. 재귀형 예측 시작값'},\n"
            "])\n"
            "service_io_df"
        ),
        nbformat.v4.new_markdown_cell(
            "### 입력 항목 상세 설명\n\n"
            "- `station_id`\n"
            "  - 어떤 대여소 모델을 사용할지 결정하는 식별자입니다.\n"
            "  - 이 값으로 `MODEL_REGISTRY`에서 station별 공식, 가중치, Ridge 계수를 선택합니다.\n"
            "- `datetime`\n"
            "  - 예측하려는 기준 시각입니다.\n"
            "  - 이 값에서 `year`, `month`, `day`, `hour`, `weekday`를 추출합니다.\n"
            "  - 공휴일 여부와 함께 `day_type`를 판별하는 핵심 입력입니다.\n"
            "- `current_bike_count_from_api`\n"
            "  - 현재 시점 실제 자전거 총 대수입니다.\n"
            "  - 단일 시점 예측 자체에는 직접 들어가지 않지만, 재귀형 예측에서는 다음 시간 총 대수를 계산하는 시작값이 됩니다."
        ),
        nbformat.v4.new_markdown_cell(
            "## 1. 상위 6개 station 확인\n\n"
            "통합 저장 대상은 `test R²` 기준 상위 6개 station입니다."
        ),
        nbformat.v4.new_code_cell(
            "ranking_df = pd.read_csv(DATA_DIR / 'summaries/top20_station_combined_test_r2_ranking.csv')\n"
            "top6_df = ranking_df.head(6).copy()\n"
            "top6_df[['rank', 'station_id', 'station_name', 'combined_test_r2', 'combined_test_rmse', 'combined_test_mae']]"
        ),
        nbformat.v4.new_markdown_cell(
            "## 2. station별 bundle 만들기\n\n"
            "각 station에서 아래 정보를 모아 하나의 bundle로 만듭니다.\n\n"
            "- Ridge 계수와 intercept\n"
            "- feature_names\n"
            "- hour 기본식\n"
            "- month/year/hour weight"
        ),
        nbformat.v4.new_code_cell(
            "def build_station_bundle(station_id):\n"
            "    coef_df = pd.read_csv(DATA_DIR / 'coefficients' / f'station_{station_id}_offday_month_ridge_coefficients.csv')\n"
            "    formula_df = pd.read_csv(DATA_DIR / 'formulas' / f'station_{station_id}_offday_hour_formulas.csv')\n"
            "    weight_df = pd.read_csv(DATA_DIR / 'weights' / f'station_{station_id}_month_weights.csv')\n"
            "\n"
            "    bundle = {\n"
            "        'station_id': int(station_id),\n"
            "        'formula': {},\n"
            "        'month_weight': {},\n"
            "        'year_weight': {},\n"
            "        'hour_weight': {},\n"
            "    }\n"
            "\n"
            "    for target in ['rental_count', 'return_count']:\n"
            "        target_coef = coef_df[coef_df['target'] == target].copy()\n"
            "        feature_df = target_coef[target_coef['feature'] != 'intercept'].copy()\n"
            "        intercept = float(target_coef.loc[target_coef['feature'] == 'intercept', 'coefficient'].iloc[0])\n"
            "        bundle_key = 'rental' if target == 'rental_count' else 'return'\n"
            "        bundle[bundle_key] = {\n"
            "            'coef': feature_df['coefficient'].astype(float).tolist(),\n"
            "            'intercept': intercept,\n"
            "            'feature_names': feature_df['feature'].tolist(),\n"
            "        }\n"
            "\n"
            "        target_formula = formula_df[formula_df['target'] == target].copy()\n"
            "        bundle['formula'][target] = {}\n"
            "        for _, row in target_formula.iterrows():\n"
            "            bundle['formula'][target][row['day_type']] = {\n"
            "                'intercept': float(row['intercept']),\n"
            "                'sin_hour_coef': float(row['sin_hour_coef']),\n"
            "                'cos_hour_coef': float(row['cos_hour_coef']),\n"
            "            }\n"
            "\n"
            "        target_weights = weight_df[weight_df['target'] == target].copy()\n"
            "        for weight_type in ['month_weight', 'year_weight', 'hour_weight']:\n"
            "            sub = target_weights[target_weights['weight_type'] == weight_type].copy()\n"
            "            bundle[weight_type][target] = {str(row['key']): float(row['value']) for _, row in sub.iterrows()}\n"
            "\n"
            "    return bundle\n"
        ),
        nbformat.v4.new_code_cell(
            "example_bundle = build_station_bundle(TOP6_STATION_IDS[0])\n"
            "example_bundle.keys()"
        ),
        nbformat.v4.new_markdown_cell(
            "## 3. 통합 h5 저장\n\n"
            "모든 station을 하나의 `top6_station_model_store.h5` 파일에 저장합니다."
        ),
        nbformat.v4.new_code_cell(
            "holiday_df = pd.read_csv(DATA_DIR / 'holiday_reference' / f'station_{TOP6_STATION_IDS[0]}_holiday_reference.csv')\n"
            "holiday_dates = sorted(pd.to_datetime(holiday_df['date']).dt.strftime('%Y-%m-%d').unique().tolist())\n"
            "\n"
            "def save_model_store(h5_path, station_ids, holiday_dates):\n"
            "    if h5_path.exists():\n"
            "        h5_path.unlink()\n"
            "    with h5py.File(h5_path, 'w') as f:\n"
            "        meta_grp = f.require_group('meta')\n"
            "        meta_grp.attrs['model_type'] = 'pattern_weight_ridge'\n"
            "        meta_grp.attrs['version'] = 'v1'\n"
            "        meta_grp.create_dataset('station_ids', data=np.asarray(station_ids, dtype=int))\n"
            "        meta_grp.create_dataset('holiday_dates', data=np.asarray(holiday_dates, dtype='S'))\n"
            "\n"
            "        stations_grp = f.require_group('stations')\n"
            "        ranking_df = pd.read_csv(DATA_DIR / 'summaries/top20_station_combined_test_r2_ranking.csv')\n"
            "        for station_id in station_ids:\n"
            "            bundle = build_station_bundle(station_id)\n"
            "            station_name = ranking_df.loc[ranking_df['station_id'] == station_id, 'station_name'].iloc[0]\n"
            "            st_grp = stations_grp.require_group(str(station_id))\n"
            "            st_grp.attrs['station_name'] = station_name\n"
            "\n"
            "            for target_key in ['rental', 'return']:\n"
            "                target_grp = st_grp.require_group(target_key)\n"
            "                target_bundle = bundle[target_key]\n"
            "                target_grp.create_dataset('coef', data=np.asarray(target_bundle['coef'], dtype=float))\n"
            "                target_grp.create_dataset('intercept', data=np.asarray([target_bundle['intercept']], dtype=float))\n"
            "                target_grp.create_dataset('feature_names', data=np.asarray(target_bundle['feature_names'], dtype='S'))\n"
            "\n"
            "            formula_grp = st_grp.require_group('formula')\n"
            "            for target in ['rental_count', 'return_count']:\n"
            "                target_formula_grp = formula_grp.require_group(target)\n"
            "                for day_type, params in bundle['formula'][target].items():\n"
            "                    day_grp = target_formula_grp.require_group(day_type)\n"
            "                    for key, value in params.items():\n"
            "                        day_grp.attrs[key] = float(value)\n"
            "\n"
            "            for weight_type in ['month_weight', 'year_weight', 'hour_weight']:\n"
            "                outer_grp = st_grp.require_group(weight_type)\n"
            "                for target in ['rental_count', 'return_count']:\n"
            "                    target_grp = outer_grp.require_group(target)\n"
            "                    keys = np.asarray(list(bundle[weight_type][target].keys()), dtype='S')\n"
            "                    values = np.asarray(list(bundle[weight_type][target].values()), dtype=float)\n"
            "                    target_grp.create_dataset('keys', data=keys)\n"
            "                    target_grp.create_dataset('values', data=values)\n"
            "\n"
            "save_model_store(H5_PATH, TOP6_STATION_IDS, holiday_dates)\n"
            "H5_PATH"
        ),
        nbformat.v4.new_markdown_cell(
            "## 4. 서비스용 로더\n\n"
            "실서비스에서는 서버 시작 시 이 함수를 한 번 실행해서 station 모델을 메모리에 올려두는 방식이 가장 효율적입니다."
        ),
        nbformat.v4.new_code_cell(
            "def load_model_store(h5_path):\n"
            "    registry = {}\n"
            "    with h5py.File(h5_path, 'r') as f:\n"
            "        holiday_dates = {x.decode('utf-8') for x in f['meta']['holiday_dates'][:]}\n"
            "        station_ids = [int(x) for x in f['meta']['station_ids'][:].tolist()]\n"
            "        for station_id in station_ids:\n"
            "            st_grp = f['stations'][str(station_id)]\n"
            "            station_bundle = {\n"
            "                'station_id': station_id,\n"
            "                'station_name': st_grp.attrs['station_name'],\n"
            "                'formula': {},\n"
            "                'month_weight': {},\n"
            "                'year_weight': {},\n"
            "                'hour_weight': {},\n"
            "            }\n"
            "            for target_key in ['rental', 'return']:\n"
            "                t_grp = st_grp[target_key]\n"
            "                station_bundle[target_key] = {\n"
            "                    'coef': t_grp['coef'][:],\n"
            "                    'intercept': float(t_grp['intercept'][0]),\n"
            "                    'feature_names': [x.decode('utf-8') for x in t_grp['feature_names'][:]],\n"
            "                }\n"
            "            for target in ['rental_count', 'return_count']:\n"
            "                station_bundle['formula'][target] = {}\n"
            "                for day_type in ['weekday', 'offday']:\n"
            "                    attrs = st_grp['formula'][target][day_type].attrs\n"
            "                    station_bundle['formula'][target][day_type] = {key: float(attrs[key]) for key in attrs.keys()}\n"
            "            for weight_type in ['month_weight', 'year_weight', 'hour_weight']:\n"
            "                station_bundle[weight_type] = {}\n"
            "                for target in ['rental_count', 'return_count']:\n"
            "                    grp = st_grp[weight_type][target]\n"
            "                    keys = [x.decode('utf-8') for x in grp['keys'][:]]\n"
            "                    values = grp['values'][:].tolist()\n"
            "                    station_bundle[weight_type][target] = dict(zip(keys, values))\n"
            "            registry[station_id] = station_bundle\n"
            "    return registry, holiday_dates\n"
            "\n"
            "MODEL_REGISTRY, HOLIDAY_DATES = load_model_store(H5_PATH)\n"
            "list(MODEL_REGISTRY.keys())"
        ),
        nbformat.v4.new_markdown_cell(
            "## 5. 입력값으로 feature 만들기\n\n"
            "서비스에서는 `station_id`와 `datetime`을 받으면 같은 로직으로 feature를 구성해야 합니다."
        ),
        nbformat.v4.new_markdown_cell(
            "### 입력값이 내부 feature로 바뀌는 과정\n\n"
            "외부 입력값은 단순하지만, 모델이 실제로 사용하는 값은 아래 8개 내부 feature입니다.\n\n"
            "- `base_value`\n"
            "- `month_weight`\n"
            "- `year_weight`\n"
            "- `hour_weight`\n"
            "- `pattern_prior`\n"
            "- `corrected_pattern_prior`\n"
            "- `day_type_weekday`\n"
            "- `day_type_offday`\n\n"
            "변환 순서는 다음과 같습니다.\n\n"
            "1. `datetime`에서 `year`, `month`, `day`, `hour`, `weekday`를 계산\n"
            "2. 공휴일 테이블을 보고 `day_type = weekday / offday` 결정\n"
            "3. `station_id`에 해당하는 기본식으로 `base_value` 계산\n"
            "4. 같은 station의 `month_weight`, `year_weight`, `hour_weight` 조회\n"
            "5. `pattern_prior = base_value * month_weight * year_weight`\n"
            "6. `corrected_pattern_prior = pattern_prior * hour_weight`\n"
            "7. `day_type_weekday`, `day_type_offday` 더미값 생성\n"
            "8. 이 8개 값을 Ridge 입력 feature로 사용"
        ),
        nbformat.v4.new_markdown_cell(
            "### 내부 feature 상세 설명\n\n"
            "- `base_value`\n"
            "  - `day_type`와 `hour`를 이용해 기본 시간 패턴식에서 계산한 값입니다.\n"
            "  - station이 원래 가지는 시간대별 평균적인 흐름을 나타냅니다.\n"
            "- `month_weight`\n"
            "  - 월별 규모 차이를 보정하는 가중치입니다.\n"
            "  - 예를 들어 5월 이용량이 1월보다 전반적으로 크면 5월 weight가 더 크게 설정됩니다.\n"
            "- `year_weight`\n"
            "  - 2023~2025 학습 데이터에서 관측된 연도별 규모 차이를 반영하는 가중치입니다.\n"
            "  - 2026 이후에는 이 고정값 위에 `dynamic_year_weight`를 추가해 운영 중 보정합니다.\n"
            "- `hour_weight`\n"
            "  - 기본 시간 패턴식으로 설명되지 않는 피크 시간대 편차를 보정하는 가중치입니다.\n"
            "  - 출퇴근 시간처럼 특정 시간대가 더 튀는 경우를 보완합니다.\n"
            "- `pattern_prior`\n"
            "  - `base_value * month_weight * year_weight`로 계산되는 1차 패턴 예측값입니다.\n"
            "  - 시간 패턴과 월/연도 규모를 먼저 결합한 값입니다.\n"
            "- `corrected_pattern_prior`\n"
            "  - `pattern_prior * hour_weight`로 계산되는 2차 보정 패턴값입니다.\n"
            "  - 실제 Ridge 입력에서 가장 중요한 설명 변수로 사용됩니다.\n"
            "- `day_type_weekday`\n"
            "  - 평일이면 1, 아니면 0인 더미 변수입니다.\n"
            "  - 평일 패턴을 별도로 구분하기 위한 feature입니다.\n"
            "- `day_type_offday`\n"
            "  - 주말 또는 공휴일이면 1, 아니면 0인 더미 변수입니다.\n"
            "  - 비근무일 패턴을 별도로 반영하기 위한 feature입니다."
        ),
        nbformat.v4.new_code_cell(
            "def resolve_weight(weight_map, key):\n"
            "    if str(key) in weight_map:\n"
            "        return float(weight_map[str(key)])\n"
            "    numeric_keys = sorted(int(k) for k in weight_map.keys())\n"
            "    fallback = max(numeric_keys)\n"
            "    return float(weight_map[str(fallback)])\n"
            "\n"
            "def compute_base_value(formula_params, hour):\n"
            "    angle = 2 * np.pi * hour / 24.0\n"
            "    return (\n"
            "        formula_params['intercept']\n"
            "        + formula_params['sin_hour_coef'] * np.sin(angle)\n"
            "        + formula_params['cos_hour_coef'] * np.cos(angle)\n"
            "    )\n"
            "\n"
            "def build_features(bundle, dt, target):\n"
            "    date_str = dt.strftime('%Y-%m-%d')\n"
            "    day_type = 'offday' if (dt.weekday() >= 5 or date_str in HOLIDAY_DATES) else 'weekday'\n"
            "    base_value = compute_base_value(bundle['formula'][target][day_type], int(dt.hour))\n"
            "    month_weight = resolve_weight(bundle['month_weight'][target], int(dt.month))\n"
            "    year_weight = resolve_weight(bundle['year_weight'][target], int(dt.year))\n"
            "    hour_weight = resolve_weight(bundle['hour_weight'][target], int(dt.hour))\n"
            "    pattern_prior = base_value * month_weight * year_weight\n"
            "    corrected_pattern_prior = pattern_prior * hour_weight\n"
            "    return {\n"
            "        'base_value': float(base_value),\n"
            "        'month_weight': float(month_weight),\n"
            "        'year_weight': float(year_weight),\n"
            "        'hour_weight': float(hour_weight),\n"
            "        'pattern_prior': float(pattern_prior),\n"
            "        'corrected_pattern_prior': float(corrected_pattern_prior),\n"
            "        'day_type_weekday': 1.0 if day_type == 'weekday' else 0.0,\n"
            "        'day_type_offday': 1.0 if day_type == 'offday' else 0.0,\n"
            "    }\n"
        ),
        nbformat.v4.new_code_cell(
            "feature_flow_example_dt = pd.Timestamp('2026-04-25 16:00:00')\n"
            "feature_flow_station_id = TOP6_STATION_IDS[0]\n"
            "feature_flow_bundle = MODEL_REGISTRY[int(feature_flow_station_id)]\n"
            "feature_flow_rental = build_features(feature_flow_bundle, feature_flow_example_dt, 'rental_count')\n"
            "pd.DataFrame([\n"
            "    {'step': 1, 'item': 'station_id', 'value': int(feature_flow_station_id)},\n"
            "    {'step': 2, 'item': 'datetime', 'value': feature_flow_example_dt.isoformat()},\n"
            "    {'step': 3, 'item': 'internal_features', 'value': json.dumps(feature_flow_rental, ensure_ascii=False)},\n"
            "])"
        ),
        nbformat.v4.new_markdown_cell(
            "## 6. 예측 함수 만들기\n\n"
            "최종적으로는 `rental_count`, `return_count`, `bike_change`를 JSON 형태로 반환합니다."
        ),
        nbformat.v4.new_markdown_cell(
            "### 예측 결과 항목 설명\n\n"
            "- `rental_count_pred`\n"
            "  - 해당 시간에 예상되는 대여 건수입니다.\n"
            "  - 내부 계산은 float로 유지됩니다.\n"
            "- `return_count_pred`\n"
            "  - 해당 시간에 예상되는 반납 건수입니다.\n"
            "  - 내부 계산은 float로 유지됩니다.\n"
            "- `bike_change_pred`\n"
            "  - `rental_count_pred - return_count_pred`로 계산한 순변화량입니다.\n"
            "  - 양수면 자전거가 줄어드는 방향, 음수면 자전거가 늘어나는 방향으로 해석할 수 있습니다.\n"
            "- `display`\n"
            "  - 사용자 화면이나 운영 대시보드에 보여주기 위한 반올림 정수값입니다.\n"
            "  - 계산용이 아니라 출력용입니다."
        ),
        nbformat.v4.new_code_cell(
            "def linear_predict(model_info, feature_dict):\n"
            "    x = np.asarray([feature_dict[name] for name in model_info['feature_names']], dtype=float)\n"
            "    return float(model_info['intercept'] + np.dot(model_info['coef'], x))\n"
            "\n"
            "def predict_station_flow(station_id, dt):\n"
            "    bundle = MODEL_REGISTRY[int(station_id)]\n"
            "    rental_features = build_features(bundle, dt, 'rental_count')\n"
            "    return_features = build_features(bundle, dt, 'return_count')\n"
            "\n"
            "    rental_pred = max(linear_predict(bundle['rental'], rental_features), 0.0)\n"
            "    return_pred = max(linear_predict(bundle['return'], return_features), 0.0)\n"
            "    bike_change = float(rental_pred - return_pred)\n"
            "\n"
            "    result = {\n"
            "        'station_id': int(station_id),\n"
            "        'station_name': bundle['station_name'],\n"
            "        'datetime': dt.isoformat(),\n"
            "        'input': {\n"
            "            'year': int(dt.year),\n"
            "            'month': int(dt.month),\n"
            "            'day': int(dt.day),\n"
            "            'hour': int(dt.hour),\n"
            "        },\n"
            "        'prediction': {\n"
            "            'rental_count_pred': float(rental_pred),\n"
            "            'return_count_pred': float(return_pred),\n"
            "            'bike_change_pred': bike_change,\n"
            "        },\n"
            "        'display': {\n"
            "            'rental_count_pred': int(round(rental_pred)),\n"
            "            'return_count_pred': int(round(return_pred)),\n"
            "            'bike_change_pred': int(round(bike_change)),\n"
            "        },\n"
            "    }\n"
            "    return result\n"
        ),
        nbformat.v4.new_markdown_cell(
            "### 서비스 요청 예시\n\n"
            "실서비스에서는 보통 아래처럼 요청이 들어온다고 가정할 수 있습니다."
        ),
        nbformat.v4.new_code_cell(
            "service_request_example = {\n"
            "    'station_id': int(TOP6_STATION_IDS[0]),\n"
            "    'datetime': '2026-04-25T16:00:00',\n"
            "    'current_bike_count_from_api': 12.0,\n"
            "}\n"
            "print(json.dumps(service_request_example, ensure_ascii=False, indent=2))"
        ),
        nbformat.v4.new_markdown_cell(
            "### 요청값을 모델에 넣는 과정\n\n"
            "서비스 코드는 보통 아래 순서로 동작합니다.\n\n"
            "1. 요청 JSON에서 `station_id`, `datetime`을 파싱\n"
            "2. `station_id`로 `MODEL_REGISTRY`에서 station 모델 선택\n"
            "3. `datetime`을 `Timestamp`로 변환\n"
            "4. `build_features(...)`로 내부 feature 생성\n"
            "5. `linear_predict(...)`로 `rental_count`, `return_count` 예측\n"
            "6. `bike_change = rental - return` 계산\n"
            "7. JSON 응답으로 반환"
        ),
        nbformat.v4.new_code_cell(
            "request_dt = pd.Timestamp(service_request_example['datetime'])\n"
            "request_station_id = int(service_request_example['station_id'])\n"
            "request_bundle = MODEL_REGISTRY[request_station_id]\n"
            "\n"
            "rental_feature_dict = build_features(request_bundle, request_dt, 'rental_count')\n"
            "return_feature_dict = build_features(request_bundle, request_dt, 'return_count')\n"
            "\n"
            "request_flow_df = pd.DataFrame([\n"
            "    {'stage': 'request', 'name': 'station_id', 'value': request_station_id},\n"
            "    {'stage': 'request', 'name': 'datetime', 'value': request_dt.isoformat()},\n"
            "    {'stage': 'feature_build', 'name': 'rental_features', 'value': json.dumps(rental_feature_dict, ensure_ascii=False)},\n"
            "    {'stage': 'feature_build', 'name': 'return_features', 'value': json.dumps(return_feature_dict, ensure_ascii=False)},\n"
            "])\n"
            "request_flow_df"
        ),
        nbformat.v4.new_markdown_cell(
            "## 7. JSON 결과 출력 예시\n\n"
            "예시 입력 시각: `2026-04-25 16:00:00`\n\n"
            "출력 형식은 실제 서비스 응답처럼 JSON 문자열로 만듭니다."
        ),
        nbformat.v4.new_code_cell(
            "example_dt = pd.Timestamp('2026-04-25 16:00:00')\n"
            "example_result = predict_station_flow(TOP6_STATION_IDS[0], example_dt)\n"
            "print(json.dumps(example_result, ensure_ascii=False, indent=2))"
        ),
        nbformat.v4.new_markdown_cell(
            "## 8. 현재 API 자전거 수량을 이용한 재귀형 7일 예측\n\n"
            "이제 단일 시점 예측을 반복 적용합니다.\n\n"
            "- 현재 시점의 자전거 수량은 API에서 받습니다.\n"
            "- 다음 1시간의 `rental_count`, `return_count`를 예측합니다.\n"
            "- `bike_change = rental_count - return_count`를 계산합니다.\n"
            "- `다음 시간 자전거 수량 = 현재 자전거 수량 + bike_change` 로 갱신합니다.\n"
            "- 이 과정을 반복해서 최대 7일, 즉 168시간 뒤까지 예측합니다."
        ),
        nbformat.v4.new_markdown_cell(
            "### 재귀형 예측 결과 항목 설명\n\n"
            "- `bike_count_from_api_or_prev_step`\n"
            "  - 현재 step 계산의 기준이 되는 자전거 총 대수입니다.\n"
            "  - 첫 step에서는 API 실제값이고, 이후 step부터는 직전 예측의 `next_bike_count_pred`입니다.\n"
            "- `next_bike_count_pred`\n"
            "  - 현재 총 대수에 `bike_change_pred`를 반영해 계산한 다음 시간 총 대수 예측값입니다.\n"
            "  - 재귀형 루프의 핵심 상태값입니다.\n"
            "- `forecast`\n"
            "  - 시간 순서대로 예측 결과가 쌓이는 배열입니다.\n"
            "  - 최대 168개 step까지 생성할 수 있습니다."
        ),
        nbformat.v4.new_code_cell(
            "def recursive_forecast(station_id, start_dt, initial_bike_count, horizon_hours=168):\n"
            "    horizon_hours = int(min(max(horizon_hours, 1), 24 * 7))\n"
            "    bundle = MODEL_REGISTRY[int(station_id)]\n"
            "    records = []\n"
            "    bike_count = float(initial_bike_count)\n"
            "\n"
            "    for step in range(1, horizon_hours + 1):\n"
            "        forecast_dt = start_dt + pd.Timedelta(hours=step)\n"
            "        pred = predict_station_flow(station_id, forecast_dt)\n"
            "        next_bike_count = max(bike_count + pred['prediction']['bike_change_pred'], 0.0)\n"
            "        records.append({\n"
            "            'step': step,\n"
            "            'datetime': forecast_dt.isoformat(),\n"
            "            'bike_count_from_api_or_prev_step': float(bike_count),\n"
            "            'rental_count_pred': float(pred['prediction']['rental_count_pred']),\n"
            "            'return_count_pred': float(pred['prediction']['return_count_pred']),\n"
            "            'bike_change_pred': float(pred['prediction']['bike_change_pred']),\n"
            "            'next_bike_count_pred': float(next_bike_count),\n"
            "            'display': {\n"
            "                'bike_count_from_api_or_prev_step': int(round(bike_count)),\n"
            "                'rental_count_pred': int(round(pred['prediction']['rental_count_pred'])),\n"
            "                'return_count_pred': int(round(pred['prediction']['return_count_pred'])),\n"
            "                'bike_change_pred': int(round(pred['prediction']['bike_change_pred'])),\n"
            "                'next_bike_count_pred': int(round(next_bike_count)),\n"
            "            },\n"
            "        })\n"
            "        bike_count = next_bike_count\n"
            "\n"
            "    return {\n"
            "        'station_id': int(station_id),\n"
            "        'station_name': bundle['station_name'],\n"
            "        'start_datetime': start_dt.isoformat(),\n"
            "        'initial_bike_count_from_api': float(initial_bike_count),\n"
            "        'horizon_hours': horizon_hours,\n"
            "        'forecast': records,\n"
            "    }\n"
        ),
        nbformat.v4.new_markdown_cell(
            "## 9. 재귀형 예측 JSON 출력 예시\n\n"
            "예시로 현재 API 수량을 `12대`라고 가정하고, 24시간 예측 결과를 JSON으로 출력합니다.\n\n"
            "실서비스에서는 `horizon_hours=168`로 주면 최대 1주일 예측이 가능합니다."
        ),
        nbformat.v4.new_code_cell(
            "start_dt = pd.Timestamp('2026-03-20 10:00:00')\n"
            "weekly_result = recursive_forecast(TOP6_STATION_IDS[0], start_dt, initial_bike_count=12.0, horizon_hours=24)\n"
            "print(json.dumps(weekly_result, ensure_ascii=False, indent=2))"
        ),
        nbformat.v4.new_markdown_cell(
            "## 10. JSON 결과를 서비스에 적용하는 방법\n\n"
            "JSON 결과가 나오면 실제 서비스에서는 이 값을 바로 화면 표시용으로 쓰거나, 다음 step 계산 입력값으로 넘깁니다.\n\n"
            "### 단일 시점 예측 결과 적용\n\n"
            "- `rental_count_pred`: 해당 시간 예상 대여량\n"
            "- `return_count_pred`: 해당 시간 예상 반납량\n"
            "- `bike_change_pred = rental - return`\n\n"
            "이 값은 대시보드, 알림, 운영 판단에 바로 사용할 수 있습니다.\n\n"
            "### 재귀형 예측 결과 적용\n\n"
            "재귀형 예측에서는 각 step의 JSON에서 아래 값을 사용합니다.\n\n"
            "- `bike_count_from_api_or_prev_step`: 현재 시간 기준 자전거 수량\n"
            "- `bike_change_pred`: 다음 1시간 변화량\n"
            "- `next_bike_count_pred`: 다음 시간 예측 자전거 수량\n\n"
            "즉 `next_bike_count_pred`를 다음 step의 입력값으로 계속 넘기면서 최대 7일까지 확장합니다."
        ),
        nbformat.v4.new_code_cell(
            "service_apply_example = {\n"
            "    'current_dashboard_value': weekly_result['forecast'][0]['bike_count_from_api_or_prev_step'],\n"
            "    'next_hour_predicted_bike_count': weekly_result['forecast'][0]['next_bike_count_pred'],\n"
            "    'next_hour_expected_rental': weekly_result['forecast'][0]['rental_count_pred'],\n"
            "    'next_hour_expected_return': weekly_result['forecast'][0]['return_count_pred'],\n"
            "    'next_hour_expected_change': weekly_result['forecast'][0]['bike_change_pred'],\n"
            "}\n"
            "print(json.dumps(service_apply_example, ensure_ascii=False, indent=2))"
        ),
        nbformat.v4.new_markdown_cell(
            "## 11. 2026 Dynamic Year Weight 보정 개념\n\n"
            "현재 `year_weight`는 2023~2025 학습 결과를 기반으로 만들어졌습니다. "
            "그래서 2026 이후 운영에서는 고정된 `year_weight`만으로는 부족할 수 있습니다.\n\n"
            "이 경우 운영에서는 아래와 같은 **동적 연도 보정값(dynamic year_weight)** 을 추가로 둡니다.\n\n"
            "- 초기값: `1.0` 또는 `2025 year_weight`\n"
            "- 예측값 생성\n"
            "- 실제값 수집\n"
            "- `actual / predicted` 비율을 계산\n"
            "- 그 비율을 바로 다 반영하지 않고 이동평균 방식으로 조금씩 업데이트\n"
            "- 업데이트된 보정값을 다음 예측부터 반영\n\n"
            "즉 구조는 아래처럼 됩니다.\n\n"
            "`최종예측 = 기존예측 × dynamic_year_weight_2026`\n\n"
            "이 방식이면 2026년 운영 데이터가 들어올수록 보정값이 실제 패턴에 적응합니다."
        ),
        nbformat.v4.new_markdown_cell(
            "### Dynamic year weight 항목 설명\n\n"
            "- `dynamic_year_weight['rental_count']`\n"
            "  - 2026년 이후 운영에서 대여 예측을 추가로 보정하는 계수입니다.\n"
            "  - 기본값은 `1.0`이며, 실제 운영 데이터에 따라 계속 갱신됩니다.\n"
            "- `dynamic_year_weight['return_count']`\n"
            "  - 2026년 이후 운영에서 반납 예측을 추가로 보정하는 계수입니다.\n"
            "  - 대여와 반납은 패턴이 다를 수 있으므로 별도로 관리합니다.\n"
            "- `alpha`\n"
            "  - 새로 관측된 실제값을 얼마나 빠르게 반영할지 결정하는 학습률입니다.\n"
            "  - 값이 크면 빠르게 적응하고, 값이 작으면 더 안정적으로 움직입니다.\n"
            "- `observed_ratio`\n"
            "  - `actual / predicted`로 계산된 관측 비율입니다.\n"
            "  - 예측보다 실제가 크면 1보다 크고, 실제가 작으면 1보다 작습니다.\n"
            "- `updated_dynamic_year_weight`\n"
            "  - `alpha`를 반영한 최종 보정 계수입니다.\n"
            "  - 다음 예측부터 이 값이 반영됩니다."
        ),
        nbformat.v4.new_code_cell(
            "dynamic_year_weight_state = {\n"
            "    station_id: {\n"
            "        'rental_count': 1.0,\n"
            "        'return_count': 1.0,\n"
            "    }\n"
            "    for station_id in TOP6_STATION_IDS\n"
            "}\n"
            "dynamic_year_weight_state"
        ),
        nbformat.v4.new_markdown_cell(
            "## 12. 보정 없는 기본 예측과 dynamic year_weight 반영 예측 비교\n\n"
            "아래 함수는 기존 예측값에 `dynamic_year_weight_2026`를 곱해서 운영용 예측값을 만듭니다."
        ),
        nbformat.v4.new_code_cell(
            "def predict_station_flow_with_dynamic_year_weight(station_id, dt, dynamic_state):\n"
            "    base_result = predict_station_flow(station_id, dt)\n"
            "    state = dynamic_state[int(station_id)]\n"
            "\n"
            "    rental_base = float(base_result['prediction']['rental_count_pred'])\n"
            "    return_base = float(base_result['prediction']['return_count_pred'])\n"
            "\n"
            "    rental_adj = max(rental_base * float(state['rental_count']), 0.0)\n"
            "    return_adj = max(return_base * float(state['return_count']), 0.0)\n"
            "    base_change = float(rental_base - return_base)\n"
            "    adjusted_change = float(rental_adj - return_adj)\n"
            "\n"
            "    return {\n"
            "        'station_id': int(station_id),\n"
            "        'station_name': base_result['station_name'],\n"
            "        'datetime': base_result['datetime'],\n"
            "        'dynamic_year_weight': {\n"
            "            'rental_count': float(state['rental_count']),\n"
            "            'return_count': float(state['return_count']),\n"
            "        },\n"
            "        'base_prediction': {\n"
            "            'rental_count_pred': rental_base,\n"
            "            'return_count_pred': return_base,\n"
            "            'bike_change_pred': base_change,\n"
            "            'display': {\n"
            "                'rental_count_pred': int(round(rental_base)),\n"
            "                'return_count_pred': int(round(return_base)),\n"
            "                'bike_change_pred': int(round(base_change)),\n"
            "            },\n"
            "        },\n"
            "        'adjusted_prediction': {\n"
            "            'rental_count_pred': float(rental_adj),\n"
            "            'return_count_pred': float(return_adj),\n"
            "            'bike_change_pred': adjusted_change,\n"
            "            'display': {\n"
            "                'rental_count_pred': int(round(rental_adj)),\n"
            "                'return_count_pred': int(round(return_adj)),\n"
            "                'bike_change_pred': int(round(adjusted_change)),\n"
            "            },\n"
            "        },\n"
            "    }\n"
        ),
        nbformat.v4.new_code_cell(
            "dynamic_example_dt = pd.Timestamp('2026-03-20 11:00:00')\n"
            "dynamic_example_result = predict_station_flow_with_dynamic_year_weight(TOP6_STATION_IDS[0], dynamic_example_dt, dynamic_year_weight_state)\n"
            "print(json.dumps(dynamic_example_result, ensure_ascii=False, indent=2))"
        ),
        nbformat.v4.new_markdown_cell(
            "## 13. 실제값이 들어오면 dynamic year_weight 업데이트\n\n"
            "실제 관측값이 들어오면 `actual / predicted` 비율을 계산하고, "
            "그 값을 이동평균 방식으로 반영합니다.\n\n"
            "예를 들어 `alpha=0.2`이면 새 관측의 20%만 반영하고, 기존 상태를 80% 유지합니다.\n\n"
            "업데이트 식:\n\n"
            "`new_weight = old_weight * (1 - alpha) + observed_ratio * alpha`"
        ),
        nbformat.v4.new_code_cell(
            "def update_dynamic_year_weight(station_id, predicted_result, actual_rental, actual_return, dynamic_state, alpha=0.2):\n"
            "    station_id = int(station_id)\n"
            "    state = dynamic_state[station_id]\n"
            "\n"
            "    pred_rental = max(float(predicted_result['adjusted_prediction']['rental_count_pred']), 1e-6)\n"
            "    pred_return = max(float(predicted_result['adjusted_prediction']['return_count_pred']), 1e-6)\n"
            "\n"
            "    rental_ratio = float(actual_rental) / pred_rental\n"
            "    return_ratio = float(actual_return) / pred_return\n"
            "\n"
            "    old_rental_weight = float(state['rental_count'])\n"
            "    old_return_weight = float(state['return_count'])\n"
            "\n"
            "    new_rental_weight = old_rental_weight * (1 - alpha) + rental_ratio * alpha\n"
            "    new_return_weight = old_return_weight * (1 - alpha) + return_ratio * alpha\n"
            "\n"
            "    dynamic_state[station_id]['rental_count'] = float(new_rental_weight)\n"
            "    dynamic_state[station_id]['return_count'] = float(new_return_weight)\n"
            "\n"
            "    return {\n"
            "        'station_id': station_id,\n"
            "        'alpha': float(alpha),\n"
            "        'observed_ratio': {\n"
            "            'rental_count': float(rental_ratio),\n"
            "            'return_count': float(return_ratio),\n"
            "        },\n"
            "        'updated_dynamic_year_weight': {\n"
            "            'rental_count': float(new_rental_weight),\n"
            "            'return_count': float(new_return_weight),\n"
            "        },\n"
            "    }\n"
        ),
        nbformat.v4.new_markdown_cell(
            "## 14. 보정 업데이트 예시\n\n"
            "예시로 2026-03-20 11시 예측 후 실제 관측값이 아래처럼 들어왔다고 가정합니다.\n\n"
            "- 실제 `rental_count = 3.1`\n"
            "- 실제 `return_count = 1.8`\n\n"
            "이 실제값으로 `dynamic_year_weight_2026`를 갱신합니다."
        ),
        nbformat.v4.new_code_cell(
            "observed_actual = {\n"
            "    'rental_count': 3.1,\n"
            "    'return_count': 1.8,\n"
            "}\n"
            "\n"
            "update_result = update_dynamic_year_weight(\n"
            "    station_id=TOP6_STATION_IDS[0],\n"
            "    predicted_result=dynamic_example_result,\n"
            "    actual_rental=observed_actual['rental_count'],\n"
            "    actual_return=observed_actual['return_count'],\n"
            "    dynamic_state=dynamic_year_weight_state,\n"
            "    alpha=0.2,\n"
            ")\n"
            "print(json.dumps(update_result, ensure_ascii=False, indent=2))"
        ),
        nbformat.v4.new_markdown_cell(
            "## 15. 보정 후 다음 시간 예측\n\n"
            "이제 방금 업데이트한 `dynamic_year_weight_2026`를 반영해서 다음 시간 예측을 다시 수행합니다.\n\n"
            "즉 흐름은 아래와 같습니다.\n\n"
            "1. 기존 예측 수행\n"
            "2. 실제값 수집\n"
            "3. dynamic year weight 업데이트\n"
            "4. 다음 시간 예측에 새 weight 반영"
        ),
        nbformat.v4.new_code_cell(
            "next_dt = pd.Timestamp('2026-03-20 12:00:00')\n"
            "next_prediction_after_update = predict_station_flow_with_dynamic_year_weight(\n"
            "    TOP6_STATION_IDS[0],\n"
            "    next_dt,\n"
            "    dynamic_year_weight_state,\n"
            ")\n"
            "print(json.dumps(next_prediction_after_update, ensure_ascii=False, indent=2))"
        ),
        nbformat.v4.new_markdown_cell(
            "## 15-1. 동적 연도 보정 전체 결과를 하나의 JSON으로 출력\n\n"
            "아래 JSON은 `보정 전 예측`, `실제값 기반 업데이트`, `보정 후 다음 시간 예측`을 한 번에 묶은 형태입니다."
        ),
        nbformat.v4.new_code_cell(
            "dynamic_year_weight_full_result = {\n"
            "    'station_id': int(TOP6_STATION_IDS[0]),\n"
            "    'station_name': MODEL_REGISTRY[int(TOP6_STATION_IDS[0])]['station_name'],\n"
            "    'before_update_prediction': dynamic_example_result,\n"
            "    'update_result': update_result,\n"
            "    'after_update_next_hour_prediction': next_prediction_after_update,\n"
            "}\n"
            "print(json.dumps(dynamic_year_weight_full_result, ensure_ascii=False, indent=2))"
        ),
        nbformat.v4.new_markdown_cell(
            "## 16. 운영 흐름 전체 요약\n\n"
            "2026년 이후 운영에서는 아래 루프를 반복하면 됩니다.\n\n"
            "1. 현재 시각 기준 예측 수행\n"
            "2. 예측 결과를 JSON으로 반환\n"
            "3. 다음 시간 실제값이 들어오면 dynamic year weight 업데이트\n"
            "4. 업데이트된 weight로 다음 예측 수행\n"
            "5. 이 과정을 계속 반복해서 2026년 이후 패턴 변화에 적응\n\n"
            "즉, 고정된 2023~2025 `year_weight` 위에 **운영 중 적응하는 2026 보정 계층**을 하나 더 얹는 방식입니다."
        ),
        nbformat.v4.new_markdown_cell(
            "### 실서비스 절차를 항목 기준으로 다시 정리\n\n"
            "1. 클라이언트 또는 스케줄러가 `station_id`, `datetime`, `current_bike_count_from_api`를 보냅니다.\n"
            "2. 서버는 `station_id`로 해당 station bundle을 메모리에서 찾습니다.\n"
            "3. `datetime`을 사용해 내부 feature를 계산합니다.\n"
            "4. `rental_count_pred`, `return_count_pred`를 float 값으로 예측합니다.\n"
            "5. `bike_change_pred`와 `next_bike_count_pred`를 계산합니다.\n"
            "6. 응답 JSON에는 `prediction`과 `display`를 함께 넣어 반환합니다.\n"
            "7. 실제 관측값이 들어오면 `dynamic_year_weight`를 업데이트합니다.\n"
            "8. 다음 요청부터는 업데이트된 `dynamic_year_weight`를 반영합니다."
        ),
    ]
    notebook.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"},
    }

    with NOTEBOOK_PATH.open("w", encoding="utf-8") as f:
        nbformat.write(notebook, f)


def main() -> None:
    H5_RELATED_DIR.mkdir(parents=True, exist_ok=True)
    top6_station_ids = get_top6_station_ids()
    holiday_dates = get_holiday_dates()
    save_model_store(H5_PATH, top6_station_ids, holiday_dates)

    example_json = build_example_json(H5_PATH)
    JSON_EXAMPLE_PATH.write_text(json.dumps(example_json, ensure_ascii=False, indent=2), encoding="utf-8")
    weekly_json = build_weekly_recursive_example(H5_PATH)
    WEEKLY_JSON_EXAMPLE_PATH.write_text(json.dumps(weekly_json, ensure_ascii=False, indent=2), encoding="utf-8")
    dynamic_json = build_dynamic_year_weight_example(H5_PATH)
    DYNAMIC_YEAR_WEIGHT_JSON_EXAMPLE_PATH.write_text(json.dumps(dynamic_json, ensure_ascii=False, indent=2), encoding="utf-8")

    create_notebook(top6_station_ids)

    print(json.dumps({
        "notebook_path": str(NOTEBOOK_PATH),
        "h5_path": str(H5_PATH),
        "json_example_path": str(JSON_EXAMPLE_PATH),
        "weekly_json_example_path": str(WEEKLY_JSON_EXAMPLE_PATH),
        "dynamic_year_weight_json_example_path": str(DYNAMIC_YEAR_WEIGHT_JSON_EXAMPLE_PATH),
        "top6_station_ids": top6_station_ids,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
