from typing import List

from requests import HTTPError


class HttpMethods:
    def search(self, **params: dict) -> List[dict]:
        try:
            resource = self.connection.get(self.base_path, **params)

            to_return = resource["objects"]
            while resource["meta"]["next"]:
                resource = self.connection.get(resource["meta"]["next"])
                to_return.extend(resource["objects"])

            return to_return

        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for search(): {e.response.text}: {e}")
            raise

    def delete(self, order):
        try:
            return self.connection.delete(self.connection._path(order["action"]))
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for delete(): {e.response.text}: {e}")
            raise

    def get(self, **params):
        try:
            return self.connection.get(self.base_path, **params)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for get(): {e.response.text}: {e}")
            raise

    def patch(self, resource_uri, to_patch):
        try:
            return self.connection.patch(resource_uri, to_patch)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for patch(): {e.response.text}: {e}")
            raise

    def put(self, resource_uri, to_put):
        try:
            return self.connection.put(resource_uri, to_put)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for put(): {e.response.text}: {e}")
            raise

    def post(self, **params):
        try:
            return self.connection.post(self.base_path, **params)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(f"Bad request for post(): {e.response.text}: {e}")
            raise
