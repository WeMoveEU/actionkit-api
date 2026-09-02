import pytest

from actionkit import ActionKit
from actionkit.connection import Connection

HOSTNAME = "example.com"
USERNAME = "user"
PASSWORD = "password"


@pytest.fixture
def base_url():
    return f"https://{HOSTNAME}"


@pytest.fixture
def connection():
    return Connection(HOSTNAME, USERNAME, PASSWORD)


@pytest.fixture
def ak():
    return ActionKit(HOSTNAME, USERNAME, PASSWORD)
