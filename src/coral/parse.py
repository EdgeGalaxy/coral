from .parser import XmlParser, JsonParser



class CoralParser:

    @classmethod
    def parse(cls, config_path: str) -> type[XmlParser] | type[JsonParser]:
        if config_path.endswith(".xml"):
            return XmlParser.parse(config_path)
        elif config_path.endswith(".json"):
            return JsonParser.parse(config_path)
        else:
            raise ValueError("Unsupported file type")