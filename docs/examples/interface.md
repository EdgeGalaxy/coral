
## 开发配置

### 代码配置
> 返回类: 采用内置的`ObjectsPayload`类

开发过程中需要的配置:

```python
...

# 注册ObjectsPayload作为ReturnPayload
RTManager.register()(ObjectsPayload)


class InterfaceNode(CoralNode):

    ...

    def sender(self, payload: dict, context: dict) -> ObjectsPayload:
        objects = [ObjectPayload(**{
            "class_id": 1,
            "label": "person",
            "prob": 0.9,
            "box": Box(x1=0, y1=0, x2=100, y2=100)
        })]
        return ObjectsPayload(mode=InterfaceMode.APPEND, objects=objects)
```



### 配置文件

作为推理节点，通信的元数据中必须包含 `sender` 和 `receivers` 的信息, 接收上游数据并返回: 
```json
{
    "node_id": "interface_node",
    "meta": {
        "receivers": [
            {
                "node_id": "input_node"
            }
        ],
        "sender": 
            {
                "node_id": "interface_node",
                "raw_type": "RawImage"
            }
    },
    "params": {
        "weight_fp": "https://xxx/weights.onnx",
    }
}

```

## 内置节点返回类

采用内置的 `ObjectsPayload` 返回类, 每个类必须是 `ObjectPayload` 的模型类, 类定义如下:

```python
class InterfaceMode(Enum):
    APPEND = "append"
    OVERWRITE = "overwrite"


class ObjectsPayload(BaseInterfacePayload):
    """
    Yolo推理返回类
    """

    mode: InterfaceMode
    objects: Union[List[ObjectPayload], NoneType] = None
```

- `mode`: 推理数据与上层订阅的数据如何合并的模式
    - `APPEND`: 追加模式，若`RawPaylod`的`objects`中存在数据，则追加
    - `OVERWRITE`: 覆盖模式，直接完全覆盖`RawPaylod`的`objects`中的数据
- `objects`: 推理结果列表, 每个元素都是`ObjectPayload`


```python
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
```

- `id`: 非必填参数，用于标识对象的id
- `label`: 对象类别
- `class_id`: 对象类别id
- `prob`: 对象置信度
- `box`: 对象框
    - `x1`: 左上角x坐标
    - `y1`: 左上角y坐标
    - `x2`: 右下角x坐标
    - `y2`: 右下角y坐标
- `objects`: 对象列表
