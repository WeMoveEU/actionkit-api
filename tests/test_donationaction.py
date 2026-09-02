import json as json_module
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import responses

from actionkit.validation import ValidationError
from urls import rest


@pytest.fixture
def donationaction(ak):
    return ak.DonationAction


PUSH_REQUIRED = dict(
    amount=Decimal("5.00"),
    currency="EUR",
    page="my-donation-page",
    payment_account="wemove-account",
    email="a@example.com",
)


# --- push() ------------------------------------------------------------


@pytest.mark.parametrize("missing", ["amount", "currency", "page", "payment_account"])
def test_push_requires_each_of_amount_currency_page_payment_account(
    donationaction, missing
):
    kwargs = {**PUSH_REQUIRED, missing: None}
    with pytest.raises(ValueError):
        donationaction.push(**kwargs)


def test_push_requires_email_or_akid(donationaction):
    kwargs = {**PUSH_REQUIRED}
    kwargs.pop("email")
    with pytest.raises(ValueError):
        donationaction.push(**kwargs)


@responses.activate
def test_push_akid_alone_is_sufficient(donationaction):
    kwargs = {**PUSH_REQUIRED}
    kwargs.pop("email")
    kwargs["akid"] = "u.42.abcdef"
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=201,
        json={"resource_uri": rest("donationaction/1/")},
    )
    donationaction.push(**kwargs)
    assert len(responses.calls) == 1


@responses.activate
def test_push_sends_expected_payload_for_non_us_country(donationaction):
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=201,
        json={"resource_uri": rest("donationaction/1/")},
    )
    donationaction.push(
        email="a@example.com",
        first_name="A",
        last_name="B",
        country="FR",
        postal="75001",
        amount=Decimal("5.00"),
        currency="EUR",
        page="my-page",
        payment_account="wemove-account",
        trans_id="tx1",
    )
    body = json_module.loads(responses.calls[0].request.body)
    assert body["order"] == {
        "card_num": "4111111111111111",
        "card_code": "007",
        "amount": "5.00",
        "currency": "EUR",
        "exp_date_month": "12",
        "exp_date_year": "9999",
        "payment_account": "wemove-account",
        "trans_id": "tx1",
    }
    assert body["user"]["postal"] == "75001"
    assert body["user"]["zip"] is None
    assert body["user"]["country"] == "FR"
    assert body["donationpage"] == {"name": "my-page"}
    assert "action" not in body
    assert "order" in body and "recurring_id" not in body["order"]


@responses.activate
def test_push_sends_zip_not_postal_for_us_country(donationaction):
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=201,
        json={"resource_uri": rest("donationaction/1/")},
    )
    donationaction.push(**{**PUSH_REQUIRED, "country": "US", "postal": "10001"})
    body = json_module.loads(responses.calls[0].request.body)
    assert body["user"]["zip"] == "10001"
    assert body["user"]["postal"] is None


@responses.activate
def test_push_sets_created_at_in_utc_isoformat(donationaction):
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=201,
        json={"resource_uri": rest("donationaction/1/")},
    )
    created_at = datetime(2024, 1, 15, 16, 21, 29, tzinfo=timezone.utc)
    donationaction.push(**PUSH_REQUIRED, created_at=created_at)
    body = json_module.loads(responses.calls[0].request.body)
    assert body["order"]["created_at"] == "2024-01-15T16:21:29+00:00"


@responses.activate
def test_push_recurring_id_adds_recurring_fields(donationaction):
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=201,
        json={"resource_uri": rest("donationaction/1/")},
    )
    donationaction.push(**PUSH_REQUIRED, recurring_id="rec-1")
    body = json_module.loads(responses.calls[0].request.body)
    assert body["order"]["recurring_id"] == "rec-1"
    assert body["order"]["recurring_period"] == "months"


@responses.activate
def test_push_custom_action_fields_and_skip_confirmation(donationaction):
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=201,
        json={"resource_uri": rest("donationaction/1/")},
    )
    donationaction.push(
        **PUSH_REQUIRED, custom_action_fields={"foo": "bar"}, skip_confirmation=True
    )
    body = json_module.loads(responses.calls[0].request.body)
    assert body["action"] == {"fields": {"foo": "bar"}, "skip_confirmation": "1"}


