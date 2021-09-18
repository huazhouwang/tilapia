class BaseWalletModuleException(Exception):
    pass


class AddressAlreadyExistsException(BaseWalletModuleException):
    def __init__(self, chain_code: str, address: str):
        super(AddressAlreadyExistsException, self).__init__(f"chain_code: {chain_code}, address: {address}")
        self.chain_code = chain_code
        self.address = address


class AddressInvalidException(BaseWalletModuleException):
    def __init__(self, chain_code: str, address: str):
        super(AddressInvalidException, self).__init__(f"chain_code: {chain_code}, address: {address}")
        self.chain_code = chain_code
        self.address = address


class DecryptingKeystoreException(BaseWalletModuleException):
    def __init__(self, origin_exception: Exception):
        super(DecryptingKeystoreException, self).__init__(
            "Something wrong in decrypting keystore, please check your keystore and password again", origin_exception
        )


class WalletNotFound(BaseWalletModuleException):
    def __init__(self, wallet_id: int):
        super(WalletNotFound, self).__init__(f"wallet_id: {wallet_id}")
        self.wallet_id = wallet_id


class IllegalWalletState(BaseWalletModuleException):
    def __init__(self, explain: str = ""):
        super(IllegalWalletState, self).__init__(explain)


class IllegalWalletOperation(BaseWalletModuleException):
    def __init__(self, explain: str = ""):
        super(IllegalWalletOperation, self).__init__(explain)


class IllegalUnsignedTx(BaseWalletModuleException):
    pass


class UnexpectedBroadcastReceipt(BaseWalletModuleException):
    pass


class InsufficientBalance(BaseWalletModuleException):
    def __init__(self, wallet_id: int, coin_code: str, address: str, balance: int, value_required: int):
        super(InsufficientBalance, self).__init__(
            f"wallet_id: {wallet_id}, coin_code: {coin_code}, address: {address}, "
            f"balance: {balance}, value_required: {value_required}"
        )
        self.wallet_id = wallet_id
        self.coin_code = coin_code
        self.address = address
        self.balance = balance
        self.value_required = value_required


class PrimaryWalletNotExists(BaseWalletModuleException):
    def __init__(self):
        super(PrimaryWalletNotExists, self).__init__("Please create primary wallet first")


class PrimaryWalletAlreadyExists(BaseWalletModuleException):
    def __init__(self):
        super(PrimaryWalletAlreadyExists, self).__init__("Primary wallet already exists")
