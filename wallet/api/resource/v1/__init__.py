from wallet.api.resource.v1 import chain, hardware, utility, wallet

__REAL_PATH__ = "/v1"
__RESOURCES__ = [
    utility.Migrate,
    chain.Collection,
    chain.Item,
    chain.Coins,
    chain.CoinItem,
    chain.AddCoin,
    wallet.Collection,
    wallet.Item,
    wallet.SoftwarePrimaryCreator,
    wallet.SoftwareStandaloneImporter,
    wallet.SoftwareExporter,
    hardware.Devices,
    hardware.DeviceFeature,
    hardware.Agent,
    hardware.XpubExporter,
]
