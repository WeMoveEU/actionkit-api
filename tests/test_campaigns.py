import json as json_module

import pytest
import responses

from urls import rest


@pytest.fixture
def campaigns(ak):
    return ak.Campaigns


@responses.activate
def test_list_returns_id_to_name_mapping(campaigns):
    responses.add(
        responses.GET,
        rest("allowedpagefield/campaign"),
        json={"choices": [["1", "First"], ["2", "Second"]]},
        status=200,
    )
    assert campaigns.list() == {1: "First", 2: "Second"}


@responses.activate
def test_create_full_sequence(campaigns):
    responses.add(
        responses.POST,
        rest("signuppage"),
        status=201,
        headers={"Location": rest("signuppage/5/")},
    )
    responses.add(
        responses.GET,
        rest("allowedpagefield/campaign"),
        json={"field_choices": "1=Existing"},
        status=200,
    )
    responses.add(responses.PATCH, rest("signuppage/5"), status=200)
    responses.add(responses.PATCH, rest("allowedpagefield/campaign"), status=200)
    responses.add(responses.PATCH, rest("allowedmailingfield/campaign"), status=200)

    result = campaigns.create(
        "My Campaign",
        "petition",
        lead_campaigner="alice",
        topic="climate",
        fields={"extra": "1"},
    )

    assert result == rest("signuppage/5/")

    create_body = json_module.loads(responses.calls[0].request.body)
    assert create_body == {
        "name": "My Campaign",
        "title": "My Campaign",
        "fields": {
            "extra": "1",
            "campaign_type": "petition",
            "lead_campaigner": "alice",
            "topic": "climate",
        },
    }

    self_ref_body = json_module.loads(responses.calls[1].request.body)
    assert self_ref_body == {"fields": {"campaign": "5"}}

    pagefield_body = json_module.loads(responses.calls[3].request.body)
    assert pagefield_body == {"field_choices": "1=Existing\n5=My Campaign"}

    mailingfield_body = json_module.loads(responses.calls[4].request.body)
    assert mailingfield_body == {"field_choices": "1=Existing\n5=My Campaign"}
