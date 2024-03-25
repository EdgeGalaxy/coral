import json
import base64

from ._base import BaseParse


class Base64Parser(BaseParse):
    @classmethod
    def parse(cls, config_path: str):
        decoded_json = base64.b64decode(config_path)
        data = json.loads(decoded_json)
        return cls(data)
