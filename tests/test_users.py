import base64
import hashlib

import pytest
import responses

from urls import rest


def _hash(secret, cleartext):
    sha = hashlib.sha256(f"{secret}.{cleartext}".encode("ascii"))
    return base64.urlsafe_b64encode(sha.digest()).decode("ascii")[:6]


@pytest.fixture
def users(ak):
    return ak.Users


# --- id() ------------------------------------------------------------------


@pytest.mark.parametrize(
    "uri,expected",
    [
        ("/user/1", "1"),
        ("/user/11/", "11"),
    ],
)
def test_id_extracts_numeric_id(users, uri, expected):
    assert users.id(uri) == expected


def test_id_raises_bare_exception_on_no_match(users):
    """
    Pins an inconsistency: this raises a bare Exception, not ValueError --
    unlike get_by_akid below, which wraps failures into ValueError.
    """
    with pytest.raises(Exception) as excinfo:
        users.id("/user/asdf")
    assert not isinstance(excinfo.value, ValueError)


# --- get_by_email() ----------------------------------------------------


@responses.activate
def test_get_by_email_no_results_returns_none(users):
    responses.add(
        responses.GET,
        rest("user"),
        json={"objects": [], "meta": {"next": None}},
        status=200,
    )
    assert users.get_by_email("nobody@example.com") is None


@responses.activate
def test_get_by_email_returns_first_result(users):
    responses.add(
        responses.GET,
        rest("user"),
        json={
            "objects": [{"id": 1, "email": "a@example.com"}],
            "meta": {"next": None},
        },
        status=200,
    )
    assert users.get_by_email("a@example.com") == {"id": 1, "email": "a@example.com"}


# --- create() / update() / uri() ------------------------------------------


@responses.activate
def test_create_posts_user(users):
    responses.add(
        responses.POST, rest("user"), status=201, headers={"Location": rest("user/1/")}
    )
    assert users.create({"email": "a@example.com"}) == rest("user/1/")


@responses.activate
def test_update_patches_user(users):
    responses.add(responses.PATCH, rest("user/1/"), status=200)
    assert users.update(rest("user/1/"), {"first_name": "A"}) is True


def test_uri_with_id(users):
    assert users.uri("42") == "user/42"


def test_uri_without_id(users):
    assert users.uri() == "user/"


# --- get_by_akid() ----------------------------------------------------------

# akid contract, reverse-engineered from get_by_akid()'s `chunks[1]` and
# verify_hashed_value()'s "pop the last dot-segment off as the hash" scheme:
# the cleartext portion must itself contain a "." so that splitting the full
# akid on "." puts the user id at index 1, e.g. "u.<user_id>.<hash>" (see
# scripts/hashme.py, which hashes an arbitrary caller-supplied string).


def _akid(secret, user_id, prefix="u"):
    cleartext = f"{prefix}.{user_id}"
    return f"{cleartext}.{_hash(secret, cleartext)}"


@responses.activate
def test_get_by_akid_limited_returns_only_three_fields(users, monkeypatch):
    monkeypatch.setenv("ACTIONKIT_SECRET_KEY", "s3cr3t")
    akid = _akid("s3cr3t", 42)
    responses.add(
        responses.GET,
        rest("user/42"),
        json={
            "id": 42,
            "first_name": "A",
            "last_name": "B",
            "email": "a@example.com",
            "phone": "12345",
        },
        status=200,
    )
    result = users.get_by_akid(akid)
    assert result == {"first_name": "A", "last_name": "B", "email": "a@example.com"}


@responses.activate
def test_get_by_akid_unlimited_returns_everything(users, monkeypatch):
    monkeypatch.setenv("ACTIONKIT_SECRET_KEY", "s3cr3t")
    akid = _akid("s3cr3t", 42)
    full_user = {"id": 42, "first_name": "A", "last_name": "B", "email": "a@example.com"}
    responses.add(responses.GET, rest("user/42"), json=full_user, status=200)
    assert users.get_by_akid(akid, limited=False) == full_user


def test_get_by_akid_bad_hash_wraps_into_value_error(users, monkeypatch):
    monkeypatch.setenv("ACTIONKIT_SECRET_KEY", "s3cr3t")
    with pytest.raises(ValueError, match="Invalid akid"):
        users.get_by_akid("u.42.wrong1")


def test_get_by_akid_missing_secret_wraps_into_value_error(users, monkeypatch):
    monkeypatch.delenv("ACTIONKIT_SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="Invalid akid"):
        users.get_by_akid("u.42.abcdef")
