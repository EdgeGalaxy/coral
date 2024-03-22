
## 后台任务执行方式

```python
class InputNode(CoralNode):

    ...

    def do_job():
        time.sleep(5)
        print('do sleep!')

    def init(self, context: dict):
        # 节点初始化时执行任务
        self.bg_tasks.add_job(self.do_job, 'interval', seconds=10)

    ...

```


## 环境变量配置

- `MOUNT_PATH`: 所有node统一挂载的路径
- `CORAL_NODE_CONFIG_PATH`: 节点配置文件变量
- `CORAL_NODE_BASE64_DATA`: 节点配置Bas64环境变量, 优先级高于`CORAL_NODE_CONFIG_PATH`
- `NODE_ID`: 注册到远端服务的节点ID
- `NODE_VERSION`: 注册到远端服务的节点版本
- `NODE_IMAGE`: 注册到远端服务的节点镜像
- `REGISTER_URL`: 注册到远端服务的地址 
- `ENABLE_SHARED_MEMORY`: 是否开启共享内存, 默认不开启
- `CORAL_NODE_SHARED_MEMORY_EXPIRE`: 节点共享内存过期时间, 默认20秒
