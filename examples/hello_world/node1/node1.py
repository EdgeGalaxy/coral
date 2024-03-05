import os
import sys
import time
import numpy as np
from typing import Union
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src'))

from coral import CoralNode, ParamsModel, FirstPayload, RTManager, PTManager, ConfigModel


@RTManager.register()
class Node1ReturnPayload(FirstPayload):
    raw: Union[np.ndarray, str] 


@PTManager.register()
class Node1ParamsModel(ParamsModel):
    model: str = 'model.pt'
    width: int = 100


class Node1(CoralNode):

    config_fp = 'config.json'
    node_type = 'DataProducerNode'

    def init(self, context: dict):
        blue_image = np.zeros((640, 640, 3), np.uint8)
        blue_image[:] = (255, 0, 0)  # BGR格式
        context.update({'init': 'node1', 'raw': blue_image})


    def sender(self, payload: dict, context: dict):
        time.sleep(0.01)
        return {'raw': context['raw']}


if __name__ == '__main__':
    Node1().run()