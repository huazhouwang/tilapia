import datetime
from typing import List, Optional

from wallet.lib.wallet import data, models


def create_wallet(
    name: str,
    wallet_type: data.WalletType,
    chain_code: str,
    hardware_key_id: str = None,
) -> models.WalletModel:
    return models.WalletModel.create(
        name=name,
        type=wallet_type,
        chain_code=chain_code,
        hardware_key_id=hardware_key_id,
    )


def list_all_wallets(
    chain_code: str = None, wallet_type: data.WalletType = None, hardware_key_id: str = None
) -> List[models.WalletModel]:
    expressions = []

    chain_code is None or expressions.append(models.WalletModel.chain_code == chain_code)
    wallet_type is None or expressions.append(models.WalletModel.type == wallet_type)
    hardware_key_id is None or expressions.append(models.WalletModel.hardware_key_id == hardware_key_id)

    items = models.WalletModel.select()
    if expressions:
        items = items.where(*expressions)

    return list(items)


def get_wallet_by_id(wallet_id: int) -> Optional[models.WalletModel]:
    return models.WalletModel.get_or_none(models.WalletModel.id == wallet_id)


def has_primary_wallet() -> bool:
    return models.WalletModel.select().where(models.WalletModel.type == data.WalletType.SOFTWARE_PRIMARY).count() > 0


def get_first_primary_wallet() -> Optional[models.WalletModel]:
    return models.WalletModel.get_or_none(models.WalletModel.type == data.WalletType.SOFTWARE_PRIMARY)


def update_wallet_name(wallet_id: int, name: str):
    models.WalletModel.update(name=name, modified_time=datetime.datetime.now()).where(
        models.WalletModel.id == wallet_id
    ).execute()


def delete_wallet_by_id(wallet_id: int):
    models.WalletModel.delete_by_id(wallet_id)
