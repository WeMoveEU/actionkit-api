import requests


class Connection:
    """
    Provide simple, but useful methods for creating and using an HTTPS session with the ActionKit API.

    """

    def __init__(self, hostname: str, username: str, password: str) -> None:
        """
        Create the HTTP session.
        """

        self.hostname = hostname

        self.session = requests.Session()
        self.session.auth = (username, password)

    def get(self, path: str, **kwargs) -> dict:
        response = self.session.get(self._path(path), params=kwargs)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, json: dict, **kwargs) -> str:
        """
        Issue a POST request with JSON and other params.
        """
        # don't catch exceptions here, different callers will want to do different things
        response = self.session.post(self._path(path), json=json)
        response.raise_for_status()
        return response.headers["Location"]

    def patch(self, path: str, json: dict) -> bool:
        response = self.session.patch(self._path(path), json=json)
        response.raise_for_status()
        return True

    def put(self, path: str, json: dict) -> bool:
        response = self.session.put(self._path(path), json=json)
        response.raise_for_status()
        return True

    def delete(self, path: str) -> bool:
        response = self.session.delete(self._path(path))
        response.raise_for_status()
        return True

    def _path(self, path: str) -> str:
        "Handle common cases of path inputs - try to be friendly without getting fancy."
        if path.startswith("http"):
            return path

        # already an API path
        if path.startswith("/rest/v1"):
            return f"https://{self.hostname}{path}"

        # prepend API path. remove // in case the provided path has a / at the beginning
        return f"https://{self.hostname}" + f"/rest/v1/{path}".replace("//", "/")
