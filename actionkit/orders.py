from typing import List

from requests import HTTPError

BASE_PATH = "order/"


class Orders:
    def __init__(self, connection):
        self.connection = connection

    def search(self, **params: dict) -> List[dict]:
        try:
            orders = self.connection.get(BASE_PATH, **params)

            to_return = orders["objects"]
            while orders["meta"]["next"]:
                orders = self.connection.get(orders["meta"]["next"])
                to_return.extend(orders["objects"])

            return to_return

        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(
                    f"Bad request for Orders.search(): {e.response.text}: {e}"
                )
            raise

    def delete(self, order):
        try:
            return self.connection.delete(self.connection._path(order["action"]))
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(
                    f"Bad request for Orders.delete(): {e.response.text}: {e}"
                )
            raise
