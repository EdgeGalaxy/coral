import os
import sys
from typing import List
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src'))

from coral import CoralNode, ParamsModel, ObjectsPayload, RTManager, PTManager



@PTManager.register()
class Node2ParamsModel(ParamsModel):
    model: str
    run: int



class Node2(CoralNode):

    config_fp = 'config.json'
    node_type = 'RecognitionNode'

    def init(self, context: dict):
        print("Hello World")
        print(self.params)
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict) -> ObjectsPayload:
        return ObjectsPayload(boxes=[[1, 2, 3, 4]], class_ids=[1], labels=['person'], probs=[0.9])


if __name__ == '__main__':
    Node2().run()