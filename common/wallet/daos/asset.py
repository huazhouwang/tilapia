import datetime
from decimal import Decimal
from typing import List, Optional

from common.wallet.models import AssetModel


def create_asset(
    wallet_id: int,
    account_id: int,
    chain_code: str,
    coin_code: str,
    balance: Decimal = 0,
    is_visible: bool = True,
) -> AssetModel:
    return AssetModel.create(
        wallet_id=wallet_id,
        account_id=account_id,
        chain_code=chain_code,
        coin_code=coin_code,
        balance=balance,
        is_visible=is_visible,
    )


def query_assets_by_accounts(account_ids: List[int], only_visible: bool = True) -> List[AssetModel]:
    selections = [AssetModel.account_id.in_(account_ids)]
    if only_visible is True:
        selections.append(AssetModel.is_visible == True)  # noqa

    models = AssetModel.select().where(*selections)
    return list(models)


def get_asset_by_account_and_coin_code(account_id: int, coin_code: str) -> Optional[AssetModel]:
    return AssetModel.get_or_none(AssetModel.account_id == account_id, AssetModel.coin_code == coin_code)


def query_assets_by_account_and_coin_codes(account_id: int, coin_codes: List[str]) -> List[AssetModel]:
    models = AssetModel.select().where(AssetModel.account_id == account_id, AssetModel.coin_code.in_(coin_codes))
    return list(models)


def query_assets_by_ids(asset_ids: List[int]) -> List[AssetModel]:
    models = AssetModel.select().where(AssetModel.id.in_(asset_ids))
    return list(models)


def bulk_update_balance(assets: List[AssetModel]):
    now = datetime.datetime.now()
    for i in assets:
        i.modified_time = now

    AssetModel.bulk_update(assets, [AssetModel.balance, AssetModel.modified_time], batch_size=10)


def hide_asset(asset_id: int):
    AssetModel.update(is_visible=False, modified_time=datetime.datetime.now()).where(
        AssetModel.id == asset_id
    ).execute()


def show_asset(asset_id: int):
    AssetModel.update(is_visible=True, modified_time=datetime.datetime.now()).where(AssetModel.id == asset_id).execute()


def delete_assets_by_wallet_id(wallet_id):
    AssetModel.delete().where(AssetModel.wallet_id == wallet_id).execute()
