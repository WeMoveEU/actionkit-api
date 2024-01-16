from decimal import Decimal

from .httpmethods import HttpMethods


class Orders(HttpMethods):
    resource_name = "order"

    def update(
        self,
        order_uri: str = None,
        order_id: str = None,
        total: Decimal = None,
        **kwargs: dict
    ) -> dict:
        """
        Update an order
        """
        if not (order_id or order_uri):
            raise ValueError('Either order_id or order_uri must be provided')

        payload = kwargs.copy()
        if total is not None:
            payload['total'] = str(total)

        return self.patch(order_uri, to_patch=payload)
