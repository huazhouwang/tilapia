import datetime
import itertools
import logging
import time
from decimal import Decimal
from typing import Iterable, List, Literal, Optional, Tuple

from common.basic.functional.require import require
from common.basic.functional.timing import timing_logger
from common.basic.functional.wraps import error_interrupter, timeout_lock
from common.basic.orm.database import db
from common.basic.ticker.utils import on_interval
from common.coin import data as coin_data
from common.coin import manager as coin_manager
from common.provider import provider_manager
from common.provider.data import Transaction, TxPaginate
from common.transaction import daos
from common.transaction.data import TX_TO_ACTION_STATUS_DIRECT_MAPPING, TxActionStatus
from common.transaction.models import TxAction
from common.utxo import manager as utxo_manager

logger = logging.getLogger("app.transaction")


def create_action(
    txid: str,
    status: TxActionStatus,
    chain_code: str,
    coin_code: str,
    value: Decimal,
    from_address: str,
    to_address: str,
    fee_limit: Decimal,
    raw_tx: str,
    **kwargs,
) -> TxAction:
    return daos.new_action(
        txid=txid,
        status=status,
        chain_code=chain_code,
        coin_code=coin_code,
        value=value,
        from_address=from_address,
        to_address=to_address,
        fee_limit=fee_limit,
        raw_tx=raw_tx,
        **kwargs,
    ).save()


def get_action_by_id(action_id: int) -> TxAction:
    return daos.get_action_by_id(action_id)


def update_action_status(
    chain_code: str,
    txid: str,
    status: TxActionStatus,
):
    daos.update_actions_status(chain_code, txid, status)


def has_actions_by_txid(chain_code: str, txid: str) -> bool:
    return daos.has_actions_by_txid(chain_code, txid)


def query_actions_by_txid(chain_code: str, txid: str) -> List[TxAction]:
    return daos.query_actions_by_txid(chain_code, txid)


def update_pending_actions(
    chain_code: Optional[str] = None,
    address: Optional[str] = None,
    txid: Optional[str] = None,
):
    pending_actions = daos.query_actions_by_status(
        TxActionStatus.PENDING,
        chain_code=chain_code,
        address=address,
        txid=txid,
    )

    if not pending_actions:
        return

    txids_of_chain = {(i.chain_code, i.txid) for i in pending_actions}
    confirmed_txids = set()

    for chain_code, tx in _query_transactions_of_chain(txids_of_chain):
        try:
            action_status = TX_TO_ACTION_STATUS_DIRECT_MAPPING.get(tx.status)
            if tx.fee is None or tx.block_header is None or action_status is None:
                continue

            _on_transaction_confirmed(
                chain_code=chain_code,
                txid=tx.txid,
                status=action_status,
                fee_used=Decimal(tx.fee.used),
                block_hash=tx.block_header.block_hash,
                block_number=tx.block_header.block_number,
                block_time=tx.block_header.block_time,
            )
            confirmed_txids.add(tx.txid)
            logger.info(
                f"TxAction confirmed. chain_code: {chain_code}, txid: {tx.txid}, action_status: {action_status}"
            )
        except Exception as e:
            logger.exception(f"Error in updating actions. chain_code: {chain_code}, txid: {tx.txid}, error: {repr(e)}")

    unconfirmed_actions = [i for i in pending_actions if i.txid not in confirmed_txids]
    if not unconfirmed_actions:
        return

    now = datetime.datetime.now()
    too_old = datetime.timedelta(days=3)
    too_old_txids = {(i.chain_code, i.txid) for i in unconfirmed_actions if now - i.created_time >= too_old}

    with db.atomic():
        for chain_code, txid in too_old_txids:
            daos.update_actions_status(chain_code, txid, status=TxActionStatus.UNKNOWN)


def _query_transactions_of_chain(txids_of_chain: Iterable[Tuple[str, str]]) -> Iterable[Tuple[str, Transaction]]:
    txids_of_chain = sorted(txids_of_chain, key=lambda i: i[0])  # in order to use itertools.groupby

    for chain_code, group in itertools.groupby(txids_of_chain, key=lambda i: i[0]):
        for (_, txid) in group:
            try:
                yield chain_code, provider_manager.get_transaction_by_txid(chain_code, txid)
            except Exception as e:
                logger.exception(
                    f"Error in getting transaction by txid. chain_code: {chain_code}, txid: {txid}, error: {repr(e)}"
                )


