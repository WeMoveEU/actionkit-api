from .orders import Orders


class OrderRecurring(Orders):
    def __init__(self, connection):
        super().__init__(connection)
        self.base_path = "orderrecurring/"
