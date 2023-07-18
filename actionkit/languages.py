from .httpmethods import HttpMethods


class Languages(HttpMethods):
    resource_name = "language"

    def by_code(self):
        langs = self.search()
        # Robotic dogs has 2 languages with same code...
        return {l["iso_code"]: l for l in langs if l["name"] != "Disco"}

    def uris(self):
        langs = self.search()
        return dict(map(lambda l: (l["iso_code"], l["resource_uri"]), langs))
