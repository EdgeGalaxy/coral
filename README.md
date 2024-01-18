# 珊瑚节点

## 功能

- 支持多种分布式通信，提供统一的接口
    - ros
    - zeromq
- 支持pub/sub模式模式
- 支持多线程处理订阅的消息
- 支持多种消息类型通信
    - RawImage
    - Metrics
- 支持自定义参数及指定类型
- 支持一些处理选项
    - 每隔几帧处理一次
- 通过XML/Json语言定义节点信息
- 支持订阅多个topic的消息
    - 支持并行处理多个Topic的消息
- 支持统计节点信息和资源占用信息


## 使用

1. 作为底层安装包, 支持继承开发
2. 支持开发时按照约定文件格式仅开发功能代码，通过命令行运行开发代码, 生成一个新节点


## 使用示例

- 详见`examples`文件夹


## 开发详情

### 继承开发

```python
import os
import sys
import numpy as np
from typing import Union

from coral import CoralNode, ParamsModel, FirstPayload, RTManager, PTManager


# 定义返回参数的数据类型
@RTManager.register()
class Node1ReturnPayload(FirstPayload):
    raw: Union[np.ndarray, str] 


# 定义入参的数据类型
@PTManager.register()
class Node1ParamsModel(ParamsModel):
    model: str
    run: dict


class Node1(CoralNode):

    # 指定配置文件路径
    config_path = 'config.json'

    def init(self, context: dict):
        "节点初始化相关逻辑，context会传递到sender方法中"
        blue_image = np.zeros((640, 640, 3), np.uint8)
        blue_image[:] = (255, 0, 0)  # BGR格式
        context.update({'init': 'node1', 'raw': blue_image})


    def sender(self, payload: dict, context: dict) -> Node1ReturnPayload:
        "节点发送逻辑，return的内容会附加到RawImage消息类型中发送"
        return {'raw': context['raw']}
```


```json
{
    "node_id": "node1",
    "meta": {
        "sender": { 
                "topic": "/topic1",
                "params": {
                    "socket_sub_port": 5759,
                    "socket_pub_port": 5758
                }
            }
    },
    "generic": {
        "enable_metrics": true,
        "metrics_sender": {
            "raw_type": "Metrics",
            "topic": "/node1_metrics",
            "params": {
                "socket_sub_port": 5859,
                "socket_pub_port": 5858
            }
        }
    },
    "params": {
        "model": "model_path",
        "run": {
            "width": 100
        }
    }
}
```


### 命令行运行（cooming soon...）