from datetime import datetime


def validate_datetime_is_timezone_aware(dt: datetime) -> None:
    """
    Simple validation to ensure that the datetime is timezone aware.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(f'Datetime {dt} must be timezone aware.')
