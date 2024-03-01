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
    model: str
    run: int


@RTManager.register()
class Node3ReturnPayload(ReturnPayload):
    result: str


class Node3(CoralNode):

    config_path = 'config.json'

    def init(self, context: dict):
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict) -> Node3ReturnPayload:
        return {"result": "hello world"}


if __name__ == '__main__':
    Node3().run()