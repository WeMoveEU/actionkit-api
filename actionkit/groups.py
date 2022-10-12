class Groups:
    def __init__(self, connection):
        self.connection = connection

    def uris(self):
        groups = self.connection.get("usergroup/")
        return dict(map(lambda g: (g['name'], g['resource_uri']), groups["objects"]))
