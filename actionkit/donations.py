import sys

from requests import HTTPError
from .httpmethods import HttpMethods


class DonationPush(HttpMethods):
    def __init__(self, connection):
        self.connection = connection
        self.base_path = "donationpush/"

    def push(self, donation):
        try:
            return self.connection.post("donationpush/", donation)
        except HTTPError as e:
            if e.response.status_code == 409:
                sys.stderr.write(
                    f"Duplicate donation_import_id, ignoring this donation: {e.response.text}\n"
                )
                return
            if e.response.status_code == 400:
                raise Exception(f"DonationPush failed: {e.response.text}: {e}")

            raise

    def cancel_recurring_profile(self, recurring_id, canceled_by):
        return self.connection.post(
            "profilecancelpush/",
            {"recurring_id": recurring_id, "canceled_by": canceled_by},
        )

    def add_recurring_payment(self, payment):
        return self.connection.post("recurringpaymentpush/", payment)
