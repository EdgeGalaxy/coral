
from functools import cached_property
from typing import List, Dict, Union
from typing_extensions import Unpack

from pydantic import BaseModel, Field, computed_field, validator

from .payload import DTManager, RawPayload, PTManager, ReturnPayload, RTManager, CoralBaseModel



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
    raw_type: str = Field(frozen=True, default="RawImage") 
    mware: str = Field(frozen=True, default='zeromq') 
    cls_name: str = Field(frozen=True, default='NoReceiverUse') 
    topic: str = Field(frozen=True) 
    carrier: str = Field(frozen=True, default='tcp') 
    blocking: bool = Field(frozen=True, default=True) 
    params: Dict[str, Union[str, int, bool, float]] = Field(frozen=True, default={}) 

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
    raw_type: str = Field(frozen=True, default="RawImage") 
    mware: str = Field(frozen=True, default='zeromq') 
    cls_name: str = Field(frozen=True, default='NoSenderUse') 
    topic: str = Field(frozen=True) 
    carrier: str = Field(frozen=True, default='tcp') 
    blocking: bool = Field(frozen=True, default=False) 
    params: Dict[str, Union[str, int, bool, float]] = Field(frozen=True) 
    
    @validator('raw_type')
    def validate_payload_type(cls, v):
        if v not in DTManager.registry:
            raise ValueError(f"Invalid payload type: {v}, should in {list(DTManager.registry.keys())}")
        if RTManager.default_type() is None:
            raise ValueError(f"Not found ReturnPayload decorator by @RTManager.registry")
        if len(RTManager.registry.keys()) > 1:
            raise ValueError(f"More than one return type: {list(RTManager.registry.keys())}")
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
        return RTManager.registry[RTManager.default_type()]
    

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
    params: Dict = Field(frozen=True, default=None)

    @validator('params')
    def check_params_type(cls, v):
        if v is None:
            return v
        if PTManager.default_type() is None:
            raise ValueError(f"Not found ParamsModel decorator by @PTManager.registry, but exist params field")
        if len(PTManager.registry.keys()) > 1:
            raise ValueError(f"More than one params type: {list(PTManager.registry.keys())}")
        pt_cls = PTManager.registry[PTManager.default_type()]
        return pt_cls(**v)

    @computed_field
    @cached_property
    def _params_cls(self) -> RawPayload:
        if PTManager.default_type() is None:
            return None
        return PTManager.registry[PTManager.default_type()]