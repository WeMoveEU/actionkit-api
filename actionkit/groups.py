from .httpmethods import HttpMethods


class Groups(HttpMethods):
    resource_name = "usergroup"

    def uris(self):
        groups = self.get(_limit=100)
        return dict(map(lambda g: (g["name"], g["resource_uri"]), groups["objects"]))

    def create(self, group):
        return self.post(json=group)
