import logging
import os

from .campaigns import Campaigns
from .connection import Connection
from .donationaction import DonationAction
from .donationpages import DonationPages
from .eventsignups import EventSignups
from .groups import Groups
from .languages import Languages
from .lists import Lists
from .multilingualcampaigns import MultilingualCampaigns
from .orderrecurring import OrderRecurring
from .orders import Orders
from .petitions import Petitions
from .profilecancelpush import ProfileCancelPush
from .profileupdatepush import ProfileUpdatePush
from .recurringpaymentpush import RecurringPaymentPush
from .signupactions import SignupActions
from .signuppages import SignupPages
from .sql import SQL
from .transactions import Transactions
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
        self.Groups = Groups(self.connection)
        self.Languages = Languages(self.connection)
        self.Lists = Lists(self.connection)
        self.Uploads = Uploads(self.connection)
        self.Users = Users(self.connection)
        self.Campaigns = Campaigns(self.connection)
        self.MultilingualCampaigns = MultilingualCampaigns(self.connection)
        self.Petitions = Petitions(self.connection)
        self.DonationPages = DonationPages(self.connection)
        self.RecurringPaymentPush = RecurringPaymentPush(self.connection)
        self.ProfileCancelPush = ProfileCancelPush(self.connection)
        self.ProfileUpdatePush = ProfileUpdatePush(self.connection)
        self.SQL = SQL(self.connection)
        self.Transactions = Transactions(self.connection)
        self.SignupPages = SignupPages(self.connection)
        self.SignupActions = SignupActions(self.connection)
        self.EventSignups = EventSignups(self.connection)

    @staticmethod
    def get_resource_uri(response):
        """
        Provides access to the underlying Connection class's get_resource_uri method
        """
        return Connection.get_resource_uri(response)

    @staticmethod
    def get_resource_uri_id(resource_uri):
        """
        Provides access to the underlying Connection class's get_resource_uri_id method
        """
        return Connection.get_resource_uri_id(resource_uri)

    @staticmethod
    def get_resource_uri_id_from_response(response):
        """
        Provides access to the underlying Connection class's get_resource_uri_id_from_response method
        """
        return Connection.get_resource_uri_id_from_response(response)
