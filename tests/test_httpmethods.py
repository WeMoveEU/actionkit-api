import json as json_module

import pytest
import responses

from actionkit.httpmethods import HttpMethods
from urls import rest


class _Dummy(HttpMethods):
    resource_name = "dummy"


@pytest.fixture
def dummy(connection):
    return _Dummy(connection)


def test_resource_name_not_defined_raises_not_implemented_error(connection):
    class _NoName(HttpMethods):
        pass

    with pytest.raises(NotImplementedError):
        _NoName(connection).resource_name


# --- get() -----------------------------------------------------------------


@responses.activate
def test_get_falls_back_to_resource_name(dummy):
    responses.add(responses.GET, rest("dummy"), json={"ok": True}, status=200)
    assert dummy.get() == {"ok": True}


@responses.activate
def test_get_uses_explicit_resource_uri_and_params(dummy):
    responses.add(responses.GET, rest("dummy/1/"), json={"id": 1}, status=200)
    result = dummy.get(rest("dummy/1/"), foo="bar")
    assert result == {"id": 1}
    assert responses.calls[0].request.url == rest("dummy/1/") + "?foo=bar"


# --- search() ----------------------------------------------------------------


@responses.activate
def test_search_single_page(dummy):
    responses.add(
        responses.GET,
        rest("dummy"),
        json={"objects": [{"id": 1}, {"id": 2}], "meta": {"next": None}},
        status=200,
    )
    assert dummy.search() == [{"id": 1}, {"id": 2}]


@responses.activate
def test_search_follows_pagination(dummy):
    next_url = rest("dummy") + "?offset=2"
    responses.add(
        responses.GET,
        rest("dummy"),
        json={"objects": [{"id": 1}], "meta": {"next": next_url}},
        status=200,
    )
    responses.add(
        responses.GET,
        next_url,
        json={"objects": [{"id": 2}], "meta": {"next": None}},
        status=200,
    )
    assert dummy.search() == [{"id": 1}, {"id": 2}]
    assert len(responses.calls) == 2


@responses.activate
def test_search_wraps_400_into_plain_exception(dummy):
    responses.add(responses.GET, rest("dummy"), status=400, body="")
    with pytest.raises(Exception) as excinfo:
        dummy.search()
    assert not isinstance(excinfo.value, ValueError)


# --- delete() ----------------------------------------------------------------


@responses.activate
def test_delete_dry_run_makes_no_request(dummy):
    assert dummy.delete(rest("dummy/1/"), dry_run=True) is True
    assert len(responses.calls) == 0


@responses.activate
def test_delete_success_returns_true(dummy):
    responses.add(responses.DELETE, rest("dummy/1/"), status=204)
    assert dummy.delete(rest("dummy/1/")) is True


@responses.activate
def test_delete_404_with_empty_body_and_ignore_404_returns_false(dummy):
    """
    Only reaches HttpMethods.delete's except-HTTPError branch when the
    response body is empty -- see test_connection.py's
    test_error_with_body_raises_validation_error_regardless_of_status. A
    real ActionKit 404 with a JSON body would raise ValidationError instead,
    which this method does not catch at all (see the next test).
    """
    responses.add(responses.DELETE, rest("dummy/1/"), status=404, body="")
    assert dummy.delete(rest("dummy/1/"), ignore_404=True) is False


@responses.activate
def test_delete_404_with_empty_body_and_ignore_404_false_raises(dummy):
    import requests

    responses.add(responses.DELETE, rest("dummy/1/"), status=404, body="")
    with pytest.raises(requests.exceptions.HTTPError):
        dummy.delete(rest("dummy/1/"), ignore_404=False)


@responses.activate
def test_delete_404_with_json_body_is_not_caught_as_ignore_404(dummy):
    """
    Pins a likely-broken interaction with the Connection-layer finding:
    a real ActionKit 404 response almost always carries a JSON body, so
    _make_request converts it to ValidationError before HttpMethods.delete's
    `except HTTPError` block ever sees it -- ignore_404=True silently does
    NOT protect the caller in that case, ValidationError propagates instead.
    """
    from actionkit.validation import ValidationError

    responses.add(
        responses.DELETE, rest("dummy/1/"), status=404, json={"error": "not found"}
    )
    with pytest.raises(ValidationError):
        dummy.delete(rest("dummy/1/"), ignore_404=True)


@responses.activate
def test_delete_non_404_error_reraises(dummy):
    """
    Uses 403, not 500 -- 500 is Connection's sole retry_code and would
    trigger the real (unmocked, in this file) backoff sleep loop.
    """
    import requests

    responses.add(responses.DELETE, rest("dummy/1/"), status=403, body="")
    with pytest.raises(requests.exceptions.HTTPError):
        dummy.delete(rest("dummy/1/"))


# --- patch() / put() -----------------------------------------------------


@responses.activate
def test_patch_sends_body_and_returns_true(dummy):
    responses.add(responses.PATCH, rest("dummy/1/"), status=200)
    assert dummy.patch(rest("dummy/1/"), {"status": "done"}) is True
    assert json_module.loads(responses.calls[0].request.body) == {"status": "done"}


@responses.activate
def test_put_sends_body_and_returns_true(dummy):
    responses.add(responses.PUT, rest("dummy/1/"), status=200)
    assert dummy.put(rest("dummy/1/"), {"status": "done"}) is True
    assert json_module.loads(responses.calls[0].request.body) == {"status": "done"}


# --- post() ----------------------------------------------------------------


@responses.activate
def test_post_returns_resource_uri_from_location_header(dummy):
    responses.add(
        responses.POST,
        rest("dummy"),
        status=201,
        headers={"Location": rest("dummy/1/")},
    )
    assert dummy.post({"name": "x"}) == rest("dummy/1/")


@responses.activate
def test_post_returns_none_when_no_location_header(dummy):
    responses.add(responses.POST, rest("dummy"), status=201)
    assert dummy.post({"name": "x"}) is None


# --- get_resource_uri_from_id() / get_by_id() -----------------------------


def test_get_resource_uri_from_id(dummy):
    assert dummy.get_resource_uri_from_id("7") == "/rest/v1/dummy/7/"


@responses.activate
def test_get_by_id(dummy):
    responses.add(responses.GET, rest("dummy/7"), json={"id": 7}, status=200)
    assert dummy.get_by_id("7") == {"id": 7}
