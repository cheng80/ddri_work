from __future__ import annotations

import argparse
import json
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
            "source_name": "mapo_camping_status_data_go_kr",
            "category": "camping_master",
            "official_site": "https://www.data.go.kr/data/15126656/fileData.do",
            "dataset_or_entry": "서울특별시 마포구_캠핑장 현황_20250403",
            "access_type": "manual_download",
            "required_auth": "no_auth_for_portal_page",
            "recommended_fields": "campground_name, road_address, dong_name, business_start_date, camping_site_count",
            "priority": 1,
        },
        {
            "source_name": "kma_weather_api",
            "category": "weather",
            "official_site": "https://data.kma.go.kr/api/selectApiDetail.do?pgmNo=42",
            "dataset_or_entry": "기상자료개방포털 Open API",
            "access_type": "api",
            "required_auth": "api_key_required",
            "recommended_fields": "timestamp, weather_temp_c, weather_precip_mm, weather_humidity, weather_wind_speed",
            "priority": 2,
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
            "source_name": "kopis_performance_list_api",
            "category": "performance",
            "official_site": "https://www.data.go.kr/data/15097805/openapi.do",
            "dataset_or_entry": "예술경영지원센터_공연예술통합전산망_DB검색_공연목록",
            "access_type": "api",
            "required_auth": "service_key_required",
            "recommended_fields": "performance_id, performance_name, venue_name, area, sigungu, performance_start_date, performance_end_date, genre",
            "priority": 2,
        },
        {
            "source_name": "kopis_venue_list_api",
            "category": "performance_venue",
            "official_site": "https://www.data.go.kr/data/15097806/openapi.do",
            "dataset_or_entry": "예술경영지원센터_공연예술통합전산망_DB검색_공연시설목록",
            "access_type": "api",
            "required_auth": "service_key_required",
            "recommended_fields": "venue_id, venue_name, sido_code, gugun_code, venue_characteristic_code",
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
            "source_name": "hangang_usage_pattern_jkila_2025",
            "category": "research_reference",
            "official_site": "https://www.jkila.org/archive/view_article?pid=jkila-53-3-31",
            "dataset_or_entry": "유동인구 데이터를 활용한 한강공원의 이용 패턴과 특성 연구",
            "access_type": "manual_review",
            "required_auth": "none",
            "recommended_fields": "park_name, peak_hour, low_hour, age_pattern, spatial_context",
            "priority": 3,
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
            "KMA_API_KEY=",
            "DATA_GO_KR_API_KEY=",
            "KOPIS_API_KEY=",
            "NANJI_PARKING_SOURCE_URL=",
        ]
    )


def build_collection_notes() -> str:
    lines = [
        "# External Data Collection Notes",
        "",
        "1. Fill API keys in a local .env file and do not commit secrets.",
        "2. Save untouched downloads into data/raw/ and keep the original filenames when possible.",
        "3. Save cleaned model-ready files into data/processed/.",
        "4. Keep timestamp timezone consistent, preferably Asia/Seoul.",
        "5. Prioritize 2023, 2024, and 2025 rows when filtering raw files.",
        "6. Start with camping or parking target data before enriching with weather, holidays, and performance schedules.",
        "7. The KOPIS performance APIs are useful for building event flags around Nanji and Hangang demand spikes.",
    ]
    return "\n".join(lines)


def build_example_request_plan() -> dict:
    open_meteo_params = {
        "latitude": 37.5665,
        "longitude": 126.8789,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "Asia/Seoul",
        "start_date": "2023-01-01",
        "end_date": "2025-12-31",
    }
    return {
        "mapo_camping_dataset": {
            "portal_url": "https://www.data.go.kr/data/15126656/fileData.do",
            "provider_url": "https://mapo.go.kr/site/main/openData/view?dataId=229",
            "notes": [
                "The public portal metadata indicates a CSV dataset called 서울특별시 마포구_캠핑장 현황_20250403.",
                "Use this as the master reference for Nanji-related campground attributes such as address and site count.",
            ],
        },
        "kopis_performance_api": {
            "performance_list_url": "https://www.data.go.kr/data/15097805/openapi.do",
            "venue_list_url": "https://www.data.go.kr/data/15097806/openapi.do",
            "notes": [
                "Use performance list data for date-based event flags.",
                "Filter Seoul venues first, then narrow to Mapo/Hangang-adjacent candidates with the venue API.",
            ],
        },
        "open_meteo_example": {
            "base_url": "https://archive-api.open-meteo.com/v1/archive",
            "query_string": urlencode(open_meteo_params),
        },
        "research_reference": {
            "article_url": "https://www.jkila.org/archive/view_article?pid=jkila-53-3-31",
            "notes": [
                "The paper analyzed 2023 KT mobile population data across 11 Hangang parks.",
                "Its park-level summary reports 16:00 as the peak usage hour for Nanji.",
            ],
        },
        "notes": [
            "Use Nanji parking lot coordinates instead of the placeholder if precise coordinates are known.",
            "After raw files are downloaded, run prepare_external_datasets.py to filter 2023-2025 rows and remove missing-value/outlier records.",
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
