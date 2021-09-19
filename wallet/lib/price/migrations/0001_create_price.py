import peewee

from wallet.lib.basic.orm.models import AutoDateTimeField, BaseModel
from wallet.lib.price.data import Channel


def update(db: peewee.Database, migrator, migrate):
    class Price(BaseModel):
        id = peewee.AutoField(primary_key=True)
        coin_code = peewee.CharField()
        price = peewee.DecimalField()
        unit = peewee.CharField()
        channel = peewee.IntegerField(choices=Channel.to_choices())
        created_time = AutoDateTimeField()
        modified_time = AutoDateTimeField()

        class Meta:
            indexes = ((("coin_code", "unit", "channel"), True),)

    db.create_tables((Price,))
