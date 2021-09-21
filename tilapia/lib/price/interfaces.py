from abc import ABC, abstractmethod
from typing import Iterable

from tilapia.lib.coin.data import CoinInfo
from tilapia.lib.price.data import YieldedPrice


class PriceChannelInterface(ABC):
    @abstractmethod
    def pricing(self, coins: Iterable[CoinInfo]) -> Iterable[YieldedPrice]:
        pass
