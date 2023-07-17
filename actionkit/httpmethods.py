from typing import List

from requests import HTTPError


class HttpMethods:
    def __init__(self, connection):
        self.connection = connection

    @property
    def resource_name(self):
        raise NotImplementedError('ActionKit resource_name must be defined')

    def search(self, **params: dict) -> List[dict]:
        """
        Returns a list of paged results from ActionKit for the resource self.resource_name
        """
        try:
            resource = self.get(**params)

            to_return = resource["objects"]
            while resource["meta"]["next"]:
                response = self.connection.get(resource["meta"]["next"])
                resource = response.json()
                to_return.extend(resource["objects"])

            return to_return

        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for search(): {e.response.text}: {e}")
            raise

    def delete(self, order: dict):
        """
        Specifically delete an action referenced by an order
        # TODO: @Romain - this seems very business-logic specific for a delete method in this class
        """
        try:
            self.connection.delete(order["action"])
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for delete(): {e.response.text}: {e}")
            raise
        return True

    def get(self, resource_uri, **params):
        """
        Get an object at path resource_uri from ActionKit

        param kwargs are passed as query params to the request
        """
        try:
            response = self.connection.get(resource_uri, params=params)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for get(): {e.response.text}: {e}")
            raise
        return response.json()

    def patch(self, resource_uri: str, to_patch: dict):
        """
        Generic patch method for ActionKit resources
        """
        try:
            self.connection.patch(resource_uri, json=to_patch)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for patch(): {e.response.text}: {e}")
            raise
        return True

    def put(self, resource_uri: str, to_put: dict):
        """
        Generic put method for ActionKit resources
        """
        try:
            self.connection.put(resource_uri, json=to_put)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for put(): {e.response.text}: {e}")
            raise
        return True

    def post(self, **kwargs):
        """
        Post a new payload for type self.resource_name to ActionKit, passing kwargs directly
        through to requests.post

        Returns the resource_uri of the newly created resource
        """
        try:
            response = self.connection.post(self.resource_name, **kwargs)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for post(): {e.response.text}: {e}")
            raise
        return self.connection.__class__.get_resource_uri(response)
