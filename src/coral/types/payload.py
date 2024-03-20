import atexit
from functools import partial
import time
from enum import Enum
from types import NoneType
from typing_extensions import Annotated
from typing import Any, List, Union, Dict, Optional

import numpy as np
import SharedArray as sa
from loguru import logger
from pydantic import BaseModel, Field, WithJsonSchema, PrivateAttr, computed_field
from wrapyfi.publishers import Publishers

from ..utils import generate_short_uid 
from ..constants import SHARED_DATA_TYPE
from ..sched import SharedMemoryIDManager as SMIM

shared_memory_store = {}
# 指定json_schema类型的numpy类型，否则numpy类型的字段无法序列化
CoralIntNdarray = Annotated[
    np.ndarray, WithJsonSchema({"type": "array", "items": {"type": "integer"}})
]
CoralFloatNdarray = Annotated[
    np.ndarray, WithJsonSchema({"type": "array", "items": {"type": "number"}})
]


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
    APPEND = "append"
    OVERWRITE = "overwrite"


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
    objects: Optional[Union[List["ObjectPayload"], NoneType]] = None


class FirstPayload(ReturnPayload):
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


class BaseRawPayload(CoralBaseModel):
    """
    Base通用节点通信数据类, 涵盖共享内存的管理
    """

    raw_id: str = Field(default_factory=lambda: generate_short_uid())

    _raw: CoralIntNdarray = PrivateAttr(default=None)
    _raw_shared_memory_id: str = PrivateAttr(default=None)
    _enable_shared_memory: bool = PrivateAttr(default=False)

    def __init__(self, **data):
        super().__init__(**data)
        self._init_private_field(data)

    def model_dump(self, *args, **kwargs):
        exclude = kwargs.get('exclude', [])
        if self._enable_shared_memory:
            exclude.append('raw')
            data = super().model_dump(exclude=exclude, *args, **kwargs)
        else:
            exclude.append('raw_shared_memory_id')
            data = super().model_dump(exclude=exclude, *args, **kwargs)
        return data

    def __check_raw_shared_memory_id(self, v: str):
        if v is None:
            return v
        if not v.startswith(SHARED_DATA_TYPE):
            raise ValueError(f"raw_shared_memory_id 必须以 {SHARED_DATA_TYPE} 开头")
        return v

    def check_raw_data(self, raw: np.ndarray):
        """可被继承的方法"""
        return raw

    def _fetch_shared_memory_data(self, _raw_shared_memory_id: str):
        """在共享内存中获取数据"""
        try:
            _raw = SMIM().attach(_raw_shared_memory_id)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"未找到共享内存: {_raw_shared_memory_id} 信息: {e}"
            )
        return _raw, _raw_shared_memory_id

    def _create_shared_memory_data(self, _raw: np.ndarray):
        """创建共享内存数据"""
        _raw_shared_memory_id = f"{SHARED_DATA_TYPE}{self.raw_id}"
        memory_data = SMIM().add(_raw_shared_memory_id, _raw.shape, _raw.dtype)
        memory_data[:] = _raw
        return _raw, _raw_shared_memory_id
    
    def _compare_and_repair_memory_data(self, _raw, _raw_shared_memory_id):
        """比较外部_raw和共享内存内的数据，并修复"""
        try:
            memory_data = SMIM().attach(_raw_shared_memory_id)
        except FileNotFoundError as e:
            _raw, _raw_shared_memory_id = self._create_shared_memory_data(_raw)
            logger.warning(
                f"未找到共享内存: {_raw_shared_memory_id} 信息, 但是存在 _raw: "
                f"{_raw.shape} {_raw.dtype} 信息，依据 _raw信息创建共享内存"
            )
        else:
            if not np.equal(memory_data, _raw):
                raise FileNotFoundError(
                    f"共享内存 {_raw_shared_memory_id} -> {memory_data.shape} {memory_data.dtype} 的值和"
                    f"字段 _raw -> {_raw.shape} {_raw.dtype} 的数据不一致 "
                )
        return _raw, _raw_shared_memory_id

    def release_shared_memory(self, shared_memroy_id: str = None):
        """释放共享内存数据"""
        _raw_shared_memory_id = shared_memroy_id or self._raw_shared_memory_id
        if _raw_shared_memory_id:
            try:
                SMIM().remove(_raw_shared_memory_id)
                self._raw_shared_memory_id = None
            except FileNotFoundError as e:
                logger.warning(f"未找到共享内存: {_raw_shared_memory_id} 信息: {e}")

    def _init_private_field(self, data):
        _raw = (
            self.check_raw_data(data.get("raw"))
            if data.get("raw") is not None
            else None
        )
        _raw_shared_memory_id = (
            self.__check_raw_shared_memory_id(data.get("raw_shared_memory_id"))
            if data.get("raw_shared_memory_id") is not None
            else None
        )
        _enable_shared_memory = data.get("enable_shared_memory")
        if _enable_shared_memory:
            # 从共享内存中获取数据
            if _raw is None and _raw_shared_memory_id:
                _raw, _raw_shared_memory_id = self._fetch_shared_memory_data(
                    _raw_shared_memory_id
                )
            # 创建共享内存
            elif _raw is not None and not _raw_shared_memory_id:
                _raw, _raw_shared_memory_id = self._create_shared_memory_data(_raw)
            # 从共享内存中获取数据与_raw数据比对
            elif _raw is not None and _raw_shared_memory_id:
                _raw, _raw_shared_memory_id = self._compare_and_repair_memory_data(
                    _raw, _raw_shared_memory_id
                )

            self._enable_shared_memory = True
            self._raw_shared_memory_id = _raw_shared_memory_id
        else:
            self._enable_shared_memory = False
            if not _raw and _raw_shared_memory_id:
                _raw, _ = self._fetch_shared_memory_data(_raw_shared_memory_id)

            self.release_shared_memory(_raw_shared_memory_id)
        # 赋值私有变量
        self._raw = _raw

    @computed_field
    def raw(self) -> np.array:
        return self._raw

    @computed_field
    def raw_shared_memory_id(self) -> str:
        return self._raw_shared_memory_id

    def set_raw(self, raw: np.ndarray):
        _raw = self.check_raw_data(raw)
        if self._enable_shared_memory:
            if self._raw_shared_memory_id is not None:
                _raw, _raw_shared_memory_id = self._compare_and_repair_memory_data(
                    _raw, self._raw_shared_memory_id
                )
            else:
                _raw, _raw_shared_memory_id = self._create_shared_memory_data(_raw)

            self._raw_shared_memory_id = _raw_shared_memory_id
        else:
            self._raw_shared_memory_id = None

        self._raw = _raw


class RawPayload(BaseRawPayload):
    """
    通用节点通信数据类
    """

    source_id: str
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
                raise ValueError(
                    f"参数名: {_params_name} 已经存在，参数类需有且仅有一个"
                )
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
                raise ValueError(
                    f"参数名: {_return_name} 已经存在，返参类需有且仅有一个"
                )

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

    def check_raw_data(self, raw: np.ndarray):
        raw = super().check_raw_data(raw)
        if not isinstance(raw, np.ndarray):
            raise ValueError("raw 参数必须是一个 CoralIntNdarray 对象")

        if len(raw.shape) != 3 or raw.shape[2] not in [3, 4]:
            raise ValueError(
                f"图片必须是 3-通道 (RGB/BGR) 或 4-通道 (RGBA/BGRA) shape格式的数组, 目前的shape值为: {raw.shape}"
            )

        if raw.dtype != np.uint8:
            raise ValueError("图片必须是 uint8 格式")
        return raw


@DTManager.register("Metrics")
class RawMetricsPayload(MetricsPayload):
    """
    指标类通信数据类
    """

    pass
