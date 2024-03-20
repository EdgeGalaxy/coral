import os
import sys
import time
import numpy as np
from typing import List

from pydantic import BaseModel
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src'))

from coral import CoralNode, BaseParamsModel, FirstPayload, NodeType, PTManager, RTManager


class Point(BaseModel):
    x1: int = 0
    y1: int = 11
    x2: int = 23
    y2: int = 33


@PTManager.register()
class Node1ParamsModel(BaseParamsModel):
    width: int = 1080
    height: int = 1280
    source: str = '/dev/video0'
    items: Point = Point()


# 手动注册FirstPayload作为returnPayload
RTManager.register()(FirstPayload)


class Node1(CoralNode):

    node_name = '模拟视频流节点'
    node_desc = 'opencv随机生成视频流传输，供测试'
    config_fp = 'config.json'
    node_type = NodeType.input

    def init(self, context: dict):
        blue_image = np.zeros((640, 640, 3), np.uint8)
        blue_image[:] = (255, 0, 0)  # BGR格式
        context.update({'init': 'node1', 'raw': blue_image})

    def sender(self, payload: dict, context: dict):
        time.sleep(0.1)
        return FirstPayload(raw=context['raw'])


if __name__ == '__main__':
    import os
    run_type = os.getenv("CORAL_NODE_RUN_TYPE", "run")
    if run_type == 'register':
        Node1.node_register()
    else:
        Node1().run()