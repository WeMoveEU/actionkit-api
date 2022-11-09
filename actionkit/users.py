from .httpmethods import HttpMethods


class Users(HttpMethods):
    def __init__(self, connection):
        self.connection = connection

    def get(self, email):
        users = self.connection.get(f"user/?email={email}")
        if users["meta"]["total_count"] == 0:
            return None
        else:
            return users["objects"][0]

    def create(self, user):
        return self.connection.post("user/", user)

    def update(self, path, user):
        return self.connection.patch(path, user)
