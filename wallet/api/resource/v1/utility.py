from wallet.lib.basic.orm import database as orm_database
from wallet.lib.basic.orm.migrate import manager as migrate_manager


class Migrate:
    URI = "migrate"

    def on_post(self, req, resp):
        migrate_manager.migrating(orm_database.db)
