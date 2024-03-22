

## 多线程加速节点处理效率

适用于:

1. 当前节点业务处理耗时
2. 一帧帧数据间没有前后关联
3. 服务器资源可负荷多线程资源消耗


开发注意事项:

- 因为采用多线程模式处理，因此线程隔离的数据需要在`init`函数中初始化


**配置**
> 只需在配置文件`config.json`中添加参数即可

```json
{
    "process": {
        "enable_parallel": true,
        "count": 5,
        "max_qsize": 180
    }
}
```

- `process`: 系统参数设定，默认单线程
    - `enable_parallel`: 是否开启多线程
    - `count`: 多线程数量
    - `max_qsize`: 多线程等待队列的最大长度


## 内存零拷贝加速节点通信延迟

适用于:

- 节点间传输的数据比较大
- 仅限`RawPayload`中的`raw`数据零拷贝
- 多个关联节点同时开启时，内存中的数据会持续存在
- 需要多个节点共享`/dev/shm`路径


**配置**
> 只需在配置文件`config.json`中添加参数即可

```json
{
    "generic": {
        "enable_shared_memory": true
    }
}
```

- `generic`: 节点通用参数，默认本地测试关闭
    - `enable_shared_memory`: 是否开启内存零拷贝
