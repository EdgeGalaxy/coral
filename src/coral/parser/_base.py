
from typing import Dict

from loguru import logger
from pydantic import create_model, Field

from ..types import ConfigModel, MetaModel, ModeModel, CoralBaseModel, ParamsModel, GenericParamsModel



class BaseParse:
    def __init__(self, data: dict):
        self.__data = self.__init_data(data)
        logger.info(f"config data: {self.data}")
    
    @classmethod
    def parse(cls, config_path: str) -> 'BaseParse':
        raise NotImplementedError
    
    def parse_json_schema(self):
        """
        Parse the JSON schema and generate a ConfigSchemaModel.

        :return: The JSON schema for the ConfigSchemaModel.
        """
        _params_cls = self.data._params_cls
        _return_cls = self.meta.sender.return_cls
        _receiver_raw_type = self.meta.receivers[0].raw_type if self.meta.receivers else None
        _receiver_topic = self.meta.receivers[0].topic if self.meta.receivers else None
        _sender_raw_type = self.meta.sender.raw_type if self.meta.sender else None
        _sender_topic = self.meta.sender.topic if self.meta.sender else None

        ConfigSchemaModel = create_model(
            'ConfigSchemaModel',
            receiver_raw_type = (str, Field(frozen=True, default=_receiver_raw_type, description='接收的类型')),
            sender_raw_type = (str, Field(frozen=True, default=_sender_raw_type, description='发送的类型')),
            receiver_topic = (str, Field(frozen=True, default=_receiver_topic, description='接收的topic')),
            sender_topic = (str, Field(frozen=True, default=_sender_topic, description='发送的topic')),
            generic_cls = (GenericParamsModel, Field(frozen=True, default=GenericParamsModel(), description='通用参数')),
            params_cls=(_params_cls, Field(frozen=True, default=None, description='节点具体参数')), 
            return_cls=(_return_cls, Field(frozen=True, description='节点返回值')), 
            __base__=CoralBaseModel, 
        )
        return ConfigSchemaModel.model_json_schema()
    
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
    def gateway_id(self):
        return self.data.gateway_id

    @property
    def pipeline_id(self):
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
    def meta(self) -> MetaModel :
        return self.data.meta
    
    @property
    def mode(self) -> ModeModel:
        return self.data.meta.mode
    
    @property
    def params(self) -> ParamsModel:
        return self.data.params


if __name__ == '__main__':
    data = {
        'process': {},
        'meta': {
            'mode': 'pubsubx',
            'receivers': [{
                'data_type': 'NativeObject',
                'mware': 'zeromq',
                'cls_name': 'Node1',
                'topic': '/node1',
                'carries': 'tcp',
                'blocking': False,
                'params': {
                    'socket_sub_port': 5659,
                    'socket_pub_port': 5658
                }

            }],
            'senders': [{
                'data_type': 'NativeObject',
                'mware': 'zeromq',
                'cls_name': 'Node2',
                'topic': '/node2',
                'carries': 'tcp',
                'blocking': False,
                'params': {
                    'socket_sub_port': 5759,
                    'socket_pub_port': 5758
                }
            }]
        },
        'params': {
            "init": {
                "model": 'model_path'
            },
            "run": {
                "width": 100
            }
        }
    }
    import json
    print(json.dumps(data, indent=2))
    # p = BaseParse(data)
    # print(p.meta)
    # print(p.meta._mode)
    # print(p.params)
    # print(p.init)
    # print(p.process)