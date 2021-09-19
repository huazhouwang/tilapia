from trezorlib import ui as trezor_ui

from wallet.lib.hardware import interfaces
from wallet.lib.hardware.callbacks import helper


class TerminalCallback(interfaces.HardwareCallbackInterface):
    def __init__(self, always_prompt: bool = False, passphrase_on_host: bool = False, pin_on_device: bool = False):
        self.impl = trezor_ui.ClickUI(always_prompt, passphrase_on_host)
        self.pin_on_device = pin_on_device

    def button_request(self, code: int) -> None:
        return self.impl.button_request(code)

    def get_pin(self, code: int = None) -> str:
        if code == trezor_ui.PIN_CURRENT and helper.get_value_of_agent(
            "is_changing_pin", False
        ):  # If the device has a PIN and now needs to change the PIN
            current_pin = self.impl.get_pin(code)
            next_pin = self.impl.get_pin(trezor_ui.PIN_NEW)
            return current_pin.ljust(9, "0") + next_pin.ljust(9, "0")
        elif code == trezor_ui.PIN_CURRENT and self.pin_on_device:
            return "000000000"
        else:
            return self.impl.get_pin(code)

    def get_passphrase(self, available_on_device: bool) -> str:
        is_bypass = helper.get_value_of_agent("pass_state", 0)
        helper.set_value_to_agent("pass_state", 0)

        if is_bypass == 0:
            return ""

        return self.impl.get_passphrase(available_on_device)
