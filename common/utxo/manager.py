import logging
import time
from typing import Dict, List, Tuple

from common.basic.functional.timing import timing_logger
from common.basic.functional.wraps import timeout_lock
from common.basic.orm import database as orm_database
from common.coin import manager as coin_manager
from common.provider import manager as provider_manager
from common.utxo import daos, data, models, utxo_chooser

logger = logging.getLogger("app.utxo")


def choose_utxos(
    coin_code: str,
    addresses: List[str],
    require_value: int,
    status: data.UTXOStatus = data.UTXOStatus.SPENDABLE,
    min_value: int = 0,
    exclude_ids: List[int] = None,
    limit: int = None,
) -> List[models.UTXO]:
    min_value = max(min_value, 0)
    if require_value <= min_value:
        logger.warning(f"Invalid require_value. require_value: {require_value}, min_value: {min_value}")
        return []

    base_query = dict(
        coin_code=coin_code,
        addresses=addresses,
        status=status,
        min_value=min_value,
        exclude_ids=exclude_ids,
        limit=limit,
        value_desc=True,
    )

    query_one_utxo__gte_require_value = {**base_query, "min_value": require_value, "limit": 1, "value_desc": False}
    candidates = daos.list_utxos_by_conditions(**query_one_utxo__gte_require_value)
    if candidates:
        return candidates

    query_utxos__lt_require_value = {**base_query, "max_value": require_value}
    sum_of_utxos__lt_require_value = daos.sum_of_utxos_by_conditions(**query_utxos__lt_require_value)
    if sum_of_utxos__lt_require_value >= require_value:
        candidates = daos.list_utxos_by_conditions(**query_utxos__lt_require_value)
        candidates = utxo_chooser.choose(candidates, require_value, key=lambda i: i.value)
        return candidates

    candidates = daos.list_utxos_by_conditions(**base_query)
    return candidates


RUNTIME_THROTTLE = {}


@timing_logger("utxo_manager.refresh_utxos_by_address")
def refresh_utxos_by_address(chain_code: str, address: str, force_update: bool = False) -> int:
    runtime_throttle_key = f"${chain_code}:{address}"
    throttle_expired_at = RUNTIME_THROTTLE.get(runtime_throttle_key)

    if not force_update and throttle_expired_at and throttle_expired_at >= time.time():
        return 0

    dust_threshold = coin_manager.get_chain_info(chain_code).dust_threshold

    try:
        remote_utxos = provider_manager.search_utxos_by_address(chain_code, address)
        remote_utxos = [i for i in remote_utxos if i.txid and i.vout >= 0 and i.value >= dust_threshold]
    except Exception as e:
        logger.exception(
            f"Error in searching utxos by address. chain_code: {chain_code}, address: {address}, error: {e}"
        )
        return 0  # Return without setting the throttle

    def key_of_utxo(_utxo):
        return f"{_utxo.txid}/{_utxo.vout}"

    with timeout_lock(f"utxo_manager.refresh_utxos_by_address.{chain_code}.{address}") as acquired:
        if not acquired:
            return 0

        coin_code = chain_code  # Only supports single token model
        remote_utxo_lookup = {key_of_utxo(i): i for i in remote_utxos}

        local_utxos = daos.list_utxos_by_conditions(coin_code, [address])
        local_utxos_lookup: Dict[str, models.UTXO] = {key_of_utxo(i): i for i in local_utxos}

        to_be_updated_utxos: List[models.UTXO] = []

        spend_utxo_keys = set(local_utxos_lookup.keys()).difference(remote_utxo_lookup.keys())
        for utxo_key in spend_utxo_keys:
            local_utxo = local_utxos_lookup[utxo_key]
            local_utxo.status = data.UTXOStatus.SPENT
            to_be_updated_utxos.append(local_utxo)

        for utxo_key, utxo in remote_utxo_lookup.items():
            local_utxo = local_utxos_lookup.get(utxo_key)
            if local_utxo and local_utxo.status not in (data.UTXOStatus.SPENDABLE, data.UTXOStatus.CHOSEN):
                local_utxo.status = data.UTXOStatus.SPENDABLE
                to_be_updated_utxos.append(local_utxo)

        to_be_created_utxos = [
            utxo for utxo_key, utxo in remote_utxo_lookup.items() if utxo_key not in local_utxos_lookup
        ]
        count = len(to_be_updated_utxos) + len(to_be_created_utxos)

        if count:
            with orm_database.db.atomic():
                if to_be_updated_utxos:
                    daos.bulk_update_utxos_status(to_be_updated_utxos)

                if to_be_created_utxos:
                    new_utxos = [
                        daos.new_utxo(
                            chain_code, coin_code, address, i.txid, i.vout, data.UTXOStatus.SPENDABLE, i.value
                        )
                        for i in to_be_created_utxos
                    ]
                    daos.bulk_create_utxos(new_utxos)

    RUNTIME_THROTTLE[runtime_throttle_key] = time.time() + 1 * 60  # expired at 1 min later
    return count


def query_utxo_ids_by_txid_vout_tuples(chain_code: str, txid_vout_tuples: List[Tuple[str, int]]) -> List[int]:
    return daos.query_utxo_ids_by_txid_vout_tuples(chain_code, txid_vout_tuples)


def get_utxos_chosen_by_txid(chain_code: str, txid: str) -> List[models.UTXO]:
    items = daos.query_who_spent_by_txid(chain_code, txid)
    return daos.query_utxos_by_ids([i.utxo_id for i in items])


@orm_database.db.atomic()
def mark_utxos_chosen_by_txid(chain_code: str, txid: str, utxo_ids: List[int]):
    if not utxo_ids:
        return

    daos.update_utxos_status(utxo_ids, data.UTXOStatus.CHOSEN)
    items = [daos.new_who_spent(chain_code, txid, i) for i in utxo_ids]
    daos.bulk_create_who_spent(items)


@orm_database.db.atomic()
def mark_utxos_spent_by_txid(chain_code: str, txid: str):
    items = daos.query_who_spent_by_txid(chain_code, txid)
    if items:
        daos.update_utxos_status([i.utxo_id for i in items], status=data.UTXOStatus.SPENT)


@orm_database.db.atomic()
def delete_utxos_by_addresses(chain_code: str, addresses: List[str]):
    utxo_ids = daos.query_utxo_ids_by_addresses(chain_code, addresses)
    if utxo_ids:
        daos.delete_utxos_by_ids(chain_code, utxo_ids)
        daos.delete_who_spent_by_utxo_ids(chain_code, utxo_ids)
