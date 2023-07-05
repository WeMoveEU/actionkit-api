import logging
import os
import re

from .connection import Connection
from .donationaction import DonationAction
from .donations import DonationPush
from .groups import Groups
from .languages import Languages
from .lists import Lists
from .orderrecurring import OrderRecurring
from .orders import Orders
from .petitions import Petitions
from .uploads import Uploads
from .users import Users


def connect(hostname=None, username=None, password=None, **kwargs):
    if not username:
        username = os.environ.get("ACTIONKIT_USERNAME")
    if not password:
        password = os.environ.get("ACTIONKIT_PASSWORD")
    if not hostname:
        hostname = os.environ.get("ACTIONKIT_HOSTNAME")

    if not (username and password and hostname):
        raise Exception(
            "Oops, I couldn't find login information for ActionKit - "
            " set ENV ACTIONKIT_USERNAME, ACTIONKIT_PASSWORD, ACTIONKIT_HOSTNAME "
            "or pass parameters to connect()"
        )
    return Connection(
        hostname,
        username,
        password,
        logger=kwargs.get('logger', logging.getLogger(__name__)),
    )


class ActionKit:
    def __init__(self, *args, **kwargs):
        self.connection = connect(*args, **kwargs)

        self.Orders = Orders(self.connection)
        self.OrderRecurring = OrderRecurring(self.connection)
        self.DonationAction = DonationAction(self.connection)
        self.DonationPush = DonationPush(self.connection)
        self.Groups = Groups(self.connection)
        self.Languages = Languages(self.connection)
        self.Lists = Lists(self.connection)
        self.Uploads = Uploads(self.connection)
        self.Users = Users(self.connection)
        self.Petitions = Petitions(self.connection)
