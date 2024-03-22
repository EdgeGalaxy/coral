


## 模型类定义

### 配置类

```python
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
```

- `pipeline_id`: 多个node_id组成的pipeline的ID
- `node_id`: 节点ID
- `process`: 进程配置
- `meta`: 通信元数据配置
- `generic`: 节点通用模式配置
- `params`: 节点入参


### 配置类的各部分子类

- 系统参数设定
```python
class ProcessModel(CoralBaseModel):
    """
    系统参数设定
    """
    max_qsize: int = Field(frozen=True, default=180)
    count: int = Field(frozen=True, default=3)
    enable_parallel: bool = Field(frozen=True, default=False)
```

- 业务通用参数
```python
class GenericParamsModel(CoralBaseModel):
    """
    业务通用参数
    """
    skip_frame: int = Field(frozen=True, default=0, description="每隔几帧处理一次")
    enable_metrics: bool = Field(frozen=True, default=True, description="是否开启服务监控")
    enable_shared_memory: bool = Field(frozen=True, default=False, validate_default=True, description="是否开启共享内存")

```

- Sender & Receivers 通信类 
```python
class MetaModel(CoralBaseModel):
    """
    sender & receiver 通信类
    """
    mode: str = Field(frozen=True, default=ProtocalType.PUBSUB)
    receivers: List[ReceiverModel] = Field(frozen=True, default=[])
    sender: SenderModel = Field(frozen=True, default=None)
```
```python
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


class ReceiverModel(PubSubBaseModel):
    pass


class SenderModel(PubSubBaseModel):
    pass

```

    - `node_id`: 节点ID
    - `raw_type`: 通信的数据类型, 默认`RawImage`, 图像类通信数据
    - `mware`: 通信的中间件, 默认`zeromq`
    - `cls_name`: 通信的类名, 默认`NoReceiverUse`, 占位符
    - `topic`: 通信的topic
    - `carrier`: 通信的协议
    - `blocking`: 是否阻塞
    - `socket_sub_port`: 订阅端口
    - `socket_pub_port`: 发布端口
    - `params`: 通信额外的参数, 一般不配置