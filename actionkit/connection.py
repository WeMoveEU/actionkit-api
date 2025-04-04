import logging
import pprint
import re
import time

import requests

from .validation import ValidationError

resource_uri_id_regex = re.compile(r"/(?P<id>\d+)/$")


class Connection:
    """
    Provide simple, but useful methods for creating and using an HTTPS session with the ActionKit API.
    """

    # retry_codes are the HTTP error codes that this service will attempt retries on
    # Reference: https://docs.python-requests.org/en/latest/api/#status-code-lookup
    retry_codes = [requests.codes.internal_server_error]
    # In the case of a response being one of the retry_codes this is how many times we try the
    # request again
    num_retries = 3
    # The initial_backoff value is the number of seconds we wait before a retry.
    # This number doubles every time
    initial_backoff = 3  # seconds

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        logger=logging.getLogger(__name__),
    ) -> None:
        """
        Initialise settings and request defaults
        """

        self.hostname = hostname
        self.request_kwargs = {
            "headers": {"Accept": "application/json"},
            "auth": requests.auth.HTTPBasicAuth(username, password),
        }
        self.logger = logger

    @staticmethod
    def get_resource_uri(response):
        """
        This method takes the response from ActionKit after a resource has been successfully
        created. It will get the resource_uri from the response headers, if present and return it.
        """
        return response.headers.get("Location", None)

    @staticmethod
    def get_resource_uri_id(resource_uri):
        """
        This method takes a resource_uri and returns the id of the resource.
        """
        match = resource_uri_id_regex.search(resource_uri)
        if match:
            return match.group("id")
        return None

    @staticmethod
    def get_resource_uri_id_from_response(response):
        """
        This method takes the response from ActionKit after a resource has been successfully
        created. It will get the resource_uri from the response headers, if present and return the id.
        """
        resource_uri = Connection.get_resource_uri(response)
        if resource_uri:
            return Connection.get_resource_uri_id(resource_uri)
        return None

    @staticmethod
    def get_resource_uri_from_id(resource_id, resource_name):
        """
        This method takes an ActionKit resource_id and returns the resource_uri, based on the
        resource_name.
        """
        return f"/rest/v1/{resource_name}/{resource_id}/"

    def _make_request(
        self, http_method: str, path: str, json=None, params=None, data=None, **kwargs
    ):
        """
        Make the request to the ActionKit API with the desired method
        """
        _http_method = http_method.lower()
        request_fn = getattr(requests, _http_method, None)
        if request_fn is None:
            raise NotImplementedError(f"HTTP method {_http_method} not supported")

        request_kwargs = {}
        request_kwargs.update(self.request_kwargs)
        request_kwargs.update(kwargs)

        if _http_method == "get":
            if json:
                raise ValueError("Cannot use json with GET requests")
            request_kwargs["params"] = params
        else:
            if params:
                raise ValueError("Cannot use params with non-GET requests")
            if data and json:
                raise ValueError("Cannot use both data and json together in a request")
            if data:
                request_kwargs["data"] = data
            elif json:
                request_kwargs["json"] = json

        url = self._path(path)

        self.logger.debug(f"Making {_http_method} request to {url}")
        self.logger.debug(f"Request kwargs:\n{pprint.pformat(request_kwargs)}")

        backoff = self.initial_backoff
        retries_left = self.num_retries

        # ActionKit REST is notoriously flaky, so we retry requests on certain HTTP error codes
        while True:
            try:
                response = request_fn(url, **request_kwargs)
                self.logger.debug(
                    f"ActionKit Request headers:\n{pprint.pformat(response.request.headers)}"
                )
                if response.content:
                    if response.headers.get("content-type") == "application/json":
                        content = pprint.pformat(response.json())
                    else:
                        content = response.text
                    self.logger.debug(f"ActionKit Response body:\n{content}")
                response.raise_for_status()
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in self.retry_codes and retries_left > 0:
                    time.sleep(backoff)
                    retries_left -= 1
                    backoff *= 2
                    continue
                if hasattr(e.response, "text") and e.response.text:
                    self.logger.warning(
                        f"Text from unsuccessful response: {e.response.text}"
                    )
                    raise ValidationError(e.response.text)
                else:
                    self.logger.error(e)
                raise

        return response

    def _path(self, path: str) -> str:
        "Handle common cases of path inputs - try to be friendly without getting fancy."
        if path.startswith("http"):
            return path

        # already an API path
        if path.startswith("/rest/v1"):
            return f"https://{self.hostname}{path}"

        # prepend API path. remove // in case the provided path has a / at the beginning
        return f"https://{self.hostname}" + f"/rest/v1/{path}".replace("//", "/")

    def get(self, path: str, *args, params: dict = None, **kwargs) -> dict:
        return self._make_request("get", path, *args, params=params, **kwargs)

    def post(self, path: str, json: dict = None, data: dict = None, **kwargs) -> str:
        """
        Issue a POST request with JSON and other params.
        """
        return self._make_request("post", path, json=json, data=data, **kwargs)

    def patch(self, path: str, json: dict = None, data: dict = None, **kwargs) -> bool:
        return self._make_request("patch", path, json=json, data=data, **kwargs)

    def put(self, path: str, json: dict = None, data: dict = None, **kwargs) -> bool:
        return self._make_request("put", path, json=json, data=data, **kwargs)

    def delete(self, path: str, *args, **kwargs) -> bool:
        return self._make_request("delete", path, *args, **kwargs)
