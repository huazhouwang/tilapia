from enum import IntEnum, unique

from wallet.lib.provider import data as provider_data


@unique
class TxActionStatus(IntEnum):
    UNEXPECTED_FAILED = -99
    REPLACED = -10
    SIGNED = -1
    UNKNOWN = 0
    PENDING = 1
    CONFIRM_REVERTED = 2
    CONFIRM_SUCCESS = 3

    @classmethod
    def to_choices(cls):
        return (
            (cls.UNEXPECTED_FAILED, "Unexpected Failed"),
            (cls.SIGNED, "Signed"),
            (cls.PENDING, "Pending"),
            (cls.REPLACED, "Replaced"),
            (cls.CONFIRM_REVERTED, "Confirm Reverted"),
            (cls.CONFIRM_SUCCESS, "Confirmed Success"),
        )


TX_TO_ACTION_STATUS_DIRECT_MAPPING = {
    provider_data.TransactionStatus.PENDING: TxActionStatus.PENDING,
    provider_data.TransactionStatus.CONFIRM_SUCCESS: TxActionStatus.CONFIRM_SUCCESS,
    provider_data.TransactionStatus.CONFIRM_REVERTED: TxActionStatus.CONFIRM_REVERTED,
}
