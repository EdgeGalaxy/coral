
from functools import cached_property
from typing import List, Dict, Union
from typing_extensions import Unpack

from pydantic import BaseModel, Field, computed_field, validator
from pydantic.config import ConfigDict

from .payload import DTManager, RawPayload, ParamsModel, PTManager, ReturnPayload, RTManager, CoralBaseModel



class ModeModel(BaseModel):
    sender: str
    receiver: str


PUBSUB = 'pubsub'
REPLY = 'reply'
RECEIVER_SINGLE_MODE = 'single'
RECEIVER_CLUSTER_MODE = 'cluster'
PUBSUM_MODE = ModeModel(sender='publish', receiver='listen')
REPLY_MODE = ModeModel(sender='reply', receiver='request')


class ReceiverModel(CoralBaseModel):
    raw_type: str = Field(frozen=True) 
    mware: str = Field(frozen=True, default='zeromq') 
    cls_name: str = Field(frozen=True, default='NoReceiverUse') 
    topic: str = Field(frozen=True) 
    carrier: str = Field(frozen=True, default='tcp') 
    blocking: bool = Field(frozen=True, default=True) 
    params: Dict[str, Union[str, int, bool, float]] = Field(frozen=True, default={}) 
    
    def __init__(self, **data):
        # if 'topic' not in data and data['mware'] == 'ros2':
        #     raise ValueError("[ topic ] must be set when mware is ros2 !!")
        # if data['mware'] == 'zeromq' and ('socket_sub_port' not in data.get('params', {}) or 'socket_pub_port' not in data.get('params', {})):
        #     raise ValueError("[ socket_sub_port ] and [ socket_pub_port ] must be set when mware is zeromq !!")
        super().__init__(**data)

    @validator('raw_type')
    def validate_payload_type(cls, v):
        if v not in DTManager.registry:
            raise ValueError(f"Invalid payload type: {v}, should in {list(DTManager.registry.keys())}")
        return v

    @computed_field
    @cached_property
    def data_type(self) -> str:
        return DTManager.registry[self.raw_type][0]
    
    @computed_field
    @cached_property
    def payload_cls(self) -> RawPayload:
        return DTManager.registry[self.raw_type][1]


class SenderModel(CoralBaseModel):
    raw_type: str = Field(frozen=True) 
    return_type: str = Field(frozen=True) 
    mware: str = Field(frozen=True, default='zeromq') 
    cls_name: str = Field(frozen=True, default='NoSenderUse') 
    topic: str = Field(frozen=True) 
    carrier: str = Field(frozen=True, default='tcp') 
    blocking: bool = Field(frozen=True, default=False) 
    params: Dict[str, Union[str, int, bool, float]] = Field(frozen=True) 

    def __init__(self, **data):
        if 'return_type' not in data:
            data['return_type'] = RTManager.default_type()
        # if 'topic' not in data and data['mware'] == 'ros2':
        #     raise ValueError("topic must be set when mware is ros2 !!")
        # if data['mware'] == 'zeromq' and ('socket_sub_port' not in data.get('params', {}) or 'socket_pub_port' not in data.get('params', {})):
        #     raise ValueError("[ socket_sub_port ] and [ socket_pub_port ] must be set when mware is zeromq !!")
        super().__init__(**data)
    
    @validator('raw_type')
    def validate_payload_type(cls, v):
        if v not in DTManager.registry:
            raise ValueError(f"Invalid payload type: {v}, should in {list(DTManager.registry.keys())}")
        return v

    @validator('return_type')
    def validate_return_type(cls, v):
        if v is None:
            # 必须存在RTManager.registry
            if not RTManager.registry:
                raise ValueError(f"Not found ReturnPayload decorator by @RTManager.registry")
            else:
                # 取第一个
                return list(RTManager.registry.keys())[0]
        else:
            if v not in RTManager.registry:
                raise ValueError(f"Invalid return type: {v}, should in {list(RTManager.registry.keys())}")
        return v

    @computed_field
    @cached_property
    def data_type(self) -> str:
        return DTManager.registry[self.raw_type][0]
    
    @computed_field
    @cached_property
    def payload_cls(self) -> RawPayload:
        return DTManager.registry[self.raw_type][1]
    
    @computed_field
    @cached_property
    def return_cls(self) -> ReturnPayload:
        return RTManager.registry[self.return_type]
    

class MetaModel(CoralBaseModel):
    mode: str = Field(frozen=True, default=PUBSUB) 
    receivers: List[ReceiverModel] = Field(frozen=True, default=[])
    sender: SenderModel = Field(frozen=True, default=None)


    @computed_field
    @cached_property
    def _mode(self) -> ModeModel:
        if self.mode == PUBSUB:
            return PUBSUM_MODE
        elif self.mode == REPLY:
            return REPLY_MODE
        raise ValueError(f"Unsupported mode: {self.mode}")


class ProcessModel(CoralBaseModel):
    max_qsize: int = Field(frozen=True, default=30)
    count: int = Field(frozen=True, default=3)
    run_mode: str = Field(frozen=True, default='threads')
    enable_parallel: bool = Field(frozen=True, default=False)


class ConfigModel(CoralBaseModel):
    node_id: str = Field(frozen=True)
    process: ProcessModel = Field(frozen=True, default=ProcessModel())
    meta: MetaModel = Field(frozen=True)
    params_type: str = Field(frozen=True)
    params: Dict = Field(frozen=True, default=None)

    def __init__(self, **data):
        if 'params_type' not in data:
            data['params_type'] = PTManager.default_type()
        super().__init__(**data)

    @validator('params_type')
    def validate_params_type(cls, v):
        if v is None:
            if not PTManager.registry:
                return v
            else:
                # 取第一个
                return list(PTManager.registry.keys())[0]
        else:
            if v not in PTManager.registry:
                raise ValueError(f"Invalid params type: {v}, should in {list(PTManager.registry.keys())}")
        return v

    @computed_field
    @cached_property
    def params_cls(self) -> ParamsModel:
        if self.params_type is None:
            if self.params is None:
                return None
            else:
                raise ValueError(f"params is not None, but not found params type class!!")
        return PTManager.registry[self.params_type]
    