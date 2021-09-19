from abc import ABC, abstractmethod
from typing import Iterable

from wallet.lib.coin.data import CoinInfo
from wallet.lib.price.data import YieldedPrice


class PriceChannelInterface(ABC):
    @abstractmethod
    def pricing(self, coins: Iterable[CoinInfo]) -> Iterable[YieldedPrice]:
        pass
