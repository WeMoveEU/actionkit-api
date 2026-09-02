import json as json_module
from datetime import datetime, timezone

import pytest
import responses

from urls import rest


@pytest.fixture
def recurringpaymentpush(ak):
    return ak.RecurringPaymentPush


def test_push_requires_order_id_or_recurring_id(recurringpaymentpush):
    with pytest.raises(ValueError):
        recurringpaymentpush.push()


@responses.activate
def test_push_sends_expected_payload_with_defaults(recurringpaymentpush):
    responses.add(responses.POST, rest("recurringpaymentpush"), status=201, json={})
    recurringpaymentpush.push(order_id="42")
    body = json_module.loads(responses.calls[0].request.body)
    assert body == {
        "success": True,
        "status": "completed",
        "failure_code": None,
        "failure_message": None,
        "failure_description": None,
        "trans_id": None,
        "order_id": "42",
    }


@responses.activate
def test_push_reports_failure(recurringpaymentpush):
    responses.add(responses.POST, rest("recurringpaymentpush"), status=201, json={})
    recurringpaymentpush.push(
        recurring_id="rec-1",
        success=False,
        status="failed",
        failure_code="card_declined",
        failure_message="Card declined",
    )
    body = json_module.loads(responses.calls[0].request.body)
    assert body["success"] is False
    assert body["status"] == "failed"
    assert body["failure_code"] == "card_declined"
    assert body["recurring_id"] == "rec-1"


def test_push_rejects_naive_created_at(recurringpaymentpush):
    with pytest.raises(ValueError):
        recurringpaymentpush.push(order_id="42", created_at=datetime.now())


@responses.activate
def test_push_strips_created_at(recurringpaymentpush):
    responses.add(responses.POST, rest("recurringpaymentpush"), status=201, json={})
    created_at = datetime(2024, 1, 15, 16, 21, 29, tzinfo=timezone.utc)
    recurringpaymentpush.push(order_id="42", created_at=created_at)
    body = json_module.loads(responses.calls[0].request.body)
    assert body["created_at"] == "2024-01-15T16:21:29"
