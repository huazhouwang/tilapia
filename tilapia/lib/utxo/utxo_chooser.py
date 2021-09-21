import random
from typing import Callable


def choose(utxos: list, target: int, key: Callable = None) -> list:
    """
    The simplest sliding window solution，and its time complexity is n.
    It isn't the best solution, but simple and fast enough.
    """
    key = key or (lambda m: m)
    random.seed(key(utxos[0]))
    random.shuffle(utxos)  # Deterministically shuffle the utxos

    min_window = None
    window_left = 0
    window_sum = 0

    for i in range(len(utxos)):
        value = key(utxos[i])
        if value >= target:
            min_window = (i, i + 1)  # Already found
            break

        window_sum += value

        while window_sum >= target:
            if not min_window or i + 1 - window_left < min_window[1] - min_window[0]:
                min_window = (window_left, i + 1)

            window_sum -= key(utxos[window_left])
            window_left += 1

    return utxos[min_window[0] : min_window[1]] if min_window else utxos
