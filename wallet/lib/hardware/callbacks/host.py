import logging

from wallet.lib.hardware.callbacks import base, helper

logger = logging.getLogger("app.callback")


class HostCallback(base.BaseCallback):
    def notify_handler(self, code: int):
        logger.debug(f"notify hardware handler. code: {code}, agent: {helper.dump_agent()}")

        if 200 <= code < 300:
            from trezorlib import ui as trezor_ui

            logger.debug(trezor_ui.PIN_MATRIX_DESCRIPTION)
