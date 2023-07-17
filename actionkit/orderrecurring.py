from .httpmethods import HttpMethods


class OrderRecurring(HttpMethods):
    resource_name = "orderrecurring"

    def __init__(self, connection):
        self.connection = connection
