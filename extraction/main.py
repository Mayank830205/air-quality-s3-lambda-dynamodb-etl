import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from .config import CITIES
    from .extract import fetch_air_quality
except ImportError:
    from config import CITIES
    from extract import fetch_air_quality

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def extract_all_cities(cities=None, output_dir=RAW_DATA_DIR):
    """Fetch all configured cities and save them into one raw JSON file."""

    city_names = list(CITIES if cities is None else cities)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_cities_data = []
    errors = {}

    for city in city_names:
        try:
            print(f"Fetching air quality data for {city}...")
            data = fetch_air_quality(city)
            all_cities_data.append(data)
        except Exception as exc:
            errors[city] = str(exc)

    if errors:
        failed = ", ".join(f"{city}: {error}" for city, error in errors.items())
        raise RuntimeError(f"Failed to fetch air quality data for {len(errors)} cities: {failed}")

    filename = f"air_quality_raw_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    filepath = output_path / filename

    with filepath.open("w", encoding="utf-8") as file:
        json.dump(all_cities_data, file, indent=4)

    return filepath, all_cities_data


def main():
    filepath, records = extract_all_cities()
    print(f"\nSaved {len(records)} records")
    print(filepath)


if __name__ == "__main__":
    main()
