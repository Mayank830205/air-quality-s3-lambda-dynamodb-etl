import json
from datetime import datetime, timezone
from pathlib import Path

from config import CITIES
from extract import fetch_air_quality

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def extract_all_cities(cities=CITIES, output_dir=RAW_DATA_DIR):
    """Fetch all configured cities and save them into one raw JSON file."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    records = []

    for city in cities:
        print(f"Fetching air quality data for {city}...")
        records.append(fetch_air_quality(city))

    filename = f"air_quality_raw_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    filepath = output_path / filename

    with filepath.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4)

    return filepath, records


def main():
    filepath, records = extract_all_cities()
    print(f"\nSaved {len(records)} records")
    print(filepath)


if __name__ == "__main__":
    main()
