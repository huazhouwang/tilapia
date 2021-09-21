from falcon.media.validators import jsonschema

from tilapia.lib.basic.functional.require import require
from tilapia.lib.hardware import manager as hardware_manager
from tilapia.lib.provider import manager as provider_manager


class _Hardware:
    URI = "hardware"


class Devices:
    URI = _Hardware.URI + "/devices"

    def on_get(self, req, resp):
        devices = list(hardware_manager.enumerate_all_devices().keys())
        resp.media = devices


class DeviceFeature:
    URI = Devices.URI + "/feature"

    def on_get(self, req, resp):
        device_path = req.params["device_path"]
        feature = hardware_manager.get_feature(device_path)
        resp.media = feature


class Agent:
    URI = _Hardware.URI + "/agent"

    def on_get(self, req, resp):
        resp.media = hardware_manager.dump_hardware_agent()

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["name", "value"],
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp):
        name, value = req.media["name"], req.media["value"]
        require(name in ("pin", "passphrase"))
        hardware_manager.update_hardware_agent(name, value)


class XpubExporter:
    URI = _Hardware.URI + "/xpub/{chain_code}"

    def on_get(self, req, resp, chain_code):
        device_path, bip44_path, confirm_on_device = (
            req.params["device_path"],
            req.params["bip44_path"],
            req.params.get("confirm_on_device", False),
        )
        resp.media = provider_manager.hardware_get_xpub(chain_code, device_path, bip44_path, confirm_on_device)
