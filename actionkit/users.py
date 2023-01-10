import re

from .httpmethods import HttpMethods

class Users(HttpMethods):
    def __init__(self, connection):
        self.connection = connection

    def get(self, email):
        users = self.connection.get(f"{self.uri()}?email={email}")
        if users["meta"]["total_count"] == 0:
            return None
        else:
            return users["objects"][0]

    def create(self, user):
        return self.connection.post(self.uri(), user)

    def update(self, path, user):
        return self.connection.patch(path, user)

    def uri(self, id=None):
        return f"user/{id or ''}"

    def id(self, uri):
        m = re.search("/user/(\d+)", uri)
        if m:
            return m[1]
        else:
            raise Exception(f"{uri} is not a user URI")
