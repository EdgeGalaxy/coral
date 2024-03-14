from functools import partial
import time
import schedule
from typing import Union
from threading import Thread

from loguru import logger
from wrapyfi.connect.wrapper import MiddlewareCommunicator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.metrics import MetricWrapperBase

from .types import SenderModel


class CoralNodeMetrics:
    """
    - 处理的数据帧
    - 主动｜被动 丢弃未处理的数据帧
    - 单次处理的耗时
    - 数据帧从发送到接收的时间
    """

    def __init__(self, enable, pipeline_id, node_id) -> None:
        self.enable = enable
        self.pipeline_id = pipeline_id
        self.node_id = node_id
        self.labels = list(self.default_labels.keys())
        self.__count_process_frames = self._count_process_frames()
        self.__count_drop_frames = self._count_drop_frames()
        self.__cost_process_frames = self._cost_process_frames()
        self.__cost_pendding_frames = self._cost_pendding_frames()

    @property
    def default_labels(self):
        return {
            "pipeline_id": self.pipeline_id,
            "node_id": self.node_id,
        }

    def register_sender(self, meta: SenderModel, interval=5):
        if not self.enable:
            logger.warning(f"Metrics disabled! not register any sender")
            return
        if meta is None:
            logger.warning(f"sender is None! not register any sender")
            return

        sender_obj = CoralWrapyfiMetricsSender(meta)

        def run_schedule():
            do_func = partial(sender_obj._sender, sender_obj)
            schedule.every(interval).seconds.do(do_func)

            while True:
                schedule.run_pending()
                time.sleep(interval / 2)

        Thread(target=run_schedule).start()
        logger.info(f"background register sender: {meta}")

    def count_process_frames(self, value: int = 1):
        return self.set(self.__count_process_frames, value)

    def count_drop_frames(self, action: str = "active", value: int = 1):
        return self.set(
            self.__count_drop_frames, value, extra_labels={"action": action}
        )

    def cost_process_frames(self, value: float):
        return self.set(self.__cost_process_frames, value)

    def cost_pendding_frames(self, value: float):
        return self.set(self.__cost_pendding_frames, value)

    def set(
        self,
        metric_obj: MetricWrapperBase,
        value: Union[int, float],
        extra_labels: dict = None,
    ):
        if not self.enable:
            return
        extra_labels = extra_labels or {}
        labels = {**self.default_labels, **extra_labels}
        if isinstance(metric_obj, Counter):
            metric_obj.labels(**labels).inc(value)
        elif isinstance(metric_obj, Histogram):
            metric_obj.labels(**labels).observe(value)
        elif isinstance(metric_obj, Gauge):
            metric_obj.labels(**labels).set(value)
        else:
            raise TypeError(f"Unsupported type: {type(metric_obj)}")

    def _count_process_frames(self) -> Counter:
        return Counter(
            "coral__pipeline__node__process_frames_count", "节点处理的数据帧", self.labels
        )

    def _count_drop_frames(self) -> Counter:
        labels = ["action", *self.labels]
        return Counter("coral__pipeline__node__drop_frames", "节点主动｜被动丢弃的数据帧", labels)

    def _cost_process_frames(self) -> Histogram:
        return Histogram(
            "coral__pipeline__node__process_frames_cost", "节点单次处理的耗时", self.labels
        )

    def _cost_pendding_frames(self) -> Histogram:
        return Histogram(
            "coral__pipeline__node__pendding_frames_cost", "节点数据帧从发送到接收的时间", self.labels
        )


class CoralWrapyfiMetricsSender(MiddlewareCommunicator):
    def __init__(self, meta: SenderModel):
        self.meta = meta
        self.__init_sender(meta)

    def __init_sender(self, meta: SenderModel):
        """
        Initialize the sender for the given SenderModel object.

        Parameters:
            meta (SenderModel): A list of SenderModel objects containing the required metadata for each sender.

        Returns:
            None

        Raises:
            None
        """
        if meta is None:
            logger.warning(f"{self.__class__.__name__} sender is None!")
            return
        self._sender = MiddlewareCommunicator.register(
            meta.data_type,
            meta.mware,
            meta.cls_name,
            meta.topic,
            carrier=meta.carrier,
            should_wait=meta.blocking,
            proxy_broker_spawn="thread",
            pubsub_monitor_listener_spawn="thread",
            **meta.params,
        )(self._sender)
        self.activate_communication(self._sender, mode="publish")

    def _sender(self, *args, **kwargs):
        try:
            data = self.sender(*args, **kwargs)
            pub_data = {"metrics": data.decode()}
        except Exception as e:
            logger.info(f"topic {self.meta.topic} sender error: ", e)

        logger.debug(f"prometheus data: {pub_data}")
        return (pub_data,)

    def sender(self, *args, **kwargs):
        return generate_latest()
