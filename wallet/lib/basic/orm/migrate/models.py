from peewee import AutoField, CharField

from wallet.lib.basic.orm.models import AutoDateTimeField, BaseModel


class MigrationRecord(BaseModel):
    id = AutoField(primary_key=True)
    module = CharField()
    name = CharField()
    created_time = AutoDateTimeField()