@responses.activate
def test_push_409_duplicate_writes_stderr_and_returns_none(donationaction, capsys):
    responses.add(responses.POST, rest("donationpush/"), status=409, body="")
    result = donationaction.push(**PUSH_REQUIRED)
    assert result is None
    assert "Duplicate donation_import_id" in capsys.readouterr().err


@responses.activate
def test_push_400_with_body_raises_validation_error_not_generic_exception(
    donationaction,
):
    """
    Pins the same systemic finding as test_connection.py and
    test_transactions.py: push()'s `except HTTPError as e: if
    e.response.status_code == 400: raise Exception(...)` branch
    (donationaction.py:111-114) is written to handle 400s, but a real
    ActionKit validation-error response carries a JSON body, so
    _make_request converts it to ValidationError first -- this branch is
    unreachable for a body-bearing 400 in practice, and ValidationError
    propagates directly to the caller instead of the intended, friendlier
    generic Exception with the response text embedded.
    """
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=400,
        json={"amount": ["This field is required."]},
    )
    with pytest.raises(ValidationError):
        donationaction.push(**PUSH_REQUIRED)


@responses.activate
def test_push_400_with_empty_body_hits_the_intended_generic_exception(donationaction):
    """
    Contrast with the previous test: only an EMPTY-bodied 400 actually
    reaches push()'s own `except HTTPError` 400-handling branch.
    """
    responses.add(responses.POST, rest("donationpush/"), status=400, body="")
    with pytest.raises(Exception) as excinfo:
        donationaction.push(**PUSH_REQUIRED)
    assert not isinstance(excinfo.value, ValidationError)
    assert "Creation of donationaction failure" in str(excinfo.value)


# --- push_and_set_incomplete() / push_and_set_pending() ------------------


@responses.activate
def test_push_and_set_incomplete_full_stack(donationaction):
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=201,
        json={
            "resource_uri": rest("donationaction/1/"),
            "status": "new",
            "order": {
                "resource_uri": rest("order/1/"),
                "transactions": [rest("transaction/1/")],
                "orderrecurrings": [],
            },
        },
    )
    responses.add(responses.PATCH, rest("donationaction/1/"), status=200)
    responses.add(responses.PATCH, rest("order/1/"), status=200)
    responses.add(responses.PATCH, rest("transaction/1/"), status=200)

    result = donationaction.push_and_set_incomplete(
        email="a@example.com",
        first_name="A",
        last_name="B",
        country="FR",
        postal="75001",
        amount=Decimal("5.00"),
        currency="EUR",
        page="my-page",
        payment_account="wemove-account",
    )
    assert result == rest("donationaction/1/")
    # 1 POST to create + 3 PATCHes (action/order/transaction) from set_push_status
    assert len(responses.calls) == 4
    assert json_module.loads(responses.calls[1].request.body) == {"status": "incomplete"}
    assert json_module.loads(responses.calls[2].request.body) == {"status": "incomplete"}
    assert json_module.loads(responses.calls[3].request.body) == {"status": "incomplete"}


@responses.activate
def test_push_and_set_pending_sets_order_and_transaction_status_pending(donationaction):
    responses.add(
        responses.POST,
        rest("donationpush/"),
        status=201,
        json={
            "resource_uri": rest("donationaction/1/"),
            "status": "new",
            "order": {
                "resource_uri": rest("order/1/"),
                "transactions": [rest("transaction/1/")],
                "orderrecurrings": [],
            },
        },
    )
    responses.add(responses.PATCH, rest("donationaction/1/"), status=200)
    responses.add(responses.PATCH, rest("order/1/"), status=200)
    responses.add(responses.PATCH, rest("transaction/1/"), status=200)

    action = donationaction.push_and_set_pending(
        email="a@example.com",
        first_name="A",
        last_name="B",
        country="FR",
        postal="75001",
        amount=Decimal("5.00"),
        currency="EUR",
        page="my-page",
        payment_account="wemove-account",
    )
    assert action["resource_uri"] == rest("donationaction/1/")
    assert json_module.loads(responses.calls[1].request.body) == {"status": "incomplete"}
    assert json_module.loads(responses.calls[2].request.body) == {"status": "pending"}
    assert json_module.loads(responses.calls[3].request.body) == {"status": "pending"}


# --- set_push_status() --------------------------------------------------


def test_set_push_status_requires_data_or_resource_uri(donationaction):
    with pytest.raises(KeyError):
        donationaction.set_push_status("completed")


