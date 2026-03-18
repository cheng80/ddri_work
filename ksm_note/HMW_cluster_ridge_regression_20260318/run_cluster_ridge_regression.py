from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
OUT_DIR = BASE_DIR / "outputs"

TRAIN_PATH = DATA_DIR / "ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv"
TEST_PATH = DATA_DIR / "ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv"

TARGET_COL = "bike_change_raw"
WEIGHT_COL = "sample_weight"
DATE_COL = "date"
CLUSTER_COL = "cluster"
DROP_FEATURES = [DATE_COL, TARGET_COL, WEIGHT_COL, CLUSTER_COL]


def k(s: str) -> str:
    return s.encode("utf-8").decode("unicode_escape")


def setup_plot_style() -> None:
    plt.rcParams["font.family"] = ["Malgun Gothic"]
    plt.rcParams["font.sans-serif"] = ["Malgun Gothic"]
    plt.rcParams["axes.unicode_minus"] = False
    sns.set_theme(style="whitegrid", font="Malgun Gothic")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)
    train[DATE_COL] = pd.to_datetime(train[DATE_COL])
    test[DATE_COL] = pd.to_datetime(test[DATE_COL])
    return train, test


def make_model() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=2.0, random_state=42)),
        ]
    )


def evaluate(y_true: pd.Series, pred: pd.Series) -> dict[str, float]:
    return {
        "rmse": float(mean_squared_error(y_true, pred) ** 0.5),
        "mae": float(mean_absolute_error(y_true, pred)),
        "r2": float(r2_score(y_true, pred)),
    }


def prepare_xy(df: pd.DataFrame, has_weight: bool) -> tuple[pd.DataFrame, pd.Series, pd.Series | None]:
    df = df[df[TARGET_COL].notna()].copy()
    if has_weight:
        df = df[df[WEIGHT_COL].notna()].copy()
    X = df.drop(columns=DROP_FEATURES if has_weight else [DATE_COL, TARGET_COL, CLUSTER_COL])
    y = df[TARGET_COL]
    w = df[WEIGHT_COL] if has_weight else None
    return X, y, w


def run_cluster_model(train_df: pd.DataFrame, test_df: pd.DataFrame, cluster_id: int) -> list[dict[str, float | int | str]]:
    train_cluster = train_df[train_df[CLUSTER_COL].eq(cluster_id)].copy()
    test_cluster = test_df[test_df[CLUSTER_COL].eq(cluster_id)].copy()

    split_train = train_cluster[train_cluster[DATE_COL].dt.year.eq(2023)].copy()
    split_valid = train_cluster[train_cluster[DATE_COL].dt.year.eq(2024)].copy()
    split_test = test_cluster.copy()

    X_train, y_train, w_train = prepare_xy(split_train, has_weight=True)
    X_valid, y_valid, _ = prepare_xy(split_valid, has_weight=True)
    X_test, y_test, _ = prepare_xy(split_test, has_weight=False)

    model = make_model()
    model.fit(X_train, y_train, ridge__sample_weight=w_train)

    rows: list[dict[str, float | int | str]] = []
    for split_name, X_split, y_split in [("train", X_train, y_train), ("valid", X_valid, y_valid), ("test", X_test, y_test)]:
        scores = evaluate(y_split, model.predict(X_split))
        rows.append({"cluster": cluster_id, "split": split_name, "rows": int(len(y_split)), **scores})
    return rows


