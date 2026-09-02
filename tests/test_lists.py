import pytest
import responses

from urls import rest


@pytest.fixture
def lists(ak):
    return ak.Lists


@responses.activate
def test_get_or_create_returns_existing_list(lists):
    responses.add(
        responses.GET,
        rest("list"),
        json={
            "meta": {"total_count": 1},
            "objects": [{"id": 1, "name": "Newsletter"}],
        },
        status=200,
    )
    result = lists.get_or_create("Newsletter")
    assert result == {"id": 1, "name": "Newsletter"}
    assert len(responses.calls) == 1


@responses.activate
def test_get_or_create_creates_when_missing(lists):
    """
    Pins the documented "terrible design" (lists.py:12): creating a list
    takes a second GET round-trip to fetch the object that was just POSTed,
    rather than trusting the POST response.
    """
    responses.add(
        responses.GET,
        rest("list"),
        json={"meta": {"total_count": 0}, "objects": []},
        status=200,
    )
    responses.add(
        responses.POST,
        rest("list"),
        status=201,
        headers={"Location": rest("list/9/")},
    )
    responses.add(
        responses.GET, rest("list/9/"), json={"id": 9, "name": "New List"}, status=200
    )

    result = lists.get_or_create("New List", notes="a note")

    assert result == {"id": 9, "name": "New List"}
    assert len(responses.calls) == 3
    import json as json_module

    assert json_module.loads(responses.calls[1].request.body) == {
        "name": "New List",
        "notes": "a note",
    }


@responses.activate
def test_all_returns_objects(lists):
    responses.add(
        responses.GET,
        rest("list"),
        json={"objects": [{"id": 1}, {"id": 2}]},
        status=200,
    )
    assert lists.all() == [{"id": 1}, {"id": 2}]
