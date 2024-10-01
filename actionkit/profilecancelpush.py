from datetime import datetime

from .httpmethods import HttpMethods
from .utils import convert_datetime_to_utc, datetime_to_stripped_isoformat
from .validation import validate_datetime_is_timezone_aware


class ProfileCancelPush(HttpMethods):
    resource_name = 'profilecancelpush'

    def push(
        self,
        canceled_by='processor',
        created_at: datetime = None,
        **kwargs,
    ):
        """
        https://action.wemove.eu/docs/manual/api/rest/donationpush.html#cancellations-of-existing-profiles

        Cancels an existing recurring payment profile connected to the given order_id or recurring_id
        """
        order_id = kwargs.get('order_id', None)
        recurring_id = kwargs.get('recurring_id', None)

        if not (recurring_id or order_id):
            raise ValueError('Either recurring_id or order_id must be provided')

        payload = dict(
            canceled_by=canceled_by,
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
            f'Cancelling recurring payment profile for id {order_id or recurring_id}'
        )
        return self.post(payload)