def _search_txs_by_address(
    chain_code: str, address: str, last_confirmed_action: TxAction = None
) -> Iterable[Transaction]:
    try:
        if last_confirmed_action is not None:
            paginate = TxPaginate(start_block_number=last_confirmed_action.block_number)
        else:
            paginate = None

        transactions = provider_manager.search_txs_by_address(chain_code, address, paginate=paginate)

        return transactions
    except Exception as e:
        logger.exception(
            f"Error in searching txs by address. chain_code: {chain_code}, "
            f"address: {address}, last_confirmed_action: {last_confirmed_action}, error: {repr(e)}"
        )
        return []


def _tx_action_factory__account_model(chain_code: str, transactions: Iterable[Transaction]) -> Iterable[TxAction]:
    transactions = [i for i in transactions if i.status in TX_TO_ACTION_STATUS_DIRECT_MAPPING]
    token_addresses = set()
    for tx in transactions:
        for tx_input in tx.inputs:
            token_addresses.add(tx_input.token_address)

    main_coin = coin_manager.get_coin_info(chain_code)
    tokens = coin_manager.query_coins_by_token_addresses(chain_code, list(token_addresses))
    tokens = {i.token_address: i for i in tokens if i.token_address}
    txids = set()

    for tx in transactions:
        if (
            tx.txid in txids
        ):  # May get two txs with the same txid here, if the receiver and the sender are at the same address
            continue

        txids.add(tx.txid)
        status = TX_TO_ACTION_STATUS_DIRECT_MAPPING.get(tx.status)

        for index, (tx_input, tx_output) in enumerate(zip(tx.inputs, tx.outputs)):
            token_address = tx_output.token_address
            if not tx_input.address or not tx_output.address or (token_address and token_address not in tokens):
                continue

            coin = main_coin if not token_address else tokens[token_address]
            info = dict(
                txid=tx.txid,
                status=status,
                chain_code=chain_code,
                coin_code=coin.code,
                value=Decimal(tx_output.value),
                from_address=tx_input.address,
                to_address=tx_output.address,
                fee_limit=Decimal(tx.fee.limit),
                fee_price_per_unit=Decimal(tx.fee.price_per_unit),
                raw_tx=tx.raw_tx,
                index=index,
            )

            if tx.block_header:
                info.update(
                    dict(
                        fee_used=Decimal(tx.fee.used),
                        block_number=tx.block_header.block_number,
                        block_hash=tx.block_header.block_hash,
                        block_time=tx.block_header.block_time,
                        created_time=datetime.datetime.fromtimestamp(
                            tx.block_header.block_time
                        ),  # Unify the ordering of local records and on-chain transactions
                    )
                )

            if tx.nonce is not None and tx.nonce >= 0:
                info["nonce"] = tx.nonce

            yield daos.new_action(**info)


_TX_ACTION_FACTORY_REGISTRY = {
    coin_data.ChainModel.ACCOUNT: _tx_action_factory__account_model,
}


def _search_actions_from_provider_by_address(
    chain_code: str, address: str, paginate: TxPaginate = None
) -> List[TxAction]:
    chain_info = coin_manager.get_chain_info(chain_code)
    action_factory = _TX_ACTION_FACTORY_REGISTRY.get(chain_info.chain_model)

    if not action_factory:
        return []

    try:
        transactions = provider_manager.search_txs_by_address(chain_code, address, paginate=paginate)
    except Exception as e:
        transactions = []
        logger.exception(
            f"Error in searching txs by address form provider. "
            f"chain_code: {chain_code}, address: {address}, paginate: {paginate}, error: {repr(e)}"
        )

    transactions = (i for i in transactions if i.status in TX_TO_ACTION_STATUS_DIRECT_MAPPING)
    actions = action_factory(chain_code, transactions)
    actions = [i for i in actions if i.from_address == address or i.to_address == address]
    return actions


_LAST_ARCHIVED_ID_CACHE = {}


@timing_logger("transaction_manager.query_actions_by_address")
def query_actions_by_address(
    chain_code: str,
    coin_code: str,
    address: str,
    page_number: int = 1,
    items_per_page: int = 20,
    searching_address_as: Literal["sender", "receiver", "both"] = "both",
) -> List[TxAction]:
    with timeout_lock("transaction_manager.query_actions_by_address") as acquired:
        if not acquired:
            return []

        address = provider_manager.verify_address(chain_code, address).normalized_address
        page_number = max(page_number, 1)
        is_first_page = page_number == 1

        archived_id_cache_key = f"{chain_code}:{address}"
        archived_id = _LAST_ARCHIVED_ID_CACHE.get(archived_id_cache_key)
        if is_first_page or not archived_id:
            archived_id = int(time.time() * 1e3)
            _LAST_ARCHIVED_ID_CACHE[archived_id_cache_key] = archived_id

        local_actions = []
        max_times = 3
        for times in range(max_times + 1):
            local_actions = daos.query_actions_by_address(
                chain_code,
                address,
                coin_code=coin_code,
                items_per_page=items_per_page,
                page_number=page_number,
                archived_ids=[archived_id, None],
                searching_address_as=searching_address_as,
            )

            if (
                len(local_actions) >= items_per_page
                or times == max_times  # No need to invoke synchronization the last time
                or _sync_actions_by_address(chain_code, address, archived_id, require_sync_number=200 * 1 << times) == 0
            ):
                break

        return local_actions


