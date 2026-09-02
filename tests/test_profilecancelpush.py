import json as json_module
from datetime import datetime, timezone

import pytest
import responses

from urls import rest


@pytest.fixture
def profilecancelpush(ak):
    return ak.ProfileCancelPush


def test_push_requires_order_id_or_recurring_id(profilecancelpush):
    with pytest.raises(ValueError):
        profilecancelpush.push()


@responses.activate
def test_push_sends_expected_payload(profilecancelpush):
    responses.add(responses.POST, rest("profilecancelpush"), status=201, json={})
    profilecancelpush.push(order_id="42", canceled_by="user")
    body = json_module.loads(responses.calls[0].request.body)
    assert body == {"canceled_by": "user", "order_id": "42"}


@responses.activate
def test_push_defaults_canceled_by_to_processor(profilecancelpush):
    responses.add(responses.POST, rest("profilecancelpush"), status=201, json={})
    profilecancelpush.push(recurring_id="rec-1")
    body = json_module.loads(responses.calls[0].request.body)
    assert body["canceled_by"] == "processor"


def test_push_rejects_naive_created_at(profilecancelpush):
    with pytest.raises(ValueError):
        profilecancelpush.push(order_id="42", created_at=datetime.now())


@responses.activate
def test_push_strips_created_at(profilecancelpush):
    responses.add(responses.POST, rest("profilecancelpush"), status=201, json={})
    created_at = datetime(2024, 1, 15, 16, 21, 29, 930080, tzinfo=timezone.utc)
    profilecancelpush.push(order_id="42", created_at=created_at)
    body = json_module.loads(responses.calls[0].request.body)
    assert body["created_at"] == "2024-01-15T16:21:29"
