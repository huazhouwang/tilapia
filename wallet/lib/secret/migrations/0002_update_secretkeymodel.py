import peewee


def update(db, migrator, migrate):
    migrate(
        migrator.add_column(
            "secretkeymodel", "encrypted_message", peewee.CharField(null=True, help_text="Extra encrypted message")
        ),
    )
