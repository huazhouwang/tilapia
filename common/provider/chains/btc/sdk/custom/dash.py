from pycoin.coins.bitcoin.Tx import Tx
from pycoin.networks.bitcoinish import create_bitcoinish_network
from pycoin.satoshi.satoshi_struct import parse_struct, stream_struct


def is_dash_special_transaction():
    pass


class DashTx(Tx):
    DASH_NORMAL = 0
    DASH_QUORUM_COMMITMENT = 6

    def __init__(self, *args, **kwargs):
        super(DashTx, self).__init__(*args, **kwargs)
        self.type = self.version >> 16
        self.real_version = self.version & 0xFFFF
        self.extra_data = b""

        if self.real_version == 3 and (self.type < self.DASH_NORMAL or self.type > self.DASH_QUORUM_COMMITMENT):
            raise Exception("Unsupported Dash transaction type")

    def is_dash_special_transaction(self) -> bool:
        return self.real_version >= 3 and self.type != self.DASH_NORMAL

    @classmethod
    def parse(cls, f, *args, **kwargs):
        instance = super(DashTx, cls).parse(f, *args, **kwargs)

        if instance.is_dash_special_transaction():
            (extra_data,) = parse_struct("S", f)
            instance.extra_data = extra_data

        return instance

    def stream(self, f, *args, **kwargs):
        super(DashTx, self).stream(f, *args, **kwargs)

        if self.is_dash_special_transaction():
            stream_struct("S", f, self.extra_data)


network = create_bitcoinish_network(
    symbol="DASH",
    network_name="DarkCoin",
    subnet_name="mainnet",
    tx=DashTx,
    wif_prefix_hex="cc",
    address_prefix_hex="4c",
    pay_to_script_prefix_hex="10",
    bip32_prv_prefix_hex="02fe52f8",
    bip32_pub_prefix_hex="02fe52cc",
)
