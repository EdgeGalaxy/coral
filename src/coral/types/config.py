import os
from functools import cached_property
from typing import List, Dict, Union

from loguru import logger
from pydantic import BaseModel, Field, computed_field, field_validator

from .payload import (
    DTManager,
    BaseParamsModel,
    RawPayload,
    PTManager,
    ReturnPayload,
    RTManager,
    CoralBaseModel,
)
from ..constants import ENABLE_SHARED_MEMORY


class ProtocalType:
    """
    通信协议类型
    """
    PUBSUB = "pubsub"
    REPLY = "reply"


class SenderMode:
    """
    发送者模式值
    """
    PUBLISH = "publish"
    REPLY = "reply"


class ReceiverMode:
    """
    接收者模式值
    """
    LISTEN = "listen"
    REQUEST = "request"


class ModeModel(BaseModel):
    """
    发送/接收者模式
    """
    sender: str 
    receiver: str


# 定义通信模式
PUBSUM_MODE = ModeModel(sender=SenderMode.PUBLISH, receiver=ReceiverMode.LISTEN)
REPLY_MODE = ModeModel(sender=SenderMode.REPLY, receiver=ReceiverMode.REQUEST)


class PubSubBaseModel(CoralBaseModel):
    """
    节点通信通用格式
    """
    node_id: str = Field(frozen=True)
    raw_type: str = Field(frozen=True, default="RawImage")
    mware: str = Field(frozen=True, default="zeromq")
    cls_name: str = Field(frozen=True, default="NoReceiverUse")
    topic: str = Field(default=None)
    carrier: str = Field(frozen=True, default="tcp")
    blocking: bool = Field(frozen=True, default=False)
    socket_sub_port: int = Field(default=5556)
    socket_pub_port: int = Field(default=5555)
    params: Dict[str, Union[str, int, bool, float]] = Field(frozen=True, default={})

    def __init__(self, **data):
        super().__init__(**data)
        if not self.topic:
            self.topic = f'{self.node_id}_{self.raw_type}_{self.mware}'

class ReceiverModel(PubSubBaseModel):

    @field_validator("raw_type")
    @classmethod
    def validate_payload_type(cls, v):
        if v not in DTManager.registry:
            raise ValueError(
                f"Invalid payload type: {v}, should in {list(DTManager.registry.keys())}"
            )
        return v

    @computed_field
    @cached_property
    def data_type(self) -> str:
        return DTManager.registry[self.raw_type][0]

    @computed_field
    @cached_property
    def payload_cls(self) -> RawPayload:
        return DTManager.registry[self.raw_type][1]


class SenderModel(PubSubBaseModel):

    @field_validator("raw_type")
    @classmethod
    def validate_payload_type(cls, v):
        if v not in DTManager.registry:
            raise ValueError(
                f"Invalid payload type: {v}, should in {list(DTManager.registry.keys())}"
            )
        if RTManager.default_type() is None:
            raise ValueError(
                f"Not found ReturnPayload decorator by @RTManager.registry"
            )
        if len(RTManager.registry.keys()) > 1:
            raise ValueError(
                f"More than one return type: {list(RTManager.registry.keys())}"
            )
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
        if RTManager.default_type() is None:
            return ReturnPayload
        return RTManager.registry[RTManager.default_type()]


class MetaModel(CoralBaseModel):
    """
    sender & receiver 通信类
    """
    mode: str = Field(frozen=True, default=ProtocalType.PUBSUB)
    receivers: List[ReceiverModel] = Field(frozen=True, default=[])
    sender: SenderModel = Field(frozen=True, default=None)

    @computed_field
    @cached_property
    def _mode(self) -> ModeModel:
        if self.mode == ProtocalType.PUBSUB:
            return PUBSUM_MODE
        elif self.mode == ProtocalType.REPLY:
            return REPLY_MODE
        raise ValueError(f"Unsupported mode: {self.mode}")


class ProcessModel(CoralBaseModel):
    """
    系统参数设定
    """
    max_qsize: int = Field(frozen=True, default=180)
    count: int = Field(frozen=True, default=3)
    enable_parallel: bool = Field(frozen=True, default=False)


class GenericParamsModel(CoralBaseModel):
    """
    业务通用参数
    """
    skip_frame: int = Field(frozen=True, default=0, description="每隔几帧处理一次")
    enable_metrics: bool = Field(frozen=True, default=True, description="是否开启服务监控")
    enable_shared_memory: bool = Field(frozen=True, default=False, validate_default=True, description="是否开启共享内存")

    @field_validator("enable_shared_memory")
    @classmethod
    def validate_enable_shared_memory(cls, v):
        if ENABLE_SHARED_MEMORY is None:
            return v

        logger.info(f'exist env [ CORAL_NODE_ENABLE_SHARED_MEMORY ], set enable_shared_memory is {ENABLE_SHARED_MEMORY} !')
        if ENABLE_SHARED_MEMORY == "true":
            return True
        elif ENABLE_SHARED_MEMORY == "false":
            return False

        return v


class ConfigModel(CoralBaseModel):
    """
    节点通用配置类
    """
    pipeline_id: str = Field(frozen=True, default="default_pipeline")
    node_id: str = Field(frozen=True)
    process: ProcessModel = Field(frozen=True, default=ProcessModel())
    meta: MetaModel = Field(frozen=True)
    generic: GenericParamsModel = Field(frozen=True, default=GenericParamsModel())
    params: Dict = Field(frozen=True, default=None)

    @field_validator("params")
    @classmethod
    def check_params_type(cls, v):
        if v is None:
            return v
        if PTManager.default_type() is None:
            raise ValueError(
                f"未发现被 @PTManager.register() 装饰器包装的 ParamsModel 类"
            )
        if len(PTManager.registry.keys()) > 1:
            raise ValueError(
                f"存在多个 @PTManager.register() 装饰的 ParamsModel 类: {list(PTManager.registry.keys())}"
            )
        pt_cls = PTManager.registry[PTManager.default_type()]
        return pt_cls(**v)

    @computed_field
    @cached_property
    def _params_cls(self) -> BaseParamsModel:
        if PTManager.default_type() is None:
            return None
        return PTManager.registry[PTManager.default_type()]
