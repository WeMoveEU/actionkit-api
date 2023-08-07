import sys
import uuid
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
        is_recurring: bool = False,
    ):
        """
        Creates a new donationpush action in ActionKit and returns the requests.Response object
        Set is_recurring to True to create a recurring payment profile

        https://action.wemove.eu/docs/manual/api/rest/donationpush.html
        """
        payload = dict(
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
        )
        if is_recurring:
            # https://action.wemove.eu/docs/manual/api/rest/donationpush.html#recurring-profiles
            payload['order'].update(
                dict(
                    recurring_id=str(uuid.uuid4()),
                    recurring_period='months',
                )
            )

        try:
            return self.connection.post("donationpush/", payload)
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
        resource_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
        admin_url: dict = None,
    ):
        """
        Sets the donation, order, and transaction status for an existing donationpush action

        If the action's status is already set to the given status, no update is performed. We only
        know this if not all the uris are passed in to the method. In that case we don't need to
        know the contents of the donationpush action data.

        Optionally takes a donationaction_data dict response from the successful creation of a
        donationaction, or alternatively you can specify the resource_uri by itself, or
        resource_uri, order_uri, and transaction_uri explicitly.

        Note that if you just specify the resource_uri, it will generate an additional request to
        look up the rest of the data from ActionKit.

        admin_url, if passed, will be used to update the action fields of the donationaction with a
        url which is a link to the payment provider admin page for the purchase.

        Returns the resource_uri of the donationpush action
        """
        if not donationaction_data:
            if resource_uri:
                if bool(order_uri) ^ bool(transaction_uri):
                    raise KeyError(
                        'If transaction_uri or order_uri is passed in addition to resource_uri, you '
                        'must specify all three'
                    )
                donationaction_data = self.get(resource_uri)
            else:
                raise KeyError(
                    'If donationaction_data is not passed, you must specify resource_uri'
                )
        elif resource_uri or order_uri or transaction_uri:
            raise KeyError('When passing donationaction_data, do not specify the uris')

        base_action_fields = {}

        if donationaction_data:
            uris = self.extract_resource_uris(donationaction_data=donationaction_data)
            resource_uri = uris['resource_uri']
            order_uri = uris['order_uri']
            transaction_uri = uris['transaction_uri']
            base_action_fields = donationaction_data.get('fields', {})

            # check to see if the status we want to set is already set
            if donationaction_data['order']['status'] == status:
                self.logger.debug(
                    f'Donationaction {resource_uri} already set to {status}. No update required'
                )
                return resource_uri
        try:
            self.logger.debug(
                f'Setting donationaction {resource_uri} status to {status}'
            )
            # Set the donation action in ActionKit to the given
            self.connection.patch(
                resource_uri,
                {
                    'status': status,
                },
            )
            # Set the corresponding order also to the given status
            self.connection.patch(
                order_uri,
                {
                    'status': status,
                },
            )
            # Set the corresponding transacion to the given status
            self.connection.patch(
                transaction_uri,
                {
                    'status': status,
                },
            )
            if base_action_fields and admin_url:
                # Update the action fields, preserving what was there before
                base_action_fields.update({'admin_url': admin_url})
                self.connection.patch(
                    resource_uri,
                    {
                        'fields': base_action_fields,
                    },
                )
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(
                    f'Failed to set donationaction status "{status}":\n{e.response.text}: {e}'
                )
            raise
        return resource_uri

    def set_push_status_incomplete(
        self,
        donationaction_data: dict = None,
        resource_uri: str = None,
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
            resource_uri,
            order_uri,
            transaction_uri,
        )

    def set_push_status_completed(
        self,
        donationaction_data: dict = None,
        resource_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
        admin_url: str = None,
    ):
        """
        Wrapper to set_push_status that sets the donation, order, and transaction status for an
        existing donationpush action to complete

        Returns the resource_uri of the donationpush action
        """
        return self.set_push_status(
            'completed',
            donationaction_data,
            resource_uri,
            order_uri,
            transaction_uri,
            admin_url,
        )

    def set_push_status_failed(
        self,
        donationaction_data: dict = None,
        resource_uri: str = None,
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
            resource_uri,
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

    def delete_donationaction(self, resource_uri: str):
        """
        Deletes a donationaction referenced by the resource_uri if the status is still "incomplete"
        """
        try:
            # Check to see if the donationaction exists
            data = self.get(resource_uri)
            # Only delete if the donationaction is incomplete
            if data['status'] == 'incomplete':
                self.connection.delete(resource_uri)
        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(
                    f'Failed to delete donationaction "{resource_uri}":\n{e.response.text}: {e}'
                )
            elif e.response.status_code == 404:
                self.connection.logger.warning(
                    f'Donationaction {resource_uri} not found. Skipping delete.\n'
                )
                return False
        return True

    def delete_donationaction_by_resource_id(self, resource_id):
        """
        Deletes a donationaction referenced by the resource_id if it exists
        """
        if resource_id:
            resource_uri = self.get_resource_uri_from_id(resource_id)
            if resource_uri:
                # Delete the referenced donation action in ActionKit
                self.delete_donationaction(resource_uri)

    def set_push_status_by_resource_id(self, resource_id, status):
        """
        Convenience method to set the status of a donationaction referenced by the resource_id
        """
        resource_uri = self.get_resource_uri_from_id(resource_id)
        self.set_push_status(status, resource_uri=resource_uri)

    def set_push_status_incomplete_by_resource_id(self, resource_id):
        """
        Convenience method to set the status of a donationaction referenced by the resource_id to
        incomplete
        """
        self.set_push_status_by_resource_id(resource_id, 'incomplete')

    def extract_resource_uris(self, resource_uri=None, donationaction_data=None):
        """
        Extracts all relevant resource uris from a donationaction record.

        If resource_uri is passed, the donationaction data will be retrieved from
        the ActionKit API. Otherwise, the donationaction_data dict can be passed directly.
        """
        # Check that at least one of the two arguments is passed
        if not (resource_uri or donationaction_data):
            raise KeyError('Must specify either resource_uri or donationaction_data')

        if not donationaction_data:
            donationaction_data = self.get(resource_uri)

        return dict(
            resource_uri=donationaction_data['resource_uri'],
            order_uri=donationaction_data['order']['resource_uri'],
            transaction_uri=donationaction_data['order']['transactions'][0],
        )
