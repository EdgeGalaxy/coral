import os

DEFAULT_NO_TOPIC = "/no_topic"
DEFAULT_NO_RECEVIER_MSG = "#no_recevier#"
# shared memory 数据类型
SHARED_DATA_TYPE = "shm://"
# 所有node统一挂载的路径
MOUNT_PATH = os.environ.get("CORAL_PIPE_MOUNT_DIR", f"{os.environ['HOME']}/.coral")