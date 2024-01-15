import uuid
import time
import queue
import multiprocessing
from typing import Dict, List, Any
from loguru import logger
from threading import Thread
from collections import deque

from wrapyfi.connect.wrapper import MiddlewareCommunicator

from .constants import DEFAULT_NO_RECEVIER_MSG
from .parse import CoralParser
from .parser import BaseParse
from .types import (
    MetaModel,
    ParamsModel,
    SenderModel,
    ReceiverModel,
    ModeModel,
    ProcessModel,
    RawPayload,
    FirstPayload,
)


class CoralNode(MiddlewareCommunicator):
    node_name = None
    config_path = "config.xml"

    def __init__(self):
        self.__config = CoralParser.parse(self.config_path)
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
        self.config_schema = self.config.parse_json_schema()

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
                proxy_broker_spawn="thread",
                pubsub_monitor_listener_spawn="thread",
                payload_cls=meta.payload_cls,
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
            payload: RawPayload = kwargs.pop("payload", {})
            context: Dict = kwargs.pop("context", {})
            sender_payload = self.sender(payload, context)
            # 尝试根据返回的dict初始化为return_cls的类型
            if isinstance(sender_payload, dict):
                try:
                    sender_payload = self.meta.sender.return_cls(**sender_payload)
                except Exception as e:
                    logger.exception(f'not init by return type: {self.meta.sender.return_cls.__name__}, error is {e}')
                    raise e

            # 首节点，类型必须为FirstPayload, 需要包含raw字段
            if payload.raw is None: 
                if not isinstance(sender_payload, FirstPayload):
                    raise TypeError(f"sender payload type error: {type(sender_payload)}, first payload is subclass of [ {FirstPayload.__name__} ]")
                # 记录原始值
                payload.raw = sender_payload.raw
            else:
                # TODO: 判断是不是objectsModel类型
                if isinstance(sender_payload, list):
                    raise TypeError(f"not support list return, {sender_payload}!!")
                elif isinstance(sender_payload, self.meta.sender.return_cls):
                    payload.metas.append({f'node.{self.config.node_id}': sender_payload})
                else:
                    raise TypeError(f"sender payload type error: {type(sender_payload)}, should is [ {self.meta.sender.return_cls.__name__} !!!!")

                payload.node_id = '$'.join([payload.node_id, self.config.node_id])
                
            # 更新发送节点的node_id
            # 记录发送的时间
            crt_time = time.time()
            self.sender_times.append(crt_time)
            logger.debug(f"{self.__class__.__name__} send data")
            data = payload.model_dump()
            return data,
        except Exception as e:
            logger.exception(f'__sender func error: {e}')

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
        # 记录接收数据的时间
        crt_time = time.time()
        self.receiver_times.append(crt_time)
        if self.process.enable_parallel:
            if not self._queue.full():
                self._queue.put_nowait(payload)
            else:
                logger.warning(
                    f"{self.__class__.__name__} queue is full! skip this topic: [ {payload} ] payload!"
                )
        else:
            self.__sender(self, payload=payload, context=context)
        # display fps 
        self.logger_fps()
    
    def logger_fps(self):
        logger.info(f"{self.__class__.__name__} receiver fps: {self.receiver_fps} sender fps: {self.sender_fps}")

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
            return RawPayload(node_id=self.config.node_id)
        else:
            receiver_wrapper_func = self._MiddlewareCommunicator__registry.get(receiver.__qualname__)
            communicator = receiver_wrapper_func["communicator"][0]
            receiver_func_kwargs = communicator["return_func_kwargs"]
            payload_cls: RawPayload = receiver_func_kwargs['payload_cls']
            return payload_cls(**payload)

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
