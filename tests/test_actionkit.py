import pytest

from actionkit import ActionKit, connect


# --- connect() ---------------------------------------------------------


def test_connect_requires_credentials(monkeypatch):
    for var in ["ACTIONKIT_USERNAME", "ACTIONKIT_PASSWORD", "ACTIONKIT_HOSTNAME"]:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(Exception, match="couldn't find login information"):
        connect()


def test_connect_uses_env_vars_when_kwargs_omitted(monkeypatch):
    monkeypatch.setenv("ACTIONKIT_USERNAME", "envuser")
    monkeypatch.setenv("ACTIONKIT_PASSWORD", "envpass")
    monkeypatch.setenv("ACTIONKIT_HOSTNAME", "env.example.com")
    connection = connect()
    assert connection.hostname == "env.example.com"
    assert connection.request_kwargs["auth"].username == "envuser"
    assert connection.request_kwargs["auth"].password == "envpass"


def test_connect_kwargs_take_precedence_over_env_vars(monkeypatch):
    monkeypatch.setenv("ACTIONKIT_USERNAME", "envuser")
    monkeypatch.setenv("ACTIONKIT_PASSWORD", "envpass")
    monkeypatch.setenv("ACTIONKIT_HOSTNAME", "env.example.com")
    connection = connect(hostname="explicit.example.com", username="u", password="p")
    assert connection.hostname == "explicit.example.com"
    assert connection.request_kwargs["auth"].username == "u"


# --- ActionKit wiring -------------------------------------------------


RESOURCE_ATTRS = [
    "Orders",
    "OrderRecurring",
    "DonationAction",
    "Groups",
    "Languages",
    "Lists",
    "Uploads",
    "Users",
    "UserFields",
    "Campaigns",
    "MultilingualCampaigns",
    "Petitions",
    "DonationPages",
    "RecurringPaymentPush",
    "ProfileCancelPush",
    "ProfileUpdatePush",
    "SQL",
    "Transactions",
    "SignupPages",
    "SignupActions",
    "GenericActions",
    "GenericPages",
]


@pytest.mark.parametrize("attr", RESOURCE_ATTRS)
def test_actionkit_wires_every_resource_attribute(ak, attr):
    resource = getattr(ak, attr)
    assert resource.connection is ak.connection


def test_actionkit_static_helpers_delegate_to_connection():
    class _FakeResponse:
        headers = {"Location": "https://example.com/rest/v1/thing/1/"}

    assert (
        ActionKit.get_resource_uri(_FakeResponse())
        == "https://example.com/rest/v1/thing/1/"
    )
    assert ActionKit.get_resource_uri_id("https://example.com/rest/v1/thing/1/") == "1"
    assert (
        ActionKit.get_resource_uri_id_from_response(_FakeResponse()) == "1"
    )
