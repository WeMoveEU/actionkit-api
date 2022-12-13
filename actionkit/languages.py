from .httpmethods import HttpMethods


class Languages(HttpMethods):
    def __init__(self, connection):
        self.connection = connection

    def by_code(self):
        langs = self.connection.get("language/")
        # Robotic dogs has 2 languages with same code...
        return {l["iso_code"]: l for l in langs["objects"] if l["name"] != "Disco"}

    def uris(self):
        langs = self.connection.get("language/")
        return dict(map(lambda l: (l["iso_code"], l["resource_uri"]), langs["objects"]))
