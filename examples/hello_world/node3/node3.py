import cv2
import os
import sys
import numpy as np
from typing import Union
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src/coral'))

from coral import CoralNode, ParamsModel, FirstPayload, RTManager, PTManager, ConfigModel


@PTManager.register()
class Node3ParamsModel(ParamsModel):
    model: str
    run: dict


class Node3(CoralNode):

    config_path = 'config.json'

    def init(self, context: dict):
        blue_image = np.zeros((640, 640, 3), np.uint8)
        blue_image[:] = (255, 0, 0)  # BGR格式
        context.update({'init': 'node1', 'raw': blue_image})


    def sender(self, payload: dict, context: dict):
        return {'raw': context['raw']}


if __name__ == '__main__':
    Node3().run()