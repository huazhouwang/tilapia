from typing import List, Optional

from tilapia.lib.wallet import models


def create_account(
    wallet_id: int,
    chain_code: str,
    address: str,
    pubkey_id: int = None,
    bip44_path: str = None,
    address_encoding: str = None,
) -> models.AccountModel:
    return models.AccountModel.create(
        wallet_id=wallet_id,
        chain_code=chain_code,
        address=address,
        pubkey_id=pubkey_id,
        bip44_path=bip44_path,
        address_encoding=address_encoding,
    )


def query_accounts_by_wallets(wallet_ids: List[int], address_encoding: str = None) -> List[models.AccountModel]:
    expressions = [models.AccountModel.wallet_id.in_(wallet_ids)]

    if address_encoding is not None:
        expressions.append(models.AccountModel.address_encoding == address_encoding)

    items = models.AccountModel.select().where(*expressions).order_by(models.AccountModel.id.asc())
    return list(items)


def query_first_account_by_wallet(wallet_id: int) -> Optional[models.AccountModel]:
    return (
        models.AccountModel.select()
        .where(models.AccountModel.wallet_id == wallet_id)
        .order_by(models.AccountModel.id.asc())
        .first()
    )


def is_account_existing(chain_code: str, address: str) -> bool:
    return (
        models.AccountModel.get_or_none(
            models.AccountModel.chain_code == chain_code, models.AccountModel.address == address
        )
        is not None
    )


def query_accounts_by_ids(account_ids: List[int]) -> List[models.AccountModel]:
    items = models.AccountModel.select().where(models.AccountModel.id.in_(account_ids))
    return list(items)


def query_accounts_by_addresses(wallet_id: int, addresses: List[str]) -> List[models.AccountModel]:
    items = models.AccountModel.select().where(
        models.AccountModel.wallet_id == wallet_id, models.AccountModel.address.in_(addresses)
    )
    return list(items)


def delete_accounts_by_wallet_id(wallet_id: int):
    models.AccountModel.delete().where(models.AccountModel.wallet_id == wallet_id).execute()
