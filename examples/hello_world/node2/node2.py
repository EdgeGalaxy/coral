import os
import sys
# 将src加入到系统路径
sys.path.append(os.path.abspath('../../../src/coral'))

from coral import CoralNode


class Node2(CoralNode):

    config_path = 'config.json'

    def init(self, context: dict):
        print("Hello World")
        print(self.init_params)
        context.update({'init': 'node1'})

    def sender(self, payload: dict, context: dict):
        print(context)
        return 'node2',


if __name__ == '__main__':
    Node2().run()