import json
from datetime import datetime, timezone

import pytest

from actionkit.validation import ValidationError, validate_datetime_is_timezone_aware


# --- ValidationError ---------------------------------------------------


def test_validation_error_parses_json_body():
    body = json.dumps({"name": ["A page with this short name already exists."]})
    err = ValidationError(body)
    assert err.error_dict == {"name": ["A page with this short name already exists."]}
    assert err.errors == [["A page with this short name already exists."]]


def test_validation_error_non_json_body_raises_json_decode_error():
    with pytest.raises(json.JSONDecodeError):
        ValidationError("<html>not json</html>")


def test_validation_error_getitem_present_key_returns_its_value():
    err = ValidationError(json.dumps({"order_id": ["already reversed"]}))
    assert err["order_id"] == ["already reversed"]


def test_validation_error_getitem_missing_key_returns_empty_list_not_keyerror():
    """
    Deliberately permissive contract: __getitem__ never raises KeyError.
    """
    err = ValidationError(json.dumps({"order_id": ["already reversed"]}))
    assert err["some_other_field"] == []


# --- validate_datetime_is_timezone_aware() --------------------------------


def test_naive_datetime_raises_value_error():
    with pytest.raises(ValueError):
        validate_datetime_is_timezone_aware(datetime.now())


def test_aware_datetime_does_not_raise():
    validate_datetime_is_timezone_aware(datetime.now(tz=timezone.utc))
