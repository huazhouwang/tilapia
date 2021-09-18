from enum import IntEnum, unique

from common.provider.data import TransactionStatus


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
    TransactionStatus.PENDING: TxActionStatus.PENDING,
    TransactionStatus.CONFIRM_SUCCESS: TxActionStatus.CONFIRM_SUCCESS,
    TransactionStatus.CONFIRM_REVERTED: TxActionStatus.CONFIRM_REVERTED,
}
