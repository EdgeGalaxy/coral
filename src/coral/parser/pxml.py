
from xmltodict import parse

from ._base import BaseParse
from .pjson import JsonParser


class XmlParser(BaseParse):

    @classmethod
    def parse(cls, config_path):
        with open(config_path, "r") as f:
            data = parse(f.read())
            return JsonParser.parse(data)