import peewee

from tilapia.lib.basic.orm.models import AutoDateTimeField, BaseModel
from tilapia.lib.wallet import data


def update(db, migrator, migrate):
    class WalletModel(BaseModel):
        id = peewee.AutoField(primary_key=True)
        type = peewee.IntegerField(choices=data.WalletType.to_choices())
        name = peewee.CharField()
        chain_code = peewee.CharField()
        created_time = AutoDateTimeField()
        modified_time = AutoDateTimeField()

    class AccountModel(BaseModel):
        id = peewee.AutoField(primary_key=True)
        wallet_id = peewee.IntegerField()
        chain_code = peewee.CharField()
        address = peewee.CharField()
        address_encoding = peewee.CharField(null=True)
        pubkey_id = peewee.IntegerField(null=True)
        bip44_path = peewee.CharField(null=True)
        created_time = AutoDateTimeField()
        modified_time = AutoDateTimeField()

    class AssetModel(BaseModel):
        id = peewee.AutoField(primary_key=True)
        wallet_id = peewee.IntegerField()
        account_id = peewee.IntegerField()
        chain_code = peewee.CharField()
        coin_code = peewee.CharField()
        balance = peewee.DecimalField(default=0)
        is_visible = peewee.BooleanField(default=True)
        created_time = AutoDateTimeField()
        modified_time = AutoDateTimeField()

        class Meta:
            indexes = ((("account_id", "coin_code"), True),)

    db.create_tables((WalletModel, AccountModel, AssetModel))
