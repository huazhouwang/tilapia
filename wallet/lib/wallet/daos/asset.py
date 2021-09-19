import datetime
from decimal import Decimal
from typing import List, Optional

from wallet.lib.wallet import models


def create_asset(
    wallet_id: int,
    account_id: int,
    chain_code: str,
    coin_code: str,
    balance: Decimal = 0,
    is_visible: bool = True,
) -> models.AssetModel:
    return models.AssetModel.create(
        wallet_id=wallet_id,
        account_id=account_id,
        chain_code=chain_code,
        coin_code=coin_code,
        balance=balance,
        is_visible=is_visible,
    )


def query_assets_by_accounts(account_ids: List[int], only_visible: bool = True) -> List[models.AssetModel]:
    selections = [models.AssetModel.account_id.in_(account_ids)]
    if only_visible is True:
        selections.append(models.AssetModel.is_visible == True)  # noqa

    items = models.AssetModel.select().where(*selections)
    return list(items)


def get_asset_by_account_and_coin_code(account_id: int, coin_code: str) -> Optional[models.AssetModel]:
    return models.AssetModel.get_or_none(
        models.AssetModel.account_id == account_id, models.AssetModel.coin_code == coin_code
    )


def query_assets_by_account_and_coin_codes(account_id: int, coin_codes: List[str]) -> List[models.AssetModel]:
    items = models.AssetModel.select().where(
        models.AssetModel.account_id == account_id, models.AssetModel.coin_code.in_(coin_codes)
    )
    return list(items)


def query_assets_by_ids(asset_ids: List[int]) -> List[models.AssetModel]:
    items = models.AssetModel.select().where(models.AssetModel.id.in_(asset_ids))
    return list(items)


def bulk_update_balance(assets: List[models.AssetModel]):
    now = datetime.datetime.now()
    for i in assets:
        i.modified_time = now

    models.AssetModel.bulk_update(assets, [models.AssetModel.balance, models.AssetModel.modified_time], batch_size=10)


def hide_asset(asset_id: int):
    models.AssetModel.update(is_visible=False, modified_time=datetime.datetime.now()).where(
        models.AssetModel.id == asset_id
    ).execute()


def show_asset(asset_id: int):
    models.AssetModel.update(is_visible=True, modified_time=datetime.datetime.now()).where(
        models.AssetModel.id == asset_id
    ).execute()


def delete_assets_by_wallet_id(wallet_id):
    models.AssetModel.delete().where(models.AssetModel.wallet_id == wallet_id).execute()
