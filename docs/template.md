
## 使用
> 采用`cookiecutter`实现的模板代码，可一键运行

```shell
# 安装运行包
pip install cookiecutter


# 生成模板
cookiecutter https://github.com/EdgeGalaxy/CoralNodeTemplate.git
```


## 运行设置参数

- `node_name`: 节点名称
- `node_slug`: 节点文件夹名，一般采用默认值
- `node_desc`: 节点描述
- `node_cls`: 节点类名
- `node_type`: 节点类型
    - `input`: 数据生产节点
    - `interface`: 推理节点
    - `rule`: 规则节点
    - `trigger`: 逻辑触发节点
    - `output`: 数据输出节点
- `receiver_node`: 接收节点, 非`input`节点时必填


## 包管理工具

采用[`poetry`](https://python-poetry.org/docs/basic-usage/)作为包管理工具。常用的命令有：

- `poetry add <package_name>`: 添加依赖
- `poetry remove <package_name>`: 移除依赖
- `poetry update <package_name>`: 更新依赖
- `poetry shell`: 激活虚拟环境