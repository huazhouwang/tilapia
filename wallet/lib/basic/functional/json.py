import dataclasses
import decimal
import json
from typing import Any

_specific_cases = [
    (lambda i: isinstance(i, decimal.Decimal), lambda i: f"{i.normalize():f}"),
    (dataclasses.is_dataclass, lambda i: i.to_dict()),
    (lambda i: isinstance(i, set), list),
    (lambda i: isinstance(i, Exception), str),
]


class _Encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        for support_it, handle_it in _specific_cases:
            if support_it(o):
                return handle_it(o)

        return super(_Encoder, self).default(o)


def json_stringify(obj: Any, *args, **kwargs) -> str:
    if isinstance(obj, str):
        return obj

    return json.dumps(obj, *args, cls=_Encoder, **kwargs)
