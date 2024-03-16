import uuid
import time
from enum import Enum
from types import NoneType
from typing_extensions import Annotated
from typing import Any, List, Union, Dict, Optional

import numpy as np
from pydantic import BaseModel, Field, WithJsonSchema
from wrapyfi.publishers import Publishers
from pydantic import validator


# 指定json_schema类型的numpy类型，否则numpy类型的字段无法序列化
CoralIntNdarray = Annotated[np.ndarray, WithJsonSchema({'type': 'array', 'items': {'type': 'integer'}})] 
CoralFloatNdarray = Annotated[np.ndarray, WithJsonSchema({'type': 'array', 'items': {'type': 'number'}})]


class CoralBaseModel(BaseModel):
    """
    Coral基类 
    """

    class Config:
        arbitrary_types_allowed = True


class BaseParamsModel(CoralBaseModel):
    """
    节点输入参数基类
    """
    pass


class MetricsPayload(CoralBaseModel):
    """
    指标监控基类
    """
    pass


class BaseInterfaceItemPayload(CoralBaseModel):
    """
    推理单项结果基类
    """
    pass


class ReturnPayload(CoralBaseModel):
    """
    节点返回基类
    """
    pass


class ReturnPayloadWithTS(ReturnPayload):
    """
    带时间戳的节点返回基类
    """
    timestamp: float = Field(default_factory=time.time)


class InterfaceMode(Enum):
    APPEND = 'append'
    OVERWRITE = 'overwrite'


class BaseInterfacePayload(ReturnPayload):
    """
    YOLO 单张图片推理结果 
    """
    mode: InterfaceMode
    objects: List[BaseInterfaceItemPayload]


class Box(CoralBaseModel):
    """
    坐标点
    """
    x1: int
    y1: int
    x2: int
    y2: int


class ObjectPayload(BaseInterfaceItemPayload):
    """
    Yolo推理任务单项结果
    """
    id: Optional[Union[int, NoneType]] = None
    label: str
    class_id: int
    prob: float
    box: Optional[Union[Box, NoneType]] = None
    objects: Optional[Union[List['ObjectPayload'], NoneType]] = None


class FirstPayload(ReturnPayloadWithTS):
    """
    输入节点返回类
    """
    raw: Union[CoralIntNdarray, str]


class ObjectsPayload(BaseInterfacePayload):
    """
    Yolo推理返回类
    """
    mode: InterfaceMode
    objects: Union[List[ObjectPayload], NoneType] = None


class RawPayload(CoralBaseModel):
    """
    通用节点通信数据类
    """
    source_id: str
    raw_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw: CoralIntNdarray = None
    nodes_cost: float = 0
    timestamp: float = Field(default_factory=time.time)
    objects: Union[List[ObjectPayload], NoneType] = None
    metas: Union[Dict[str, ReturnPayload], NoneType] = None



class DataTypeManager:
    """
    通信节点类型映射管理器

    :raises ValueError: 输入参数值错误
    :raises TypeError: 输入参数类型错误
    """
    registry = {}
    # 注册wrapyfi的数据类型, 需要上层的数据类型映射到对应的一个wrapyfi的数据类型上
    mapping_types: List[str] = [t.split(":")[0] for t in Publishers.registry.keys()]

    @classmethod
    def register(
        cls: "DataTypeManager", payload_type: str, data_type: str = "NativeObject"
    ):
        def decorator(cls_: type):
            if data_type not in cls.mapping_types:
                raise ValueError(
                    f"无效的节点类型值: {data_type}, 应属于以下值中之一: {cls.mapping_types}"
                )
            if not issubclass(cls_, RawPayload) and not issubclass(
                cls_, MetricsPayload
            ):
                raise TypeError(
                    f"无效的节点类型: {cls_.__name__}, 应该属于 {RawPayload.__name__} 的子类"
                )
            cls.registry[payload_type] = (data_type, cls_)
            return cls_

        return decorator


class ParamsManager:
    """
    节点输入参数校验&映射管理器

    :raises TypeError: 输入参数类型错误
    :raises ValueError: 输入参数值错误
    """
    registry = {}

    @classmethod
    def register(cls: "ParamsManager", params_name: str = None):
        def decorator(cls_: type):
            if not issubclass(cls_, BaseParamsModel):
                raise TypeError(
                    f"无效的参数类型: {cls_}, 应该属于 {BaseParamsModel.__name__} 的子类"
                )
            _params_name = params_name or cls_.__name__
            if _params_name in cls.registry:
                raise ValueError(f"参数名: {_params_name} 已经存在，参数类需有且仅有一个")
            cls.registry[_params_name] = cls_
            return cls_

        return decorator

    @classmethod
    def default_type(cls):
        if cls.registry:
            return list(cls.registry.keys())[0]
        return None


class ReturnManager:
    """
    节点输出参数校验&映射管理器

    :raises TypeError: _description_
    :raises ValueError: _description_
    :return: _description_
    """
    registry = {}

    @classmethod
    def register(cls: "ReturnManager", return_name: str = None):
        def decorator(cls_: type):
            if not issubclass(cls_, ReturnPayload):
                raise TypeError(
                    f"无效的返参类型: {cls_}, 应该属于 {ReturnPayload.__name__} 的子类"
                )
            _return_name = return_name or cls_.__name__
            if _return_name in cls.registry:
                raise ValueError(f"参数名: {_return_name} 已经存在，返参类需有且仅有一个")

            cls.registry[_return_name] = cls_
            return cls_

        return decorator

    @classmethod
    def default_type(cls):
        if cls.registry:
            return list(cls.registry.keys())[0]
        return None


DTManager = DataTypeManager
PTManager = ParamsManager
RTManager = ReturnManager


@DTManager.register("RawImage")
class RawImagePayload(RawPayload):
    """
    图片类通信数据类
    """

    @validator("raw")
    def check_image(cls, v):
        if not isinstance(v, np.ndarray):
            raise ValueError("raw 参数必须是一个 CoralIntNdarray 对象")
        
        if len(v.shape) != 3 or v.shape[2] not in [3, 4]:
            raise ValueError(
                f"图片必须是 3-通道 (RGB/BGR) 或 4-通道 (RGBA/BGRA) shape格式的数组, 目前的shape值为: {v.shape}"
            )

        if v.dtype != np.uint8:
            raise ValueError("图片必须是 uint8 格式")
        return v


@DTManager.register("Metrics")
class RawMetricsPayload(MetricsPayload):
    """
    指标类通信数据类
    """
    pass


