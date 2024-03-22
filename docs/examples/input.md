


## 开发配置


### 代码配置
> 返回类: 采用内置的`FirstPayload`类

开发过程中需要的配置:


```python
...


# 注册FirstPayload作为ReturnPayload
RTManager.register()(FirstPayload)


class InputNode(CoralNode):

    ...

    def sender(self, payload: dict, context: dict) -> FirstPayload:
        raw = np.zeros((640, 640, 3), np.uint8)
        raw[:] = (255, 0, 0)  # BGR格式
        return FirstPayload(raw=raw)
```


### 配置文件

作为输入节点，通信的元数据中必须包含 `sender` 信息，无需设置 `receivers` 的信息:
```json
{
    "node_id": "input_node",
    "meta": {
        "sender": { 
            "node_id": "input_node"
        }
    },
    "params": {
        "width": 640,
        "height": 640
    }
}

```

## 内置节点返回类

采用内置的 `FirstPayload` 作为返回格式，需要传入 `raw` 数据, `FirstPayload` 内部格式定义如下:
```python
class FirstPayload(ReturnPayload):
    """
    输入节点返回类
    """

    raw: Union[CoralIntNdarray, str]
```