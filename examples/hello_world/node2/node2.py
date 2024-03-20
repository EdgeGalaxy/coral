import os
import sys
import time
from typing import List

# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src'))

from coral import CoralNode, BaseParamsModel, PTManager, RTManager, ObjectsPayload, InterfaceMode, NodeType, ObjectPayload


@PTManager.register()
class Node2ParamsModel(BaseParamsModel):
    threshold: float = 0.3
    canvas: List[int] = [4, 4, 4, 4]
    max_scores: float = 0.98
    

# 手动注册ObjectsPayload作为returnPayload
RTManager.register()(ObjectsPayload)



class Node2(CoralNode):

    node_name = 'Yolo节点'
    node_desc = '模型推理节点'
    config_fp = 'config.json'
    node_type = NodeType.interface

    def init(self, context: dict):
        print("Hello World")
        print(self.params)
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict) -> ObjectsPayload:
        time.sleep(0.05)
        objects = [ObjectPayload(**{
            "class_id": 1,
            "label": "person",
            "prob": 0.9,
            "box": {'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0},
        })]
        return ObjectsPayload(objects=objects, mode=InterfaceMode.APPEND)


if __name__ == '__main__':
    import os
    run_type = os.getenv("CORAL_NODE_RUN_TYPE", "run")
    if run_type == 'register':
        Node2.node_register()
    else:
        Node2().run()