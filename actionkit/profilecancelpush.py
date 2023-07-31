from .httpmethods import HttpMethods


class ProfileCancelPush(HttpMethods):
    resource_name = 'profilecancelpush'

    def push(
        self,
        order_id,
        canceled_by='processor',
        **kwargs,
    ):
        """
        https://action.wemove.eu/docs/manual/api/rest/donationpush.html#cancellations-of-existing-profiles

        Cancels an existing recurring payment profile connected to the given order_id
        """
        self.logger.debug(
            f'Cancelling recurring payment profile for order_id {order_id}'
        )
        return self.post(
            dict(
                order_id=order_id,
                canceled_by=canceled_by,
                **kwargs,
            )
        )
