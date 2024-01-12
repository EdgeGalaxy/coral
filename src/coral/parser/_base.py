
from typing import Dict

from loguru import logger

from ..types.config import ConfigModel, MetaModel, ModeModel, ParamsModel



class BaseParse:
    def __init__(self, data: dict):
        # self.check(data)
        self.__data = self.__init_data(data)
        logger.info(f"config data: {data}")

    # def check(cls, data: dict):
    #     raise NotImplementedError
    
    @classmethod
    def parse(cls, config_path: str) -> 'BaseParse':
        raise NotImplementedError
    
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
    def node_id(self):
        return self.data.node_id
    
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
        return self.data.params_cls(**self.data.params)


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