from enum import IntEnum, unique


@unique
class WalletType(IntEnum):
    WATCHONLY = 10

    SOFTWARE_PRIMARY = 21
    SOFTWARE_STANDALONE_MNEMONIC = 22
    SOFTWARE_STANDALONE_PRVKEY = 23

    HARDWARE_PRIMARY = 31
    HARDWARE_STANDALONE = 32

    @classmethod
    def to_choices(cls):
        return (
            (cls.WATCHONLY, "Watchonly Wallet"),
            (cls.SOFTWARE_PRIMARY, "Primary Software Wallet"),
            (cls.SOFTWARE_STANDALONE_MNEMONIC, "Standalone Software Wallet From Mnemonic"),
            (cls.SOFTWARE_STANDALONE_PRVKEY, "Standalone Software Wallet From PrivateKey"),
            (cls.HARDWARE_PRIMARY, "Primary Hardware Wallet"),
            (cls.HARDWARE_STANDALONE, "Standalone Hardware Wallet"),
        )

    @staticmethod
    def is_watchonly_wallet(wallet_type: int) -> bool:
        return wallet_type == WalletType.WATCHONLY

    @staticmethod
    def is_software_wallet(wallet_type: int) -> bool:
        return wallet_type in (
            WalletType.SOFTWARE_PRIMARY,
            WalletType.SOFTWARE_STANDALONE_PRVKEY,
            WalletType.SOFTWARE_STANDALONE_MNEMONIC,
        )

    @staticmethod
    def is_hardware_wallet(wallet_type: int) -> bool:
        return wallet_type in (WalletType.HARDWARE_PRIMARY, WalletType.HARDWARE_STANDALONE)

    @classmethod
    def from_int(cls, val: int) -> "WalletType":
        return cls(val)
