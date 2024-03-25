import json

from ._base import BaseParse


class JsonParser(BaseParse):
    @classmethod
    def parse(cls, config_path: str):
        with open(config_path, "r") as f:
            data = json.load(f)
            return cls(data)
