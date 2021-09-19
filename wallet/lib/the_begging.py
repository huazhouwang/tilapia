def initialize():
    import logging.config

    from wallet.lib.conf import settings

    # prepare logging
    logging.config.dictConfig(settings.LOGGING)

    # database migrating
    from wallet.lib.basic.orm.database import db
    from wallet.lib.basic.orm.migrate import manager as migrate_manager

    migrate_manager.migrating(db)


def reset_runtime():
    import os

    from wallet.lib.basic.orm import database

    database.db.close()
    os.remove(database.db.database)
    initialize()
