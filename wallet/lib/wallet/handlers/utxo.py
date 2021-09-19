import logging
from typing import List, Optional, Tuple

from wallet.lib.basic.functional.timing import timing_logger
from wallet.lib.coin import data as coin_data
from wallet.lib.coin import manager as coin_manager
from wallet.lib.provider import data as provider_data
from wallet.lib.provider import manager as provider_manager
from wallet.lib.utxo import data as utxo_data
from wallet.lib.utxo import manager as utxo_manager
from wallet.lib.utxo import models as utxo_models
from wallet.lib.wallet import daos, interfaces

logger = logging.getLogger("app.chain")


class UTXOChainModelHandler(interfaces.ChainModelInterface):
    def generate_unsigned_tx(
        self,
        wallet_id: int,
        coin_code: str,
        to_address: Optional[str] = None,
        value: Optional[int] = None,
        nonce: Optional[int] = None,
        fee_limit: Optional[int] = None,
        fee_price_per_unit: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> provider_data.UnsignedTx:
        chain_coin, _, fee_coin = coin_manager.get_related_coins(coin_code)
        chain_code = chain_coin.code

        if chain_coin.code != fee_coin.code:
            raise Exception("Dual token model isn't supported yet")

        chain_info = coin_manager.get_chain_info(chain_code)

        if not to_address or not value or value < chain_info.dust_threshold:
            return provider_manager.fill_unsigned_tx(chain_code, provider_data.UnsignedTx())

        account = daos.account.query_first_account_by_wallet(wallet_id)

        fee_limit = int(fee_limit) if fee_limit is not None else 0
        fee_price_per_unit = int(fee_price_per_unit) if fee_price_per_unit is not None else 0
        payload = dict(payload) if payload is not None else {}
        input_addresses = [account.address]
        outputs = [provider_data.TransactionOutput(address=to_address, value=int(value))]
        change_output_placeholder = provider_data.TransactionOutput(
            address=account.address,
            value=0,
            payload={"is_change": True, "bip44_path": account.bip44_path},  # Required by hardware
        )
        utxos, fee_price_per_unit, fee_limit = _choose_utxos(
            coin_code,
            chain_info,
            input_addresses,
            outputs,
            change_output_placeholder,
            fee_limit,
            fee_price_per_unit,
            payload,
        )

        input_value = sum(i.value for i in utxos)
        fee = fee_price_per_unit * fee_limit
        change = input_value - value - fee
        if change < 0:
            logger.warning("Input value is lower than output value")
            value = input_value - fee
            if value <= 0:
                raise Exception("Not enough utxos for fee, please wait until the previous transactions are confirmed")

            logger.warning(
                f"Use new value({value}) as output which is calculated by input_value({input_value}) - fee({fee})"
            )
            outputs = [provider_data.TransactionOutput(address=to_address, value=value)]
            change = 0
        elif 0 < change < chain_info.dust_threshold:
            # Spend change as fee if it is less than dust_threshold
            fee = input_value - value - change
            fee_price_per_unit = int(fee / fee_limit)
            change = 0

        unsigned_tx = _build_unsigned_tx(
            chain_info, utxos, change, outputs, change_output_placeholder, fee_price_per_unit, fee_limit, payload
        )
        return unsigned_tx


@timing_logger("utxo_handler.choose_utxos")
def _choose_utxos(
    coin_code: str,
    chain_info: coin_data.ChainInfo,
    input_addresses: List[str],
    outputs: List[provider_data.TransactionOutput],
    change_output_placeholder: provider_data.TransactionOutput,
    fee_limit: int,
    fee_price_per_unit: int,
    payload: dict,
) -> Tuple[List[utxo_models.UTXO], int, int]:
    for address in input_addresses:
        utxo_manager.refresh_utxos_by_address(coin_code, address)

    chain_code, dust_threshold = chain_info.chain_code, chain_info.dust_threshold

    fee = fee_price_per_unit * fee_limit
    output_value = sum(i.value for i in outputs)
    require_value = output_value + fee
    ratio = 1
    input_value = 0
    utxos = ()

    for times in range(4):  # ratio is 1, 1.1, 1.3, 1.7
        utxos = utxo_manager.choose_utxos(
            coin_code,
            input_addresses,
            require_value=int(require_value * ratio),
            status=utxo_data.UTXOStatus.SPENDABLE,
            min_value=dust_threshold,
        )
        ratio += (1 << times) / 10

        sum_of_utxos = sum(i.value for i in utxos)
        if sum_of_utxos <= input_value:  # Can't find more UTXOs
            break

        input_value = sum_of_utxos
        change = max(input_value - require_value, 0)
        unsigned_tx = _build_unsigned_tx(
            chain_info, utxos, change, outputs, change_output_placeholder, fee_price_per_unit, fee_limit, payload
        )
        unsigned_tx = provider_manager.fill_unsigned_tx(chain_code, unsigned_tx)
        fee_limit, fee_price_per_unit = unsigned_tx.fee_limit, unsigned_tx.fee_price_per_unit
        fee = fee_limit * fee_price_per_unit
        require_value = output_value + fee
        if input_value >= require_value:
            break

    return utxos, fee_price_per_unit, fee_limit


def _build_unsigned_tx(
    chain_info: coin_data.ChainInfo,
    utxos: List[utxo_models.UTXO],
    change: int,
    outputs: List[provider_data.TransactionOutput],
    change_output_placeholder: provider_data.TransactionOutput,
    fee_price_per_unit: int,
    fee_limit: int,
    payload: dict,
) -> provider_data.UnsignedTx:
    change_output = () if change < chain_info.dust_threshold else (change_output_placeholder.clone(value=int(change)),)

    return provider_data.UnsignedTx(
        inputs=[
            provider_data.TransactionInput(
                address=i.address,
                value=int(i.value),
                utxo=provider_data.UTXO(
                    txid=i.txid,
                    vout=int(i.vout),
                    value=int(i.value),
                ),
            )
            for i in utxos
        ],
        outputs=[
            *outputs,
            *change_output,
        ],
        fee_price_per_unit=fee_price_per_unit,
        fee_limit=fee_limit,
        payload=payload,
    )
