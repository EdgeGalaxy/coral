import os
import time
import json

import numpy as np
import SharedArray as sa
from loguru import logger
from wrapyfi.utils import SingletonOptimized
from apscheduler.schedulers.background import BackgroundScheduler

from .constants import SHARED_MEMORY_ID_STORE_DIR


bg_tasks = BackgroundScheduler()


class SharedMemoryIDManager(metaclass=SingletonOptimized):
    def __init__(self, expire: int = 60):
        self._expire = expire
        self._memory_store = dict()
    
    def init_mamager(self, mamager_id):
        self.manager_id = mamager_id
        self._fp = os.path.join(SHARED_MEMORY_ID_STORE_DIR, f"{self.manager_id}.json")
        self.__load_and_flush()
        # 此处默认启动定时器, expire * 3的轮询时间删除过期的内存, 内存保留 expire时间
        self.interval_flush(self._expire * 3)
    
    def attach(self, memory_id):
        memory_data = sa.attach(memory_id)
        self._memory_store.setdefault(memory_id, time.time())
        logger.debug(f'attach shared memory: {memory_id}')
        return memory_data

    def add(self, memory_id: str, shape: tuple, dtype: np.dtype):
        memory_data = sa.create(memory_id, shape, dtype)
        self._memory_store.update({memory_id: time.time()})
        logger.debug(f"create shared memory: {memory_id}")
        return memory_data
    
    def remove(self, memory_id):
        try:
            self._memory_store.pop(memory_id, None)
            sa.delete(memory_id)
        except FileNotFoundError:
            logger.warning(f"not found memory id: {memory_id} info")

        logger.debug(f"release shared memory: {memory_id}")
    
    def dump(self):
        with open(self._fp, "w") as f:
            json.dump(self._memory_store, f)
        logger.info(f'dump shared memory id store: {self._fp} length: {len(self._memory_store)}')
    
    def interval_flush(self, interval: int):
        bg_tasks.add_job(self.remove_expired, 'interval', seconds=interval)
        logger.info(f'interval flush shared memory id store: {self._fp} every {interval} seconds')

    def remove_expired(self):
        count = 0
        for memory_id, timestamp in self._memory_store.copy().items():
            if time.time() - timestamp > self._expire:
                self.remove(memory_id)
                count += 1
        logger.info(f'remove expired shared memory id store: {self._fp} count: {count}')

    def __load(self):
        try:
            with open(self._fp, "r") as f:
                data = json.load(f)
                # 更新内存数据
                self._memory_store.update(data)
        except Exception as e:
            logger.warning(f"load shared memory id store: {self._fp} failed: {e}")
            return {}
    
    def __load_and_flush(self):
        self.__load()
        self.remove_expired()

        
