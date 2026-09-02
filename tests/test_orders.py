import json as json_module
from decimal import Decimal

import pytest
import responses

from urls import rest


@pytest.fixture
def orders(ak):
    return ak.Orders


def test_update_requires_resource_id_or_resource_uri(orders):
    with pytest.raises(ValueError):
        orders.update(total=Decimal("5.00"))


@responses.activate
def test_update_with_resource_uri_sends_decimal_as_string(orders):
    responses.add(responses.PATCH, rest("order/1/"), status=200)
    orders.update(resource_uri=rest("order/1/"), total=Decimal("5.00"))
    assert json_module.loads(responses.calls[0].request.body) == {"total": "5.00"}


@responses.activate
def test_update_with_resource_id_builds_uri(orders):
    responses.add(responses.PATCH, rest("order/1/"), status=200)
    orders.update(resource_id="1", total=Decimal("5.00"))
    assert responses.calls[0].request.url == rest("order/1/")


@responses.activate
def test_update_without_total_omits_it_from_payload(orders):
    responses.add(responses.PATCH, rest("order/1/"), status=200)
    orders.update(resource_uri=rest("order/1/"), status="paid")
    assert json_module.loads(responses.calls[0].request.body) == {"status": "paid"}
