from datetime import datetime
from decimal import Decimal

from .httpmethods import HttpMethods
from .utils import convert_datetime_to_utc, datetime_to_stripped_isoformat
from .validation import validate_datetime_is_timezone_aware


class ProfileUpdatePush(HttpMethods):
    resource_name = 'profileupdatepush'

    def push(
        self,
        amount: Decimal,
        currency: str,  # actionkit defaults to USD if currency is not provided
        trans_id: str = None,
        created_at: datetime = None,
        **kwargs,
    ):
        """
        https://action.wemove.eu/docs/manual/api/rest/donationpush.html#updates-to-existing-profiles

        Updates an existing recurring payment profile connected to the given order_id or recurring_id
        """
        order_id = kwargs.get('order_id', None)
        recurring_id = kwargs.get('recurring_id', None)

        if not (recurring_id or order_id):
            raise ValueError('Either recurring_id or order_id must be provided')

        payload = dict(
            amount=str(amount),
            currency=currency.upper(),
            trans_id=trans_id,
            **kwargs,
        )

        # Validate and convert datetime as necessary
        if created_at:
            validate_datetime_is_timezone_aware(created_at)
            # TODO: Replace the below line with this commented out one once ActionKit fixes the bug
            # payload['created_at'] = convert_datetime_to_utc(created_at).isoformat()
            payload['created_at'] = datetime_to_stripped_isoformat(
                convert_datetime_to_utc(created_at)
            )

        self.logger.debug(
            f'Updating recurring payment profile for id {order_id or recurring_id}'
        )
        return self.post(payload)
