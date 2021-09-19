import peewee


def update(db, migrator, migrate):
    migrate(
        migrator.add_column("txaction", "archived_id", peewee.IntegerField(null=True)),
    )
