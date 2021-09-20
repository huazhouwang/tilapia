import traceback

import falcon

__ERROR__ = Exception


def handle(ex, req, resp, params):
    resp.status = falcon.HTTP_500
    resp.context.error = ex
    resp.context.trace = traceback.format_exc()
