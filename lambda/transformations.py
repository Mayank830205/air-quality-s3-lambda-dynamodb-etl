from decimal import Decimal, InvalidOperation


def _to_decimal(value, field_name):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc


def _optional_decimal(value, field_name):
    if value is None:
        return Decimal("0")

    return _to_decimal(value, field_name)


def get_air_quality_status(aqi):
    """Return air quality status based on US AQI."""

    aqi = _to_decimal(aqi, "us_aqi")

    if aqi < Decimal("0"):
        raise ValueError("us_aqi must not be negative")

    if aqi <= Decimal("50"):
        return "GOOD"
    elif aqi <= Decimal("100"):
        return "MODERATE"
    elif aqi <= Decimal("150"):
        return "UNHEALTHY_FOR_SENSITIVE"
    elif aqi <= Decimal("200"):
        return "UNHEALTHY"
    elif aqi <= Decimal("300"):
        return "VERY_UNHEALTHY"
    else:
        return "HAZARDOUS"


def validate_record(record):
    """Validate source record."""

    if not isinstance(record, dict):
        return False

    city = record.get("city")

    if not isinstance(city, str) or not city.strip():
        return False

    current = record.get("current")

    if not isinstance(current, dict):
        return False

    if not current.get("time"):
        return False

    try:
        _to_decimal(record.get("latitude"), "latitude")
        _to_decimal(record.get("longitude"), "longitude")

        for field in ["pm2_5", "pm10", "us_aqi"]:
            _to_decimal(current.get(field), field)

        get_air_quality_status(current.get("us_aqi"))

        for field in [
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
        ]:
            if current.get(field) is not None:
                _to_decimal(current.get(field), field)
    except ValueError:
        return False

    return True


def build_item(record, processed_at):
    """Convert API record into DynamoDB item."""

    if not validate_record(record):
        raise ValueError("Invalid air quality record")

    current = record["current"]
    city = record["city"].strip().upper()
    timestamp = current["time"]

    return {

        "record_id": f"{city}#{timestamp}",

        "city": city,

        "timestamp": timestamp,

        "latitude": _to_decimal(record["latitude"], "latitude"),

        "longitude": _to_decimal(record["longitude"], "longitude"),

        "pm25": _to_decimal(current["pm2_5"], "pm2_5"),

        "pm10": _to_decimal(current["pm10"], "pm10"),

        "carbon_monoxide": _optional_decimal(current.get("carbon_monoxide"), "carbon_monoxide"),

        "nitrogen_dioxide": _optional_decimal(current.get("nitrogen_dioxide"), "nitrogen_dioxide"),

        "sulphur_dioxide": _optional_decimal(current.get("sulphur_dioxide"), "sulphur_dioxide"),

        "ozone": _optional_decimal(current.get("ozone"), "ozone"),

        "air_quality_index": _to_decimal(current["us_aqi"], "us_aqi"),

        "air_quality_status": get_air_quality_status(current["us_aqi"]),

        "processed_at_utc": processed_at
    }
