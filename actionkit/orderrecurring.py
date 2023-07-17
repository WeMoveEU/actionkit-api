from .httpmethods import HttpMethods


class OrderRecurring(HttpMethods):
    def __init__(self, connection):
        self.connection = connection
        self.resource_name = "orderrecurring/"
