from decimal import Decimal
from os import path

from requests import HTTPError

from .httpmethods import HttpMethods
from .orders import Orders
from .validation import ValidationError

TRANSACTION_TYPES = ['sale', 'refund', 'credit']


class Transactions(HttpMethods):
    resource_name = 'transaction'

    def reverse(self, transaction_uri: str = None, transaction_id: str = None):
        """
        Reverse a transaction
        """
        if not (transaction_id or transaction_uri):
            raise ValueError(
                'Either transaction_id or transaction_uri must be provided'
            )

        # fmt: off
        transaction_uri = transaction_uri or self.get_resource_uri_from_id(transaction_id)
        # fmt: on
        reversal_uri = path.join(transaction_uri, 'reverse')

        try:
            return self.connection.post(reversal_uri)
        except HTTPError as e:
            if e.response.status_code == 400:
                error_json = e.response.json()
                order_id_message = error_json.get('order_id', None)
                if order_id_message == 'Transaction has already been reversed.':
                    self.connection.logger.warning(
                        f'Transaction {transaction_id} already reversed'
                    )
                else:
                    raise e
            elif e.response.status_code == 404:
                self.connection.logger.warning(
                    f'Reversal not possible. Transaction {transaction_uri} was not found'
                )
            else:
                raise e
        except ValidationError as e:
            # Since the underlying http code can now raise a ValidationError, we need to catch it
            # here in case it's flagging an already reversed transaction
            order_id_message = e.errors
            if order_id_message == 'Transaction has already been reversed.':
                self.connection.logger.warning(
                    f'Transaction {transaction_id} already reversed'
                )
            else:
                raise e
        return None

    def create(
        self,
        account: str,
        amount: Decimal,
        currency: str,
        order_uri: str = None,
        order_id: str = None,
        type: str = 'sale',
    ):
        """
        Create a new transaction and associate it with an order
        {
            'account': 'WM-Card',
            'amount': '5.00',
            'amount_converted': '5.47',
            'created_at': '2024-01-15T16:21:29.930080',
            'currency': 'EUR',
            'failure_code': '',
            'failure_description': '',
            'failure_message': '',
            'id': 881294,
            'order': /rest/v1/order/293978/,
            'resource_uri': /rest/v1/transaction/881294/,
            'status': 'reversed',
            'success': True,
            'test_mode': False,
            'trans_id': 'pi_3OYsulLEJyfuWvBB1rHuqTzN',
            'type': 'sale',
            'updated_at': '2024-01-15T18:14:40.756863'
        }
        """
        if not (order_uri or order_id):
            raise ValueError('Either order_uri or order_id must be provided')

        if not type in TRANSACTION_TYPES:
            raise ValueError('Transaction type must be one of sale, refund, or credit')

        order_uri = order_uri or Orders.get_resource_uri_from_id(order_id)

        payload = dict(
            account=account,
            amount=str(amount),
            currency=currency,
            type=type,
            order=order_uri,
        )

        return self.post(json=payload)
