# 珊瑚节点

## 功能

- 支持多种分布式通信，提供统一的接口
    - ros
    - zeromq
    - ...
- 支持pub/sub模式 && reply/request模式
- 支持多线程/多进程处理订阅的消息
- 支持多种消息类型通信
    - RawImage
- 支持自定义参数及指定类型
- 支持一些处理选项
    - 每隔几帧处理一次
- 通过XML语言定义节点信息，可通过XML还原节点
    - XML解析: xml2json
    - XML校验
    - XML还原: json2xml
- 支持订阅多个topic的消息
    - 支持并行处理多个Topic的消息
    - 支持等待某一时间段内多个topic消息同时到达后处理(待定)
- 支持统计节点信息和资源占用信息


## 使用

1. 作为底层安装包, 支持继承开发
2. 支持开发时按照约定文件格式仅开发功能代码，通过命令行运行开发代码, 生成一个新节点


## 使用示例

- 详见`examples`文件夹


## 开发详情

### 继承开发

```python
from coral import CoralNode


class CamreaNode(CoralNode):
    config_path = 'config.xml'

    def init(self, context):
        context.model = ''

    def send(self, payload, context, *args, **kwargs):
        frame = payload.frame
        model = context.model
        data = model.predict(frame)
        return data
```


```xml
<node>
    <name disable></name>
    <desc disable></desc>
    <mode edited></mode>
    <send>
        <data_type select></data_type>
        <mware select></mware>
        <cls_name></cls_name>
        <topic></topic>
        <carries></carries>
        <blocking></blocking>
        <socket_sub_port></socket_sub_port>
        <socket_pub_port></socket_pub_port>
    </send>
    <recv>
        <data_type select></data_type>
        <mware select></mware>
        <cls_name></cls_name>
        <topic></topic>
        <carries></carries>
        <blocking></blocking>
        <socket_sub_port></socket_sub_port>
        <socket_pub_port></socket_pub_port>
    </recv>
    <init>
        <model>
            <type select></type>
            <default></default>
        </model>
    </init>
    <params>
        <width edited></width>
        <cavans></cavans>
    </params>
</node>
```


### 命令行运行（cooming soon...）