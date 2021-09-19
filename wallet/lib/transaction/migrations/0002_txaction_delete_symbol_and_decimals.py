def update(db, migrator, migrate):
    migrate(
        migrator.drop_column("txaction", "symbol"),
        migrator.drop_column("txaction", "decimals"),
    )
