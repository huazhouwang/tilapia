from typing import List, Optional

from common.wallet.models import AccountModel


def create_account(
    wallet_id: int,
    chain_code: str,
    address: str,
    pubkey_id: int = None,
    bip44_path: str = None,
    address_encoding: str = None,
) -> AccountModel:
    return AccountModel.create(
        wallet_id=wallet_id,
        chain_code=chain_code,
        address=address,
        pubkey_id=pubkey_id,
        bip44_path=bip44_path,
        address_encoding=address_encoding,
    )


def query_accounts_by_wallets(wallet_ids: List[int], address_encoding: str = None) -> List[AccountModel]:
    expressions = [AccountModel.wallet_id.in_(wallet_ids)]

    if address_encoding is not None:
        expressions.append(AccountModel.address_encoding == address_encoding)

    models = AccountModel.select().where(*expressions).order_by(AccountModel.id.asc())
    return list(models)


def query_first_account_by_wallet(wallet_id: int) -> Optional[AccountModel]:
    return AccountModel.select().where(AccountModel.wallet_id == wallet_id).order_by(AccountModel.id.asc()).first()


def is_account_existing(chain_code: str, address: str) -> bool:
    return AccountModel.get_or_none(AccountModel.chain_code == chain_code, AccountModel.address == address) is not None


def query_accounts_by_ids(account_ids: List[int]) -> List[AccountModel]:
    models = AccountModel.select().where(AccountModel.id.in_(account_ids))
    return list(models)


def query_accounts_by_addresses(wallet_id: int, addresses: List[str]) -> List[AccountModel]:
    models = AccountModel.select().where(AccountModel.wallet_id == wallet_id, AccountModel.address.in_(addresses))
    return list(models)


def delete_accounts_by_wallet_id(wallet_id: int):
    AccountModel.delete().where(AccountModel.wallet_id == wallet_id).execute()
