import json
from typing import Dict, Union

from loguru import logger
from pydantic import create_model, Field

from coral.types.payload import ReturnPayload

from ..types import (
    ConfigModel,
    MetaModel,
    ModeModel,
    CoralBaseModel,
    BaseParamsModel,
    GenericParamsModel,
    ProcessModel,
)


class BaseParse:
    def __init__(self, data: dict):
        self.__data = self.__init_data(data)
        logger.info(f"{self.data.node_id} config data: {self.data}")

    @classmethod
    def parse(cls, config_path: str) -> "BaseParse":
        raise NotImplementedError

    def parse_json_schema(self, node_name: str, node_desc: str, node_type: str):
        """
        Parse the JSON schema and generate a ConfigSchemaModel.

        :return: The JSON schema for the ConfigSchemaModel.
        """
        _receiver_raw_type = (
            self.meta.receivers[0].raw_type if self.meta.receivers else ""
        )
        _receiver_topic = self.meta.receivers[0].topic if self.meta.receivers else ""
        _sender_raw_type = self.meta.sender.raw_type if self.meta.sender else ""
        _sender_topic = self.meta.sender.topic if self.meta.sender else ""
        _params_cls = self.data._params_cls if self.data._params_cls else None
        _return_cls = self.meta.sender.return_cls if self.meta.sender else None

        ConfigSchemaModel = create_model(
            "ConfigSchemaModel",
            process=(
                ProcessModel,
                Field(
                    frozen=True,
                    default=self.data.process.model_dump(),
                    description="系统运行参数",
                ),
            ),
            generic=(
                GenericParamsModel,
                Field(
                    frozen=True,
                    default=self.data.generic.model_dump(),
                    description="业务通用参数",
                ),
            ),
            __base__=CoralBaseModel,
        )

        if _params_cls is not None:
            ConfigSchemaModel = create_model(
                "ConfigSchemaModel",
                params=(
                    _params_cls,
                    Field(
                        frozen=True,
                        default=self.data.params.model_dump(),
                        description="节点具体参数",
                    ),
                ),
                __base__=ConfigSchemaModel,
            )

        result = {
            "name": node_name,
            "description": node_desc,
            "node_type": node_type,
            "input_type": _receiver_raw_type,
            "output_type": _sender_raw_type,
            "input_topic": _receiver_topic,
            "output_topic": _sender_topic,
            "returns": None,
            
        }

        def iter_schema_key_type(properties: dict, defs: dict, defaults: dict = {}):
            iter_result = {}
            for key, value in properties.items():
                if 'allOf' in value:
                    ref_key = value['allOf'][0]["$ref"].split("/")[-1]
                    _properties = defs[ref_key]["properties"]
                    iter_result[key] = iter_schema_key_type(
                        _properties, defs, defaults.get(key, {})
                    )
                else:
                    iter_result[key] = {
                        "type": value["type"],
                        "title": value.get("title", key),
                        "default": defaults.get(key),
                        "description": value.get("description", ""),
                    }
            return iter_result

        config_schema = ConfigSchemaModel.model_json_schema()
        defaults = ConfigSchemaModel().model_dump()
        configs = iter_schema_key_type(config_schema['properties'], config_schema['$defs'], defaults)
        result.update({'configs': configs, 'config_schema': config_schema})

        if _return_cls is not None:
            return_schema = _return_cls.model_json_schema()
            returns = iter_schema_key_type(return_schema['properties'], return_schema.get('$defs', {}), {})
            if returns:
                result.update({"returns": returns})

        return result

    def __init_data(self, data) -> ConfigModel:
        """
        Initializes the data by creating a new instance of the ConfigModel class using the provided data.

        Parameters:
            data (Any): The data to be used to initialize the ConfigModel instance.

        Returns:
            ConfigModel: The newly created ConfigModel instance.
        """
        return ConfigModel(**data)

    @property
    def data(self) -> ConfigModel:
        return self.__data

    @property
    def pipeline_id(self) -> str:
        return self.data.pipeline_id

    @property
    def node_id(self):
        return self.data.node_id

    @property
    def generic_params(self):
        return self.data.generic

    @property
    def process(self) -> int:
        return self.data.process

    @property
    def meta(self) -> MetaModel:
        return self.data.meta

    @property
    def mode(self) -> ModeModel:
        return self.data.meta.mode

    @property
    def params(self) -> BaseParamsModel:
        return self.data.params