def save_r2_plot(result_df: pd.DataFrame) -> Path:
    path = OUT_DIR / "cluster_r2_by_split.png"
    plot_df = result_df.copy()
    plot_df["cluster"] = plot_df["cluster"].astype(str)
    plot_df["split"] = plot_df["split"].map({"train": k("\ud559\uc2b5"), "valid": k("\uac80\uc99d"), "test": k("\ud14c\uc2a4\ud2b8")})
    plt.figure(figsize=(10, 5.2))
    sns.barplot(data=plot_df, x="cluster", y="r2", hue="split", palette=["#1f4e79", "#4f7942", "#c26a2e"])
    plt.title(k("\ud074\ub7ec\uc2a4\ud130\ubcc4 Ridge R2"))
    plt.xlabel(k("\ud074\ub7ec\uc2a4\ud130"))
    plt.ylabel("R2")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_rmse_plot(result_df: pd.DataFrame) -> Path:
    path = OUT_DIR / "cluster_rmse_by_split.png"
    plot_df = result_df.copy()
    plot_df["cluster"] = plot_df["cluster"].astype(str)
    plot_df["split"] = plot_df["split"].map({"train": k("\ud559\uc2b5"), "valid": k("\uac80\uc99d"), "test": k("\ud14c\uc2a4\ud2b8")})
    plt.figure(figsize=(10, 5.2))
    sns.barplot(data=plot_df, x="cluster", y="rmse", hue="split", palette=["#1f4e79", "#4f7942", "#c26a2e"])
    plt.title(k("\ud074\ub7ec\uc2a4\ud130\ubcc4 Ridge RMSE"))
    plt.xlabel(k("\ud074\ub7ec\uc2a4\ud130"))
    plt.ylabel("RMSE")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def build_report(result_df: pd.DataFrame, img_r2: Path, img_rmse: Path) -> str:
    valid_best = result_df[result_df["split"].eq("valid")].sort_values("r2", ascending=False)
    test_best = result_df[result_df["split"].eq("test")].sort_values("r2", ascending=False)

    lines: list[str] = []
    lines.append(k("\ud074\ub7ec\uc2a4\ud130\ubcc4 Ridge \ud68c\uadc0 \uacb0\uacfc \ubcf4\uace0\uc11c"))
    lines.append("")
    lines.append(k("## 1. \uc2e4\ud5d8 \uc124\uc815"))
    lines.append("- ??: Ridge(alpha=2.0)")
    lines.append(k("- ???: median imputation + standardization"))
    lines.append(k("- ?? ???: sample_weight ??"))
    lines.append(k("- ??: 2023=train, 2024=valid, 2025=test"))
    lines.append(k("- ????? ????? `cluster` ??? feature?? ??"))
    lines.append("")
    lines.append(k("## 2. ????? ??"))
    lines.append("")
    lines.append(result_df.to_markdown(index=False))
    lines.append("")
    lines.append(f"![cluster r2]({img_r2.name})")
    lines.append("")
    lines.append(f"![cluster rmse]({img_rmse.name})")
    lines.append("")
    lines.append(k("## 3. ??"))
    lines.append(k(f"- valid ?? ?? ????? `cluster {int(valid_best.iloc[0]['cluster'])}`?? R2={valid_best.iloc[0]['r2']:.6f} ???."))
    lines.append(k(f"- test ?? ?? ????? `cluster {int(test_best.iloc[0]['cluster'])}`?? R2={test_best.iloc[0]['r2']:.6f} ???."))
    lines.append(k("- ????? ?? ??? ???? ??, ??? ??? ????? ?????? ??? ?? ??? ?? ?? ?? ????? ????."))
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    setup_plot_style()

    train_df, test_df = load_data()
    clusters = sorted(train_df[CLUSTER_COL].dropna().astype(int).unique().tolist())

    rows: list[dict[str, float | int | str]] = []
    for cluster_id in clusters:
        rows.extend(run_cluster_model(train_df, test_df, cluster_id))

    result_df = pd.DataFrame(rows).sort_values(["split", "cluster"]).reset_index(drop=True)
    result_df.to_csv(OUT_DIR / "cluster_ridge_scores.csv", index=False, encoding="utf-8-sig")

    img_r2 = save_r2_plot(result_df)
    img_rmse = save_rmse_plot(result_df)

    report_path = OUT_DIR / "cluster_ridge_report.md"
    report_path.write_text(build_report(result_df, img_r2, img_rmse), encoding="utf-8")

    meta = {"train_path": TRAIN_PATH.as_posix(), "test_path": TEST_PATH.as_posix(), "clusters": clusters}
    (OUT_DIR / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(result_df.to_string(index=False))


if __name__ == "__main__":
    main()
