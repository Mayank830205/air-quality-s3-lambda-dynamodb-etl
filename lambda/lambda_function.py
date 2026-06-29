import os
import json
from urllib.parse import unquote_plus

import boto3

from transformations import build_item, validate_record
from utils import generate_timestamp, load_json_from_s3


def get_s3_location(event):
    """Return the S3 bucket/key from an S3 event, falling back to env vars."""

    records = event.get("Records") if isinstance(event, dict) else None

    if records:
        s3_record = records[0].get("s3", {})
        bucket_name = s3_record.get("bucket", {}).get("name")
        object_key = s3_record.get("object", {}).get("key")

        if bucket_name and object_key:
            return bucket_name, unquote_plus(object_key)

    bucket_name = os.environ.get("BUCKET_NAME")
    object_key = os.environ.get("OBJECT_KEY")

    if bucket_name and object_key:
        return bucket_name, object_key

    raise ValueError("S3 bucket/key not found in event or BUCKET_NAME/OBJECT_KEY env vars")


def lambda_handler(event, context):

    print("========== Air Quality ETL Pipeline Started ==========")

    bucket_name, object_key = get_s3_location(event)
    table_name = os.environ["TABLE_NAME"]

    print(f"Reading data from S3 Bucket: {bucket_name}")
    print(f"Object Key: {object_key}")

    records = load_json_from_s3(bucket_name, object_key)

    if not isinstance(records, list):
        raise ValueError("S3 object must contain a JSON array of city records")

    print(f"Total records loaded: {len(records)}")

    processed_at = generate_timestamp()

    table = boto3.resource("dynamodb").Table(table_name)

    inserted = 0
    rejected = 0

    print("Starting data transformation...")

    with table.batch_writer(overwrite_by_pkeys=["record_id"]) as batch:

        for record in records:

            if not validate_record(record):
                rejected += 1
                continue

            item = build_item(record, processed_at)

            batch.put_item(Item=item)

            inserted += 1

    audit_summary = {
        "source_bucket": bucket_name,
        "source_key": object_key,
        "records_processed": len(records),
        "records_inserted": inserted,
        "records_rejected": rejected,
        "processed_at": processed_at,
    }

    print("Data successfully loaded into DynamoDB")
    print("Audit Summary: " + json.dumps(audit_summary))

    print("========== Air Quality ETL Pipeline Completed ==========")

    return {
        "statusCode": 200,
        "message": "Air Quality ETL Completed Successfully",
        **audit_summary,
    }
