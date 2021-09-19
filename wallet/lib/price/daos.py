import datetime
import functools
from decimal import Decimal
from typing import Dict, Set, Tuple

from wallet.lib.price import data, models


def create_or_update(
    coin_code: str,
    unit: str,
    channel: data.Channel,
    price: Decimal,
):
    model, is_newborn = models.Price.get_or_create(
        coin_code=coin_code,
        unit=unit,
        channel=channel,
        defaults=dict(price=price),
    )

    if not is_newborn:
        models.Price.update(
            price=price,
            modified_time=datetime.datetime.now(),
        ).where(models.Price.id == model.id).execute()


def get_last_price(
    coin_code: str,
    unit: str,
    default: Decimal = 0,
    channel: data.Channel = None,
) -> Decimal:
    query = [models.Price.coin_code == coin_code, models.Price.unit == unit]
    if channel is not None:
        query.append(models.Price.channel == channel)

    model = models.Price.select().where(*query).order_by(models.Price.modified_time.desc()).first()
    return model.price if model else default


def load_price_by_pairs(pairs: Set[Tuple[str, str]]) -> Dict[Tuple[str, str], Decimal]:
    expression = [(models.Price.coin_code == pair[0]) & (models.Price.unit == pair[1]) for pair in pairs]
    expression = functools.reduce(lambda a, b: a | b, expression)

    pair_prices = {}
    items = models.Price.select().where(expression).order_by(models.Price.modified_time.asc())

    for i in items:
        pair_prices[(i.coin_code, i.unit)] = i.price

    return pair_prices
