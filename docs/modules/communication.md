
## 内置通信数据格式基类


```python

class BaseRawPayload(CoralBaseModel):
    """
    Base通用节点通信数据类, 涵盖共享内存的管理
    """

    raw_id: str = Field(default_factory=lambda: generate_short_uid())

    _raw: CoralIntNdarray = PrivateAttr(default=None)
    _raw_shared_memory_id: str = PrivateAttr(default=None)
    _enable_shared_memory: bool = PrivateAttr(default=False)

    ...

    @computed_field
    def raw(self) -> np.array:
        return self._raw

    @computed_field
    def raw_shared_memory_id(self) -> str:
        return self._raw_shared_memory_id


    def set_raw(self, raw: np.ndarray):
        ....



class RawPayload(BaseRawPayload):
    """
    通用节点通信数据类
    """

    source_id: str
    nodes_cost: float = 0
    timestamp: float = Field(default_factory=time.time)
    objects: Union[List[ObjectPayload], NoneType] = None
    metas: Union[Dict[str, ReturnPayload], NoneType] = None

```

参数解释: 

- `source_id`: 第一个输入数据的节点ID
- `nodes_cost`: 第一个节点到当前节点的总耗时
- `timestamp`: 当前节点处理完毕的时间戳
- `objects`: 推理节点存储的数据格式
- `metas`:  通用节点存储数据的容器

通信类`RawPayload` 支持的操作:

- `payload.raw`: 获取输入的numpy数据
- `payload.raw_id`: 获取当前输入数据的唯一ID
- `payload.set_raw(raw)`: 更改输入的numpy数据


## 继承基类实现的通信类

### 图片数据通信

```python
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
```

图片数据通信类定义：

- `DTManager.register("RawImage")`: 注册节点类型
    - `RawImage`: 图片类数据对外的ID，默认的通信类型。在`config.json`中可配置节点出入参类型

- `check_raw_data`: 校验输入的数据是否符合规范图片格式