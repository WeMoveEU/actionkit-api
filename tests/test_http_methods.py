
import unittest
import actionkit

from unittest.mock import patch


class HttpMethodsTest(unittest.TestCase):

    def test_complete_path(self):
        with patch('actionkit.Connection') as mocked:
            ak = actionkit.ActionKit("example.com", "user", "password")
            ak.DonationAction.get("1")
            mocked.return_value.get.assert_called_with("donationaction/1/", params={})

            ak.DonationAction.get("/donationaction/1/")
            mocked.return_value.get.assert_called_with("/donationaction/1/", params={})


    def test_request_uri(self):
        with patch('requests.get') as request:
            ak = actionkit.ActionKit("example.com", "user", "password")
            for args in (["1"], ["donationaction/1/"], ["/donationaction/1/"], ["donationaction/1"]):
                ak.DonationAction.get(*args)

                request.assert_called()
                uri = request.call_args[0][0]
                self.assertRegex(uri, "https://example.com/rest/v1/donationaction/1/?", f"Testing {args}")