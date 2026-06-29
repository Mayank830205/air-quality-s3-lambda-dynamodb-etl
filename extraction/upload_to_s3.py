import boto3
import os
from pathlib import Path

DEFAULT_BUCKET_NAME = "cities-air-quality-bucket"
S3_FOLDER = "raw"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_FOLDER = PROJECT_ROOT / "data" / "raw"


def get_latest_json_file(local_folder=LOCAL_FOLDER):
    """Return the newest raw JSON file from the local raw data folder."""

    folder = Path(local_folder)

    if not folder.exists():
        raise FileNotFoundError(f"Local data folder does not exist: {folder}")

    files = [file for file in folder.glob("*.json") if file.is_file()]

    if not files:
        raise FileNotFoundError(f"No JSON files found in {folder}")

    return max(files, key=lambda file: file.stat().st_mtime)


def upload_latest_file(
    bucket_name=None,
    local_folder=LOCAL_FOLDER,
    s3_folder=S3_FOLDER,
    s3_client=None,
):
    """Upload the newest raw JSON file to the configured S3 raw folder."""

    bucket = bucket_name or os.getenv("BUCKET_NAME", DEFAULT_BUCKET_NAME)
    latest = get_latest_json_file(local_folder)
    key = f"{s3_folder}/{latest.name}"
    client = s3_client or boto3.client("s3")

    client.upload_file(str(latest), bucket, key)

    print(f"Uploaded to s3://{bucket}/{key}")
    return key


if __name__ == "__main__":
    upload_latest_file()
