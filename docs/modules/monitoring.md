
## 监控指标

- `process_frames_count`: 当前节点处理的帧数, 处理一帧发送一次
- `drop_frames_count`: 当前节点丢弃的帧数, 丢弃一帧发送一次
- `skip_frames_count`: 当前节点跳过的帧数, 跳过一帧发送一次
- `process_frames_cost`: 当前节点纯处理的消耗时间
- `pendding_frames_cost`: 当前节点从上一个节点订阅数据到接收的消耗时间
- `process_node_cost`: 当前节点总耗时


## MQTT 通用格式TOPIC定义

TOPIC 定义格式: `organization/+/gateway/+/pipeline/+/node/+/+/+`


每一个`+`代表一个占位符，依次为:

- `organization_id` 组织/用户ID
- `gateway_id` 网关ID
- `pipeline_id` 管道ID
- `node_id` 节点ID
- `metric` 节点监控指标, 以上定义的监控指标
- `data_type` 数据类型


## 自定义指标上报实现

```python

class InputNode(CoralNode):

    ...

    def sender(self, payload: RawPayload, context: dict):
        time.sleep(0.05)
        # 自定义指标使用
        self.metrics.business_set('business_topic_defind', 1)
        return FirstPayload(raw=context['raw'])
```


## 上报指标配置文件设置
> 默认节点Metrics上报的配置文件一般不会发生变化，与`config.json`文件分开，放置在 `$HOME/.coral/common-config.json` 路径下

```json
{
    "organization_id": "coral-user",
    "gateway_id": "coral-gateway",
    "mqtt": {
        "broker": "localhost",
        "port": 1883,
        "username": "admin",
        "password": "admin"
    }
}
```