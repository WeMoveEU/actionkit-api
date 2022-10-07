import json
import sys

from requests import HTTPError

DONATION_PUSH_PATH = "donationpush/"


class DonationPush:
    def __init__(self, connection):
        self.connection = connection

    def push(self, donation):
        try:
            response = self.connection.session.post(DONATION_PUSH_PATH, donation)
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            if e.response.status_code == 409:
                sys.stderr.write(
                    f"Duplicate donation_import_id, ignoring this donation: {e.response.text}\n"
                )
            if e.response.status_code == 400:
                raise Exception(f"DonationPush failed: {e.response.text}: {e}")

            raise
