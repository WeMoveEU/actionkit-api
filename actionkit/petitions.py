class Petitions:
    def __init__(self, connection):
        self.connection = connection

    def create(self, **kwargs):
        return self.connection.get(self.connection.post("petitionpage/", kwargs))

    def get(self, id):
        return self.connection.get(f"petitionpage/{id}/")

    def patch(self, id, **params):
        return self.connection.patch(f"petitionpage/{id}/", params)
