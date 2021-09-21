import datetime
import functools
from decimal import Decimal
from typing import Iterable, List, Literal, Optional, Set

from tilapia.lib.transaction.data import TxActionStatus
from tilapia.lib.transaction.models import TxAction


def new_action(
    txid: str,
    status: TxActionStatus,
    chain_code: str,
    coin_code: str,
    value: Decimal,
    from_address: str,
    to_address: str,
    fee_limit: Decimal,
    raw_tx: str,
    fee_used: Decimal = 0,
    fee_price_per_unit: Decimal = 1,
    block_number: int = None,
    block_hash: str = None,
    block_time: int = None,
    index: int = 0,
    nonce: int = -1,
    created_time: datetime.datetime = None,
) -> TxAction:
    data = dict(
        txid=txid,
        status=status,
        chain_code=chain_code,
        coin_code=coin_code,
        value=value,
        from_address=from_address,
        to_address=to_address,
        fee_limit=fee_limit,
        raw_tx=raw_tx,
        fee_used=fee_used,
        fee_price_per_unit=fee_price_per_unit,
        block_number=block_number,
        block_hash=block_hash,
        block_time=block_time,
        index=index,
        nonce=nonce,
    )
    if created_time is not None:
        data["created_time"] = created_time

    return TxAction(**data)


def bulk_create(actions: Iterable[TxAction]):
    return TxAction.bulk_create(actions, 10)


def on_transaction_confirmed(
    chain_code: str,
    txid: str,
    status: TxActionStatus,
    fee_used: Decimal,
    block_number: int,
    block_hash: str,
    block_time: int,
    archived_id: int = None,
):
    return (
        TxAction.update(
            status=status,
            fee_used=fee_used,
            block_number=block_number,
            block_hash=block_hash,
            block_time=block_time,
            archived_id=archived_id,
            modified_time=datetime.datetime.now(),
        )
        .where(TxAction.chain_code == chain_code, TxAction.txid == txid)
        .execute()
    )


def query_actions_by_txid(chain_code: str, txid: str, index: int = None) -> List[TxAction]:
    expression = [TxAction.chain_code == chain_code, TxAction.txid == txid]
    index is None or expression.append(TxAction.index == index)
    models = TxAction.select().where(*expression).order_by(TxAction.index.asc())
    return list(models)


def query_actions_by_nonce(chain_code: str, from_address: str, nonce: int) -> List[TxAction]:
    models = TxAction.select().where(
        TxAction.chain_code == chain_code, TxAction.from_address == from_address, TxAction.nonce == nonce
    )
    return list(models)


def update_actions_status(
    chain_code: str,
    txid: str,
    status: TxActionStatus,
):
    return (
        TxAction.update(
            status=status,
            modified_time=datetime.datetime.now(),
        )
        .where(TxAction.chain_code == chain_code, TxAction.txid == txid)
        .execute()
    )


def query_actions_by_address(
    chain_code: str,
    address: str,
    coin_code: str = None,
    page_number: int = 1,
    items_per_page: int = 20,
    archived_ids: List[int] = None,
    searching_address_as: Literal["sender", "receiver", "both"] = "both",
) -> List[TxAction]:
    address_query_expression_options = (
        TxAction.from_address == address,
        TxAction.to_address == address,
    )

    if searching_address_as == "sender":
        address_query_expression = address_query_expression_options[0]
    elif searching_address_as == "receiver":
        address_query_expression = address_query_expression_options[1]
    else:
        address_query_expression = address_query_expression_options[0] | address_query_expression_options[1]

    expressions = [
        TxAction.chain_code == chain_code,
        address_query_expression,
    ]

    coin_code is None or expressions.append(TxAction.coin_code == coin_code)
    not archived_ids or expressions.append(
        functools.reduce(lambda a, b: a | b, (TxAction.archived_id == i for i in archived_ids))
    )

    actions = TxAction.select().where(*expressions).order_by(TxAction.created_time.desc())
    if page_number is not None and items_per_page is not None:
        actions = actions.paginate(page_number, items_per_page)

    return list(actions)


def get_first_confirmed_action_at_the_same_archived_id(
    chain_code: str, address: str, archived_id: int
) -> Optional[TxAction]:
    return (
        TxAction.select()
        .where(
            TxAction.chain_code == chain_code,
            (TxAction.from_address == address) | (TxAction.to_address == address),
            TxAction.block_number != None,  # noqa
            TxAction.archived_id == archived_id,
        )
        .order_by(TxAction.block_number.asc())
        .first()
    )


def get_last_confirmed_action_before_archived_id(chain_code: str, address: str, archived_id: int) -> Optional[TxAction]:
    return (
        TxAction.select()
        .where(
            TxAction.chain_code == chain_code,
            (TxAction.from_address == address) | (TxAction.to_address == address),
            TxAction.block_number != None,  # noqa
            TxAction.archived_id < archived_id,
        )
        .order_by(TxAction.archived_id.desc(), TxAction.block_number.desc())
        .first()
    )


def query_existing_archived_ids(chain_code: str, txids: List[str]) -> Set[int]:
    items = (
        TxAction.select(TxAction.archived_id.distinct())
        .where(
            TxAction.chain_code == chain_code,
            TxAction.txid.in_(txids),
            TxAction.archived_id != None,  # noqa
        )
        .tuples()
    )
    return {i[0] for i in items}


def filter_existing_txids(chain_code: str, txids: List[str], status: TxActionStatus = None) -> Set[str]:
    expressions = [TxAction.chain_code == chain_code, TxAction.txid.in_(txids)]

    if status is not None:
        expressions.append(TxAction.status == status)

    items = TxAction.select(TxAction.txid.distinct()).where(*expressions).tuples()
    return {i[0] for i in items}


def update_archived_id(from_archived_ids: List[int], archived_id: int) -> int:
    return (
        TxAction.update(archived_id=archived_id, modified_time=datetime.datetime.now())
        .where(TxAction.archived_id.in_(from_archived_ids))
        .execute()
    )


def get_action_by_id(action_id: int) -> Optional[TxAction]:
    return TxAction.get_or_none(TxAction.id == action_id)


def query_actions_by_status(
    status: TxActionStatus,
    chain_code: str = None,
    address: str = None,
    txid: str = None,
) -> List[TxAction]:
    expressions = [TxAction.status == status]

    chain_code is None or expressions.append(TxAction.chain_code == chain_code)
    address is None or expressions.append(TxAction.from_address == address or TxAction.to_address == address)
    txid is None or expressions.append(TxAction.txid == txid)

    models = TxAction.select().where(*expressions)
    return list(models)


def delete_actions_by_addresses(chain_code: str, addresses: List[str]) -> int:
    return (
        TxAction.delete()
        .where(
            TxAction.chain_code == chain_code,
            TxAction.from_address.in_(addresses) or TxAction.to_address.in_(addresses),
        )
        .execute()
    )


def has_actions_by_txid(chain_code: str, txid: str) -> bool:
    return TxAction.select().where(TxAction.chain_code == chain_code, TxAction.txid == txid).count() > 0
