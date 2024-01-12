import os
import sys
from typing import List
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src/coral'))

from coral import CoralNode, ParamsModel, ReturnPayload, RTManager, PTManager


@RTManager.register()
class Node2ReturnPayload(ReturnPayload):
    boxes: List
    classes_id: int
    tag: str


@PTManager.register()
class Node2ParamsModel(ParamsModel):
    model: str
    run: dict



class Node2(CoralNode):

    config_path = 'config.json'

    def init(self, context: dict):
        print("Hello World")
        print(self.params)
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict) -> Node2ReturnPayload:
        return Node2ReturnPayload(boxes=[1, 2, 3, 4], classes_id=1, tag="hello world")


if __name__ == '__main__':
    Node2().run()