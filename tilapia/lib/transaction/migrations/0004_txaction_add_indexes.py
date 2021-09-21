import logging

from tilapia.lib.transaction import data, models

logger = logging.getLogger("app.transaction")


def update(db, migrator, migrate):
    try:
        count = models.TxAction.delete().where(models.TxAction.status != data.TxActionStatus.PENDING).execute()
        logger.info(f"Delete all txns without pending status. count: {count}")

        migrate(
            migrator.add_index("txaction", ("txid", "coin_code", "index"), True),
        )
        return
    except Exception as e:
        logger.exception(f"Error in migration plan a. error: {e}")

    try:
        count = models.TxAction.delete().execute()
        logger.info(f"Delete all txns. count: {count}")

        migrate(
            migrator.add_index("txaction", ("txid", "coin_code", "index"), True),
        )
    except Exception as e:
        logger.exception(f"Error in migration plan b. error: {e}")
