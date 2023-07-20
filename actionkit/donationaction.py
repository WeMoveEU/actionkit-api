import sys
from decimal import Decimal

from requests import HTTPError

from .httpmethods import HttpMethods


class DonationAction(HttpMethods):
    resource_name = 'donationaction'

    def push(
        self,
        email: str,
        akid: str,
        first_name: str,
        last_name: str,
        country: str,
        postal: str,
        amount: Decimal,
        currency: str,
        page: str,
        payment_account: str,
        action_fields: dict,
    ):
        """
        Creates a new donationpush action in ActionKit and returns the requests.Response object
        """
        try:
            return self.connection.post(
                "donationpush/",
                dict(
                    order=dict(
                        card_num='4111111111111111',
                        card_code='007',
                        amount=str(amount),
                        currency=currency,
                        exp_date_month='12',
                        exp_date_year='9999',
                        payment_account=payment_account,
                    ),
                    user=dict(
                        # Only supply actionkit with the email if the akid is not passed in
                        email=email if not akid else None,
                        akid=akid,
                        first_name=first_name,
                        last_name=last_name,
                        address1=None,
                        region=None,
                        city=None,
                        state=None,
                        country=country,
                        postal=postal if country != 'US' else None,
                        zip=postal if country == 'US' else None,
                    ),
                    donationpage=dict(name=page),
                    action=dict(
                        fields=action_fields,
                    ),
                ),
            )
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

    def push_and_set_incomplete(
        self,
        email: str,
        akid: str,
        first_name: str,
        last_name: str,
        country: str,
        postal: str,
        amount: Decimal,
        currency: str,
        page: str,
        payment_account: str,
        action_fields: dict,
    ):
        """
        Convenience method that creates a new donation action then sets it to incomplete

        Returns the resource_uri of the created donationpush action
        """
        response = self.push(
            email,
            akid,
            first_name,
            last_name,
            country,
            postal,
            amount,
            currency,
            page,
            payment_account,
            action_fields,
        )
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
            data = self.get(donationaction_uri)
            # Only delete if the donationaction is incomplete
            if data['status'] == 'incomplete':
                self.connection.delete(donationaction_uri)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(
                    f'Failed to delete donationaction "{donationaction_uri}":\n{e.response.text}: {e}'
                )
            elif e.response.status_code == 404:
                self.connection.logger.warning(
                    f'Donationaction {donationaction_uri} not found. Skipping delete.\n'
                )
                return False
        return True