@error_interrupter(logger, interrupt=True, default=0)
def _sync_actions_by_address(chain_code: str, address: str, archived_id: int, require_sync_number: int = 200) -> int:
    first_confirmed_action = daos.get_first_confirmed_action_at_the_same_archived_id(chain_code, address, archived_id)
    last_confirmed_action_before_this_archived = daos.get_last_confirmed_action_before_archived_id(
        chain_code, address, archived_id
    )

    paginate = TxPaginate(
        start_block_number=(
            max(
                0, last_confirmed_action_before_this_archived.block_number - 1
            )  # Ensure that the requested block overlaps the recorded block
            if last_confirmed_action_before_this_archived
            else None
        ),
        end_block_number=first_confirmed_action.block_number if first_confirmed_action else None,
        items_per_page=require_sync_number,
    )
    syncing_actions = _search_actions_from_provider_by_address(chain_code, address, paginate)
    syncing_txids = list({i.txid for i in syncing_actions})

    pending_txids = daos.filter_existing_txids(chain_code, syncing_txids, status=TxActionStatus.PENDING)
    to_be_confirmed_actions = {
        i.txid: i for i in syncing_actions if i.txid in pending_txids and i.block_number is not None
    }

    old_archived_ids = daos.query_existing_archived_ids(chain_code, syncing_txids)
    if archived_id in old_archived_ids:
        old_archived_ids.remove(archived_id)

    existing_txids = daos.filter_existing_txids(chain_code, syncing_txids)
    to_be_created_actions = [i for i in syncing_actions if i.txid not in existing_txids]

    expand_count = 0
    with db.atomic():
        if to_be_confirmed_actions:
            for txid, action in to_be_confirmed_actions.items():
                _on_transaction_confirmed(
                    chain_code=chain_code,
                    txid=txid,
                    status=action.status,
                    fee_used=action.fee_used,
                    block_hash=action.block_hash,
                    block_number=action.block_number,
                    block_time=action.block_time,
                    archived_id=archived_id,
                )

            expand_count += len(to_be_confirmed_actions)

        if old_archived_ids:
            expand_count += daos.update_archived_id(list(old_archived_ids), archived_id)

        if to_be_created_actions:
            for i in to_be_created_actions:
                i.archived_id = archived_id

            daos.bulk_create(to_be_created_actions)
            expand_count += len(to_be_created_actions)

    return expand_count


def _on_transaction_confirmed(
    chain_code: str,
    txid: str,
    status: TxActionStatus,
    fee_used: Decimal,
    block_number: int,
    block_hash: str,
    block_time: int,
    archived_id: int = None,
):
    require(status in (TxActionStatus.CONFIRM_SUCCESS, TxActionStatus.CONFIRM_REVERTED))
    logger.info(
        f"Transaction confirmed. chain_code: {chain_code}, txid: {txid}, status: {status}, block_number: {block_number}"
    )

    daos.on_transaction_confirmed(
        chain_code=chain_code,
        txid=txid,
        status=status,
        fee_used=fee_used,
        block_hash=block_hash,
        block_number=block_number,
        block_time=block_time,
        archived_id=archived_id,
    )

    chain_info = coin_manager.get_chain_info(chain_code)

    if chain_info.chain_model == coin_data.ChainModel.UTXO:
        utxo_manager.mark_utxos_spent_by_txid(chain_code, txid)

    if chain_info.nonce_supported is not True:
        return

    actions = daos.query_actions_by_txid(chain_code, txid, index=0)
    main_action = actions[0] if actions and actions[0].nonce >= 0 else None
    if not main_action:
        return

    same_nonce_actions = daos.query_actions_by_nonce(chain_code, main_action.from_address, main_action.nonce)
    replaced_action_txids = {
        i.txid for i in same_nonce_actions if i.txid != txid and i.status == TxActionStatus.PENDING
    }
    for txid in replaced_action_txids:
        daos.update_actions_status(chain_code, txid, TxActionStatus.REPLACED)


def delete_actions_by_addresses(chain_code: str, addresses: List[str]) -> int:
    return daos.delete_actions_by_addresses(chain_code, addresses)


@on_interval(60)
@timing_logger("transaction_manager.on_ticker_signal")
def on_ticker_signal():
    update_pending_actions()
