import cv2
import os
import sys
import numpy as np
from typing import Union
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src'))

from coral import CoralNode, ParamsModel, ReturnPayload, RTManager, PTManager, ConfigModel


@PTManager.register()
class Node3ParamsModel(ParamsModel):
    model: str = 'model.pt'
    run: int = 200


@RTManager.register()
class Node3ReturnPayload(ReturnPayload):
    result: str


class Node3(CoralNode):

    node_name = '视频流展示'
    node_desc = '视频流展示节点，通过web展示视频流'
    config_path = 'config.json'
    node_type = 'MediaProcessNode'

    def init(self, context: dict):
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict) -> Node3ReturnPayload:
        return {"result": "hello world"}


if __name__ == '__main__':
    import os
    run_type = os.getenv("CORAL_NODE_RUN_TYPE", "run")
    if run_type == 'register':
        Node3.node_register()
    else:
        Node3().run()