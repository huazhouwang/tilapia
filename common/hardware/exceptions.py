from trezorlib.exceptions import Cancelled  # noqa F401


class GeneralHardwareException(Exception):
    pass


class NoAvailableDevice(GeneralHardwareException):
    pass


class CallbackTimeout(Cancelled):
    def __init__(self):
        super(CallbackTimeout, self).__init__("timeout")
