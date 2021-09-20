import abc


class SelfHandleException(Exception):
    @abc.abstractmethod
    def handle(self, req, resp, params):
        pass


__ERROR__ = SelfHandleException


def handle(ex: SelfHandleException, req, resp, params):
    return ex.handle(req, resp, params)
