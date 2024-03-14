import os
import sys
import time
from typing import List
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src'))

from coral import CoralNode, ParamsModel, PTManager, ObjectsPayload



@PTManager.register()
class Node2ParamsModel(ParamsModel):
    model: str
    run: int


class Node2(CoralNode):

    node_name = 'Yolo节点'
    node_desc = '模型推理节点'
    config_fp = 'config.json'
    node_type = 'RecognitionNode'

    def init(self, context: dict):
        print("Hello World")
        print(self.params)
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict) -> ObjectsPayload:
        time.sleep(0.1)
        objects = {
            "class_ids": [1],
            "labels": ["person"],
            "probs": [0.9],
            "boxes": [[1, 2, 3, 4]]
        }
        return ObjectsPayload(**objects)


if __name__ == '__main__':
    import os
    run_type = os.getenv("CORAL_NODE_RUN_TYPE", "run")
    if run_type == 'register':
        Node2.node_register()
    else:
        Node2().run()