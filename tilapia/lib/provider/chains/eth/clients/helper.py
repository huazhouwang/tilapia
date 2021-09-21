from tilapia.lib.provider import exceptions

_MAPPING = {
    "already known": exceptions.TransactionAlreadyKnown,
    "nonce too low": exceptions.TransactionNonceTooLow,
    "transaction underpriced": exceptions.TransactionUnderpriced,
    "gas too low": exceptions.TransactionGasTooLow,
    "gas limit exceeded": exceptions.TransactionGasLimitExceeded,
    "insufficient funds": exceptions.InsufficientBalance,
}


def raise_broadcast_error(error_message: str) -> None:
    for keywords, exception_class in _MAPPING.items():
        if keywords in error_message:
            break
    else:
        exception_class = exceptions.UnknownBroadcastError

    raise exception_class(error_message)
