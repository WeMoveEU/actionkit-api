from datetime import datetime

from .httpmethods import HttpMethods


def datetime_to_stripped_isoformat(dt: datetime) -> str:
    """
    ActionKit does not support the timezone-aware part of the ISO 8601 standard when it comes to
    expressing datetimes for this endpoint. A big has been filed with ActionKit to fix this.

    In the meantime, this function strips away the timezone info at the end if present. This allows
    the datetime expression to pass for recurringpaymentpush requests.
    """
    iso_datetime = dt.isoformat()
    tokens = iso_datetime.split('+')
    return tokens[0] if len(tokens) > 1 else iso_datetime


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
        self.logger.debug(f'Pushing recurring payment for order_id {order_id}')

        return self.post(
            dict(
                order_id=order_id,
                success=success,
                status=status,
                failure_code=failure_code,
                failure_message=failure_message,
                failure_description=failure_description,
                trans_id=trans_id,
                created_at=(
                    datetime_to_stripped_isoformat(created_at) if created_at else None
                ),
                **kwargs,
            )
        )
