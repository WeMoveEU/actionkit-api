import sys

from requests import HTTPError

from .httpmethods import HttpMethods


class DonationAction(HttpMethods):
    resource_name = 'donationaction'

    def __init__(self, connection):
        self.connection = connection

    def push(self, donation: dict):
        """
        Creates a new donationpush action in ActionKit and returns the requests.Response object
        """
        try:
            return self.connection.post("donationpush/", donation)
        except HTTPError as e:
            if e.response.status_code == 409:
                sys.stderr.write(
                    f"Duplicate donation_import_id. Can't create this donation: {e.response.text}\n"
                )
                return
            if e.response.status_code == 400:
                raise Exception(
                    f'Creation of donationaction failure:\n{e.response.text}: {e}'
                )
            raise

    def push_and_set_incomplete(self, donation: dict):
        """
        Convenience method that creates a new donation action then sets it to incomplete

        Returns the resource_uri of the created donationpush action
        """
        response = self.push(donation)
        data = response.json()
        # TODO: Do this async?
        self.set_push_status_incomplete(data)
        return data['resource_uri']

    def set_push_status(
        self,
        status,
        donationaction_data: dict = None,
        donationaction_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
    ):
        """
        Sets the donation, order, and transaction status for an existing donationpush action

        Optionally takes a donationaction_data dict response from the successful creation of a
        donationaction, or alternatively you can specify the donationaction_uri, order_uri, and
        transaction_uri explicitly

        Returns the resource_uri of the donationpush action
        """
        if donationaction_data:
            donationaction_uri = donationaction_data['resource_uri']
            order_uri = donationaction_data['order']['resource_uri']
            transaction_uri = donationaction_data['order']['transactions'][0]
        else:
            if not (donationaction_uri and order_uri and transaction_uri):
                raise KeyError('Must specify donationaction_data or all three uris')
        try:
            # Set the donation action in ActionKit to incomplete
            self.connection.patch(
                donationaction_uri,
                {
                    'status': status,
                },
            )
            # Set the corresponding order also to incomplete status
            self.connection.patch(
                order_uri,
                {
                    'status': status,
                },
            )
            # Set the corresponding transacion to incomplete status
            self.connection.patch(
                transaction_uri,
                {
                    'status': status,
                },
            )
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(
                    f'Failed to set donationaction status "{status}":\n{e.response.text}: {e}'
                )
            raise
        return donationaction_data['resource_uri']

    def set_push_status_incomplete(
        self,
        donationaction_data: dict = None,
        donationaction_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
    ):
        """
        Wrapper to set_push_status that sets the donation, order, and transaction status for an
        existing donationpush action to incomplete

        Returns the resource_uri of the donationpush action
        """
        return self.set_push_status(
            'incomplete',
            donationaction_data,
            donationaction_uri,
            order_uri,
            transaction_uri,
        )

    def set_push_status_complete(
        self,
        donationaction_data: dict = None,
        donationaction_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
    ):
        """
        Wrapper to set_push_status that sets the donation, order, and transaction status for an
        existing donationpush action to complete

        Returns the resource_uri of the donationpush action
        """
        return self.set_push_status(
            'complete',
            donationaction_data,
            donationaction_uri,
            order_uri,
            transaction_uri,
        )

    def set_push_status_failed(
        self,
        donationaction_data: dict = None,
        donationaction_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
    ):
        """
        Wrapper to set_push_status that sets the donation, order, and transaction status for an
        existing donationpush action to failed

        Returns the resource_uri of the donationpush action
        """
        return self.set_push_status(
            'failed',
            donationaction_data,
            donationaction_uri,
            order_uri,
            transaction_uri,
        )

    def cancel_recurring_profile(self, recurring_id, canceled_by):
        return self.connection.post(
            "profilecancelpush/",
            {"recurring_id": recurring_id, "canceled_by": canceled_by},
        )

    def add_recurring_payment(self, payment):
        return self.connection.post("recurringpaymentpush/", payment)

    def delete_donationaction(self, donationaction_uri: str):
        try:
            # Check to see if the donationaction exists
            response = self.connection.get(donationaction_uri)
            data = response.json()
            # Only delete if the donationaction is incomplete
            if data['status'] == 'incomplete':
                self.connection.delete(donationaction_uri)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(
                    f'Failed to delete donationaction "{donationaction_uri}":\n{e.response.text}: {e}'
                )
            elif e.response.status_code == 404:
                self.connection.logger.info(
                    f'Donationaction {donationaction_uri} not found. Skipping delete.\n'
                )
                return False
        return True

    def get_resource_uri_from_id(self, resource_id):
        """
        Utility method to convert a given resource id to the ActionKit resource_uri
        """
        return self.connection.get_resource_uri_from_id(resource_id, self.resource_name)
