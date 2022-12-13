class Petitions:
    def __init__(self, connection):
        self.connection = connection

    def create(self, page, content):
        page_uri = self.connection.post("petitionpage", page)
        content = dict(content)
        content["page"] = page_uri
        self.connection.post("petitionform", content)
        return page_uri

    def get(self, id):
        return self.connection.get(f"petitionpage/{id}/")

    def update(self, id, params):
        return self.connection.patch(f"petitionpage/{id}/", params)
