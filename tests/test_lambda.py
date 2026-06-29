"""Unit tests for Lambda handler."""

import sys
from pathlib import Path

LAMBDA_DIR = Path(__file__).resolve().parents[1] / "lambda"
sys.path.insert(0, str(LAMBDA_DIR))

import lambda_function


VALID_RECORD = {
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
        "us_aqi": 105,
    },
}


class FakeBatchWriter:
    def __init__(self, table):
        self.table = table

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def put_item(self, Item):
        self.table.items.append(Item)


class FakeTable:
    def __init__(self):
        self.items = []
        self.overwrite_by_pkeys = None

    def batch_writer(self, overwrite_by_pkeys=None):
        self.overwrite_by_pkeys = overwrite_by_pkeys
        return FakeBatchWriter(self)


class FakeDynamoDB:
    def __init__(self, table):
        self.table = table
        self.table_name = None

    def Table(self, table_name):
        self.table_name = table_name
        return self.table


def test_lambda_handler_reads_s3_event_and_writes_valid_records(monkeypatch):
    table = FakeTable()
    dynamodb = FakeDynamoDB(table)
    loaded_from = {}

    def fake_load_json_from_s3(bucket_name, object_key):
        loaded_from["bucket"] = bucket_name
        loaded_from["key"] = object_key
        return [VALID_RECORD, {}]

    monkeypatch.setenv("TABLE_NAME", "air_quality_readings")
    monkeypatch.delenv("BUCKET_NAME", raising=False)
    monkeypatch.delenv("OBJECT_KEY", raising=False)
    monkeypatch.setattr(lambda_function, "load_json_from_s3", fake_load_json_from_s3)
    monkeypatch.setattr(lambda_function, "generate_timestamp", lambda: "2026-06-29T18:30:00Z")
    monkeypatch.setattr(lambda_function.boto3, "resource", lambda service_name: dynamodb)

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "cities-air-quality-bucket"},
                    "object": {"key": "raw%2Fair_quality_raw.json"},
                }
            }
        ]
    }

    response = lambda_function.lambda_handler(event, None)

    assert loaded_from == {
        "bucket": "cities-air-quality-bucket",
        "key": "raw/air_quality_raw.json",
    }
    assert dynamodb.table_name == "air_quality_readings"
    assert table.overwrite_by_pkeys == ["record_id"]
    assert len(table.items) == 1
    assert table.items[0]["record_id"] == "DELHI#2026-06-29T18:00"
    assert table.items[0]["air_quality_status"] == "UNHEALTHY_FOR_SENSITIVE"
    assert response["records_processed"] == 2
    assert response["records_inserted"] == 1
    assert response["records_rejected"] == 1


def test_lambda_handler_falls_back_to_env_s3_location(monkeypatch):
    table = FakeTable()
    dynamodb = FakeDynamoDB(table)
    loaded_from = {}

    def fake_load_json_from_s3(bucket_name, object_key):
        loaded_from["bucket"] = bucket_name
        loaded_from["key"] = object_key
        return [VALID_RECORD]

    monkeypatch.setenv("TABLE_NAME", "air_quality_readings")
    monkeypatch.setenv("BUCKET_NAME", "manual-bucket")
    monkeypatch.setenv("OBJECT_KEY", "raw/manual.json")
    monkeypatch.setattr(lambda_function, "load_json_from_s3", fake_load_json_from_s3)
    monkeypatch.setattr(lambda_function, "generate_timestamp", lambda: "2026-06-29T18:30:00Z")
    monkeypatch.setattr(lambda_function.boto3, "resource", lambda service_name: dynamodb)

    response = lambda_function.lambda_handler({}, None)

    assert loaded_from == {"bucket": "manual-bucket", "key": "raw/manual.json"}
    assert response["records_inserted"] == 1
