from wallet.api.resource.v1 import chain, hardware, hardware_wallet, software_wallet, utility, wallet

__REAL_PATH__ = "/v1"
__RESOURCES__ = [
    utility.Migrate,
    utility.Ticker,
    chain.Collection,
    chain.Item,
    chain.Coins,
    chain.CoinItem,
    chain.AddCoin,
    chain.FeePrice,
    wallet.Collection,
    wallet.Item,
    wallet.PreSend,
    wallet.Send,
    software_wallet.PrimaryCreator,
    software_wallet.StandaloneImporter,
    software_wallet.Exporter,
    hardware.Devices,
    hardware.DeviceFeature,
    hardware.Agent,
    hardware.XpubExporter,
    hardware_wallet.PrimaryCreator,
    hardware_wallet.StandaloneCreator,
]
