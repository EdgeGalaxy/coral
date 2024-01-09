import os
import sys
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src/coral'))

from coral import CoralNode


class Node1(CoralNode):

    config_path = 'config.json'

    def init(self, context: dict):
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict):
        return 'success',


if __name__ == '__main__':
    Node1().run()