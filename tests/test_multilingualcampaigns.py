import json as json_module
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from actionkit.multilingualcampaigns import MultilingualCampaigns
from urls import rest


@pytest.fixture
def mlc(ak):
    return ak.MultilingualCampaigns


def test_name_joins_campaign_and_action_type():
    assert MultilingualCampaigns.name("My Campaign", "petition") == "My Campaign: petition"


@responses.activate
def test_get_step_returns_none_when_not_found(mlc):
    responses.add(
        responses.GET,
        rest("multilingualcampaign"),
        json={"objects": [], "meta": {"next": None}},
        status=200,
    )
    assert mlc.get_step("My Campaign", "petition") is None
    query = parse_qs(urlparse(responses.calls[0].request.url).query)
    assert query["name"] == ["My Campaign: petition"]


@responses.activate
def test_get_step_returns_first_match(mlc):
    responses.add(
        responses.GET,
        rest("multilingualcampaign"),
        json={"objects": [{"id": 1}], "meta": {"next": None}},
        status=200,
    )
    assert mlc.get_step("My Campaign", "petition") == {"id": 1}


@responses.activate
def test_create_posts_generated_name(mlc):
    responses.add(
        responses.POST,
        rest("multilingualcampaign"),
        status=201,
        headers={"Location": rest("multilingualcampaign/1/")},
    )
    assert mlc.create("My Campaign", "petition") == rest("multilingualcampaign/1/")
    body = json_module.loads(responses.calls[0].request.body)
    assert body == {"name": "My Campaign: petition"}
