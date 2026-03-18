from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"
REPORT_DIR = ROOT / "reports" / "feature_compaction_assets"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PATH = DATA_DIR / "station_hour_bike_change_deseason_reduced_train_2023.csv.gz"
VALID_PATH = DATA_DIR / "station_hour_bike_change_deseason_reduced_valid_2024.csv.gz"
TEST_PATH = DATA_DIR / "station_hour_bike_change_deseason_reduced_test_2025.csv.gz"

SEED = 42


def load_split(path: Path) -> pd.DataFrame:
    parquet = path.with_suffix("").with_suffix(".parquet")
    resolved = parquet if parquet.exists() else path
    if resolved.suffix == ".parquet":
        df = pd.read_parquet(resolved)
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
    else:
        df = pd.read_csv(resolved, parse_dates=["time"])
    return df.sort_values(["station_id", "time"]).reset_index(drop=True)


def build_profile_matrix(df: pd.DataFrame, axis_col: str, profile_cols: list[str]) -> pd.DataFrame:
    return (
        df.groupby([axis_col] + profile_cols)["bike_change"]
        .mean()
        .unstack(profile_cols)
        .fillna(0.0)
        .sort_index()
    )


def build_similarity_map(
    df: pd.DataFrame,
    axis_col: str,
    profile_cols: list[str],
    corr_threshold: float,
    prefix: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    profile = build_profile_matrix(df, axis_col, profile_cols)
    magnitude = df.groupby(axis_col)["bike_change"].apply(lambda s: float(np.mean(np.abs(s))) + 1e-6)
    corr = profile.T.corr().fillna(0.0)

    remaining = list(profile.index)
    rows: list[dict[str, float | int]] = []
    group_id = 1

    while remaining:
        representative = remaining[0]
        current = [value for value in remaining if corr.loc[representative, value] >= corr_threshold]
        current = sorted(current)
        for value in current:
            rows.append(
                {
                    axis_col: int(value),
                    f"{prefix}_pattern_group": int(group_id),
                    f"representative_{axis_col}": int(representative),
                    f"{prefix}_pattern_corr": float(corr.loc[representative, value]),
                    f"{prefix}_scale_weight": float(magnitude.loc[value] / magnitude.loc[representative]),
                    f"is_representative_{axis_col}": int(value == representative),
                }
            )
        remaining = [value for value in remaining if value not in current]
        group_id += 1

    mapping = pd.DataFrame(rows).sort_values(axis_col).reset_index(drop=True)
    return mapping, corr


def apply_similarity_map(df: pd.DataFrame, mapping: pd.DataFrame, axis_col: str, prefix: str) -> pd.DataFrame:
    out = df.merge(mapping, on=axis_col, how="left")
    out[f"{prefix}_pattern_group"] = out[f"{prefix}_pattern_group"].fillna(out[axis_col]).astype(int)
    out[f"representative_{axis_col}"] = out[f"representative_{axis_col}"].fillna(out[axis_col]).astype(int)
    out[f"{prefix}_pattern_corr"] = out[f"{prefix}_pattern_corr"].fillna(1.0).astype(float)
    out[f"{prefix}_scale_weight"] = out[f"{prefix}_scale_weight"].fillna(1.0).astype(float)
    out[f"is_representative_{axis_col}"] = out[f"is_representative_{axis_col}"].fillna(1).astype(int)
    return out


def numeric_feature_candidates(df: pd.DataFrame) -> list[str]:
    candidates = [
        "station_activity_total",
        "bike_change_seasonal_expected",
        "bike_change_deseasonalized",
        "rental_count_deseasonalized",
        "return_count_deseasonalized",
        "bike_change_resid_lag_1",
        "bike_change_resid_lag_24",
        "bike_change_resid_lag_168",
        "bike_change_resid_rollmean_24",
        "bike_change_resid_rollstd_24",
        "bike_change_resid_rollmean_168",
        "bike_change_resid_rollstd_168",
        "bike_change_resid_trend_1_24",
        "bike_change_resid_trend_24_168",
        "month_pattern_group",
        "weekday_pattern_group",
        "hour_pattern_group",
        "month_scale_weight",
        "weekday_scale_weight",
        "hour_scale_weight",
        "month_pattern_corr",
        "weekday_pattern_corr",
        "hour_pattern_corr",
        "pattern_weight_combined",
        "is_weekend_or_holiday",
        "is_commute_hour",
        "is_night_hour",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "is_rainy",
        "heavy_rain",
        "lat",
        "lon",
        "dock_total",
        "qr_ratio",
    ]
    return [col for col in candidates if col in df.columns]


def remove_zero_variance_features(df: pd.DataFrame, cols: list[str]) -> tuple[list[str], list[dict[str, float | str]]]:
    kept = []
    dropped = []
    for col in cols:
        if float(df[col].nunique(dropna=True)) <= 1:
            dropped.append(
                {
                    "reason": "zero_variance",
                    "dropped_column": col,
                    "kept_column": "",
                    "metric": 0.0,
                }
            )
        else:
            kept.append(col)
    return kept, dropped


def choose_columns_by_correlation(
    df: pd.DataFrame,
    candidate_cols: list[str],
    threshold: float = 0.92,
) -> tuple[list[str], list[dict[str, float | str]], pd.DataFrame]:
    corr = df[candidate_cols].corr().abs().fillna(0.0)
    priority = [
        "bike_change_deseasonalized",
        "bike_change_seasonal_expected",
        "bike_change_resid_lag_1",
        "bike_change_resid_lag_24",
        "bike_change_resid_lag_168",
        "bike_change_resid_rollmean_24",
        "bike_change_resid_rollstd_24",
        "bike_change_resid_rollmean_168",
        "bike_change_resid_rollstd_168",
        "bike_change_resid_trend_1_24",
        "bike_change_resid_trend_24_168",
        "station_activity_total",
        "rental_count_deseasonalized",
        "return_count_deseasonalized",
        "month_pattern_group",
        "weekday_pattern_group",
        "hour_pattern_group",
        "month_scale_weight",
        "weekday_scale_weight",
        "hour_scale_weight",
        "pattern_weight_combined",
        "is_weekend_or_holiday",
        "is_commute_hour",
        "is_night_hour",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "is_rainy",
        "heavy_rain",
        "dock_total",
        "qr_ratio",
        "lat",
        "lon",
    ]
    rank = {col: idx for idx, col in enumerate(priority)}
    ordered = sorted(candidate_cols, key=lambda col: rank.get(col, len(priority)))

    kept: list[str] = []
    dropped: list[dict[str, float | str]] = []
    for col in ordered:
        matched = None
        for kept_col in kept:
            if corr.loc[col, kept_col] >= threshold:
                matched = kept_col
                break
        if matched is None:
            kept.append(col)
        else:
            dropped.append(
                {
                    "reason": "correlation",
                    "dropped_column": col,
                    "kept_column": matched,
                    "metric": float(corr.loc[col, matched]),
                }
            )
    return kept, dropped, corr


def sample_for_diagnostics(df: pd.DataFrame, max_rows: int = 120_000) -> pd.DataFrame:
    if len(df) <= max_rows:
        return df.copy()
    return df.sample(max_rows, random_state=SEED)


def compute_vif_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    clean = df[cols].replace([np.inf, -np.inf], np.nan).dropna().copy()
    if len(clean) > 25_000:
        clean = clean.sample(25_000, random_state=SEED)
    if clean.empty:
        return pd.DataFrame(columns=["feature", "vif"])
    values = clean.astype(float).to_numpy()
    rows = []
    for idx, col in enumerate(cols):
        vif = variance_inflation_factor(values, idx)
        rows.append({"feature": col, "vif": float(vif)})
    return pd.DataFrame(rows).sort_values("vif", ascending=False).reset_index(drop=True)


def prune_by_vif(
    df: pd.DataFrame,
    cols: list[str],
    threshold: float = 10.0,
    protected: set[str] | None = None,
) -> tuple[list[str], list[dict[str, float | str]], pd.DataFrame, pd.DataFrame]:
    protected = protected or set()
    working = cols.copy()
    dropped: list[dict[str, float | str]] = []
    before = compute_vif_table(df, working)

    while True:
        vif_table = compute_vif_table(df, working)
        if vif_table.empty:
            break
        over = vif_table[vif_table["vif"] > threshold]
        if over.empty:
            after = vif_table
            break
        drop_feature = None
        for feature in over["feature"]:
            if feature not in protected:
                drop_feature = feature
                break
        if drop_feature is None:
            after = vif_table
            break
        dropped.append(
            {
                "reason": "vif",
                "dropped_column": str(drop_feature),
                "kept_column": "",
                "metric": float(vif_table.loc[vif_table["feature"] == drop_feature, "vif"].iloc[0]),
            }
        )
        working.remove(drop_feature)
    else:
        after = compute_vif_table(df, working)

    if "after" not in locals():
        after = compute_vif_table(df, working)
    return working, dropped, before, after


def add_pattern_weight(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["pattern_weight_combined"] = (
        out.get("month_scale_weight", 1.0)
        * out.get("weekday_scale_weight", 1.0)
        * out.get("hour_scale_weight", 1.0)
    )
    return out


def build_balanced_sampled_train(df: pd.DataFrame, final_features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rep_mask = (
        (df["is_representative_month"] == 1)
        & (df["is_representative_weekday"] == 1)
        & (df["is_representative_hour"] == 1)
    )
    representative_pool = df.loc[rep_mask].copy()

    combo_counts = (
        df.groupby(
            [
                "month_pattern_group",
                "weekday_pattern_group",
                "hour_pattern_group",
                "month",
                "weekday",
                "hour",
            ]
        )
        .size()
        .reset_index(name="raw_count")
    )
    balanced_counts = (
        combo_counts.groupby(["month_pattern_group", "weekday_pattern_group", "hour_pattern_group"])["raw_count"]
        .min()
        .reset_index(name="balanced_count")
    )

    rep_cell = (
        representative_pool.groupby(["month_pattern_group", "weekday_pattern_group", "hour_pattern_group"])
        .size()
        .reset_index(name="representative_pool_count")
    )
    balanced_counts = balanced_counts.merge(
        rep_cell,
        on=["month_pattern_group", "weekday_pattern_group", "hour_pattern_group"],
        how="inner",
    )
    balanced_counts["sample_count"] = balanced_counts[["balanced_count", "representative_pool_count"]].min(axis=1)
    balanced_counts = balanced_counts[balanced_counts["sample_count"] > 0].copy()

    representative_pool = representative_pool.merge(
        balanced_counts[
            ["month_pattern_group", "weekday_pattern_group", "hour_pattern_group", "sample_count"]
        ],
        on=["month_pattern_group", "weekday_pattern_group", "hour_pattern_group"],
        how="inner",
    )

    sampled = (
        representative_pool.groupby(["month_pattern_group", "weekday_pattern_group", "hour_pattern_group"], group_keys=False)
        .apply(lambda g: g.sample(n=int(g["sample_count"].iloc[0]), random_state=SEED))
        .reset_index(drop=True)
    )

    cols = ["station_id", "time", "bike_change"] + [col for col in final_features if col not in {"station_id", "time", "bike_change"}]
    return sampled[cols].copy(), balanced_counts.sort_values(
        ["month_pattern_group", "weekday_pattern_group", "hour_pattern_group"]
    ).reset_index(drop=True)


def build_output_dataset(df: pd.DataFrame, final_features: list[str]) -> pd.DataFrame:
    cols = ["station_id", "time", "bike_change"] + [col for col in final_features if col not in {"station_id", "time", "bike_change"}]
    return df[cols].copy()


def save_gzip(df: pd.DataFrame, name: str) -> Path:
    path = DATA_DIR / name
    df.to_csv(path, index=False, encoding="utf-8-sig", compression="gzip")
    return path


def save_heatmap(matrix: pd.DataFrame, title: str, path: Path, figsize: tuple[float, float]):
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(matrix, cmap="RdBu_r", center=0, ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_vif_barplot(vif_df: pd.DataFrame, title: str, path: Path):
    if vif_df.empty:
        return
    plot_df = vif_df.head(20).sort_values("vif", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(plot_df["feature"], plot_df["vif"], color="#4C78A8")
    ax.axvline(10, color="#E45756", linestyle="--", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel("VIF")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_scatter_pair(df: pd.DataFrame, x_col: str, y_col: str, metric: float, path: Path):
    sample = sample_for_diagnostics(df[[x_col, y_col]].dropna(), max_rows=12000)
    if sample.empty:
        return
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.scatterplot(data=sample, x=x_col, y=y_col, s=8, alpha=0.15, linewidth=0, ax=ax)
    ax.set_title(f"{x_col} vs {y_col} | corr={metric:.3f}")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_group_bar(mapping: pd.DataFrame, axis_col: str, prefix: str, path: Path):
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=mapping, x=axis_col, y=f"{prefix}_pattern_group", color="#72B7B2", ax=ax)
    ax.set_title(f"{axis_col} representative grouping")
    ax.set_ylabel("pattern_group")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def write_visual_report(image_paths: list[Path], output_pdf: Path):
    with PdfPages(output_pdf) as pdf:
        for image_path in image_paths:
            img = plt.imread(image_path)
            height, width = img.shape[:2]
            fig_w = 11
            fig_h = max(6, 11 * height / max(width, 1))
            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            ax.imshow(img)
            ax.axis("off")
            ax.set_title(image_path.stem)
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def main():
    sns.set_theme(style="whitegrid")

    train_df = load_split(TRAIN_PATH)
    valid_df = load_split(VALID_PATH)
    test_df = load_split(TEST_PATH)

    month_map, month_corr = build_similarity_map(train_df, "month", ["weekday", "hour"], 0.78, "month")
    weekday_map, weekday_corr = build_similarity_map(train_df, "weekday", ["month", "hour"], 0.72, "weekday")
    hour_map, hour_corr = build_similarity_map(train_df, "hour", ["month", "weekday"], 0.60, "hour")

    for axis_col, prefix, mapping in [
        ("month", "month", month_map),
        ("weekday", "weekday", weekday_map),
        ("hour", "hour", hour_map),
    ]:
        train_df = apply_similarity_map(train_df, mapping, axis_col, prefix)
        valid_df = apply_similarity_map(valid_df, mapping, axis_col, prefix)
        test_df = apply_similarity_map(test_df, mapping, axis_col, prefix)

    train_df = add_pattern_weight(train_df)
    valid_df = add_pattern_weight(valid_df)
    test_df = add_pattern_weight(test_df)

    rep_diag_df = train_df[
        (train_df["is_representative_month"] == 1)
        & (train_df["is_representative_weekday"] == 1)
        & (train_df["is_representative_hour"] == 1)
    ].copy()
    diag_df = sample_for_diagnostics(train_df, max_rows=150_000)

    candidates = numeric_feature_candidates(train_df)
    candidates, zero_var_dropped = remove_zero_variance_features(diag_df, candidates)
    corr_kept, corr_dropped, pre_corr = choose_columns_by_correlation(diag_df, candidates, threshold=0.92)
    protected = {
        "bike_change_deseasonalized",
        "bike_change_resid_lag_1",
        "bike_change_resid_lag_24",
        "month_pattern_group",
        "weekday_pattern_group",
        "hour_pattern_group",
    }
    final_features, vif_dropped, vif_before, vif_after = prune_by_vif(diag_df, corr_kept, threshold=10.0, protected=protected)
    pruning_log = pd.DataFrame(zero_var_dropped + corr_dropped + vif_dropped)

    compact_train = build_output_dataset(train_df, final_features)
    compact_valid = build_output_dataset(valid_df, final_features)
    compact_test = build_output_dataset(test_df, final_features)
    sampled_train, balanced_counts = build_balanced_sampled_train(train_df, final_features)

    train_path = save_gzip(compact_train, "station_hour_bike_change_hierarchical_compact_train_2023.csv.gz")
    valid_path = save_gzip(compact_valid, "station_hour_bike_change_hierarchical_compact_valid_2024.csv.gz")
    test_path = save_gzip(compact_test, "station_hour_bike_change_hierarchical_compact_test_2025.csv.gz")
    sampled_path = save_gzip(sampled_train, "station_hour_bike_change_hierarchical_compact_sampled_train_2023.csv.gz")

    month_map_path = DATA_DIR / "station_hour_bike_change_month_hierarchical_map.csv"
    weekday_map_path = DATA_DIR / "station_hour_bike_change_weekday_hierarchical_map.csv"
    hour_map_path = DATA_DIR / "station_hour_bike_change_hour_hierarchical_map.csv"
    balanced_counts_path = DATA_DIR / "station_hour_bike_change_hierarchical_balanced_counts.csv"
    pruning_log_path = DATA_DIR / "station_hour_bike_change_hierarchical_pruning_log.csv"
    final_features_path = DATA_DIR / "station_hour_bike_change_hierarchical_final_features.csv"
    vif_before_path = DATA_DIR / "station_hour_bike_change_vif_before.csv"
    vif_after_path = DATA_DIR / "station_hour_bike_change_vif_after.csv"

    month_map.to_csv(month_map_path, index=False, encoding="utf-8-sig")
    weekday_map.to_csv(weekday_map_path, index=False, encoding="utf-8-sig")
    hour_map.to_csv(hour_map_path, index=False, encoding="utf-8-sig")
    balanced_counts.to_csv(balanced_counts_path, index=False, encoding="utf-8-sig")
    pruning_log.to_csv(pruning_log_path, index=False, encoding="utf-8-sig")
    pd.DataFrame({"feature": final_features}).to_csv(final_features_path, index=False, encoding="utf-8-sig")
    vif_before.to_csv(vif_before_path, index=False, encoding="utf-8-sig")
    vif_after.to_csv(vif_after_path, index=False, encoding="utf-8-sig")

    image_paths: list[Path] = []
    heatmap_paths = [
        (month_corr, "Month Pattern Correlation", REPORT_DIR / "month_pattern_heatmap.png", (8, 6)),
        (weekday_corr, "Weekday Pattern Correlation", REPORT_DIR / "weekday_pattern_heatmap.png", (7, 5)),
        (hour_corr, "Hour Pattern Correlation", REPORT_DIR / "hour_pattern_heatmap.png", (10, 8)),
        (pre_corr.loc[corr_kept, corr_kept], "Feature Correlation After Correlation Pruning", REPORT_DIR / "feature_corr_after_correlation_pruning.png", (10, 8)),
    ]
    for matrix, title, path, figsize in heatmap_paths:
        save_heatmap(matrix, title, path, figsize)
        image_paths.append(path)

    for mapping, axis_col, prefix, name in [
        (month_map, "month", "month", "month_group_bar.png"),
        (weekday_map, "weekday", "weekday", "weekday_group_bar.png"),
        (hour_map, "hour", "hour", "hour_group_bar.png"),
    ]:
        path = REPORT_DIR / name
        save_group_bar(mapping, axis_col, prefix, path)
        image_paths.append(path)

    vif_before_img = REPORT_DIR / "vif_before.png"
    vif_after_img = REPORT_DIR / "vif_after.png"
    save_vif_barplot(vif_before, "VIF before pruning", vif_before_img)
    save_vif_barplot(vif_after, "VIF after pruning", vif_after_img)
    image_paths.extend([vif_before_img, vif_after_img])

    scatter_source = sample_for_diagnostics(diag_df, max_rows=12000)
    for row in corr_dropped[:8]:
        dropped_col = str(row["dropped_column"])
        kept_col = str(row["kept_column"])
        path = REPORT_DIR / f"scatter_{dropped_col}_vs_{kept_col}.png"
        save_scatter_pair(scatter_source, dropped_col, kept_col, float(row["metric"]), path)
        image_paths.append(path)

    report_pdf = REPORT_DIR / "feature_compaction_diagnostics.pdf"
    write_visual_report([path for path in image_paths if path.exists()], report_pdf)

    meta = {
        "target": "bike_change",
        "source": {
            "train": TRAIN_PATH.name,
            "valid": VALID_PATH.name,
            "test": TEST_PATH.name,
        },
        "outputs": {
            "train": train_path.name,
            "valid": valid_path.name,
            "test": test_path.name,
            "sampled_train": sampled_path.name,
            "month_map": month_map_path.name,
            "weekday_map": weekday_map_path.name,
            "hour_map": hour_map_path.name,
            "balanced_counts": balanced_counts_path.name,
            "pruning_log": pruning_log_path.name,
            "final_features": final_features_path.name,
            "vif_before": vif_before_path.name,
            "vif_after": vif_after_path.name,
            "diagnostic_pdf": str(report_pdf.relative_to(ROOT)),
        },
        "row_counts": {
            "train": int(len(compact_train)),
            "valid": int(len(compact_valid)),
            "test": int(len(compact_test)),
            "sampled_train": int(len(sampled_train)),
        },
        "column_counts": {
            "train_columns": int(len(compact_train.columns)),
            "feature_columns": int(len(compact_train.columns) - 3),
        },
        "group_counts": {
            "month_groups": int(month_map["month_pattern_group"].nunique()),
            "weekday_groups": int(weekday_map["weekday_pattern_group"].nunique()),
            "hour_groups": int(hour_map["hour_pattern_group"].nunique()),
        },
        "thresholds": {
            "month_corr": 0.78,
            "weekday_corr": 0.72,
            "hour_corr": 0.60,
            "feature_corr": 0.92,
            "vif": 10.0,
        },
        "representatives": {
            "month": month_map.loc[month_map["is_representative_month"] == 1, "month"].astype(int).tolist(),
            "weekday": weekday_map.loc[weekday_map["is_representative_weekday"] == 1, "weekday"].astype(int).tolist(),
            "hour": hour_map.loc[hour_map["is_representative_hour"] == 1, "hour"].astype(int).tolist(),
        },
    }
    meta_path = DATA_DIR / "station_hour_bike_change_hierarchical_compact_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
