from types import NoneType
from typing_extensions import Annotated
import uuid
import time

from typing import Any, List, Union, Dict, Optional, Tuple
from pydantic import BaseModel, Field, WithJsonSchema

import numpy as np
from wrapyfi.publishers import Publishers
from pydantic import validator


CoralIntNdarray = Annotated[np.ndarray, WithJsonSchema({'type': 'array', 'items': {'type': 'integer'}})] 
CoralFloatNdarray = Annotated[np.ndarray, WithJsonSchema({'type': 'array', 'items': {'type': 'number'}})]


class CoralBaseModel(BaseModel):

    class Config:
        arbitrary_types_allowed = True



class ReturnPayload(CoralBaseModel):
    pass


class BaseInterfacePayload(ReturnPayload):
    objects: Any


class ReturnPayloadWithTS(ReturnPayload):
    timestamp: float = Field(default_factory=time.time)


class FirstPayload(ReturnPayloadWithTS):
    raw: Union[CoralIntNdarray, str]


class ObjectsPayload(BaseInterfacePayload):
    id: Optional[Union[List[int], NoneType]] = None
    labels: List[str]
    class_ids: List[int]
    probs: List[float]
    boxes: List[Tuple] = []
    objects: Optional[Union['ObjectsPayload', NoneType]] = None


class ParamsModel(CoralBaseModel):
    pass


class RawPayload(CoralBaseModel):
    node_id: str
    raw_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw: Union[CoralIntNdarray, str] = None
    nodes_cost: float = 0
    timestamp: float = Field(default_factory=time.time)
    objects: Optional[ObjectsPayload] = None
    metas: Optional[Dict[str, ReturnPayload]] = None


class MetricsPayload(CoralBaseModel):
    pass


class BatchRawPayload(BaseModel):
    payloads: List[RawPayload]


class DataTypeManager:
    registry = {}
    mapping_types: List[str] = [t.split(":")[0] for t in Publishers.registry.keys()]

    @classmethod
    def register(
        cls: "DataTypeManager", payload_type: str, data_type: str = "NativeObject"
    ):
        def decorator(cls_: Union[RawPayload, MetricsPayload]):
            if data_type not in cls.mapping_types:
                raise ValueError(
                    f"Invalid mapping type: {data_type}, should include in {cls.mapping_types}"
                )
            if not issubclass(cls_, RawPayload) and not issubclass(
                cls_, MetricsPayload
            ):
                raise TypeError(
                    f"Invalid class model type: {cls_.__name__}, should be a subclass of {RawPayload.__name__}"
                )
            cls.registry[payload_type] = (data_type, cls_)
            return cls_

        return decorator


class ParamsManager:
    registry = {}

    @classmethod
    def register(cls: "ParamsManager", params_name: str = None):
        def decorator(cls_: ParamsModel):
            if not issubclass(cls_, ParamsModel):
                raise TypeError(
                    f"Invalid class model type: {cls_}, should be a subclass of {ParamsModel.__name__}"
                )
            _params_name = params_name or cls_.__name__
            if _params_name in cls.registry:
                raise ValueError(f"Duplicate params name: {_params_name}")
            cls.registry[_params_name] = cls_
            return cls_

        return decorator

    @classmethod
    def default_type(cls):
        if cls.registry:
            return list(cls.registry.keys())[0]
        return None


class ReturnManager:
    registry = {}

    @classmethod
    def register(cls: "ReturnManager", return_name: str = None):
        def decorator(cls_: ReturnPayload):
            if not issubclass(cls_, ReturnPayload):
                raise TypeError(
                    f"Invalid class model type: {cls_}, should be a subclass of {ReturnPayload.__name__}"
                )
            _return_name = return_name or cls_.__name__
            if _return_name in cls.registry:
                raise ValueError(f"Duplicate return name: {_return_name}")
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

    @validator("raw")
    def check_image(cls, v):
        if not isinstance(v, np.ndarray):
            raise ValueError("Image must be a numpy array")
        
        if len(v.shape) != 3 or v.shape[2] not in [3, 4]:
            raise ValueError(
                "Image must be a 3-channel (RGB/BGR) or 4-channel (RGBA/BGRA) format"
            )

        if v.dtype != np.uint8:
            raise ValueError("Image dtype must be uint8")
        return v


@DTManager.register("Metrics")
class RawMetricsPayload(MetricsPayload):
    pass


