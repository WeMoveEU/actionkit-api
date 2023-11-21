from datetime import datetime

from .httpmethods import HttpMethods


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
                created_at=created_at.isoformat() if created_at else None,
                **kwargs,
            )
        )
