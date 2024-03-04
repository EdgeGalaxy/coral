import os
import time
import json
import uuid
import queue
import requests
import multiprocessing
from typing import Dict, List, Any, NamedTuple
from loguru import logger
from threading import Thread
from collections import defaultdict, deque

from wrapyfi.connect.wrapper import MiddlewareCommunicator

from .constants import DEFAULT_NO_RECEVIER_MSG
from .parse import CoralParser
from .parser import BaseParse
from .metrics import CoralNodeMetrics
from .types import (
    MetaModel,
    ParamsModel,
    SenderModel,
    ReceiverModel,
    ModeModel,
    ProcessModel,
    RawPayload,
    FirstPayload,
    ObjectsPayload,
)


# 节点配置文件变量
CORAL_NODE_CONFIG_PATH = os.environ.get("CORAL_NODE_CONFIG_PATH")
# 节点配置Bas64环境变量
CORAL_NODE_BASE64_DATA = os.environ.get("CORAL_NODE_BASE64_DATA")
# 节点类型
NODE_TYPES = ["DataProducerNode", "RecognitionNode", "BusinessNode", "MediaProcessNode"]


class CoralNode(MiddlewareCommunicator):
    config_fp = 'config.json'
    node_type = None

    def __init__(self):
        assert self.node_type in NODE_TYPES, 'node type must in {}'.format(NODE_TYPES)
        config_path, file_type = self.get_config()
        self.__config = CoralParser.parse(config_path, file_type)
        self._queue = self.__queue()
        self._process_cls = self.__process_cls()
        self.receivers = self.__init_receivers(self.meta.receivers)
        self.__init_sender(self.meta.sender)
        # run time
        self.run_time = time.time()
        # fps cal
        self.receiver_times = deque(maxlen=1000)
        self.sender_times = deque(maxlen=1000)
        self.receiver_times.append(self.run_time)
        self.sender_times.append(self.run_time)
        # node info report
        self.config_schema = self.config.parse_json_schema(self.node_type)
        # publish node schema
        self.publish_node_schema()
        # metrics
        self.metrics = CoralNodeMetrics(
            pipeline_id=self.config.pipeline_id,
            node_id=self.config.node_id,
            enable=self.config.generic_params.enable_metrics,
        )
        self.metrics.register_sender(
            meta=SenderModel(node_id=f"{self.config.node_id}_Metrics", raw_type="Metrics"),
            interval=self.config.generic_params.metrics_interval,
        )
        # skip frame recorder
        self.receiver_frames_count = defaultdict(int)
    
    def get_config(self):
        if CORAL_NODE_BASE64_DATA:
            logger.info(f'use env CORAL_NODE_BASE64_DATA: {CORAL_NODE_BASE64_DATA}')
            return CORAL_NODE_BASE64_DATA, 'base64'
        if CORAL_NODE_CONFIG_PATH:
            logger.info(f'use env CORAL_NODE_CONFIG_PATH: {CORAL_NODE_CONFIG_PATH}')
            return CORAL_NODE_CONFIG_PATH, CORAL_NODE_CONFIG_PATH.split('.')[-1]
        logger.info(f'use default config path: {self.config_fp}')
        return self.config_fp, self.config_fp.split('.')[-1]
    
    def publish_node_schema(self):
        """
        publish node schema info to remote

        :raises Exception:
        """
        node_id = os.environ.get("CORAL_NODE_NAME")
        node_version = os.environ.get("CORAL_NODE_VERSION")
        node_image = os.environ.get("CORAL_NODE_DOCKER_IMAGE")
        register_url = os.environ.get("CORAL_NODE_REGISTER_URL")
        logger.info(f"publish node schema: {node_id} {node_version} {node_image} {register_url}!")
        if all([node_id, node_version, node_image, register_url]):
            url = register_url.format(node_id=node_id, version=node_version)
            self.config_schema.update({'image': node_image})
            r = requests.post(url, json=self.config_schema, timeout=5)
            if r.ok:
                logger.info(f"publish node schema success: {url} {json.dumps(self.config_schema)}!")
            else:
                raise Exception(f"publish node schema failed: {r.status_code} {r.content}!")
        else:
            logger.info(f"not need publish node schema: {json.dumps(self.config_schema)}!")
        
    @property
    def skip_frame_count(self):
        return self.config.generic_params.skip_frame

    @property
    def config(self) -> BaseParse:
        return self.__config

    @property
    def process(self) -> ProcessModel:
        return self.config.process

    @property
    def meta(self) -> MetaModel:
        return self.config.meta

    @property
    def params(self) -> ParamsModel:
        return self.config.params

    @property
    def mode(self) -> ModeModel:
        return self.meta._mode

    @property
    def receiver_fps(self):
        duration = self.receiver_times[-1] - self.receiver_times[0]
        if duration == 0:
            return 0
        return len(self.receiver_times) / duration

    @property
    def sender_fps(self):
        duration = self.sender_times[-1] - self.sender_times[0]
        if duration == 0:
            return 0
        return len(self.sender_times) / duration

    def __queue(self):
        """
        Return a queue object based on the run mode of the process.

        Returns:
            - If the run mode is 'threads', return a queue.Queue object with a maximum size of self.process.max_qsize.
            - If the run mode is not 'threads', return a multiprocessing.Queue object with a maximum size of self.process.max_qsize.
        """
        if self.process.run_mode == "threads":
            return queue.Queue(maxsize=self.process.max_qsize)
        else:
            return multiprocessing.Queue(maxsize=self.process.max_qsize)

    def __process_cls(self):
        """
        Return the appropriate class for process execution based on the run mode.

        Parameters:
            None

        Returns:
            Type: Either `Thread` or `multiprocessing.Process`

        """
        if self.process.run_mode == "threads":
            return Thread
        else:
            return multiprocessing.Process

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
        self.__sender = MiddlewareCommunicator.register(
            meta.data_type,
            meta.mware,
            meta.cls_name,
            meta.topic,
            carrier=meta.carrier,
            should_wait=meta.blocking,
            socket_sub_port=meta.socket_sub_port,
            socket_pub_port=meta.socket_pub_port,
            proxy_broker_spawn="thread",
            pubsub_monitor_listener_spawn="thread",
            **meta.params,
        )(self.__sender)
        self.activate_communication(self.__sender, mode=self.mode.sender)

    def __init_receivers(self, metas: List[ReceiverModel]):
        """
        Initializes a list of receiver functions based on the given receiver models.

        Args:
            metas (List[ReceiverModel]): A list of receiver models.

        Returns:
            List[Callable]: A list of receiver functions.

        Raises:
            None

        Example Usage:
            >>> __init_receivers([ReceiverModel1, ReceiverModel2])
            [<function __lambda_recevier_0 at 0x7f0e8c672160>, <function __lambda_recevier_1 at 0x7f0e8c672280>]
        """
        receivers = []
        default_func = self.__receiver_wrapper(
            f"__lambda_recevier_{0}", lambda x: (DEFAULT_NO_RECEVIER_MSG,)
        )
        for idx, meta in enumerate(metas):
            func = self.__receiver_wrapper(
                f"__lambda_recevier_{idx}", lambda x: (DEFAULT_NO_RECEVIER_MSG,)
            )
            receiver = MiddlewareCommunicator.register(
                meta.data_type,
                meta.mware,
                meta.cls_name,
                meta.topic,
                carrier=meta.carrier,
                should_wait=meta.blocking,
                payload_cls=meta.payload_cls,
                node_id=meta.node_id,
                socket_sub_port=meta.socket_sub_port,
                socket_pub_port=meta.socket_pub_port,
                proxy_broker_spawn="thread",
                pubsub_monitor_listener_spawn="thread",
                **meta.params,
            )(func)
            self.activate_communication(receiver, mode=self.mode.receiver)
            receivers.append(receiver)
        if not receivers:
            logger.warning(f"no receiver, use default receiver!!!")
            receivers.append(default_func)
        return receivers

    def __sender(self, *args, **kwargs):
        """
        Send data using the sender method and log the result.

        Args:
            payload (dict): A dictionary containing the payload data.
            context (dict): A dictionary containing the context data.

        Returns:
            Any: The data returned by the sender method.
        """
        try:
            st = time.perf_counter()
            payload: RawPayload = kwargs.pop("payload", {})
            context: Dict = kwargs.pop("context", {})
            sender_payload = self.sender(payload, context)
            # 不存在sender的情况，直接返回
            if self.meta.sender is None:
                # 记录节点处理耗时&数量
                cost_time = time.perf_counter() - st
                self.metrics.cost_process_frames(cost_time)
                self.metrics.count_process_frames()
                logger.info(f"{self.config.node_id} no sender, return immediately!")
                return sender_payload
            # 尝试根据返回的dict初始化为return_cls的类型
            if isinstance(sender_payload, dict):
                try:
                    sender_payload = self.meta.sender.return_cls(**sender_payload)
                except Exception as e:
                    logger.exception(
                        f"not init by return type: {self.meta.sender.return_cls.__name__}, error is {e}"
                    )
                    raise e

            # 首节点，类型必须为FirstPayload, 需要包含raw字段
            if payload.raw is None:
                if not isinstance(sender_payload, FirstPayload):
                    raise TypeError(
                        f"sender payload type error: {type(sender_payload)}, first payload is subclass of [ {FirstPayload.__name__} ]"
                    )
                # 记录原始值
                payload.raw = sender_payload.raw
            else:
                # ObjectsModel类型
                if isinstance(sender_payload, ObjectsPayload):
                    payload.objects = sender_payload
                # 结果记录到Meta中
                elif isinstance(sender_payload, self.meta.sender.return_cls):
                    payload.metas = payload.metas or {}
                    _node_id = f'node.{self.config.node_id}'
                    if _node_id in payload.metas:
                        raise ValueError(
                            f"node_id: {self.config.node_id} already exist in payload.metas"
                        )
                    payload.metas.update({_node_id: sender_payload})
                else:
                    raise TypeError(
                        f"sender payload type error: {type(sender_payload)}, should is [ {self.meta.sender.return_cls.__name__} !!!!"
                    )

                payload.node_id = "$".join([payload.node_id, self.config.node_id])

            # node整体耗时：从接收到处理
            payload.nodes_cost += time.perf_counter() - payload.timestamp
            # 更新发送时间
            payload.timestamp = time.perf_counter()
            # 记录节点处理耗时&数量
            cost_time = time.perf_counter() - st
            self.metrics.cost_process_frames(cost_time)
            self.metrics.count_process_frames()

            # 更新发送节点的node_id
            # 记录发送的时间
            crt_time = time.time()
            self.sender_times.append(crt_time)
            data = payload.model_dump()
            logger.debug(f"{payload.node_id} send data cost time: {cost_time} ")
            return (data,)
        except Exception as e:
            logger.exception(f"__sender func error: {e}")

    def __init(self):
        """
        Initializes the class.

        :return: The initialized context.
        """
        context = {}
        self.init(context)
        logger.info(f"{self.__class__.__name__} init context: {context}")
        return context

    def __receiver_wrapper(self, name: str, func: type):
        """
        A wrapper function that takes in a name and a function object and returns a new function that calls the input function with the given arguments.

        Parameters:
            name (str): The name of the new function.
            func (type): The function object to be wrapped.

        Returns:
            Function: A new function object that calls the input function with the given arguments.
        """

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__name__ = name
        wrapper.__qualname__ = name
        return wrapper

    def __run(self):
        """
        Runs the function indefinitely, continuously checking for payloads in the queue.

        Parameters:
            None

        Returns:
            None
        """
        context = self.__init()
        while True:
            if self._queue.empty():
                continue
            payload = self._queue.get()
            if payload is None:
                continue
            self.__sender(self, payload=payload, context=context)

    def __on_payload_callback(self, payload: RawPayload, context: Dict = {}):
        """
        Callback function for handling payloads.

        Args:
            payload (Dict): The payload to be processed.
            context (Dict, optional): The context for processing the payload. Defaults to {}.

        Returns:
            None
        """
        is_pass = self._record_and_just_is_pass_frame(recv_node_id=payload.node_id)
        if is_pass:
            logger.debug(f"{payload.node_id} frame is passed!")
            return

        # 处理对应的帧
        if self.process.enable_parallel:
            if not self._queue.full():
                self._queue.put_nowait(payload)
            else:
                logger.warning(
                    f"{self.__class__.__name__} queue is full! skip this topic: [ {payload} ] payload!"
                )
                self.metrics.count_drop_frames(action="full")
        else:
            self.__sender(self, payload=payload, context=context)
        # display fps
        self.logger_fps()

    def logger_fps(self):
        logger.info(
            f"{self.__class__.__name__} receiver fps: {self.receiver_fps} sender fps: {self.sender_fps}"
        )

    def __on_receiver_callback(self, receiver) -> RawPayload:
        """
        Executes the receiver callback function and returns the result.

        :param receiver: The receiver callback function.
        :type receiver: Callable[[Any], Tuple[Optional[Any], ...]]

        :return: A dictionary containing the topic and the payload.
        :rtype: Dict[str, Any]
        """
        _payload = receiver(self)
        if _payload[0] is None:
            return None
        payload = _payload[0]

        if payload == DEFAULT_NO_RECEVIER_MSG:
            raw_payload = RawPayload(node_id=self.config.node_id)
        else:
            receiver_wrapper_func = self._MiddlewareCommunicator__registry.get(
                receiver.__qualname__
            )
            communicator = receiver_wrapper_func["communicator"][0]
            receiver_func_kwargs = communicator["return_func_kwargs"]
            payload_cls: RawPayload = receiver_func_kwargs["payload_cls"]
            raw_payload = payload_cls(**payload)
        # 从上一个节点发送到该节点接受耗时
        self.metrics.cost_pendding_frames(time.perf_counter() - raw_payload.timestamp)
        return raw_payload

    def __run_background_senders(self):
        """
        Runs background senders.

        This function starts the background processing program for each index in the range of the count of processes. It creates a new process for each index using the _process_cls class and starts the process by calling the __run method. The name of each process is set as 'coral_{self.process.run_mode}_{idx}'.

        Parameters:
            None

        Returns:
            None
        """
        # 启动后台处理程序
        for idx in range(self.process.count):
            self._process_cls(
                target=self.__run, name=f"coral_{self.process.run_mode}_{idx}"
            ).start()

    def _record_and_just_is_pass_frame(self, recv_node_id):
        """
        A function that records whether a frame is skipped or not and updates the receiver frame count.

        Parameters:
            recv_node_id (int): The ID of the receiver node.

        Returns:
            bool: True if the frame is skipped, False otherwise.
        """
        is_pass = False
        # 记录此帧是否被skip
        if self.skip_frame_count != 0:
            recv_frame_count = self.receiver_frames_count[recv_node_id]
            # 不等于被skip的frame count，则pass掉对应的帧
            if recv_frame_count != self.skip_frame_count:
                is_pass = True
                self.receiver_frames_count[recv_node_id] = recv_frame_count + 1
                self.metrics.count_drop_frames(action="pass")
            else:
                # 重置重新计算
                self.receiver_frames_count[recv_node_id] = 0

        # 记录真实处理的队列fps
        if not is_pass:
            crt_time = time.time()
            self.receiver_times.append(crt_time)
        return is_pass

    def on_solo_receivers(self):
        """
        Execute the on_solo_receivers function.
        This function iterates over a list of receivers and calls the __on_receiver_callback
        method for each receiver. If a payload is returned from the callback, the __on_payload_callback
        method is called with the payload and the context. This process continues indefinitely
        until the program is terminated.

        Parameters:
            self (object): The current instance of the class.

        Returns:
            None
        """
        context = self.__init()
        while True:
            for receiver in self.receivers:
                payload = self.__on_receiver_callback(receiver)
                if payload is None:
                    continue
                self.__on_payload_callback(payload, context)

    def on_process_receviers(self):
        """
        Runs the process for all receivers.

        This function runs the background senders and then enters an infinite loop.
        In each iteration of the loop, it iterates over all the receivers and
        calls the __on_receiver_callback method for each receiver. If the
        __on_receiver_callback method returns a non-None payload, it calls the
        __on_payload_callback method with that payload.

        Parameters:
        None

        Returns:
        None
        """
        self.__run_background_senders()
        while True:
            for receiver in self.receivers:
                try:
                    payload = self.__on_receiver_callback(receiver)
                    if payload is None:
                        continue
                    self.__on_payload_callback(payload)
                except Exception as e:
                    logger.exception(e)

    def init(self, context: Dict[str, Any]):
        """
        Initializes the object with the provided context.

        Parameters:
            context (Dict[str, Any]): A dictionary containing the context information.

        Raises:
            NotImplementedError: This method is not implemented and should be overridden in a subclass.
        """
        raise NotImplementedError

    def sender(self, payload: Dict[str, Any], context: Dict[str, Any]) -> RawPayload:
        """
        Send a payload to the recipient.

        Args:
            payload (Dict[str, Any]): The payload to be sent.
            context (Dict[str, Any]): The context in which the payload is sent.

        Returns:
            Tuple: A tuple containing the result of the send operation.

        Raises:
            NotImplementedError: If the send operation is not implemented.
        """
        raise NotImplementedError

    def run(self):
        """
        Run the function.

        This function is responsible for executing the logic of the program. It checks if the process is enabled for parallel execution and calls the appropriate function accordingly.

        Parameters:
            None

        Returns:
            None
        """
        if self.process.enable_parallel:
            self.on_process_receviers()
        else:
            self.on_solo_receivers()
