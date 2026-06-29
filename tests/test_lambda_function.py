from decimal import Decimal

import lambda_function


SAMPLE_RECORD = {
    "city": "Delhi",
    "latitude": 28.6139,
    "longitude": 77.209,
    "current": {
        "time": "2026-06-29T18:00",
        "pm2_5": 42.5,
        "pm10": 81.7,
        "carbon_monoxide": 310,
        "nitrogen_dioxide": 22,
        "sulphur_dioxide": 3,
        "ozone": 66,
        "us_aqi": 105,
    },
}


def test_get_air_quality_status():
    assert lambda_function.get_air_quality_status(25) == "GOOD"
    assert lambda_function.get_air_quality_status(75) == "MODERATE"
    assert lambda_function.get_air_quality_status(125) == "UNHEALTHY_FOR_SENSITIVE"
    assert lambda_function.get_air_quality_status(175) == "UNHEALTHY"
    assert lambda_function.get_air_quality_status(250) == "VERY_UNHEALTHY"
    assert lambda_function.get_air_quality_status(350) == "HAZARDOUS"


def test_validate_record():
    assert lambda_function.validate_record(SAMPLE_RECORD) is True
    assert lambda_function.validate_record({}) is False


def test_build_item():
    item = lambda_function.build_item(SAMPLE_RECORD, "2026-06-29T18:30:00Z")

    assert item["record_id"] == "DELHI#2026-06-29T18:00"
    assert item["city"] == "DELHI"
    assert item["pm25"] == Decimal("42.5")
    assert item["air_quality_status"] == "UNHEALTHY_FOR_SENSITIVE"
    assert item["processed_at_utc"] == "2026-06-29T18:30:00Z"
