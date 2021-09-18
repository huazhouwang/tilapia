import decimal
import json


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return f"{o.normalize():f}"
        return super(DecimalEncoder, self).default(o)
