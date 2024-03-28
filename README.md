# 珊瑚节点

## 功能

- 支持多种分布式通信，提供统一的接口
    - ros2
    - zeromq
- 支持pub/sub模式模式
- 支持多线程处理订阅的消息
- 支持多种消息类型通信
    - RawImage
    - Metrics
- 支持自定义参数及指定类型
- 支持一些处理选项
    - 每隔几帧处理一次
- 通过Json语言定义节点信息
- 支持订阅多个topic的消息
    - 支持并行处理多个Topic的消息
- 支持统计节点信息和资源占用信息


## 使用

1. 作为底层安装包, 支持继承开发
2. 支持开发时按照约定文件格式仅开发功能代码，通过命令行运行开发代码, 生成一个新节点

### 安装
```shell
pip install pycoral -i http://47.116.14.85:9000/simple --trusted-host 47.116.14.85
```

### 构建&发布
```shell
rye build --clean
rye publish --repository looptech --repository-url http://47.116.14.85:9000/simple -u looptech
```


## 使用示例

- 详见`examples`文件夹


## 开发详情

### 继承开发


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


## 注意事项

1. zeromq pub/sub传输的速率如何？

与传输的的消息大小有关，模拟测试（640，640，3）的图片向量PUB速率在传输 120帧/s， SUB的速率在65帧/s。这种情况下就会存在比较大的延迟, 可以通过多线程模式来加速处理