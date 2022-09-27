import requests

from .donations import DonationPush


class Connection:
    def __init__(self, hostname, username, password):

        self.base_url = "https://" + hostname + "/rest/v1/"
        self.session = requests.Session()
        self.session.auth = (username, password)
        # test the connection
        self.session.get(self.base_url + "user/?_limit=1")

    def post(self, path, params):
        response = self.session.post(self.base_url + path, json=params)
        response.raise_for_status()
        return response

    def donation_push(self):
        return DonationPush(connection=self)
