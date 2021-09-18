import datetime
from typing import List, Optional

from common.wallet.data import WalletType
from common.wallet.models import WalletModel


def create_wallet(
    name: str,
    wallet_type: WalletType,
    chain_code: str,
    hardware_key_id: str = None,
) -> WalletModel:
    return WalletModel.create(
        name=name,
        type=wallet_type,
        chain_code=chain_code,
        hardware_key_id=hardware_key_id,
    )


def list_all_wallets(
    chain_code: str = None, wallet_type: WalletType = None, hardware_key_id: str = None
) -> List[WalletModel]:
    expressions = []

    chain_code is None or expressions.append(WalletModel.chain_code == chain_code)
    wallet_type is None or expressions.append(WalletModel.type == wallet_type)
    hardware_key_id is None or expressions.append(WalletModel.hardware_key_id == hardware_key_id)

    models = WalletModel.select()
    if expressions:
        models = models.where(*expressions)

    return list(models)


def get_wallet_by_id(wallet_id: int) -> Optional[WalletModel]:
    return WalletModel.get_or_none(WalletModel.id == wallet_id)


def has_primary_wallet() -> bool:
    return WalletModel.select().where(WalletModel.type == WalletType.SOFTWARE_PRIMARY).count() > 0


def get_first_primary_wallet() -> Optional[WalletModel]:
    return WalletModel.get_or_none(WalletModel.type == WalletType.SOFTWARE_PRIMARY)


def update_wallet_name(wallet_id: int, name: str):
    WalletModel.update(name=name, modified_time=datetime.datetime.now()).where(WalletModel.id == wallet_id).execute()


def delete_wallet_by_id(wallet_id: int):
    WalletModel.delete_by_id(wallet_id)
