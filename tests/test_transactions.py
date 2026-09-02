import json as json_module
from decimal import Decimal

import pytest
import responses

from actionkit.validation import ValidationError
from urls import rest


@pytest.fixture
def transactions(ak):
    return ak.Transactions


# --- create() ----------------------------------------------------------


@responses.activate
def test_create_with_order_uri_sends_expected_payload(transactions):
    responses.add(
        responses.POST,
        rest("transaction"),
        status=201,
        headers={"Location": rest("transaction/1/")},
    )
    result = transactions.create(
        account="WM-Card",
        amount=Decimal("5.00"),
        currency="EUR",
        order_uri=rest("order/1/"),
    )
    assert result == rest("transaction/1/")
    body = json_module.loads(responses.calls[0].request.body)
    assert body == {
        "account": "WM-Card",
        "amount": "5.00",
        "currency": "EUR",
        "type": "sale",
        "order": rest("order/1/"),
    }


def test_create_requires_order_uri_or_order_id(transactions):
    with pytest.raises(ValueError):
        transactions.create(account="WM-Card", amount=Decimal("5.00"), currency="EUR")


def test_create_rejects_invalid_type(transactions):
    with pytest.raises(ValueError):
        transactions.create(
            account="WM-Card",
            amount=Decimal("5.00"),
            currency="EUR",
            order_uri=rest("order/1/"),
            type="not-a-real-type",
        )


def test_create_with_order_id_is_broken(transactions):
    """
    Pins a real bug, does not fix it: Transactions.create (transactions.py:97)
    calls `Orders.get_resource_uri_from_id(order_id)` UNBOUND on the Orders
    class rather than on an instance. HttpMethods.get_resource_uri_from_id is
    `def get_resource_uri_from_id(self, resource_id)`, so this call binds
    order_id to `self` and leaves the real `resource_id` parameter unfilled.
    Transactions.create(order_id=...) (without order_uri) currently always
    raises TypeError, never reaching the network. Contrast with the correct
    `self.get_resource_uri_from_id(resource_id)` pattern in orders.py:23.
    """
    with pytest.raises(TypeError):
        transactions.create(
            account="WM-Card",
            amount=Decimal("5.00"),
            currency="EUR",
            order_id="123",
        )


# --- reverse() ---------------------------------------------------------


@responses.activate
def test_reverse_with_transaction_uri(transactions):
    responses.add(
        responses.POST, rest("transaction/1/reverse"), status=201, json={"ok": True}
    )
    transactions.reverse(transaction_uri=rest("transaction/1/"))
    assert len(responses.calls) == 1


@responses.activate
def test_reverse_with_transaction_id_builds_uri(transactions):
    responses.add(
        responses.POST, rest("transaction/1/reverse"), status=201, json={"ok": True}
    )
    transactions.reverse(transaction_id="1")
    assert len(responses.calls) == 1


def test_reverse_requires_id_or_uri(transactions):
    with pytest.raises(ValueError):
        transactions.reverse()


@responses.activate
def test_reverse_404_warns_and_returns_none(transactions):
    responses.add(
        responses.POST, rest("transaction/1/reverse"), status=404, body=""
    )
    assert transactions.reverse(transaction_uri=rest("transaction/1/")) is None


@responses.activate
def test_reverse_400_already_reversed_message_returns_none(transactions):
    """
    Only reachable when the 400 response body is EMPTY of a status-code
    trigger... actually the opposite: _make_request only lets a bare
    requests.HTTPError through when the body is empty. A real "already
    reversed" 400 response from ActionKit carries a JSON body, so in
    practice it surfaces as ValidationError, not HTTPError -- see the next
    test, which is what actually happens against a real server.
    """
    responses.add(responses.POST, rest("transaction/1/reverse"), status=400, body="")
    with pytest.raises(Exception):
        transactions.reverse(transaction_uri=rest("transaction/1/"))


@responses.activate
def test_reverse_400_with_body_raises_validation_error_and_is_not_caught(transactions):
    """
    Pins a likely-broken interaction: a real ActionKit "already reversed"
    400 response has a JSON body like {"order_id": "Transaction has already
    been reversed."}, which _make_request converts to ValidationError before
    reverse()'s `except HTTPError` branch can inspect the status code. The
    `except ValidationError` branch below it is meant to catch this instead,
    but see test_reverse_validation_error_already_reversed_branch_is_dead --
    that branch's own comparison looks broken too.
    """
    responses.add(
        responses.POST,
        rest("transaction/1/reverse"),
        status=400,
        json={"order_id": "Transaction has already been reversed."},
    )
    with pytest.raises(ValidationError):
        transactions.reverse(transaction_uri=rest("transaction/1/"))


def test_reverse_validation_error_already_reversed_branch_is_dead(transactions):
    """
    Pins a second bug in reverse()'s `except ValidationError` branch
    (transactions.py:48-57): it compares `e.errors` -- a LIST, per
    ValidationError.__init__ (`self.errors = list(response.values())`) --
    against the string literal 'Transaction has already been reversed.'. A
    list can never equal that string, so this branch's "swallow an
    already-reversed error" behavior can never actually fire; it always
    falls through to `raise e`. This test exercises the comparison directly
    rather than through a live HTTP call, to isolate it from the (also
    broken) exception-type mismatch covered above.
    """
    err = ValidationError(
        json_module.dumps({"order_id": "Transaction has already been reversed."})
    )
    assert err.errors == ["Transaction has already been reversed."]
    assert err.errors != "Transaction has already been reversed."
