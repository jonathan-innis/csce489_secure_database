import unittest
from principal import Principal

class TestPasswordAuthentication(unittest.TestCase):

    def test_valid_password(self):
        p = Principal("test", "password")
        self.assertEqual(True, p.authenticate("password"))
    
    def test_invalid_password(self):
        p = Principal("test", "password")
        self.assertEqual(False, p.authenticate("pas$word"))

    def test_prefix_password(self):
        p = Principal("test", "password")
        self.assertEqual(False, p.authenticate("password123"))

    def test_postfix_password(self):
        p = Principal("test", "password")
        self.assertEqual(False, p.authenticate("thisismypassword"))


if __name__ == "__main__":
    unittest.main()