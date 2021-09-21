import datetime

from peewee import DateTimeField, Model

from tilapia.lib.basic.orm.database import db


class BaseModel(Model):
    class Meta:
        database = db


class AutoDateTimeField(DateTimeField):
    def __init__(self, *args, default=datetime.datetime.now, **kwargs):
        super().__init__(*args, default=default, **kwargs)
