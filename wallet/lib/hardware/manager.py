import logging
import os
import time
from typing import Dict, Tuple

from trezorlib import transport as trezor_transport
from trezorlib.transport import bridge as trezor_bridge

from wallet.lib.conf import settings
from wallet.lib.hardware import callbacks, exceptions, proxy

logger = logging.getLogger("app.hardware")

_CLIENTS: Dict[str, Tuple[proxy.HardwareProxyClient, int]] = {}


def enumerate_all_devices() -> Dict[str, trezor_transport.Transport]:
    try:
        try:
            enumerates_by_bridge = trezor_bridge.call_bridge("enumerate").json()
        except Exception as e:
            logger.debug(f"Error in enumerating devices from bridge, try others. error: {e}", exc_info=True)
            devices = trezor_transport.enumerate_devices()
        else:
            legacy = trezor_bridge.is_legacy_bridge()
            devices = [trezor_bridge.BridgeTransport(i, legacy) for i in enumerates_by_bridge]
    except Exception as e:
        logger.exception(f"Error in enumerating devices. error: {e}")
        devices = []

    return {i.get_path(): i for i in devices}


def _create_client(device: trezor_transport.Transport) -> proxy.HardwareProxyClient:
    if settings.runtime == "ios":
        callback = callbacks.IOSCallback()
    elif settings.runtime == "android":
        callback = callbacks.AndroidCallback()
    else:
        callback = callbacks.TerminalCallback(
            always_prompt=True, pin_on_device=os.environ.get("HARDWARE_PIN_ON_DEVICE") == "True"
        )

    return proxy.HardwareProxyClient(device, callback)


def get_client(hardware_device_path: str, force_check: bool = False) -> proxy.HardwareProxyClient:
    client, expired_at = _CLIENTS.get(hardware_device_path) or (None, None)

    if not force_check and expired_at is not None and expired_at > time.time():
        return client

    if not client:
        devices = enumerate_all_devices()
        devices = [device for path, device in devices.items() if path == hardware_device_path]
        client = _create_client(devices[0]) if devices else None

    if not client:
        raise exceptions.NoAvailableDevice()

    client.ensure_device()
    _CLIENTS[hardware_device_path] = (client, int(time.time() + 10))
    return client


def ping(hardware_device_path: str, message: str) -> str:
    return get_client(hardware_device_path).ping(message)


def get_feature(hardware_device_path: str, force_refresh: bool = False) -> dict:
    return get_client(hardware_device_path, force_check=force_refresh).get_feature(force_refresh)


def get_key_id(hardware_device_path: str) -> str:
    return get_client(hardware_device_path).get_key_id()


def apply_settings(hardware_device_path: str, settings: dict) -> bool:
    return get_client(hardware_device_path).apply_settings(settings)


def setup_mnemonic_on_device(
    hardware_device_path: str,
    language: str = "english",
    label: str = "OneKey",
    mnemonic_strength: int = 128,
) -> bool:
    return get_client(hardware_device_path).setup_mnemonic_on_device(language, label, mnemonic_strength)


def setup_or_change_pin(hardware_device_path: str) -> bool:
    return get_client(hardware_device_path).setup_or_change_pin()


def wipe_device(hardware_device_path: str) -> bool:
    return get_client(hardware_device_path).wipe_device()
