from .httpmethods import HttpMethods


class Languages(HttpMethods):
    def __init__(self, connection):
        self.connection = connection

    def uris(self):
        langs = self.connection.get("language/")
        return dict(map(lambda l: (l["iso_code"], l["resource_uri"]), langs["objects"]))