def test_set_push_status_resource_uri_with_only_one_of_order_or_transaction_uri(
    donationaction,
):
    with pytest.raises(KeyError):
        donationaction.set_push_status(
            "completed", resource_uri=rest("donationaction/1/"), order_uri=rest("order/1/")
        )


def test_set_push_status_data_plus_uris_is_rejected(donationaction):
    with pytest.raises(KeyError):
        donationaction.set_push_status(
            "completed",
            donationaction_data={"status": "new"},
            resource_uri=rest("donationaction/1/"),
        )


@responses.activate
def test_set_push_status_skips_when_already_set(donationaction):
    result = donationaction.set_push_status(
        "completed",
        donationaction_data={
            "status": "completed",
            "resource_uri": rest("donationaction/1/"),
            "order": {
                "resource_uri": rest("order/1/"),
                "transactions": [rest("transaction/1/")],
                "orderrecurrings": [],
            },
        },
        no_action_if_status_is_already_set=True,
    )
    assert result == rest("donationaction/1/")
    assert len(responses.calls) == 0


@responses.activate
def test_set_push_status_full_uri_sequence(donationaction):
    responses.add(responses.PATCH, rest("donationaction/1/"), status=200)
    responses.add(responses.PATCH, rest("order/1/"), status=200)
    responses.add(responses.PATCH, rest("transaction/1/"), status=200)

    result = donationaction.set_push_status(
        "completed",
        donationaction_data={
            "status": "new",
            "resource_uri": rest("donationaction/1/"),
            "order": {
                "resource_uri": rest("order/1/"),
                "transactions": [rest("transaction/1/")],
                "orderrecurrings": [],
            },
        },
    )
    assert result == rest("donationaction/1/")
    assert len(responses.calls) == 3


@responses.activate
def test_set_push_status_custom_action_fields_adds_fourth_patch(donationaction):
    responses.add(responses.PATCH, rest("donationaction/1/"), status=200)
    responses.add(responses.PATCH, rest("order/1/"), status=200)
    responses.add(responses.PATCH, rest("transaction/1/"), status=200)
    responses.add(responses.PATCH, rest("donationaction/1/"), status=200)

    donationaction.set_push_status(
        "completed",
        donationaction_data={
            "status": "new",
            "resource_uri": rest("donationaction/1/"),
            "fields": {"existing": "1"},
            "order": {
                "resource_uri": rest("order/1/"),
                "transactions": [rest("transaction/1/")],
                "orderrecurrings": [],
            },
        },
        custom_action_fields={"new_field": "2"},
    )
    assert len(responses.calls) == 4
    fields_body = json_module.loads(responses.calls[3].request.body)
    assert fields_body == {"fields": {"existing": "1", "new_field": "2"}}


@responses.activate
def test_set_push_status_recurring_id_patches_first_orderrecurring_uri(donationaction):
    responses.add(responses.PATCH, rest("donationaction/1/"), status=200)
    responses.add(responses.PATCH, rest("order/1/"), status=200)
    responses.add(responses.PATCH, rest("transaction/1/"), status=200)
    responses.add(responses.PATCH, rest("orderrecurring/1/"), status=200)

    donationaction.set_push_status(
        "completed",
        donationaction_data={
            "status": "new",
            "resource_uri": rest("donationaction/1/"),
            "order": {
                "resource_uri": rest("order/1/"),
                "transactions": [rest("transaction/1/")],
                "orderrecurrings": [rest("orderrecurring/1/"), rest("orderrecurring/2/")],
            },
        },
        recurring_id="rec-1",
    )
    assert len(responses.calls) == 4
    body = json_module.loads(responses.calls[3].request.body)
    assert body == {"recurring_id": "rec-1", "recurring_period": "months"}


# --- set_push_status_* wrappers ------------------------------------------


@pytest.mark.parametrize(
    "wrapper,expected_kwargs",
    [
        ("set_push_status_incomplete", {"action_status": "incomplete"}),
        (
            "set_push_status_completed",
            {"action_status": "completed", "no_action_if_status_is_already_set": True},
        ),
        ("set_push_status_failed", {"action_status": "failed"}),
        (
            "set_push_status_pending",
            {
                "action_status": "incomplete",
                "order_status": "pending",
                "transaction_status": "pending",
            },
        ),
    ],
)
def test_status_wrappers_delegate_to_set_push_status(
    donationaction, monkeypatch, wrapper, expected_kwargs
):
    calls = []

    def fake_set_push_status(self, action_status, *args, **kwargs):
        calls.append((action_status, kwargs))
        return "resource_uri"

    monkeypatch.setattr(
        "actionkit.donationaction.DonationAction.set_push_status", fake_set_push_status
    )
    getattr(donationaction, wrapper)(donationaction_data={"status": "new"})
    assert len(calls) == 1
    action_status, kwargs = calls[0]
    assert action_status == expected_kwargs["action_status"]
    for key, value in expected_kwargs.items():
        if key == "action_status":
            continue
        assert kwargs.get(key) == value


