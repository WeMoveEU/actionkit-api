import json as json_module

import pytest
import responses

from actionkit.validation import ValidationError
from urls import rest


# --- _path() -----------------------------------------------------------


def test_path_bare_path(connection):
    assert connection._path("/a/b/c/") == rest("a/b/c/")


def test_path_without_leading_slash(connection):
    assert connection._path("a/b/c") == rest("a/b/c")


def test_path_already_api_path(connection):
    assert connection._path("/rest/v1/b/c/") == rest("b/c/")


def test_path_absolute_url_passed_through(connection):
    assert connection._path("https://example.com/i/am/complete") == (
        "https://example.com/i/am/complete"
    )


def test_path_collapses_a_legitimate_double_slash_in_the_input():
    """
    Documents a quirk, not a fix: `_path` blindly does
    f"/rest/v1/{path}".replace("//", "/"), so a caller-provided "//" inside
    `path` gets silently collapsed along with the deliberate one the method
    itself introduces when `path` has no leading slash.
    """
    from actionkit.connection import Connection

    connection = Connection("example.com", "user", "password")
    assert connection._path("orders//1") == rest("orders/1")


# --- _make_request() argument validation --------------------------------


def test_get_with_json_raises_value_error(connection):
    with pytest.raises(ValueError):
        connection.get("thing", json={"a": 1})


def test_non_get_with_params_raises_value_error(connection):
    with pytest.raises(ValueError):
        connection.post("thing", json={"a": 1}, params={"b": 2})


def test_data_and_json_together_raises_value_error(connection):
    with pytest.raises(ValueError):
        connection.post("thing", json={"a": 1}, data={"b": 2})


# --- happy path per verb -------------------------------------------------


@responses.activate
def test_get_sends_auth_and_accept_headers_and_params(connection):
    responses.add(responses.GET, rest("thing/"), json={"ok": True}, status=200)
    response = connection.get("thing/", params={"q": "1"})

    req = responses.calls[0].request
    assert req.headers["Accept"] == "application/json"
    assert req.headers["Authorization"].startswith("Basic ")
    assert req.url == rest("thing/") + "?q=1"
    assert response.json() == {"ok": True}


@responses.activate
def test_post_sends_json_body(connection):
    responses.add(responses.POST, rest("thing/"), status=201, headers={"Location": rest("thing/1/")})
    connection.post("thing/", json={"name": "x"})

    req = responses.calls[0].request
    assert json_module.loads(req.body) == {"name": "x"}


@responses.activate
def test_patch_sends_json_body(connection):
    responses.add(responses.PATCH, rest("thing/1/"), status=200)
    connection.patch("thing/1/", json={"status": "done"})
    assert json_module.loads(responses.calls[0].request.body) == {"status": "done"}


@responses.activate
def test_put_sends_json_body(connection):
    responses.add(responses.PUT, rest("thing/1/"), status=200)
    connection.put("thing/1/", json={"status": "done"})
    assert json_module.loads(responses.calls[0].request.body) == {"status": "done"}


@responses.activate
def test_delete_makes_request(connection):
    responses.add(responses.DELETE, rest("thing/1/"), status=204)
    connection.delete("thing/1/")
    assert len(responses.calls) == 1


# --- retry / backoff on 5xx ----------------------------------------------


@pytest.fixture(autouse=True)
def no_real_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr("time.sleep", lambda seconds: sleeps.append(seconds))
    return sleeps


@responses.activate
def test_retries_on_500_then_succeeds(connection, no_real_sleep):
    responses.add(responses.GET, rest("thing/"), status=500)
    responses.add(responses.GET, rest("thing/"), status=500)
    responses.add(responses.GET, rest("thing/"), json={"ok": True}, status=200)

    response = connection.get("thing/")

    assert len(responses.calls) == 3
    assert response.json() == {"ok": True}
    # initial_backoff = 3, doubling each retry
    assert no_real_sleep == [3, 6]


@responses.activate
def test_exhausts_retries_and_raises(connection, no_real_sleep):
    for _ in range(4):
        responses.add(responses.GET, rest("thing/"), status=500)

    with pytest.raises(Exception):
        connection.get("thing/")

    # num_retries = 3, so the initial attempt plus 3 retries = 4 total calls
    assert len(responses.calls) == 4
    assert no_real_sleep == [3, 6, 12]


# --- error-response handling: HTTPError vs ValidationError ---------------


@responses.activate
def test_error_with_body_raises_validation_error_regardless_of_status(connection):
    """
    Pins current behavior: _make_request only special-cases retry_codes
    (just 500). Any other HTTPError whose response has a non-empty body is
    unconditionally converted to ValidationError, independent of the status
    code -- 400, 404, 409, whatever it is. Callers that do
    `except HTTPError as e: if e.response.status_code == 404: ...` elsewhere
    in this library never see that exception for a body-bearing response;
    see test_httpmethods.py and test_donationaction.py for the fallout.
    """
    responses.add(
        responses.GET,
        rest("thing/1/"),
        status=404,
        json={"error": "not found"},
    )
    with pytest.raises(ValidationError):
        connection.get("thing/1/")


@responses.activate
def test_error_with_empty_body_raises_plain_http_error(connection):
    import requests

    responses.add(responses.GET, rest("thing/1/"), status=404, body="")
    with pytest.raises(requests.exceptions.HTTPError):
        connection.get("thing/1/")


@responses.activate
def test_error_with_non_json_body_raises_json_decode_error(connection):
    """
    ValidationError.__init__ does an unguarded json.loads(response_text), so
    a non-JSON error body (e.g. an HTML error page) blows up with
    json.JSONDecodeError instead of producing a ValidationError.
    """
    responses.add(
        responses.GET,
        rest("thing/1/"),
        status=400,
        body="<html>Internal Server Error</html>",
        content_type="text/html",
    )
    with pytest.raises(json_module.JSONDecodeError):
        connection.get("thing/1/")


# --- static resource-uri helpers -----------------------------------------


class _FakeResponse:
    def __init__(self, headers):
        self.headers = headers


@pytest.mark.parametrize(
    "headers,expected",
    [
        ({"Location": rest("thing/1/")}, rest("thing/1/")),
        ({}, None),
    ],
)
def test_get_resource_uri(headers, expected):
    from actionkit.connection import Connection

    assert Connection.get_resource_uri(_FakeResponse(headers)) == expected


@pytest.mark.parametrize(
    "uri,expected",
    [
        (rest("thing/1/"), "1"),
        (rest("thing/42/"), "42"),
        (rest("thing/"), None),
    ],
)
def test_get_resource_uri_id(uri, expected):
    from actionkit.connection import Connection

    assert Connection.get_resource_uri_id(uri) == expected


def test_get_resource_uri_id_from_response():
    from actionkit.connection import Connection

    response = _FakeResponse({"Location": rest("thing/7/")})
    assert Connection.get_resource_uri_id_from_response(response) == "7"


def test_get_resource_uri_from_id():
    from actionkit.connection import Connection

    assert Connection.get_resource_uri_from_id("5", "thing") == "/rest/v1/thing/5/"
