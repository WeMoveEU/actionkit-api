from datetime import datetime


def convert_datetime_to_utc(dt: datetime) -> datetime:
    """
    Converts a timezone-aware datetime to UTC.
    """
    return dt.astimezone(tz=datetime.timezone.utc)


def datetime_to_stripped_isoformat(dt: datetime) -> str:
    """
    ActionKit does not support the timezone-aware part of the ISO 8601 standard when it comes to
    expressing datetimes for some endpoints. A bug has been filed with ActionKit to fix this.

    In the meantime, this function strips away the timezone info at the end if present. This allows
    the datetime expression to pass for AK endpoints that aren't so tolerate of iso 8601 formats.
    """
    iso_datetime = dt.isoformat()
    tokens = iso_datetime.split('.')
    if len(tokens) < 2:
        tokens = iso_datetime.split('+')
    return tokens[0] if len(tokens) > 1 else iso_datetime
