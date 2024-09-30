import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from requests import HTTPError

from .httpmethods import HttpMethods


class DonationAction(HttpMethods):
    resource_name = 'donationaction'

    def push(
        self,
        email: str = None,
        first_name: str = None,
        last_name: str = None,
        country: str = None,
        postal: str = None,
        amount: Decimal = None,
        currency: str = None,
        page: str = None,
        payment_account: str = None,
        custom_action_fields: dict = {},
        recurring_id: str = None,
        created_at: datetime = None,
        skip_confirmation: bool = False,
        akid: str = None,
        trans_id: str = None,
    ):
        """
        Creates a new donationpush action in ActionKit and returns the requests.Response object
        If recurring_id is set then the donation will be set to recurring and the recurring_id will
        be set in ActionKit accordingly.

        https://action.wemove.eu/docs/manual/api/rest/donationpush.html
        """
        for required in [
            'email',
            'country',
            'postal',
            'amount',
            'currency',
            'page',
            'payment_account',
        ]:
            if not locals()[required]:
                raise ValueError(f'{required} must be provided')

        order = dict(
            card_num='4111111111111111',
            card_code='007',
            amount=str(amount),
            currency=currency,
            exp_date_month='12',
            exp_date_year='9999',
            payment_account=payment_account,
            trans_id=trans_id,
        )

        if created_at:
            # Set order created_at key to a serializable string in UTC format
            order['created_at'] = created_at.astimezone(tz=timezone.utc).isoformat()

        payload = dict(
            order=order,
            user=dict(
                email=email,
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
        )

        # Define action info if needed
        action = {}
        if custom_action_fields:
            action['fields'] = custom_action_fields
        if skip_confirmation:
            action['skip_confirmation'] = '1'
        if action:
            payload['action'] = action

        if recurring_id:
            # https://action.wemove.eu/docs/manual/api/rest/donationpush.html#recurring-profiles
            payload['order'].update(
                dict(
                    recurring_id=recurring_id,
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
        first_name: str,
        last_name: str,
        country: str,
        postal: str,
        amount: Decimal,
        currency: str,
        page: str,
        payment_account: str,
        custom_action_fields: dict = {},
        is_recurring: bool = False,
        created_at: datetime = None,
        skip_confirmation: bool = False,
        akid: str = None,
    ):
        """
        Convenience method that creates a new donation action then sets it to incomplete

        Returns the resource_uri of the created donationpush action
        """
        response = self.push(
            email,
            first_name,
            last_name,
            country,
            postal,
            amount,
            currency,
            page,
            payment_account,
            custom_action_fields,
            is_recurring,
            created_at,
            skip_confirmation,
            akid,
        )
        action = response.json()
        # TODO: Do this async?
        self.set_push_status_incomplete(action)
        return action['resource_uri']

    def push_and_set_pending(
        self,
        email: str,
        first_name: str,
        last_name: str,
        country: str,
        postal: str,
        amount: Decimal,
        currency: str,
        page: str,
        payment_account: str,
        custom_action_fields: dict = {},
        is_recurring: bool = False,
        created_at: datetime = None,
        skip_confirmation: bool = False,
        akid: str = None,
    ):
        """
        Convenience method that creates a new donation action then sets it to pending.
        Returns the response from the creation of the donationpush action
        """
        response = self.push(
            email,
            first_name,
            last_name,
            country,
            postal,
            amount,
            currency,
            page,
            payment_account,
            custom_action_fields,
            is_recurring,
            created_at,
            skip_confirmation,
            akid,
        )
        action = response.json()
        self.set_push_status_pending(action)
        return action

    def set_push_status(
        self,
        action_status,
        donationaction_data: dict = None,
        resource_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
        custom_action_fields: dict = None,
        created_at: datetime = None,
        no_action_if_status_is_already_set: bool = False,
        recurring_id: str = None,
        order_status: str = None,
        transaction_status: str = None,
        **kwargs,
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

        custom_action_fields, if passed, will be used to update the action fields with the content of the
        current dictionary

        created_at, if passed indicates the time the payment or event occurred

        no_action_if_status_is_already_set, if True, will result in this method not making any
        requests if status is already the same as what was passed in

        kwargs can be one of:
        trans_id: The payment provider's transaction id. Typically a subscription or single payment id
        failure_message: The payment provider's failure reason, if any
        failure_description: The payment provider's failure description, if any

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
            orderrecurring_uris = uris['orderrecurring_uris']
            base_action_fields = donationaction_data.get('fields', {})

        if (
            no_action_if_status_is_already_set
            and donationaction_data['status'] == action_status
        ):
            self.logger.debug(
                f'donationaction status is already {action_status}. Skipping update.'
            )
            return resource_uri

        try:
            self.logger.debug(
                f'Setting donationaction {resource_uri} status to {action_status}'
            )
            action_payload = {'status': action_status}

            # Set the donation action in ActionKit to the given status
            self.connection.patch(resource_uri, action_payload)

            # Set the corresponding order also to the given status
            order_payload = action_payload.copy()
            order_payload['status'] = order_status or action_status

            if created_at:
                # fmt: off
                order_payload['created_at'] = created_at.astimezone(tz=timezone.utc).isoformat()
                # fmt: on

            self.connection.patch(order_uri, order_payload)

            # Set the corresponding transaction to the given status, adding the merchant trans_id
            # if it is passed in
            transaction_payload = action_payload.copy()
            transaction_payload['status'] = transaction_status or action_status

            for key in ['failure_message', 'failure_description', 'trans_id']:
                if key in kwargs and kwargs[key] is not None:
                    transaction_payload[key] = kwargs[key]
            self.connection.patch(transaction_uri, transaction_payload)

            # Update the action fields if they are passed in
            if custom_action_fields:
                # Update the action fields, preserving what was there before
                base_action_fields.update(custom_action_fields)
                self.connection.patch(
                    resource_uri,
                    {
                        'fields': base_action_fields,
                    },
                )

            # Set the recurring_id if it is passed in
            if recurring_id and orderrecurring_uris:
                # We only set this when the donation is new so we can just reference the first
                # orderrecurring uri for the update
                self.connection.patch(
                    orderrecurring_uris[0],
                    {
                        'recurring_id': recurring_id,
                        'recurring_period': 'months',
                    },
                )

        except HTTPError as e:
            if e.response.status_code == 400:
                raise Exception(
                    f'Failed to set donationaction status "{action_status}":\n{e.response.text}: {e}'
                )
            raise
        return resource_uri

    def set_push_status_incomplete(
        self,
        donationaction_data: dict = None,
        resource_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
        custom_action_fields: dict = None,
        trans_id: str = None,
        created_at: datetime = None,
        recurring_id: str = None,
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
            custom_action_fields,
            trans_id=trans_id,
            created_at=created_at,
            recurring_id=recurring_id,
        )

    def set_push_status_completed(
        self,
        donationaction_data: dict = None,
        resource_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
        custom_action_fields: dict = None,
        trans_id: str = None,
        created_at: datetime = None,
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
            custom_action_fields,
            trans_id=trans_id,
            created_at=created_at,
            # Ensure no changes are made if the status is already set to completed
            no_action_if_status_is_already_set=True,
        )

    def set_push_status_failed(
        self,
        donationaction_data: dict = None,
        resource_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
        custom_action_fields: dict = None,
        trans_id: str = None,
        failure_message: str = None,
        failure_description: str = None,
        created_at: datetime = None,
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
            custom_action_fields,
            trans_id=trans_id,
            failure_message=failure_message,
            failure_description=failure_description,
            created_at=created_at,
        )

    def set_push_status_pending(
        self,
        donationaction_data: dict = None,
        resource_uri: str = None,
        order_uri: str = None,
        transaction_uri: str = None,
        custom_action_fields: dict = None,
        trans_id: str = None,
        created_at: datetime = None,
        recurring_id: str = None,
    ):
        """
        Wrapper to set_push_status that sets the donation action to incomplete, and the order and
        transaction status to pending

        Returns the resource_uri of the donationpush action
        """
        return self.set_push_status(
            'incomplete',
            donationaction_data,
            resource_uri,
            order_uri,
            transaction_uri,
            custom_action_fields,
            trans_id=trans_id,
            created_at=created_at,
            recurring_id=recurring_id,
            order_status='pending',
            transaction_status='pending',
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
            orderrecurring_uris=donationaction_data['order']['orderrecurrings'],
        )
