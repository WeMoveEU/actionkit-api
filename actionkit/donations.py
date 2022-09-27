import json

DONATION_PUSH_PATH = "donationpush/"


class DonationPush:
    def __init__(self, connection):
        self.connection = connection

    def push(self, donation):
        self.connection.post(DONATION_PUSH_PATH, donation)
