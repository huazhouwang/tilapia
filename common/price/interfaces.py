from abc import ABC, abstractmethod
from typing import Iterable

from common.coin.data import CoinInfo
from common.price.data import YieldedPrice


class PriceChannelInterface(ABC):
    @abstractmethod
    def pricing(self, coins: Iterable[CoinInfo]) -> Iterable[YieldedPrice]:
        pass
