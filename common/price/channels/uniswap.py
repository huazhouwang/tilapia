import decimal
import itertools
import operator
from typing import Any, Iterable, List, Tuple

import eth_abi

from common.coin import data as coin_data
from common.coin import manager as coin_manager
from common.conf import settings
from common.price import data, interfaces
from common.provider import manager as provider_manager
from common.provider.chains.eth.clients import geth as geth_client

SUPPORTED_VERSIONS = {2, 3}
BATCH_SIZE = 50

# Refer to
#   v2: https://uniswap.org/docs/v2/smart-contracts/router02
#   v3: https://docs.uniswap.org/protocol/reference/periphery/interfaces/IQuoter


def _get_v2_eth_call_data(coin: coin_data.CoinInfo, paths: Tuple[Tuple]) -> List[str]:
    ret = []

    # >>> eth_utils.keccak("getAmountsOut(uint256,address[])".encode())[:4].hex()
    # 'd06ca61f'
    method_id = "d06ca61f"
    amount_in = 10 ** coin.decimals

    for path in paths:
        addresses = (coin.token_address, *path)
        params = eth_abi.encode_single("(uint256,address[])", (amount_in, addresses))
        ret.append("0x" + method_id + params.hex())

    return ret


def _get_v3_eth_call_data(coin: coin_data.CoinInfo, paths: Tuple[Tuple]) -> List[str]:
    ret = []

    # >>> eth_utils.keccak("quoteExactInput(bytes,uint256)".encode())[:4].hex()
    # 'cdca1753'
    method_id = "cdca1753"
    amount_in = 10 ** coin.decimals

    for path in paths:
        addresses = (address[-40:] for address in (coin.token_address, *path))
        # https://github.com/Uniswap/uniswap-v3-periphery/blob/main/contracts/libraries/Path.sol
        # The struct of path is
        #   token In (20 bytes) + ( ... + fee (3 bytes) + token X (20 bytes) + ...) + fee (3 bytes) + token Out (20 bytes)
        path = "000bb8".join(addresses)  # 0x000bb8(int 3000) means 0.3% fee (devided by 10^6).
        params = eth_abi.encode_single("(bytes,uint256)", (bytes.fromhex(path), amount_in))
        ret.append("0x" + method_id + params.hex())

    return ret


def _extract_price_from_resp(resp: str) -> int:
    # We want the last number only.
    return eth_abi.decode_single("uint256", bytes.fromhex(resp[2:])[-32:])


def _obtain_prices_from_dex(
    chain_code: str,
    contract_address: str,  # Router address for Uniswap V2, quoter address for V3.
    base_divisor: int,
    coins: List[Tuple[coin_data.CoinInfo, int]],
    call_data: List[str],
) -> Iterable[data.YieldedPrice]:
    client: Any = provider_manager.get_client_by_chain(chain_code, instance_required=geth_client.Geth)

    resp_iterator = iter(client.call_contract(contract_address, call_data))
    for coin, paths_count in coins:
        price = (
            decimal.Decimal(
                max(
                    _extract_price_from_resp(resp) if resp is not None else 0
                    for resp in itertools.islice(resp_iterator, paths_count)
                )
            )
            / base_divisor
        )
        if price > 0:
            yield data.YieldedPrice(coin_code=coin.code, unit=chain_code, price=price)

    yield from tuple()


class _Uniswap(interfaces.PriceChannelInterface):
    version: int

    @staticmethod
    def config(version: int) -> dict:
        return getattr(settings, "PRICE", {}).get(f"uniswap_configs_v{version}", {})

    def pricing(self, coins: Iterable[coin_data.CoinInfo]) -> Iterable[data.YieldedPrice]:
        if self.version not in SUPPORTED_VERSIONS:
            return

        coins: List[coin_data.CoinInfo] = sorted(coins, key=operator.attrgetter("chain_code"))
        for chain_code, coins_on_chain in itertools.groupby(coins, operator.attrgetter("chain_code")):
            chain_code: str
            uniswap_config = self.config(self.version).get(chain_code)
            if uniswap_config is None:
                continue

            if self.version == 2:
                contract_address = uniswap_config["router_address"]
            elif self.version == 3:
                contract_address = uniswap_config["quoter_address"]
            else:
                # Should not reach here.
                continue

            base_token_address = uniswap_config["base_token_address"]
            media_token_addresses = tuple(uniswap_config["media_token_addresses"])
            paths_for_media_tokens = ((base_token_address,),)  # Direct exchange
            paths_for_normal_tokens = paths_for_media_tokens + tuple(
                itertools.product(media_token_addresses, [base_token_address])
            )

            base_coin = coin_manager.get_coin_info(chain_code)
            base_divisor = 10 ** base_coin.decimals

            total_paths_count = 0
            coins_in_one_request = []
            data_in_one_request = []
            for coin in coins_on_chain:
                if coin.token_address is None:  # Not a token
                    continue
                elif coin.token_address == base_token_address:  # It's a base token, i.e., a WETH/WBNB/WHT...
                    yield data.YieldedPrice(coin_code=coin.code, unit=base_coin.code, price=decimal.Decimal("1"))
                    continue
                elif coin.token_address in media_token_addresses:  # A media token
                    paths = paths_for_media_tokens
                else:
                    paths = paths_for_normal_tokens

                paths_count_of_this_coin = len(paths)
                coins_in_one_request.append((coin, paths_count_of_this_coin))
                if self.version == 2:
                    data_in_one_request.extend(_get_v2_eth_call_data(coin, paths))
                elif self.version == 3:
                    data_in_one_request.extend(_get_v3_eth_call_data(coin, paths))

                total_paths_count += paths_count_of_this_coin
                if total_paths_count >= BATCH_SIZE:
                    yield from _obtain_prices_from_dex(
                        chain_code, contract_address, base_divisor, coins_in_one_request, data_in_one_request
                    )
                    total_paths_count = 0
                    coins_in_one_request = []
                    data_in_one_request = []

            if data_in_one_request:
                yield from _obtain_prices_from_dex(
                    chain_code, contract_address, base_divisor, coins_in_one_request, data_in_one_request
                )
            else:
                yield from tuple()


class UniswapV2(_Uniswap):
    version = 2


class UniswapV3(_Uniswap):
    version = 3
