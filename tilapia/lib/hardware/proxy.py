import hashlib
import logging
import time
from typing import Any

from trezorlib import client as trezor_client
from trezorlib import device as trezor_device
from trezorlib import ethereum as trezor_ethereum
from trezorlib import exceptions as trezor_exceptions
from trezorlib import protobuf as trezor_protobuf
from trezorlib import transport as trezor_transport
from trezorlib.transport import bridge as trezor_bridge

from tilapia.lib.basic import bip44
from tilapia.lib.hardware import exceptions, interfaces
from tilapia.lib.hardware.callbacks import helper

logger = logging.getLogger("app.hardware")


def _force_release_old_session_as_need(device: trezor_transport.Transport):
    if not isinstance(device, trezor_bridge.BridgeTransport):
        return

    splits = device.get_path().split(":")
    target_path = splits[1] if len(splits) == 2 else None
    if not target_path:
        return

    try:
        enumerates_by_bridge = trezor_bridge.call_bridge("enumerate").json()
        target = [i for i in enumerates_by_bridge if i.get("path") == target_path and i.get("session")]
        if target:
            old_session = target[0].get("session")
            trezor_bridge.call_bridge(f"release/{old_session}")
    except Exception as e:
        logger.exception(
            f"Error in enumerating or releasing specific device. device_path: {device.get_path()}, error: {e}"
        )


class HardwareProxyClient(interfaces.HardwareClientInterface):
    def __init__(self, device: trezor_transport.Transport, callback: interfaces.HardwareCallbackInterface):
        _force_release_old_session_as_need(device)
        self._client = trezor_client.TrezorClient(device, ui=callback)

    def ensure_device(self):
        """
        Ensure device, clear old connection and apply migrations
        """
        _force_release_old_session_as_need(self._client.transport)
        self._client.init_device(new_session=True)

    def call(self, *args, **kwargs) -> Any:
        return self._client.call(*args, **kwargs)

    def open(self) -> None:
        return self._client.open()

    def close(self) -> None:
        return self._client.close()

    def ping(self, message: str) -> str:
        """
        Ping the device, then device should return the same string as the requesting message
        """
        return self._client.ping(message)

    def get_feature(self, force_refresh: bool = False) -> dict:
        """
        Get the feature of device.
        See trezorlib.messages.Features for details
        """
        if force_refresh:
            self._client.refresh_features()

        return trezor_protobuf.to_dict(self._client.features)

    def get_key_id(self) -> str:
        """
        Bind the mnemonic of the device through the public key hash under a certain path
        """
        binding_path = bip44.BIP44Path.from_bip44_path(
            "m/10146782'/0'/0'"
        )  # 10146782 = int(b"One".hex(), base=16) + int(b"Key".hex(), base=16)
        pubkey = trezor_ethereum.get_public_node(
            self._client,
            n=binding_path.to_bip44_int_path(),
        ).node.public_key
        return hashlib.sha256(pubkey).digest().hex()[:16]

    def apply_settings(self, settings: dict) -> bool:
        """
        Apply settings.
        See trezorlib.messages.ApplySettings for details
        """
        result = trezor_device.apply_settings(self._client, **settings)
        return result == "Settings applied"

    def setup_mnemonic_on_device(
        self,
        language: str = "english",
        label: str = "OneKey",
        mnemonic_strength: int = 128,
    ) -> bool:
        """
        Set the device to hardware wallet mode, then automatically create mnemonic inside the device.
        Require 'wipe_device' first if the device is initialized already
        """
        result = trezor_device.reset(
            self._client,
            language=language,
            label=label,
            strength=mnemonic_strength,
        )
        return result == "Device successfully initialized"

    def setup_or_change_pin(self) -> bool:
        """
        Setup or change the PIN of device
        """
        try:
            helper.set_value_to_agent("is_changing_pin", True)
            result = trezor_device.change_pin(self._client, False)
            return result == "PIN changed"
        except (trezor_exceptions.PinException, RuntimeError):
            return False
        except Exception:
            raise exceptions.Cancelled()
        finally:
            helper.set_value_to_agent("is_changing_pin", False)

    def wipe_device(self) -> bool:
        """
        Wipe device data
        """
        try:
            result = trezor_device.wipe(self._client)
            return result == "Device wiped"
        except (trezor_exceptions.PinException, RuntimeError):
            return False

    def reboot_to_bootloader(self) -> bool:
        """
        Reboot to bootloader
        """
        if self.get_feature(force_refresh=True).get("bootloader_mode", False):
            return True

        trezor_device.reboot_to_bootloader(self._client)
        time.sleep(2)
        self.ensure_device()
        return self.get_feature().get("bootloader_mode", False)
