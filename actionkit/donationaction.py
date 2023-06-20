from typing import List

from requests import HTTPError

from .httpmethods import HttpMethods


class DonationAction(HttpMethods):
    def __init__(self, connection):
        self.connection = connection
        self.base_path = "donationaaction/"
