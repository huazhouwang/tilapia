import decimal
from dataclasses import dataclass
from unittest import TestCase

from tilapia.lib.basic.dataclass.dataclass import DataClassMixin


@dataclass
class Person(DataClassMixin):
    name: str
    age: int
    height: decimal.Decimal
    desc: str = None


class TestDataClassMixin(TestCase):
    def setUp(self) -> None:
        self.joe = Person(name="joe", age=18, height=decimal.Decimal("178.3"), desc="boring")

    def test_clone(self):
        dev = Person(name="dev", age=18, height=decimal.Decimal("173.8"))
        self.assertEqual(self.joe, self.joe.clone())
        self.assertEqual(dev, self.joe.clone(name="dev", height=decimal.Decimal("173.8"), desc=None))

    def test_from_dict(self):
        self.assertEqual(
            self.joe,
            Person.from_dict(dict(name="joe", age=18, height=decimal.Decimal("178.3"), desc="boring")),
        )

    def test_to_dict(self):
        self.assertEqual(
            dict(name="joe", age=18, height=decimal.Decimal("178.3"), desc="boring"),
            self.joe.to_dict(),
        )

    def test_from_json(self):
        self.assertEqual(
            self.joe,
            Person.from_json(r'{"name": "joe", "age": 18, "height": "178.3", "desc": "boring"}'),
        )

    def test_to_json(self):
        self.assertEqual(
            r'{"name": "joe", "age": 18, "height": "178.3", "desc": "boring"}',
            self.joe.to_json(),
        )
