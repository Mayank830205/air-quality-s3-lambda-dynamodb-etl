"""Unit tests for transformation functions."""

from copy import deepcopy
import sys
from decimal import Decimal
from pathlib import Path

LAMBDA_DIR = Path(__file__).resolve().parents[1] / "lambda"
sys.path.insert(0, str(LAMBDA_DIR))

from transformations import (
    build_item,
    get_air_quality_status,
    validate_record,
)


sample_record = {
    "city": "Delhi",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "current": {
        "time": "2026-06-29T18:00",
        "pm2_5": 42.5,
        "pm10": 81.7,
        "carbon_monoxide": 310,
        "nitrogen_dioxide": 22,
        "sulphur_dioxide": 3,
        "ozone": 66,
        "us_aqi": 105
    }
}


def make_record():
    return deepcopy(sample_record)


def test_get_air_quality_status():

    assert get_air_quality_status(25) == "GOOD"
    assert get_air_quality_status(75) == "MODERATE"
    assert get_air_quality_status(125) == "UNHEALTHY_FOR_SENSITIVE"
    assert get_air_quality_status(175) == "UNHEALTHY"
    assert get_air_quality_status(250) == "VERY_UNHEALTHY"
    assert get_air_quality_status(350) == "HAZARDOUS"


def test_validate_record():

    assert validate_record(sample_record) is True

    invalid = {}

    assert validate_record(invalid) is False


def test_validate_record_rejects_missing_geo_and_bad_aqi():

    missing_geo = make_record()
    del missing_geo["latitude"]

    assert validate_record(missing_geo) is False

    bad_aqi = make_record()
    bad_aqi["current"]["us_aqi"] = "not-a-number"

    assert validate_record(bad_aqi) is False


def test_build_item():

    item = build_item(
        sample_record,
        "2026-06-29T18:30:00Z"
    )

    assert item["city"] == "DELHI"

    assert item["record_id"] == "DELHI#2026-06-29T18:00"

    assert item["timestamp"] == "2026-06-29T18:00"

    assert item["pm25"] == Decimal("42.5")

    assert item["pm10"] == Decimal("81.7")

    assert item["air_quality_index"] == Decimal("105")

    assert (
        item["air_quality_status"]
        == "UNHEALTHY_FOR_SENSITIVE"
    )

    assert item["processed_at_utc"] == "2026-06-29T18:30:00Z"

def test_build_item_defaults_optional_null_pollutants_to_zero():

    record = make_record()
    record["current"]["ozone"] = None

    item = build_item(record, "2026-06-29T18:30:00Z")

    assert item["ozone"] == Decimal("0")
