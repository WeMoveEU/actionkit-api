import json as json_module

import pytest
import responses

from urls import rest


@pytest.fixture
def genericactions(ak):
    return ak.GenericActions


def test_update_requires_resource_id_or_resource_uri(genericactions):
    with pytest.raises(ValueError):
        genericactions.update()


@responses.activate
def test_update_with_resource_id_builds_uri(genericactions):
    responses.add(responses.PATCH, rest("action/1/"), status=200)
    genericactions.update(resource_id="1", foo="bar")
    assert responses.calls[0].request.url == rest("action/1/")
    assert json_module.loads(responses.calls[0].request.body) == {"foo": "bar"}


@responses.activate
def test_update_with_fields_fetches_and_merges_before_patching(genericactions):
    responses.add(
        responses.GET,
        rest("action/1/"),
        json={"fields": {"existing": "1"}},
        status=200,
    )
    responses.add(responses.PATCH, rest("action/1/"), status=200)

    genericactions.update(resource_uri=rest("action/1/"), fields={"new": "2"})

    assert len(responses.calls) == 2
    body = json_module.loads(responses.calls[1].request.body)
    assert body == {"fields": {"existing": "1", "new": "2"}}


@responses.activate
def test_update_without_fields_does_not_fetch_first(genericactions):
    responses.add(responses.PATCH, rest("action/1/"), status=200)
    genericactions.update(resource_uri=rest("action/1/"), status="done")
    assert len(responses.calls) == 1
