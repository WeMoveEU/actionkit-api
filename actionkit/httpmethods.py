from typing import List

from requests import HTTPError


def complete_path(fn):
        def _wrapper(self, uri=None, *args, **kwargs):
            if uri is None:
                return fn(self, uri, *args, **kwargs)
            resource_uri = str(uri)
            if resource_uri.startswith(self.resource_name):
                pass
            elif resource_uri.startswith('/'):
                pass
            else:
                resource_uri = f"{self.resource_name}/{resource_uri}/"
            return fn(self, resource_uri, *args, **kwargs)
        return _wrapper


class HttpMethods:
    def __init__(self, connection):
        self.connection = connection

    @property
    def logger(self):
        return self.connection.logger

    @property
    def resource_name(self):
        raise NotImplementedError('ActionKit resource_name must be defined')

    def search(self, **params: dict) -> List[dict]:
        """
        Returns a list of *all* paged results from ActionKit for the resource self.resource_name
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

    @complete_path
    def delete(
        self, resource_uri: str, *args, ignore_404=True, dry_run=False, **kwargs
    ):
        """
        Generic delete method for ActionKit resources
        """


        if dry_run:
            self.logger.info(
                f"Dry run: Would have deleted {self.connection._path(resource_uri)}"
            )
            return True
        try:
            self.connection.delete(resource_uri, *args, **kwargs)
        except HTTPError as e:
            if e.response.status_code == 404 and ignore_404:
                return False
            raise
        return True

    @complete_path
    def get(self, resource_uri=None, *args, **params):
        """
        Get an object at path resource_uri from ActionKit

        param kwargs are passed as query params to the request
        """
        response = self.connection.get(
            resource_uri or self.resource_name, *args, params=params
        )
        return response.json()

    @complete_path
    def patch(self, resource_uri: str, to_patch: dict, *args, **kwargs):
        """
        Generic patch method for ActionKit resources
        """
        self.connection.patch(resource_uri, *args, json=to_patch, **kwargs)
        return True

    @complete_path
    def put(self, resource_uri: str, to_put: dict, *args, **kwargs):
        """
        Generic put method for ActionKit resources
        """
        self.connection.put(resource_uri, *args, json=to_put, **kwargs)
        return True

    def post(self, *args, **kwargs):
        """
        Post a new payload for type self.resource_name to ActionKit, passing kwargs directly
        through to requests.post

        Returns the resource_uri of the newly created resource
        """
        response = self.connection.post(self.resource_name, *args, **kwargs)
        return self.connection.__class__.get_resource_uri(response)

    # XXX: Why so many different ways to get the same thing?

    def get_resource_uri_from_id(self, resource_id):
        """
        Utility method to convert a given resource id to the ActionKit resource_uri for the existing
        self.resource_name
        """
        return self.connection.get_resource_uri_from_id(resource_id, self.resource_name)

    def get_resource_uri(self, response):
        """
        Wrapper to the internal Connection.get_resource_uri method
        """
        return self.connection.get_resource_uri(response)

    def get_resource_uri_id(self, resource_uri):
        """
        Wrapper to the internal Connection.get_resource_uri_id method
        """
        return self.connection.get_resource_uri_id(resource_uri)

    def get_resource_uri_id_from_response(self, response):
        """
        Wrapper to the internal Connection.get_resource_uri_id_from_response method
        """
        return self.connection.get_resource_uri_id_from_response(response)

    def get_by_id(self, id, *args, **params):
        """
        Get an object by its id from ActionKit
        """
        self.logger.warning(f"get_by_id is no longer needed, you can just call get() with {id} now.")
        return self.get(*args, resource_uri=f'{self.resource_name}/{id}', params=params)
