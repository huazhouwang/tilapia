import peewee


def update(db, migrator, migrate):
    migrate(
        migrator.add_column("walletmodel", "hardware_key_id", peewee.CharField(null=True)),
    )
