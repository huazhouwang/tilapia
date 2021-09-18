from common.basic.functional.require import require_not_none
from common.hardware.callbacks import base


class IOSCallback(base.BaseCallback):
    def __init__(self):
        # noinspection PyUnresolvedReferences, PyPackageRequirements
        from rubicon.objc import ObjCClass

        self.ios_handler = require_not_none(
            ObjCClass("OKHwNotiManager").sharedInstance().getNotificationCenter(),
            "Failed to init NotificationCenter for iOS",
        )

    def notify_handler(self, code: int):
        self.ios_handler.postNotificationName_object_("HardwareNotifications", str(code))
