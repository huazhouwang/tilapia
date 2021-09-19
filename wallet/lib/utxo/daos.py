import datetime
import functools
from typing import List, Tuple

import peewee

from wallet.lib.utxo import data, models


def new_utxo(
    chain_code: str,
    coin_code: str,
    address: str,
    txid: str,
    vout: int,
    status: data.UTXOStatus,
    value: int,
) -> models.UTXO:
    return models.UTXO(
        chain_code=chain_code,
        coin_code=coin_code,
        address=address,
        txid=txid,
        vout=vout,
        status=status,
        value=value,
    )


def bulk_create_utxos(utxos: List[models.UTXO]):
    return models.UTXO.bulk_create(utxos, batch_size=10)


def list_utxos_by_conditions(
    coin_code: str,
    addresses: List[str],
    status: data.UTXOStatus = None,
    min_value: int = None,
    max_value: int = None,
    value_desc: bool = True,
    exclude_ids: List[int] = None,
    limit: int = None,
) -> List[models.UTXO]:
    return list(
        _select_utxos_by_conditions(
            coin_code=coin_code,
            addresses=addresses,
            status=status,
            min_value=min_value,
            max_value=max_value,
            value_desc=value_desc,
            exclude_ids=exclude_ids,
            limit=limit,
        )
    )


def sum_of_utxos_by_conditions(
    coin_code: str,
    addresses: List[str],
    status: data.UTXOStatus = None,
    min_value: int = None,
    max_value: int = None,
    value_desc: bool = True,
    exclude_ids: List[int] = None,
    limit: int = None,
) -> int:
    sub_query = _select_utxos_by_conditions(
        coin_code=coin_code,
        addresses=addresses,
        status=status,
        min_value=min_value,
        max_value=max_value,
        value_desc=value_desc,
        exclude_ids=exclude_ids,
        limit=limit,
    ).select(models.UTXO.value)
    sum_of_query = sub_query.select_from(peewee.fn.SUM(sub_query.c.value)).scalar()
    return sum_of_query or 0


def _select_utxos_by_conditions(
    coin_code: str,
    addresses: List[str],
    status: data.UTXOStatus = None,
    min_value: int = None,
    max_value: int = None,
    value_desc: bool = True,
    exclude_ids: List[int] = None,
    limit: int = None,
) -> peewee.ModelSelect:
    expressions = [models.UTXO.coin_code == coin_code, models.UTXO.address.in_(addresses)]

    status is None or expressions.append(models.UTXO.status == status)
    min_value is None or expressions.append(models.UTXO.value >= int(min_value))
    max_value is None or expressions.append(models.UTXO.value < int(max_value))
    exclude_ids is None or expressions.append(models.UTXO.id.not_in(exclude_ids))

    return (
        models.UTXO.select()
        .where(*expressions)
        .order_by(models.UTXO.value.desc() if value_desc else models.UTXO.value.asc())
        .limit(limit)
    )


def query_utxos_by_ids(utxo_ids: List[int]) -> List[models.UTXO]:
    return list(models.UTXO.select().where(models.UTXO.id.in_(utxo_ids)))


def query_utxo_ids_by_txid_vout_tuples(chain_code: str, txid_vout_tuples: List[Tuple[str, int]]) -> List[models.UTXO]:
    res = []

    for batch in peewee.chunked(txid_vout_tuples, 10):
        expression = [
            models.UTXO.chain_code == chain_code,
            functools.reduce(
                lambda a, b: a | b, ((models.UTXO.txid == txid) & (models.UTXO.vout == vout) for txid, vout in batch)
            ),
        ]

        query = models.UTXO.select(models.UTXO.id).where(*expression).tuples()
        res.extend(i[0] for i in query)

    return res


def query_utxo_ids_by_addresses(chain_code: str, addresses: List[str]) -> List[int]:
    query = (
        models.UTXO.select(models.UTXO.id)
        .where(models.UTXO.chain_code == chain_code, models.UTXO.address.in_(addresses))
        .tuples()
    )
    return [i[0] for i in query]


def delete_utxos_by_ids(chain_code: str, utxo_ids: List[int]):
    for batch in peewee.chunked(utxo_ids, 10):
        models.UTXO.delete().where(models.UTXO.chain_code == chain_code, models.UTXO.id.in_(batch)).execute()


def update_utxos_status(utxo_ids: List[int], status: data.UTXOStatus) -> int:
    return (
        models.UTXO.update(status=status, modified_time=datetime.datetime.now())
        .where(models.UTXO.id.in_(utxo_ids))
        .execute()
    )


def bulk_update_utxos_status(utxos: List[models.UTXO]) -> int:
    now = datetime.datetime.now()
    for i in utxos:
        i.modified_time = now

    return models.UTXO.bulk_update(utxos, [models.UTXO.status, models.UTXO.modified_time], batch_size=10)


def new_who_spent(chain_code: str, txid: str, utxo_id: int) -> models.WhoSpent:
    return models.WhoSpent(chain_code=chain_code, txid=txid, utxo_id=utxo_id)


def bulk_create_who_spent(who_spent: List[models.WhoSpent]):
    return models.WhoSpent.bulk_create(who_spent, batch_size=10)


def query_who_spent_by_txid(chain_code: str, txid: str) -> List[models.WhoSpent]:
    return list(models.WhoSpent.select().where(models.WhoSpent.chain_code == chain_code, models.WhoSpent.txid == txid))


def delete_who_spent_by_utxo_ids(chain_code: str, utxo_ids: List[int]):
    for batch in peewee.chunked(utxo_ids, 10):
        models.WhoSpent.delete().where(
            models.WhoSpent.chain_code == chain_code, models.WhoSpent.utxo_id.in_(batch)
        ).execute()
