from datetime import datetime
from decimal import Decimal

from .httpmethods import HttpMethods
from .validation import convert_datetime_to_utc, validate_datetime_is_timezone_aware


class ProfileUpdatePush(HttpMethods):
    resource_name = 'profileupdatepush'

    def push(
        self,
        order_id: str,
        amount: Decimal,
        currency: str,  # actionkit defaults to USD if currency is not provided
        trans_id: str = None,
        created_at: datetime = None,
        **kwargs,
    ):
        """
        https://action.wemove.eu/docs/manual/api/rest/donationpush.html#updates-to-existing-profiles

        Updates an existing recurring payment profile connected to the given order_id
        """
        payload = dict(
            order_id=order_id,
            amount=str(amount),
            currency=currency.upper(),
            trans_id=trans_id,
            **kwargs,
        )

        # Validate and convert datetime as necessary
        if created_at:
            validate_datetime_is_timezone_aware(created_at)
            payload['created_at'] = convert_datetime_to_utc(created_at)

        self.logger.debug(f'Updating recurring payment profile for order_id {order_id}')
        return self.post(payload)
