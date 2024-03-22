# 开发

Coral支持继承开发，作为开发节点的底层类，实现了主页提供的各种功能，上层用户只需关心标准接口开发即可

## 最小实现

- `node.py` - 作为程序运行的入口

```python
import os
import sys
import time
import numpy as np
from typing import List, Dict

from pydantic import BaseModel

from coral import CoralNode, BaseParamsModel, FirstPayload, NodeType, PTManager, RTManager, RawPayload


# 注册入参
@PTManager.register()
class Node1ParamsModel(BaseParamsModel):
    width: int = 1080
    height: int = 1280


# 注册FirstPayload作为ReturnPayload
RTManager.register()(FirstPayload)


class InputNode(CoralNode):

    node_name = '模拟视频流节点'
    node_desc = 'opencv随机生成视频流传输'
    config_fp = 'config.json'
    node_type = NodeType.input

    def init(self, context: Dict):
        """节点初始化参数，多线程时线程间Context数据隔离"""
        blue_image = np.zeros((640, 640, 3), np.uint8)
        blue_image[:] = (255, 0, 0)  # BGR格式
        context.update({'init': 'node1', 'raw': blue_image})

    def sender(self, payload: RawPayload, context: Dict):
        time.sleep(0.05)
        return FirstPayload(raw=context['raw'])


if __name__ == '__main__':
    import os
    run_type = os.getenv("CORAL_NODE_RUN_TYPE", "run")
    if run_type == 'register':
        InputNode.node_register()
    else:
        InputNode().run()

```

- `config.json` - 作为程序运行默认的配置文件

```json
{
    "node_id": "node1",
    "meta": {
        "sender": { 
            "node_id": "node1"
        }
    },
    "params": {
        "width": 640,
        "height": 640
    }
}
```



## 各模块解释

### 入参设置

```python
# 注册入参
@PTManager.register()
class Node1ParamsModel(BaseParamsModel):
    width: int = 1080
    height: int = 1280
```

该段代码描述了入参的定义
- `PTManager.register()` - 注册入参到入参管理器中
- `BaseParamsModel` - 最基础的入参模型，需要入参模型均继承该类


基于以上的装饰器和继承后，可以将入参交由Coral管理，程序会在运行时校验入参数据以及元数据上报时注册正确的入参格式和默认值。


### 出参设置
```python
# 注册FirstPayload作为ReturnPayload
RTManager.register()(FirstPayload)
```

该段代码描述了节点出参的定义
- `RTManager.register()` - 注册出参到出参管理器中
- `FirstPayload` - 作为第一个数据输入节点的返回类, 定义如下:

```python
class FirstPayload(ReturnPayload):
    """
    输入节点返回类
    """

    raw: Union[CoralIntNdarray, str]
```


### 节点描述类属性设置
```python

class InputNode(CoralNode):

    node_name = '模拟视频流节点'
    node_desc = 'opencv随机生成视频流传输'
    config_fp = 'config.json'
    node_type = NodeType.input

```

该段代码描述了节点描述类的定义:
- `CoralNode` - 节点基类，所有Coral节点开发都需要继承该类
- `node_name` - 节点中文名称
- `node_desc` - 节点中文描述
- `config_fp` - 节点配置文件路径，默认当前路径下的`config.json`文件
- `node_type` - 节点类型，默认为`NodeType.input`, `NodeType`类型如下

```python
class NodeType(Enum):
    input = "input"
    interface = "interface"
    rule = "rule"
    trigger = "trigger"
    output = "output"
```

以上的配置信息会在节点上报时作为元数据发送出去。


### 节点初始化数据函数
```python
    ...

    def init(self, context: Dict):
        """节点初始化参数，多线程时线程间Context数据隔离"""
        blue_image = np.zeros((640, 640, 3), np.uint8)
        blue_image[:] = (255, 0, 0)  # BGR格式
        context.update({'init': 'node1', 'raw': blue_image})
```

该段代码描述了节点初始化数据函数的定义:
- `init` - 节点初始化函数
    - 支持`context`参数，用于传递数据到业务逻辑中，运行时一个线程中只初始化一次

- `context.update({})` - 用于将数据更新到context中

### 节点逻辑实现函数
```python
    ...

    def sender(self, payload: RawPayload, context: Dict):
        time.sleep(0.05)
        return FirstPayload(raw=context['raw'])
```

该段代码描述了节点逻辑实现函数的定义:
- `sender` - 节点逻辑实现函数
    - 支持`payload`参数用于传递消息订阅的节点的通信数据到业务逻辑中
    - 支持`context`参数用于传递节点初始化的数据到业务逻辑中

- return - 返回数据，可通过`return`语句返回, 返回的格式必须是上面定义的`FirstPayload`格式


### 运行配置
```
if __name__ == '__main__':
    import os
    run_type = os.getenv("CORAL_NODE_RUN_TYPE", "run")
    if run_type == 'register':
        InputNode.node_register()
    else:
        InputNode().run()
```

运行配置：
- `CORAL_NODE_RUN_TYPE`: 作为节点运行中的环境变量，可配置为`register`和`run`两种类型，支持节点做不同的操作

- `InputNode.node_register()`: 节点注册，可以通过运行输出查看上报的节点数据格式，如果需要上报到远端服务，还需额外配置
- `InputNode().run()`: 节点运行，不需要额外配置，持续订阅指定的上游节点的数据并处理


### 节点通信格式: `RawPayload`

`RawPayload` 作为节点间通信的基础的数据格式，定义如下:
```python
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

- `source_id`: 第一个输入数据的的节点ID
- `nodes_cost`: 第一个节点到当前节点的总耗时
- `timestamp`: 当前节点处理完毕的时间戳
- `objects`: 推理节点存储的数据格式
- `metas`:  通用节点存储数据的容器

通信类：`RawPayload` 支持的操作:
- `payload.raw`: 获取输入的numpy数据
- `payload.raw_id`: 获取当前输入数据的唯一ID
- `payload.set_raw(raw)`: 更改输入的numpy数据


#### 内置的节点通信

##### `RawImagePayload`

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
- `DTManager.register`: 注册节点类型
    - `RawImage`: 图片类数据对外的ID，默认的通信类型。在`config.json`中可配置节点出入参类型

- `check_raw_data`: 校验输入的数据是否图片格式符合规范


### 配置文件`config.json`

```json
{
    "node_id": "node1",
    "meta": {
        "sender": { 
            "node_id": "node1"
        }
    },
    "params": {
        "width": 640,
        "height": 640
    }
}
```

配置文件最小版配置:
- `node_id`: 当前节点的ID，需要不能与其他节点同名
- `meta`: 当前节点通信模式的元数据
    - `sender`: 发送者的元数据
- `params`: 当前节点的入参
