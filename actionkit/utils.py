from datetime import datetime, timezone

import hashlib
import base64
import os


def convert_datetime_to_utc(dt: datetime) -> datetime:
    """
    Converts a timezone-aware datetime to UTC.
    """
    return dt.astimezone(tz=timezone.utc)


def datetime_to_stripped_isoformat(dt: datetime) -> str:
    """
    ActionKit does not support the timezone-aware part of the ISO 8601 standard when it comes to
    expressing datetimes for some endpoints. A bug has been filed with ActionKit to fix this.

    In the meantime, this function strips away the timezone info at the end if present. This allows
    the datetime expression to pass for AK endpoints that aren't so tolerate of iso 8601 formats.
    """
    iso_datetime = dt.isoformat()
    tokens = iso_datetime.split(".")
    if len(tokens) < 2:
        tokens = iso_datetime.split("+")
    return tokens[0] if len(tokens) > 1 else iso_datetime


def verify_hashed_value(hashed_value: str) -> str:
    # pop off the input hash
    chunks = hashed_value.split(".")
    input_hash = chunks.pop()
    cleartext = ".".join(chunks)

    secret = os.environ.get("ACTIONKIT_SECRET_KEY")
    if not secret:
        raise Exception("ACTIONKIT_SECRET_KEY must be defined.")

    # run the hashing algorithm
    sha = hashlib.sha256("{0}.{1}".format(secret, cleartext).encode("ascii"))
    raw_hash = sha.digest()
    urlsafe_hash = base64.urlsafe_b64encode(raw_hash).decode("ascii")
    short_hash = urlsafe_hash[:6]

    # compare the results
    if input_hash == short_hash:
        return cleartext

    raise Exception(f"Invalid value: {hashed_value} {input_hash} {short_hash}")
