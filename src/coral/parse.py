from .parser import XmlParser, JsonParser


class CoralParser:
    @classmethod
    def parse(cls, config_path: str) -> type[XmlParser] | type[JsonParser]:
        """
        Parses the given `config_path` and returns an instance of either `XmlParser` or `JsonParser` based on the file type.

        Args:
            config_path (str): The path to the configuration file.

        Returns:
            type[XmlParser] | type[JsonParser]: An instance of `XmlParser` if the file type is XML, or an instance of `JsonParser` if the file type is JSON.

        Raises:
            ValueError: If the file type is unsupported.
        """
        if config_path.endswith(".xml"):
            return XmlParser.parse(config_path)
        elif config_path.endswith(".json"):
            return JsonParser.parse(config_path)
        else:
            raise ValueError("Unsupported file type")
