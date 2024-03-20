import os

DEFAULT_NO_TOPIC = "/no_topic"
DEFAULT_NO_RECEVIER_MSG = "#no_recevier#"
# 所有node统一挂载的路径
MOUNT_PATH = os.environ.get("CORAL_PIPE_MOUNT_DIR", f"{os.environ['HOME']}/.coral")
# lock dir
LOCK_DIR = os.path.join(MOUNT_PATH, "lock")
os.makedirs(LOCK_DIR, exist_ok=True)
# shared memory 数据类型
SHARED_DATA_TYPE = "shm://"
# shared memory save dir
SHARED_MEMORY_ID_STORE_DIR = os.path.join(MOUNT_PATH, "shared_memory_ids")
os.makedirs(SHARED_MEMORY_ID_STORE_DIR, exist_ok=True)
# shared memory lock file
DELETE_SHARED_MEMORY_LOCK = os.path.join(LOCK_DIR, "shared_memory_delete.lock")
