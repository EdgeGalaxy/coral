import uuid
import time

from typing import List, Union
from pydantic import BaseModel

import numpy as np
from wrapyfi.publishers import Publishers
from pydantic import validator 


class CoralBaseModel(BaseModel):

    class Config:
        arbitrary_types_allowed = True


class Rect(BaseModel):
    top: int
    left: int
    width: int
    height: int

class Attribute(BaseModel):
    id: int
    label: str
    probability: float
    class_id: int


class ObjectsModel(BaseModel):
    id: int
    label: str
    class_id: int
    probability: float
    rect: Rect = []
    attributes: List[Attribute] = []


class ReturnPayload(CoralBaseModel):
    timestamp: float = time.perf_counter()


class FirstPayload(ReturnPayload):
    raw: Union[np.ndarray, str] = None


class ParamsModel(CoralBaseModel):
    pass


class RawPayload(CoralBaseModel):
    node_id: str
    raw_id: str = str(uuid.uuid4())
    raw: Union[np.ndarray, str] = None
    timestamp: float = time.perf_counter()
    objects: List[ObjectsModel] = []
    metas: List[ReturnPayload] = []


class BatchRawPayload(BaseModel):
    payloads: List[RawPayload]


class DataTypeManager:
    registry = {}
    mapping_types: List[str] = [t.split(':')[0] for t in Publishers.registry.keys()]

    @classmethod
    def register(cls: 'DataTypeManager', payload_type: str, data_type: str = "NativeObject"):
        def decorator(cls_: RawPayload):
            if data_type not in cls.mapping_types:
                raise ValueError(f"Invalid mapping type: {data_type}, should include in {cls.mapping_types}")
            if not issubclass(cls_, RawPayload):
                raise TypeError(f"Invalid class model type: {cls_.__name__}, should be a subclass of {RawPayload.__name__}")
            cls.registry[payload_type] = (data_type, cls_)
            return cls_
        return decorator


class ParamsManager:
    registry = {}

    @classmethod
    def register(cls: 'ParamsManager', params_name: str = None):
        def decorator(cls_: ParamsModel):
            if not issubclass(cls_, ParamsModel):
                raise TypeError(f"Invalid class model type: {cls_}, should be a subclass of {ParamsModel.__name__}")
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
    def register(cls: 'ReturnManager', return_name: str = None):
        def decorator(cls_: ReturnPayload):
            if not issubclass(cls_, ReturnPayload):
                raise TypeError(f"Invalid class model type: {cls_}, should be a subclass of {ReturnPayload.__name__}")
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

    @validator('raw')
    def check_image(cls, v):
        if not isinstance(v, np.ndarray):
            raise ValueError('Image must be a numpy array')

        if len(v.shape) != 3 or v.shape[2] not in [3, 4]:
            raise ValueError('Image must be a 3-channel (RGB/BGR) or 4-channel (RGBA/BGRA) format')

        if v.dtype != np.uint8:
            raise ValueError('Image dtype must be uint8')
        return v


@DTManager.register("RawTest")
class RawTestPayload(RawPayload):
    pass


# @DTManager.register("RawBatchImage")
# class RawBatchImagePayload(BatchRawPayload):
#     pass


@DTManager.register("")
class DetectPayload(RawPayload):
    pass


@DTManager.register("")
class ClassifyPayload(RawPayload):
    pass


@DTManager.register("")
class RecognizePayload(RawPayload):
    pass