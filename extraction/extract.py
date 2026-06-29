import json
import os
from datetime import datetime, timezone

import boto3
import requests

# ----------------------------
# Configuration
# ----------------------------

CITIES = [
    "Delhi",
    "Mumbai",
    "Pune",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Kolkata",
    "Jaipur",
]

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

RAW_FOLDER = "data/raw"

BUCKET_NAME = "cities-air-quality-bucket"
S3_FOLDER = "raw"

# ----------------------------
# Get Coordinates
# ----------------------------

def get_coordinates(city):

    response = requests.get(
        GEOCODE_URL,
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=30,
    )

    response.raise_for_status()

    results = response.json().get("results")

    if not results:
        raise Exception(f"Coordinates not found for {city}")

    return (
        results[0]["latitude"],
        results[0]["longitude"],
    )

# ----------------------------
# Fetch Air Quality
# ----------------------------

def fetch_air_quality(city):

    latitude, longitude = get_coordinates(city)

    response = requests.get(
        AIR_QUALITY_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "pm10,"
                "pm2_5,"
                "carbon_monoxide,"
                "nitrogen_dioxide,"
                "sulphur_dioxide,"
                "ozone,"
                "us_aqi"
            ),
            "timezone": "auto",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    data["city"] = city

    return data

# ----------------------------
# Extract
# ----------------------------

def extract():

    os.makedirs(RAW_FOLDER, exist_ok=True)

    records = []

    for city in CITIES:

        print(f"Fetching {city}...")

        records.append(fetch_air_quality(city))

    filename = (
        f"air_quality_raw_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )

    filepath = os.path.join(RAW_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4)

    print(f"\nSaved {len(records)} records")
    print(filepath)

    return filepath

# ----------------------------
# Upload to S3
# ----------------------------

def upload_to_s3(filepath):

    s3 = boto3.client("s3")

    key = f"{S3_FOLDER}/{os.path.basename(filepath)}"

    s3.upload_file(
        filepath,
        BUCKET_NAME,
        key,
    )

    print(f"Uploaded to s3://{BUCKET_NAME}/{key}")

# ----------------------------
# Main
# ----------------------------

if __name__ == "__main__":

    filepath = extract()

    upload_to_s3(filepath)

