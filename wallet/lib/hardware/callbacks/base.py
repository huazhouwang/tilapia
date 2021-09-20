import abc
import logging

from wallet.lib.hardware import exceptions, interfaces
from wallet.lib.hardware.callbacks import helper

logger = logging.getLogger("app.hardware")


class BaseCallback(interfaces.HardwareCallbackInterface, abc.ABC):
    @abc.abstractmethod
    def notify_handler(self, code: int):
        pass

    def button_request(self, code: int):
        code = 100 + int(code)
        self.notify_handler(code)

    def get_pin(self, code: int = None) -> str:
        code = 200 + int(code)

        with helper.require_specific_value_of_agent("pin", code) as waiting_input:
            self.notify_handler(code)
            pin = waiting_input()

            if not isinstance(pin, str) or not pin:
                raise exceptions.Cancelled()

            return pin

    def get_passphrase(self, available_on_device: bool) -> str:
        is_bypass = helper.get_value_of_agent("bypass_passphrase", 0)
        helper.set_value_to_agent("bypass_passphrase", 0)

        if is_bypass:
            return ""

        code = 300 + 1
        with helper.require_specific_value_of_agent("passphrase", code) as waiting_input:
            self.notify_handler(code)
            passphrase = waiting_input()

            if not isinstance(passphrase, str):
                raise exceptions.Cancelled()

            return passphrase
