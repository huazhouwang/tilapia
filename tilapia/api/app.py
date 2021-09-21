def _register_routers(app):
    from tilapia.api.resource import root, v1

    for module in (root, v1):
        real_path = getattr(module, "__REAL_PATH__")
        resources = getattr(module, "__RESOURCES__")

        for clazz in resources:
            path = "/".join((real_path.rstrip("/"), getattr(clazz, "URI").lstrip("/")))
            app.add_route(path, clazz())


def _register_middlewares(app):
    from tilapia.api.middleware import json_translator

    for module in (json_translator,):
        app.add_middleware(module.Middleware())


def _register_error_handlers(app):
    from tilapia.api.error_handler import fallback, self_handle

    for module in (fallback, self_handle):
        app.add_error_handler(getattr(module, "__ERROR__"), getattr(module, "handle"))


def _ensure_env():
    import os

    os.environ["API_HOSTING"] = "1"

    import logging.config

    from tilapia.lib.conf import settings

    logging.config.dictConfig(settings.LOGGING)


def create_app():
    import falcon

    _ensure_env()

    app = falcon.App()

    _register_middlewares(app)
    _register_error_handlers(app)
    _register_routers(app)

    return app
