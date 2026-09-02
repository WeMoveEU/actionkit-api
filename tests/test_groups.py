import json as json_module

import pytest
import responses

from urls import rest


@pytest.fixture
def groups(ak):
    return ak.Groups


@responses.activate
def test_uris_maps_name_to_resource_uri_with_limit_100(groups):
    responses.add(
        responses.GET,
        rest("usergroup"),
        json={
            "objects": [
                {"name": "Volunteers", "resource_uri": rest("usergroup/1/")},
                {"name": "Donors", "resource_uri": rest("usergroup/2/")},
            ]
        },
        status=200,
    )
    result = groups.uris()
    assert result == {
        "Volunteers": rest("usergroup/1/"),
        "Donors": rest("usergroup/2/"),
    }
    assert responses.calls[0].request.url == rest("usergroup") + "?_limit=100"


@responses.activate
def test_create_posts_group(groups):
    responses.add(
        responses.POST,
        rest("usergroup"),
        status=201,
        headers={"Location": rest("usergroup/3/")},
    )
    assert groups.create({"name": "New Group"}) == rest("usergroup/3/")
    assert json_module.loads(responses.calls[0].request.body) == {"name": "New Group"}
