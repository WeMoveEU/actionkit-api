from datetime import datetime

from .httpmethods import HttpMethods
from .utils import convert_datetime_to_utc, datetime_to_stripped_isoformat
from .validation import validate_datetime_is_timezone_aware


class RecurringPaymentPush(HttpMethods):
    resource_name = 'recurringpaymentpush'

    def push(
        self,
        order_id,
        success=True,
        status='completed',
        failure_code=None,
        failure_message=None,
        failure_description=None,
        trans_id=None,
        created_at: datetime = None,
        **kwargs,
    ):
        """
        https://action.wemove.eu/docs/manual/api/rest/donationpush.html#recurring-payments-and-attempts

        Registers a recurring payment connected to the given order_id
        """
        payload = dict(
            order_id=order_id,
            success=success,
            status=status,
            failure_code=failure_code,
            failure_message=failure_message,
            failure_description=failure_description,
            trans_id=trans_id,
            **kwargs,
        )

        # Validate and convert datetime as necessary
        if created_at:
            validate_datetime_is_timezone_aware(created_at)
            # TODO: Remove datetime_to_stripped_isoformat wrapper function once ActionKit fixes the bug
            payload['created_at'] = datetime_to_stripped_isoformat(
                convert_datetime_to_utc(created_at)
            )

        self.logger.debug(f'Pushing recurring payment for order_id {order_id}')

        return self.post(payload)
