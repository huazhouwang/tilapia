import peewee

from wallet.lib.basic.orm.models import AutoDateTimeField, BaseModel


def update(db, migrator, migrate):
    class UTXO(BaseModel):
        id = peewee.IntegerField(primary_key=True)
        chain_code = peewee.CharField()
        coin_code = peewee.CharField()
        address = peewee.CharField()
        txid = peewee.CharField()
        vout = peewee.SmallIntegerField()
        status = peewee.IntegerField()
        value = peewee.DecimalField(max_digits=32, decimal_places=0)
        created_time = AutoDateTimeField()
        modified_time = AutoDateTimeField()

        class Meta:
            indexes = ((("coin_code", "address", "txid", "vout"), True),)

    db.create_tables((UTXO,))
