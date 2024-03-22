
## 开发配置

### 代码配置

> 返回类: 需要继承`ReturnPayloadWithTS`返回类

开发过程中需要的配置:

```python
...


@RTManager.register()
class CommonReturnPayload(ReturnPayloadWithTS):
    height: int


class CommonNode(CoralNode):

    ...

    def sender(self, payload: RawPayload, context: Dict) -> CommonReturnPayload:
        return CommonReturnPayload(height=100)

```

### 配置文件

```json
{
    "node_id": "common_node",
    "meta": {
        "receivers": [{
            "node_id": "interface_node"
        }],
        "sender": {
            "node_id": "common_node",
            "raw_type": "RawImage"
        }
    },
    "params": {
        "height": 100
    }
}
```


## 内置节点返回类

该类为内置的返回子类，一般被外部继承使用，作为返回类的基类

```python
class ReturnPayloadWithTS(ReturnPayload):
    """
    带时间戳的节点返回基类
    """

    timestamp: float = Field(default_factory=time.time)
```