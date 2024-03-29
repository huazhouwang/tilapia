import time


class Root:
    URI = ""

    def on_get(self, req, resp):
        resp.media = "Tilapia"


class Ping:
    URI = "ping"

    def on_get(self, req, resp):
        resp.media = {"pong": int(time.time())}


__REAL_PATH__ = "/"
__RESOURCES__ = [
    Root,
    Ping,
]
