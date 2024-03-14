import cv2
import os
import sys
import numpy as np
from typing import Union
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src'))

from coral import CoralNode, ParamsModel, PTManager


@PTManager.register()
class Node3ParamsModel(ParamsModel):
    width: int = 100
    height: int = 100
    encode: str = 'jpg'


class Node3(CoralNode):

    node_name = '视频流展示'
    node_desc = '视频流展示节点，通过web展示视频流'
    config_path = 'config.json'
    node_type = 'MediaProcessNode'

    def init(self, context: dict):
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict):
        return None


if __name__ == '__main__':
    import os
    run_type = os.getenv("CORAL_NODE_RUN_TYPE", "run")
    if run_type == 'register':
        Node3.node_register()
    else:
        Node3().run()