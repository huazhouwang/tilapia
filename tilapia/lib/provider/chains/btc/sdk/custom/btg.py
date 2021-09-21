from pycoin.coins.bgold.Block import Block as BgoldBlock
from pycoin.coins.bgold.Tx import Tx as BgoldTx
from pycoin.networks.bitcoinish import create_bitcoinish_network

network = create_bitcoinish_network(
    symbol="BTG",
    network_name="Bitcoin Gold",
    subnet_name="mainnet",
    tx=BgoldTx,
    block=BgoldBlock,
    wif_prefix_hex="80",
    sec_prefix="BTGSEC:",
    address_prefix_hex="26",
    pay_to_script_prefix_hex="17",
    bip32_prv_prefix_hex="0488ade4",
    bip32_pub_prefix_hex="0488B21E",
    magic_header_hex="e1476d44",
    bech32_hrp="btg",
)
