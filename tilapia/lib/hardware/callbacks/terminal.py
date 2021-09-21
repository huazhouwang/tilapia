from trezorlib import ui as trezor_ui

from tilapia.lib.hardware import interfaces
from tilapia.lib.hardware.callbacks import helper


class TerminalCallback(interfaces.HardwareCallbackInterface):
    def __init__(self, always_prompt: bool = False, passphrase_on_host: bool = False, pin_on_device: bool = False):
        self.impl = trezor_ui.ClickUI(always_prompt, passphrase_on_host)
        self.pin_on_device = pin_on_device

    def button_request(self, code: int) -> None:
        return self.impl.button_request(code)

    def get_pin(self, code: int = None) -> str:
        return self.impl.get_pin(code)

    def get_passphrase(self, available_on_device: bool) -> str:
        is_bypass = helper.get_value_of_agent("bypass_passphrase", 0)
        helper.set_value_to_agent("bypass_passphrase", 0)

        if is_bypass:
            return ""

        return self.impl.get_passphrase(available_on_device)
