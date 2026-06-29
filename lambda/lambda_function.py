import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote_plus

import boto3


def to_decimal(value):
    return Decimal(str(value))


def get_air_quality_status(aqi):
    aqi = to_decimal(aqi)

    if aqi <= Decimal("50"):
        return "GOOD"
    if aqi <= Decimal("100"):
        return "MODERATE"
    if aqi <= Decimal("150"):
        return "UNHEALTHY_FOR_SENSITIVE"
    if aqi <= Decimal("200"):
        return "UNHEALTHY"
    if aqi <= Decimal("300"):
        return "VERY_UNHEALTHY"

    return "HAZARDOUS"


def validate_record(record):
    if not isinstance(record, dict):
        return False

    current = record.get("current", {})
    required_fields = ["time", "pm2_5", "pm10", "us_aqi"]

    if not record.get("city") or not isinstance(current, dict):
        return False

    if any(current.get(field) is None for field in required_fields):
        return False

    try:
        to_decimal(record.get("latitude"))
        to_decimal(record.get("longitude"))
        to_decimal(current["pm2_5"])
        to_decimal(current["pm10"])
        to_decimal(current["us_aqi"])
    except (InvalidOperation, TypeError, ValueError):
        return False

    return True


def build_item(record, processed_at):
    current = record["current"]
    city = record["city"].strip().upper()
    timestamp = current["time"]

    return {
        "record_id": f"{city}#{timestamp}",
        "city": city,
        "timestamp": timestamp,
        "latitude": to_decimal(record["latitude"]),
        "longitude": to_decimal(record["longitude"]),
        "pm25": to_decimal(current["pm2_5"]),
        "pm10": to_decimal(current["pm10"]),
        "carbon_monoxide": to_decimal(current.get("carbon_monoxide", 0)),
        "nitrogen_dioxide": to_decimal(current.get("nitrogen_dioxide", 0)),
        "sulphur_dioxide": to_decimal(current.get("sulphur_dioxide", 0)),
        "ozone": to_decimal(current.get("ozone", 0)),
        "air_quality_index": to_decimal(current["us_aqi"]),
        "air_quality_status": get_air_quality_status(current["us_aqi"]),
        "processed_at_utc": processed_at,
    }


def get_s3_location(event):
    if event.get("Records"):
        s3_record = event["Records"][0]["s3"]
        bucket = s3_record["bucket"]["name"]
        key = unquote_plus(s3_record["object"]["key"])
        return bucket, key

    return os.environ["BUCKET_NAME"], os.environ["OBJECT_KEY"]


def load_records_from_s3(bucket, key):
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)

    return json.loads(
        response["Body"].read().decode("utf-8"),
        parse_float=Decimal,
        parse_int=Decimal,
    )


def lambda_handler(event, context):
    bucket, key = get_s3_location(event)
    table_name = os.environ["TABLE_NAME"]

    print("Air Quality ETL started")
    print(f"Source: s3://{bucket}/{key}")

    records = load_records_from_s3(bucket, key)
    processed_at = datetime.now(timezone.utc).isoformat()
    table = boto3.resource("dynamodb").Table(table_name)

    inserted = 0
    rejected = 0

    with table.batch_writer(overwrite_by_pkeys=["record_id"]) as batch:
        for record in records:
            if not validate_record(record):
                rejected += 1
                continue

            batch.put_item(Item=build_item(record, processed_at))
            inserted += 1

    audit_summary = {
        "records_processed": len(records),
        "records_inserted": inserted,
        "records_rejected": rejected,
        "processed_at": processed_at,
    }

    print(f"Audit Summary: {audit_summary}")

    return {
        "statusCode": 200,
        "message": "ETL completed successfully",
        **audit_summary,
    }
