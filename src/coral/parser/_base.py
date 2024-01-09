
from functools import cached_property
from typing import List, Dict, Union, Optional

from pydantic import BaseModel, Field, computed_field


class ReceiverModel(BaseModel):
    data_type: str = Field(frozen=True) 
    mware: str = Field(frozen=True) 
    cls_name: str = Field(frozen=True) 
    topic: str = Field(frozen=True) 
    carries: str = Field(frozen=True) 
    blocking: bool = Field(frozen=True) 
    params: Dict[str, Union[str, int, bool, float]] = Field(frozen=True) 


class SenderModel(BaseModel):
    data_type: str = Field(frozen=True) 
    mware: str = Field(frozen=True) 
    cls_name: str = Field(frozen=True) 
    topic: str = Field(frozen=True) 
    carries: str = Field(frozen=True) 
    blocking: bool = Field(frozen=True) 
    params: Dict[str, Union[str, int, bool, float]] = Field(frozen=True) 


class ModeModel(BaseModel):
    sender: str
    receiver: str


PUBSUB = 'pubsub'
REPLY = 'reply'
RECEIVER_SINGLE_MODE = 'single'
RECEIVER_CLUSTER_MODE = 'cluster'
PUBSUM_MODE = ModeModel(sender='publish', receiver='listen')
REPLY_MODE = ModeModel(sender='reply', receiver='request')


class MetaModel(BaseModel):
    mode: str = Field(frozen=True, default=PUBSUB) 
    receiver_mode: str = Field(default=RECEIVER_SINGLE_MODE, frozen=True)
    receiver_timeout: float = Field(default=0.5, frozen=True)
    receivers: List[ReceiverModel] = Field(frozen=True, default=[])
    senders: List[SenderModel] = Field(frozen=True, default=[])


    @computed_field
    @cached_property
    def _mode(self) -> ModeModel:
        if self.mode == PUBSUB:
            return PUBSUM_MODE
        elif self.mode == REPLY:
            return REPLY_MODE
        raise ValueError(f"Unsupported mode: {self.mode}")


class ParamsModel(BaseModel):
    init: Dict[str, Union[str, int, bool, float]] = Field(frozen=True, default={})
    run: Dict[str, Union[str, int, bool, float]] = Field(frozen=True, default={})


class ProcessModel(BaseModel):
    max_qsize: int = Field(frozen=True, default=30)
    count: int = Field(frozen=True, default=3)
    run_mode: str = Field(frozen=True, default='threads')
    enable_parallel: bool = Field(frozen=True, default=False)


class ConfigModel(BaseModel):
    process: ProcessModel = Field(frozen=True, default=ProcessModel(max_qsize=30, count=3, run_mode='threads', enable_parallel=False))
    meta: MetaModel = Field(frozen=True)
    params: ParamsModel = Field(frozen=True)


class BaseParse:
    def __init__(self, data: dict):
        # self.check(data)
        self.__data = self.init_data(data)

    # def check(cls, data: dict):
    #     raise NotImplementedError
    
    @classmethod
    def parse(cls, config_path: str) -> 'BaseParse':
        raise NotImplementedError
    
    def init_data(self, data) -> ConfigModel:
        return ConfigModel(**data)
    
    @property
    def data(self) -> ConfigModel:
        return self.__data
    
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
    
    @property
    def init(self) -> Dict:
        return self.params.init
    
    @property
    def run(self) -> Dict:
        return self.params.run


if __name__ == '__main__':
    data = {
        'process': {},
        'meta': {
            'mode': 'pubsubx',
            'receiver_mode': 'single',
            'receiver_timeout': 0.5,
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