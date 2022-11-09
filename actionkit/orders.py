from .httpmethods import HttpMethods


class Orders(HttpMethods):
    def __init__(self, connection):
        self.connection = connection
        self.base_path = "order/"
