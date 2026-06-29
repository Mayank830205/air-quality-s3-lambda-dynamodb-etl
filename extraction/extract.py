import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def get_coordinates(city: str):
    response = requests.get(
        GEOCODE_URL,
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results") or []

    if not results:
        raise Exception(f"Coordinates not found for {city}")

    result = results[0]

    return result["latitude"], result["longitude"]


def fetch_air_quality(city: str):

    latitude, longitude = get_coordinates(city)

    response = requests.get(
        AIR_QUALITY_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
            "timezone": "auto"
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    data["city"] = city

    return data