# --- cancel_recurring_profile() / add_recurring_payment() ----------------


@responses.activate
def test_cancel_recurring_profile_posts_expected_payload(donationaction):
    responses.add(responses.POST, rest("profilecancelpush/"), status=201, json={})
    donationaction.cancel_recurring_profile("rec-1", "processor")
    body = json_module.loads(responses.calls[0].request.body)
    assert body == {"recurring_id": "rec-1", "canceled_by": "processor"}


@responses.activate
def test_add_recurring_payment_posts_payload_unchanged(donationaction):
    responses.add(responses.POST, rest("recurringpaymentpush/"), status=201, json={})
    payment = {"order_id": "1", "success": True}
    donationaction.add_recurring_payment(payment)
    assert json_module.loads(responses.calls[0].request.body) == payment


# --- extract_resource_uris() ----------------------------------------------


def test_extract_resource_uris_requires_an_argument(donationaction):
    with pytest.raises(KeyError):
        donationaction.extract_resource_uris()


def test_extract_resource_uris_from_data(donationaction):
    data = {
        "resource_uri": rest("donationaction/1/"),
        "order": {
            "resource_uri": rest("order/1/"),
            "transactions": [rest("transaction/1/")],
            "orderrecurrings": [rest("orderrecurring/1/")],
        },
    }
    assert donationaction.extract_resource_uris(donationaction_data=data) == {
        "resource_uri": rest("donationaction/1/"),
        "order_uri": rest("order/1/"),
        "transaction_uri": rest("transaction/1/"),
        "orderrecurring_uris": [rest("orderrecurring/1/")],
    }


@responses.activate
def test_extract_resource_uris_fetches_by_resource_uri(donationaction):
    responses.add(
        responses.GET,
        rest("donationaction/1/"),
        json={
            "resource_uri": rest("donationaction/1/"),
            "order": {
                "resource_uri": rest("order/1/"),
                "transactions": [rest("transaction/1/")],
                "orderrecurrings": [],
            },
        },
        status=200,
    )
    result = donationaction.extract_resource_uris(resource_uri=rest("donationaction/1/"))
    assert result["order_uri"] == rest("order/1/")


# --- delete_donationaction() / delete_donationaction_by_resource_id ------


@responses.activate
def test_delete_donationaction_incomplete_deletes(donationaction):
    responses.add(
        responses.GET,
        rest("donationaction/1/"),
        json={"status": "incomplete"},
        status=200,
    )
    responses.add(responses.DELETE, rest("donationaction/1/"), status=204)
    assert donationaction.delete_donationaction(rest("donationaction/1/")) is True
    assert len(responses.calls) == 2


@responses.activate
def test_delete_donationaction_non_incomplete_does_not_delete(donationaction):
    responses.add(
        responses.GET,
        rest("donationaction/1/"),
        json={"status": "completed"},
        status=200,
    )
    assert donationaction.delete_donationaction(rest("donationaction/1/")) is True
    assert len(responses.calls) == 1


@responses.activate
def test_delete_donationaction_404_returns_false(donationaction):
    responses.add(responses.GET, rest("donationaction/1/"), status=404, body="")
    assert donationaction.delete_donationaction(rest("donationaction/1/")) is False


@responses.activate
def test_delete_donationaction_by_resource_id_builds_uri_and_delegates(donationaction):
    responses.add(
        responses.GET,
        rest("donationaction/1/"),
        json={"status": "incomplete"},
        status=200,
    )
    responses.add(responses.DELETE, rest("donationaction/1/"), status=204)
    donationaction.delete_donationaction_by_resource_id("1")
    assert len(responses.calls) == 2


def test_delete_donationaction_by_resource_id_noop_without_resource_id(donationaction):
    donationaction.delete_donationaction_by_resource_id(None)
