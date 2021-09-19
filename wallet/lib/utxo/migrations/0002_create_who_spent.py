import peewee

from wallet.lib.basic.orm.models import AutoDateTimeField, BaseModel


def update(db, migrator, migrate):
    class WhoSpent(BaseModel):
        id = peewee.IntegerField(primary_key=True)
        chain_code = peewee.CharField()
        txid = peewee.CharField()
        utxo_id = peewee.IntegerField()
        created_time = AutoDateTimeField()

        class Meta:
            indexes = ((("chain_code", "txid", "utxo_id"), True),)

    db.create_tables((WhoSpent,))
