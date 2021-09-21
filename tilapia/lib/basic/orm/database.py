from peewee import SqliteDatabase

from tilapia.lib.conf import settings

db = SqliteDatabase(settings.DATABASE["default"]["name"])
