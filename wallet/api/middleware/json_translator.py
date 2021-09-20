import logging

from wallet import version
from wallet.lib.basic.functional.json import json_stringify
from wallet.lib.conf import settings

logger = logging.getLogger("app.middleware")


class Middleware(object):
    def process_response(self, req, resp, resource, req_succeeded):
        logger.debug(
            f"json_translator.process_response. "
            f"req: {req}, resp: {resp}, resource: {resource}, req_succeeded: {req_succeeded}"
        )

        context = {"version": version.__VERSION__}

        if not req_succeeded:
            context["error"] = getattr(resp.context, "error", None)
            if settings.IS_DEV:
                context["trace"] = getattr(resp.context, "trace", None)
                logger.info("trace: ")
                logger.info(context["trace"])

        result = {
            "succeed": req_succeeded,
            "data": resp.media,
            "context": context,
        }

        resp.text = json_stringify(result)
