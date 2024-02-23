from datetime import datetime, timezone

from .httpmethods import HttpMethods


class GenericActions(HttpMethods):
    resource_name = "action"

    def update(
        self,
        resource_uri: str = None,
        resource_id: str = None,
        created_at: datetime = None,
        **kwargs: dict,
    ) -> dict:
        """
        Update a generic action
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
            custom_action_fields = action.get('fields', {})
            custom_action_fields.update(fields)
            payload['fields'] = custom_action_fields

        if created_at:
            payload['created_at'] = created_at.astimezone(tz=timezone.utc).isoformat()

        return self.patch(resource_uri, payload)
