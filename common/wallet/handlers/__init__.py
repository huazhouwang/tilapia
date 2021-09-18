from common.coin import data as coin_data
from common.wallet.handlers import account, utxo

_REGISTER = {
    coin_data.ChainModel.ACCOUNT: account.AccountChainModelHandler,
    coin_data.ChainModel.UTXO: utxo.UTXOChainModelHandler,
}
_CACHE = {}


def get_handler_by_chain_model(chain_model: coin_data.ChainModel):
    if chain_model not in _REGISTER:
        raise NotImplementedError()

    handler = _CACHE.get(chain_model)
    if handler is None:
        handler = _REGISTER[chain_model]()
        _CACHE[chain_model] = handler

    return handler
