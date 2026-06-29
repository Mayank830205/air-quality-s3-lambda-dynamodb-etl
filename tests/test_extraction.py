"""Unit tests for the local extraction script."""

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTRACTION_DIR = Path(__file__).resolve().parents[1] / "extraction"
sys.path.insert(0, str(EXTRACTION_DIR))

import main as extraction_main


def test_extract_all_cities_writes_one_json_file(monkeypatch):
    def fake_fetch_air_quality(city):
        return {
            "city": city,
            "latitude": 10,
            "longitude": 20,
            "current": {
                "time": "2026-06-29T18:00",
                "pm2_5": 1,
                "pm10": 2,
                "us_aqi": 3,
            },
        }

    monkeypatch.setattr(extraction_main, "fetch_air_quality", fake_fetch_air_quality)

    output_dir = PROJECT_ROOT / "data" / "test_raw" / "extraction"
    filepath, records = extraction_main.extract_all_cities(
        ["Delhi", "Mumbai"],
        output_dir=output_dir,
    )

    assert filepath.parent == output_dir
    assert filepath.name.startswith("air_quality_raw_")
    assert filepath.suffix == ".json"
    assert [record["city"] for record in records] == ["Delhi", "Mumbai"]
    assert json.loads(filepath.read_text(encoding="utf-8")) == records


def test_extract_all_cities_fails_when_any_city_fails(monkeypatch):
    def fake_fetch_air_quality(city):
        if city == "Mumbai":
            raise RuntimeError("API unavailable")

        return {"city": city, "latitude": 10, "longitude": 20, "current": {}}

    monkeypatch.setattr(extraction_main, "fetch_air_quality", fake_fetch_air_quality)

    with pytest.raises(RuntimeError, match="Mumbai"):
        extraction_main.extract_all_cities(
            ["Delhi", "Mumbai"],
            output_dir=PROJECT_ROOT / "data"