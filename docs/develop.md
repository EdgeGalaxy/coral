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
        # 获取入参数据
        timestamp = time.time()
        context.update({'init_time': timestamp})

    def sender(self, payload: RawPayload, context: Dict):
        print('init time', context['init_time'])
        raw = np.zeros((self.params.width, self.params.height, 3), np.uint8)
        raw[:] = (255, 0, 0)  # BGR格式
        return FirstPayload(raw=raw)


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
    "node_id": "input_node",
    "meta": {
        "sender": { 
            "node_id": "input_node"
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

- `PTManager.register()`: 注册入参到入参管理器中
- `BaseParamsModel`: 最基础的入参模型，需要入参模型均继承该类


基于以上的装饰器和类继承后，可以将入参交由CoralNode管理，程序会在运行时校验入参数据以及元数据上报时注册正确的入参格式和默认值。


### 出参设置
```python
# 注册FirstPayload作为ReturnPayload
RTManager.register()(FirstPayload)
```

该段代码描述了节点出参的定义

- `RTManager.register()`: 注册出参到出参管理器中
- `FirstPayload`: 作为第一个数据输入节点的返回类, 定义如下:

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

- `CoralNode`: 节点基类，所有Coral节点开发都需要继承该类
- `node_name`: 节点中文名称
- `node_desc`: 节点中文描述
- `config_fp`: 节点配置文件路径，默认当前路径下的`config.json`文件
- `node_type`: 节点类型，默认为`NodeType.input`, `NodeType`类型如下
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
        # 获取入参数据
        timestamp = time.time()
        context.update({'init_time': timestamp})
```

该段代码描述了节点初始化数据函数的定义:

- `init` - 节点初始化函数
    - `context`: 函数参数，用于传递数据到业务逻辑中，运行时一个线程中只初始化一次
    - `context.update({})`: 用于将数据更新到context中

### 节点逻辑实现函数
```python
    ...

    def sender(self, payload: RawPayload, context: Dict):
        print('init time', context['init_time'])
        raw = np.zeros((self.params.width, self.params.height, 3), np.uint8)
        raw[:] = (255, 0, 0)  # BGR格式
        return FirstPayload(raw=raw)
```

该段代码描述了节点逻辑实现函数的定义:

- `sender`: 节点逻辑和发送节点数据函数
    - `payload`参数用于传递订阅的节点消息数据到业务逻辑中
    - `context`参数用于传递节点初始化的数据到业务逻辑中

- return返回数据，可通过`return`语句返回, 返回的格式必须是上面定义的`FirstPayload`格式


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





### 配置文件`config.json`

```json
{
    "node_id": "input_node",
    "meta": {
        "sender": { 
            "node_id": "input_node"
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
- `meta`: 节点通信的元数据
    - `sender`: 发送者的元数据
- `params`: 当前节点的入参
