from decimal import Decimal

from .httpmethods import HttpMethods


class Orders(HttpMethods):
    resource_name = "order"

    # def add_partial_refund(
    #     self, order_id: str, amount: Decimal, reason: str, **kwargs: dict
    # ) -> dict:
    #     """
    #     Add a partial refund to an order
    #     """
    #     return self.connection.post(
    #         f"{self.resource_name}/{order_id}/refund",
    #         json={"amount": amount, "reason": reason},
    #         **kwargs,
    #     ).json()