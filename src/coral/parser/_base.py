import json

from loguru import logger
from pydantic import create_model, Field

from coral.types.payload import ReturnPayload

from ..types import ConfigModel, MetaModel, ModeModel, CoralBaseModel, ParamsModel, GenericParamsModel



class BaseParse:
    def __init__(self, data: dict):
        self.__data = self.__init_data(data)
        logger.info(f"config data: {self.data}")
    
    @classmethod
    def parse(cls, config_path: str) -> 'BaseParse':
        raise NotImplementedError
    
    def parse_json_schema(self, node_type):
        """
        Parse the JSON schema and generate a ConfigSchemaModel.

        :return: The JSON schema for the ConfigSchemaModel.
        """
        _receiver_raw_type = self.meta.receivers[0].raw_type if self.meta.receivers else ''
        _receiver_topic = self.meta.receivers[0].topic if self.meta.receivers else ''
        _sender_raw_type = self.meta.sender.raw_type if self.meta.sender else ''
        _sender_topic = self.meta.sender.topic if self.meta.sender else ''
        _params_cls = self.data._params_cls if self.data._params_cls else None
        _return_cls = self.meta.sender.return_cls if self.meta.sender else None

        ConfigSchemaModel = create_model(
            'ConfigSchemaModel',
            generic_cls = (GenericParamsModel, Field(frozen=True, default=GenericParamsModel(), description='通用参数')),
            __base__=CoralBaseModel, 
        )

        if _params_cls is None and _return_cls is None:
            ConfigSchemaModel = ConfigSchemaModel
        elif _params_cls is None:
            ConfigSchemaModel = create_model(
                'ConfigSchemaModel',
                return_cls=(_return_cls, Field(frozen=True, description='节点返回值', default=None)), 
                __base__=ConfigSchemaModel, 
            )
        elif _return_cls is None:
            ConfigSchemaModel = create_model(
                'ConfigSchemaModel',
                params_cls=(_params_cls, Field(frozen=True, default=None, description='节点具体参数')), 
                __base__=ConfigSchemaModel, 
            )
        else:
            ConfigSchemaModel = create_model(
                'ConfigSchemaModel',
                params_cls=(_params_cls, Field(frozen=True, default=None, description='节点具体参数')), 
                return_cls=(_return_cls, Field(frozen=True, description='节点返回值', default=None)), 
                __base__=ConfigSchemaModel, 
            )
        
        result = {
            'node_type': node_type,
            'receiver_raw_type': _receiver_raw_type,
            'sender_raw_type': _sender_raw_type,
            'receiver_topic': _receiver_topic,
            'sender_topic': _sender_topic,
        }
        data = ConfigSchemaModel.model_json_schema()

        def rebuild_schema_data(schema):
            return_data = {}
            for k, v in schema['properties'].items():
                ref = v.pop('allOf', None)
                if not ref:
                    return_data[k] = v
                    continue
                if len(ref) != 1:
                    raise ValueError(f"一个字段仅支持一种类型参数, 当前字段: {k} 不符合要求")
                _, defs, model_name = ref[0]['$ref'].split('/')
                ref_model = schema[defs][model_name]
                properties = {}
                for k1, v1 in ref_model['properties'].items():
                    if 'allOf' in v1:
                        raise ValueError(f"不支持嵌套定义, 当前字段: {k} -> {k1} 不符合要求")
                    properties[k1] = v1
                return_data[k] = properties
            return return_data

        result.update(rebuild_schema_data(data))
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