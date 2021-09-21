import peewee

from tilapia.lib.basic.orm.models import AutoDateTimeField, BaseModel
from tilapia.lib.utxo import data


class UTXO(BaseModel):
    id = peewee.IntegerField(primary_key=True)
    chain_code = peewee.CharField()
    coin_code = peewee.CharField()
    address = peewee.CharField()
    txid = peewee.CharField()
    vout = peewee.SmallIntegerField()
    status = peewee.IntegerField(choices=data.UTXOStatus.to_choices())
    value = peewee.DecimalField(max_digits=32, decimal_places=0)
    created_time = AutoDateTimeField()
    modified_time = AutoDateTimeField()

    class Meta:
        indexes = ((("coin_code", "address", "txid", "vout"), True),)

    def __str__(self):
        return (
            f"id: {self.id}, coin_code: {self.coin_code}, status: {self.status}, "
            f"utxo: {self.txid}/{self.vout}/{self.value}"
        )


class WhoSpent(BaseModel):
    id = peewee.IntegerField(primary_key=True)
    chain_code = peewee.CharField()
    txid = peewee.CharField()
    utxo_id = peewee.IntegerField()
    created_time = AutoDateTimeField()

    class Meta:
        indexes = ((("chain_code", "txid", "utxo_id"), True),)

    def __str__(self):
        return f"id: {self.id}, chain_code: {self.chain_code}, txid: {self.txid}, utxo_id: {self.utxo_id}"
