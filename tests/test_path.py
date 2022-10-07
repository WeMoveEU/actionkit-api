import unittest
import actionkit


class BaseUrlTest(unittest.TestCase):
    def setUp(self):
        self.ak = actionkit.ActionKit("example.com", "user", "password").connection

    def test_absolute_path(self):

        self.assertEquals(
            self.ak._path("/a/b/c/"), "https://example.com/rest/v1/a/b/c/"
        )

    def test_api_path(self):
        ak = actionkit.ActionKit("example.com", "user", "password")
        self.assertEquals(
            self.ak._path("/rest/v1/b/c/"), "https://example.com/rest/v1/b/c/"
        )

    def test_absolute_url(self):
        ak = actionkit.ActionKit("example.com", "user", "password")
        self.assertEquals(
            self.ak._path("https://example.com/i/am/complete"),
            "https://example.com/i/am/complete",
        )
