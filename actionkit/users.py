import re

from .httpmethods import HttpMethods

class Users(HttpMethods):
    resource_name = "user"

    def get_by_email(self, email):
        users = self.search(email=email)
        if len(users) == 0:
            return None
        else:
            return users[0]

    def create(self, user):
        return self.post(user)

    def update(self, path, user):
        return self.patch(path, user)

    def uri(self, id=None):
        return f"{self.resource_name}/{id or ''}"

    def id(self, uri):
        m = re.search(f"/{self.resource_name}/(\d+)", uri)
        if m:
            return m[1]
        else:
            raise Exception(f"{uri} is not a user URI")
