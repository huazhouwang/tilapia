from peewee import SqliteDatabase

from wallet.lib.conf import settings

db = SqliteDatabase(settings.DATABASE["default"]["name"])
