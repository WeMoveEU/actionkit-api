from .httpmethods import HttpMethods


class GenericActions(HttpMethods):
    resource_name = "action"

    def update(
        self,
        resource_uri: str = None,
        resource_id: str = None,
        **kwargs: dict,
    ) -> dict:
        """
        Update an generic action
        """
        if not (resource_id or resource_uri):
            raise ValueError('Either resource_id or resource_uri must be provided')

        if not resource_uri:
            resource_uri = self.get_resource_uri_from_id(resource_id)

        fields = kwargs.pop('fields', {})

        payload = kwargs.copy()

        if fields:
            # We gotta update the custom action fields so we need to fetch what is there first
            action = self.get(resource_uri)
            action_fields = action.get('fields', {})
            action_fields.update(fields)
            payload['fields'] = action_fields

        return self.patch(resource_uri, payload)
