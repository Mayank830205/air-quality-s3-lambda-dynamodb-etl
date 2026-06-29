"""Utility functions for the air quality ETL pipeline."""

import json
from datetime import datetime, timezone
from decimal import Decimal

import boto3


def load_json_from_s3(bucket_name, object_key):

    print(f"Downloading file from s3://{bucket_name}/{object_key}")

    s3 = boto3.client("s3")

    response = s3.get_object(
        Bucket=bucket_name,
        Key=object_key,
    )

    data = json.loads(
        response["Body"].read().decode("utf-8"),
        parse_float=Decimal,
        parse_int=Decimal,
    )

    print("File downloaded successfully")

    return data


def generate_timestamp():
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()
