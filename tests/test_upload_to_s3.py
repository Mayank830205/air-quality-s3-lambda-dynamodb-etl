"""Unit tests for S3 upload helper."""

import os
import sys
from pathlib import Path

import pytest

EXTRACTION_DIR = Path(__file__).resolve().parents[1] / "extraction"
sys.path.insert(0, str(EXTRACTION_DIR))

import upload_to_s3

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeS3Client:
    def __init__(self):
        self.uploads = []

    def upload_file(self, filename, bucket, key):
        self.uploads.append((filename, bucket, key))


def test_upload_latest_file_uploads_newest_json():
    local_folder = PROJECT_ROOT / "data" / "test_raw" / "upload"
    local_folder.mkdir(parents=True, exist_ok=True)
    old_file = local_folder / "test_upload_old.json"
    new_file = local_folder / "test_upload_new.json"

    old_file.write_text("[]", encoding="utf-8")
    new_file.write_text("[]", encoding="utf-8")

    os.utime(old_file, (4102444700, 4102444700))
    os.utime(new_file, (4102444800, 4102444800))

    fake_s3 = FakeS3Client()

    key = upload_to_s3.upload_latest_file(
        bucket_name="cities-air-quality-bucket",
        local_folder=local_folder,
        s3_folder="raw",
        s3_client=fake_s3,
    )

    assert key == f"raw/{new_file.name}"
    assert fake_s3.uploads == [
        (str(new_file), "cities-air-quality-bucket", f"raw/{new_file.name}")
    ]


def test_get_latest_json_file_raises_when_folder_has_no_json():
    with pytest.raises(FileNotFoundError):
        upload_to_s3.get_latest_json_file(PROJECT_ROOT / "screenshots")
