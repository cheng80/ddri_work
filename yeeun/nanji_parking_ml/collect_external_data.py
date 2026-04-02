from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build external data collection plan for Nanji parking project")
    parser.add_argument(
        "--output-dir",
        default="yeeun/nanji_parking_ml/external_data_plan",
        help="Directory where collection plan files will be saved",
    )
    return parser.parse_args()


def build_source_catalog() -> pd.DataFrame:
    rows = [
        {
            "source_name": "seoul_open_data_hangang_parking_info",
            "category": "parking_master",
            "official_site": "https://data.seoul.go.kr",
            "dataset_or_entry": "한강공원 주차장 정보",
            "access_type": "manual_check_or_api_if_available",
            "required_auth": "depends_on_dataset",
            "recommended_fields": "parking_lot_id, parking_lot_name, total_spaces, address, lat, lon",
            "priority": 1,
        },
        {
            "source_name": "kma_weather_api",
            "category": "weather",
            "official_site": "https://data.kma.go.kr",
            "dataset_or_entry": "기상자료개방포털 Open API",
            "access_type": "api",
            "required_auth": "api_key_required",
            "recommended_fields": "timestamp, weather_temp_c, weather_precip_mm, weather_humidity, weather_wind_speed",
            "priority": 2,
        },
        {
            "source_name": "open_meteo",
            "category": "weather_backup",
            "official_site": "https://open-meteo.com",
            "dataset_or_entry": "Historical Weather API",
            "access_type": "api",
            "required_auth": "no_key_or_check_current_policy",
            "recommended_fields": "timestamp, temperature_2m, precipitation, relative_humidity_2m, wind_speed_10m",
            "priority": 3,
        },
        {
            "source_name": "korean_holiday_api",
            "category": "calendar",
            "official_site": "https://www.data.go.kr",
            "dataset_or_entry": "특일 정보 API",
            "access_type": "api",
            "required_auth": "api_key_required",
            "recommended_fields": "date, holiday_name, is_holiday",
            "priority": 2,
        },
        {
            "source_name": "nanji_facility_usage_manual",
            "category": "nanji_special",
            "official_site": "manual_or_official_booking_site",
            "dataset_or_entry": "난지 캠핑장/행사/시설 이용량",
            "access_type": "manual_or_crawling",
            "required_auth": "unknown",
            "recommended_fields": "date, event_flag, facility_demand_level",
            "priority": 4,
        },
    ]
    return pd.DataFrame(rows).sort_values(["priority", "source_name"]).reset_index(drop=True)


def build_env_template() -> str:
    return "\n".join(
        [
            "SEOUL_OPEN_DATA_API_KEY=",
            "KMA_API_KEY=",
            "DATA_GO_KR_API_KEY=",
            "NANJI_PARKING_SOURCE_URL=",
        ]
    )


def build_collection_notes() -> str:
    lines = [
        "# External Data Collection Notes",
        "",
        "1. Fill API keys in a local .env file and do not commit secrets.",
        "2. Save untouched downloads into data/raw/.",
        "3. Save merged model-ready files into data/processed/.",
        "4. Keep timestamp timezone consistent, preferably Asia/Seoul.",
        "5. Start with parking target data before enriching with weather and holidays.",
    ]
    return "\n".join(lines)


def build_example_request_plan() -> dict:
    open_meteo_params = {
        "latitude": 37.5665,
        "longitude": 126.8789,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "Asia/Seoul",
    }
    return {
        "open_meteo_example": {
            "base_url": "https://archive-api.open-meteo.com/v1/archive",
            "query_string": urlencode(open_meteo_params),
        },
        "notes": [
            "Use Nanji parking lot coordinates instead of the placeholder if precise coordinates are known.",
            "For Seoul Open Data and data.go.kr, fill the exact endpoint after dataset selection and key issuance.",
        ],
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data_dir = output_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    catalog_df = build_source_catalog()
    catalog_df.to_csv(output_dir / "source_catalog.csv", index=False, encoding="utf-8-sig")

    (output_dir / ".env.example").write_text(build_env_template(), encoding="utf-8")
    (output_dir / "COLLECTION_NOTES.md").write_text(build_collection_notes(), encoding="utf-8")
    (output_dir / "request_plan.json").write_text(
        json.dumps(build_example_request_plan(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Collection plan scaffold created at: {output_dir}")
    print("Files created:")
    for path in [
        output_dir / "source_catalog.csv",
        output_dir / ".env.example",
        output_dir / "COLLECTION_NOTES.md",
        output_dir / "request_plan.json",
    ]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
