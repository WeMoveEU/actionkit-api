from decimal import Decimal

from .httpmethods import HttpMethods


class Orders(HttpMethods):
    resource_name = "order"

    def update(
        self,
        resource_uri: str = None,
        resource_id: str = None,
        total: Decimal = None,
        **kwargs: dict
    ) -> dict:
        """
        Update an order
        """
        if not (resource_id or resource_uri):
            raise ValueError('Either resource_id or resource_uri must be provided')

        if not resource_uri:
            resource_uri = self.get_resource_uri_from_id(resource_id)

        payload = kwargs.copy()
        if total is not None:
            payload['total'] = str(total)

        return self.patch(resource_uri, to_patch=payload)
