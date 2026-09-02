import base64
import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from actionkit.utils import (
    convert_datetime_to_utc,
    datetime_to_stripped_isoformat,
    verify_hashed_value,
)


def _hash(secret, cleartext):
    sha = hashlib.sha256(f"{secret}.{cleartext}".encode("ascii"))
    return base64.urlsafe_b64encode(sha.digest()).decode("ascii")[:6]


# --- convert_datetime_to_utc() --------------------------------------------


def test_convert_datetime_to_utc_from_other_timezone():
    minus_five = timezone(timedelta(hours=-5))
    dt = datetime(2024, 1, 15, 11, 21, 29, tzinfo=minus_five)
    converted = convert_datetime_to_utc(dt)
    assert converted == datetime(2024, 1, 15, 16, 21, 29, tzinfo=timezone.utc)


def test_convert_datetime_to_utc_already_utc_is_unchanged():
    dt = datetime(2024, 1, 15, 16, 21, 29, tzinfo=timezone.utc)
    assert convert_datetime_to_utc(dt) == dt


# --- datetime_to_stripped_isoformat() ---------------------------------

def test_strips_microseconds_and_positive_offset():
    dt = datetime(2024, 1, 15, 16, 21, 29, 930080, tzinfo=timezone.utc)
    assert datetime_to_stripped_isoformat(dt) == "2024-01-15T16:21:29"


def test_strips_positive_offset_without_microseconds():
    dt = datetime(2024, 1, 15, 16, 21, 29, tzinfo=timezone.utc)
    assert datetime_to_stripped_isoformat(dt) == "2024-01-15T16:21:29"


def test_naive_datetime_without_microseconds_is_a_no_op():
    dt = datetime(2024, 1, 15, 16, 21, 29)
    assert datetime_to_stripped_isoformat(dt) == "2024-01-15T16:21:29"


def test_negative_offset_without_microseconds_is_not_stripped():
    """
    Documents a quirk, not a fix: the function only ever splits on "." then
    falls back to splitting on "+", never "-". A negative-offset datetime
    with no microseconds survives with its offset intact. In practice every
    production call site runs convert_datetime_to_utc() first, which always
    produces a "+00:00" offset, so this path isn't hit for real -- but it's
    part of the function's actual contract.
    """
    minus_five = timezone(timedelta(hours=-5))
    dt = datetime(2024, 1, 15, 16, 21, 29, tzinfo=minus_five)
    assert datetime_to_stripped_isoformat(dt) == "2024-01-15T16:21:29-05:00"


def test_negative_offset_with_microseconds_is_stripped():
    """
    Contrast with the previous test: when microseconds ARE present, the
    "." split fires first and discards everything after it, offset included.
    """
    minus_five = timezone(timedelta(hours=-5))
    dt = datetime(2024, 1, 15, 16, 21, 29, 930080, tzinfo=minus_five)
    assert datetime_to_stripped_isoformat(dt) == "2024-01-15T16:21:29"


# --- verify_hashed_value() -------------------------------------------------


def test_verify_hashed_value_correct_hash_returns_cleartext():
    secret = "s3cr3t"
    cleartext = "42"
    hashed = f"{cleartext}.{_hash(secret, cleartext)}"
    assert verify_hashed_value(hashed, secret) == cleartext


def test_verify_hashed_value_wrong_hash_raises():
    with pytest.raises(Exception):
        verify_hashed_value("42.wrong1", "s3cr3t")


def test_verify_hashed_value_missing_secret_raises_specific_message(monkeypatch):
    monkeypatch.delenv("ACTIONKIT_SECRET_KEY", raising=False)
    with pytest.raises(Exception, match="ACTIONKIT_SECRET_KEY must be defined."):
        verify_hashed_value("42.abcdef", None)


def test_verify_hashed_value_param_takes_precedence_over_env(monkeypatch):
    monkeypatch.setenv("ACTIONKIT_SECRET_KEY", "env-secret")
    param_secret = "param-secret"
    cleartext = "42"
    hashed = f"{cleartext}.{_hash(param_secret, cleartext)}"
    assert verify_hashed_value(hashed, param_secret) == cleartext


def test_verify_hashed_value_falls_back_to_env_var(monkeypatch):
    env_secret = "env-secret"
    monkeypatch.setenv("ACTIONKIT_SECRET_KEY", env_secret)
    cleartext = "42"
    hashed = f"{cleartext}.{_hash(env_secret, cleartext)}"
    assert verify_hashed_value(hashed, None) == cleartext
