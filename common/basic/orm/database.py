from peewee import SqliteDatabase

from common.conf import settings

db = SqliteDatabase(settings.DATABASE["default"]["name"])
