from unittest import TestCase
from unittest.mock import patch

from tilapia.lib.basic import cipher


class TestCipher(TestCase):
    @patch("tilapia.lib.basic.cipher.os")
    def test_encrypt(self, fake_os):
        fake_os.urandom.return_value = bytes.fromhex("00000000000000000000000000000001")
        self.assertEqual("AAAAAAAAAAAAAAAAAAAAAZgN8KLZ7sJmofSYXYqIcb0=", cipher.encrypt("123", "Hello OneKey"))
        fake_os.urandom.assert_called_once()

    def test_decrypt(self):
        self.assertEqual("Hello OneKey", cipher.decrypt("123", "AAAAAAAAAAAAAAAAAAAAAZgN8KLZ7sJmofSYXYqIcb0="))

        with self.assertRaises(cipher.InvalidPassword):
            cipher.decrypt("12", "AAAAAAAAAAAAAAAAAAAAAZgN8KLZ7sJmofSYXYqIcb0=")
