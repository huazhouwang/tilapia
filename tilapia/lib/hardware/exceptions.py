from trezorlib.exceptions import Cancelled  # noqa F401


class NoAvailableDevice(Exception):
    pass


class CallbackTimeout(Cancelled):
    def __init__(self):
        super(CallbackTimeout, self).__init__("timeout")
