from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path("/Users/cheng80/Desktop/ddri_work")
FLOW_DIR = ROOT / "3조 공유폴더" / "station_hour_bike_flow_2023_2025"
TRAIN_PATH = FLOW_DIR / "station_hour_bike_flow_train_2023_2024.csv"
TEST_PATH = FLOW_DIR / "station_hour_bike_flow_test_2025.csv"


def load_frame(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    return df


def add_targets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["station_id", "time"]).copy()
    group = df.groupby("station_id", sort=False)
    df["target_bike_change_h1"] = group["bike_change"].shift(-1)
    df["target_bike_change_h2"] = group["bike_change"].shift(-2)
    df["target_bike_count_index_h1"] = group["bike_count_index"].shift(-1)
    df["target_bike_count_index_h2"] = group["bike_count_index"].shift(-2)
    return df


def print_summary(name: str, df: pd.DataFrame) -> None:
    print(f"\n[{name}]")
    print(f"rows={len(df):,}, stations={df['station_id'].nunique():,}")
    print("columns=", ", ".join(df.columns))
    print("\nnon-null target ratios:")
    for col in [
        "target_bike_change_h1",
        "target_bike_change_h2",
        "target_bike_count_index_h1",
        "target_bike_count_index_h2",
    ]:
        print(f"  {col}: {df[col].notna().mean():.4f}")
    sample = df[
        [
            "station_id",
            "time",
            "rental_count",
            "return_count",
            "bike_change",
            "bike_count_index",
            "target_bike_change_h1",
            "target_bike_change_h2",
            "target_bike_count_index_h1",
            "target_bike_count_index_h2",
        ]
    ].head(10)
    print("\nsample:")
    print(sample.to_string(index=False))


def validate_flow_identity(df: pd.DataFrame) -> None:
    mismatch = ((df["return_count"] - df["rental_count"]) != df["bike_change"]).sum()
    print(f"bike_change identity mismatches: {mismatch:,}")


def main() -> None:
    train = add_targets(load_frame(TRAIN_PATH))
    test = add_targets(load_frame(TEST_PATH))
    validate_flow_identity(train)
    print_summary("train_2023_2024", train)
    print_summary("test_2025", test)


if __name__ == "__main__":
    main()
