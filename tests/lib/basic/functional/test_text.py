import datetime
import decimal
from unittest import TestCase

from wallet.lib.basic.functional.text import force_bytes, force_text


class TestText(TestCase):
    def test_force_text(self):
        mock_datetime = datetime.datetime.utcfromtimestamp(1600000000)

        with self.subTest("with strings_only is False as default"):
            self.assertEqual(
                ["None", "1", "1.1", "1.13", "z", "zb", "2020-09-13 12:26:40", "2020-09-13", "12:26:40"],
                [
                    force_text(None),
                    force_text(1),
                    force_text(1.1),
                    force_text(decimal.Decimal("1.13")),
                    force_text("z"),
                    force_text(b"zb"),
                    force_text(mock_datetime),
                    force_text(datetime.datetime.date(mock_datetime)),
                    force_text(datetime.datetime.time(mock_datetime)),
                ],
            )

        with self.subTest("with strings_only is True"):
            self.assertEqual(
                [
                    None,
                    1,
                    1.1,
                    decimal.Decimal("1.13"),
                    "z",
                    "zb",
                    mock_datetime,
                    datetime.datetime.date(mock_datetime),
                    datetime.datetime.time(mock_datetime),
                ],
                [
                    force_text(None, strings_only=True),
                    force_text(1, strings_only=True),
                    force_text(1.1, strings_only=True),
                    force_text(decimal.Decimal("1.13"), strings_only=True),
                    force_text("z", strings_only=True),
                    force_text(b"zb", strings_only=True),
                    force_text(mock_datetime, strings_only=True),
                    force_text(datetime.datetime.date(mock_datetime), strings_only=True),
                    force_text(datetime.datetime.time(mock_datetime), strings_only=True),
                ],
            )

        with self.subTest("decode invalid unicode bytes"):
            with self.assertRaisesRegex(UnicodeDecodeError, "invalid start byte"):
                force_text(bytes.fromhex("adadad"))

    def test_force_bytes(self):
        mock_datetime = datetime.datetime.utcfromtimestamp(1600000000)

        with self.subTest("with strings_only is False as default"):
            self.assertEqual(
                [
                    b"None",
                    b"1",
                    b"1.1",
                    b"1.13",
                    b"z",
                    b"zb",
                    b"2020-09-13 12:26:40",
                    b"2020-09-13",
                    b"12:26:40",
                ],
                [
                    force_bytes(None),
                    force_bytes(1),
                    force_bytes(1.1),
                    force_bytes(decimal.Decimal("1.13")),
                    force_bytes("z"),
                    force_bytes(b"zb"),
                    force_bytes(mock_datetime),
                    force_bytes(datetime.datetime.date(mock_datetime)),
                    force_bytes(datetime.datetime.time(mock_datetime)),
                ],
            )

        with self.subTest("with strings_only is True"):
            self.assertEqual(
                [
                    None,
                    1,
                    1.1,
                    decimal.Decimal("1.13"),
                    b"z",
                    b"zb",
                    mock_datetime,
                    datetime.datetime.date(mock_datetime),
                    datetime.datetime.time(mock_datetime),
                ],
                [
                    force_bytes(None, strings_only=True),
                    force_bytes(1, strings_only=True),
                    force_bytes(1.1, strings_only=True),
                    force_bytes(decimal.Decimal("1.13"), strings_only=True),
                    force_bytes("z", strings_only=True),
                    force_bytes(b"zb", strings_only=True),
                    force_bytes(mock_datetime, strings_only=True),
                    force_bytes(datetime.datetime.date(mock_datetime), strings_only=True),
                    force_bytes(datetime.datetime.time(mock_datetime), strings_only=True),
                ],
            )
