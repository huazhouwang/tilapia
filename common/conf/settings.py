import os
from os import environ, path
from typing import Literal

runtime: Literal["android", "ios", "others"] = "others"
if "iOS_DATA" in environ:
    runtime = "ios"
elif "ANDROID_DATA" in environ:
    runtime = "android"

IS_DEV = os.environ.get("IS_DEV") == "True"

PROJECT_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
DATA_DIR = f"{PROJECT_DIR}/data"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }
    },
}

DATABASE = {
    "default": {
        "name": f"{DATA_DIR}/database.sqlite",
    },
}

DB_MODULES = [
    "common.coin",
    "common.price",
    "common.transaction",
    "common.secret",
    "common.wallet",
    "common.utxo",
]

# loading local_settings.py on project root
try:
    from local_settings import *  # noqa
except ImportError:
    pass
