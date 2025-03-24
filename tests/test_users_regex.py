
import unittest
import actionkit


class BaseUrlTest(unittest.TestCase):
    def setUp(self):
        self.ak = actionkit.ActionKit("example.com", "user", "password")

    def test_user_id_check(self):
        self.assertEqual(self.ak.Users.id("/user/1"), "1")
        self.assertEqual(self.ak.Users.id("/user/11/"), "11")

        with self.assertRaises(Exception):
            self.ak.Users.id("/user/asdf")



