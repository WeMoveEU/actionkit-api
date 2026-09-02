import json as json_module
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import responses

from urls import rest


@pytest.fixture
def profileupdatepush(ak):
    return ak.ProfileUpdatePush


def test_push_requires_order_id_or_recurring_id(profileupdatepush):
    with pytest.raises(ValueError):
        profileupdatepush.push(amount=Decimal("5.00"), currency="eur")


@responses.activate
def test_push_sends_expected_payload_and_uppercases_currency(profileupdatepush):
    responses.add(responses.POST, rest("profileupdatepush"), status=201, json={})
    profileupdatepush.push(
        amount=Decimal("5.00"), currency="eur", order_id="42", trans_id="tx1"
    )
    body = json_module.loads(responses.calls[0].request.body)
    assert body == {
        "amount": "5.00",
        "currency": "EUR",
        "trans_id": "tx1",
        "order_id": "42",
    }


def test_push_rejects_naive_created_at(profileupdatepush):
    with pytest.raises(ValueError):
        profileupdatepush.push(
            amount=Decimal("5.00"),
            currency="eur",
            order_id="42",
            created_at=datetime.now(),
        )


@responses.activate
def test_push_strips_created_at(profileupdatepush):
    responses.add(responses.POST, rest("profileupdatepush"), status=201, json={})
    created_at = datetime(2024, 1, 15, 16, 21, 29, tzinfo=timezone.utc)
    profileupdatepush.push(
        amount=Decimal("5.00"), currency="eur", order_id="42", created_at=created_at
    )
    body = json_module.loads(responses.calls[0].request.body)
    assert body["created_at"] == "2024-01-15T16:21:29"
