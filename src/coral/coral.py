import os
import queue
import multiprocessing
from typing import Dict, List, Union, Any, Tuple
from loguru import logger
from threading import Thread

from wrapyfi.connect.listeners import Listener
from wrapyfi.connect.clients import Client
from wrapyfi.connect.wrapper import MiddlewareCommunicator

from .messages.sync import TimeSyncMessagesFilter
from .constants import DEFAULT_NO_RECEVIER_MSG, DEFAULT_NO_TOPIC
from .parse import CoralParser
from .parser._base import RECEIVER_CLUSTER_MODE
from .parser import (
    BaseParse,
    MetaModel,
    ParamsModel,
    SenderModel,
    ReceiverModel,
    ModeModel,
    ProcessModel,
)


class CoralNode(MiddlewareCommunicator):
    node_name = None
    config_path = "config.xml"

    def __init__(self):
        self.__config = CoralParser.parse(self.config_path)
        self._queue = self.__queue()
        self._process_cls = self.__process_cls()
        self.receivers = self.__init_receivers(self.meta.receivers)
        self.__init_senders(self.meta.senders)
        self.sync_message_filter = TimeSyncMessagesFilter(
            self.receivers,
            receiver_func=self.__on_receiver_callback,
            callback_func=self.__on_payload_callback,
            timeout=self.meta.receiver_timeout
        )

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
    def init_params(self):
        return self.params.init

    @property
    def run_params(self):
        return self.params.run
    
    def __queue(self):
        if self.process.run_mode == 'threads':
            return queue.Queue(maxsize=self.process.max_qsize)
        else:
            return multiprocessing.Queue(maxsize=self.process.max_qsize)
    
    def __process_cls(self):
        if self.process.run_mode == 'threads':
            return Thread
        else:
            return multiprocessing.Process

    def __init_senders(self, metas: List[SenderModel]):
        for meta in metas:
            self.__sender = MiddlewareCommunicator.register(
                meta.data_type,
                meta.mware,
                meta.cls_name,
                meta.topic,
                carrier=meta.carries,
                should_wait=meta.blocking,
                proxy_broker_spawn='thread',
                pubsub_monitor_listener_spawn='thread',
                **meta.params,
            )(self.__sender)
        self.activate_communication(self.__sender, mode=self.mode.sender)

    def __init_receivers(self, metas: List[ReceiverModel]):
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
                carrier=meta.carries,
                should_wait=meta.blocking,
                proxy_broker_spawn='thread',
                pubsub_monitor_listener_spawn='thread',
                **meta.params,
            )(func)
            self.activate_communication(receiver, mode=self.mode.receiver)
            receivers.append(receiver)
        if not receivers:
            logger.warning(f'no receiver, use default receiver!!!')
            receivers.append(default_func)
        return receivers

    def __sender(self, *args, **kwargs):
        payload = kwargs.pop("payload", {})
        context = kwargs.pop("context", {})
        data = self.sender(payload, context)
        logger.debug(f'{self.__class__.__name__} send data: {data}')
        return data

    def __init(self):
        context = {}
        self.init(context)
        logger.info(f"{self.__class__.__name__} init context: {context}")
        return context

    def __receiver_wrapper(self, name: str, func: type):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__name__ = name
        wrapper.__qualname__ = name
        return wrapper

    def __run(self):
        context = self.__init()
        while True:
            if self._queue.empty():
                continue
            payload = self._queue.get()
            if payload is None:
                continue
            self.__sender(self, payload=payload, context=context)

    def __on_payload_callback(self, payload: Dict, context: Dict = {}):
        if self.process.enable_parallel:
            if not self._queue.full():
                self._queue.put_nowait(payload)
            else:
                logger.warning(
                    f"{self.__class__.__name__} queue is full! skip this topic: [ {payload} ] payload!"
                )
        else:
            self.__sender(self, payload=payload, context=context)

    def __on_receiver_callback(self, receiver):
        _payload = receiver(self)
        if _payload[0] is None:
            return None
        receiver_wrapper_func = self._MiddlewareCommunicator__registry.get(
            receiver.__qualname__
        )
        if not receiver_wrapper_func:
            topic = DEFAULT_NO_TOPIC
        else:
            receiver_func: Union[Listener, Client] = receiver_wrapper_func[
                "communicator"
            ][0]["wrapped_executor"]
            topic = receiver_func.in_topic
        return {topic: _payload[0]}

    def __run_background_senders(self):
        # 启动后台处理程序
        for idx in range(self.process.count):
            self._process_cls(target=self.__run, name=f'coral_{self.process.run_mode}_{idx}').start()

    def on_solo_receivers(self):
        context = self.__init()
        while True:
            for receiver in self.receivers:
                payload = self.__on_receiver_callback(receiver)
                if payload is None:
                    continue
                self.__on_payload_callback(payload, context)
    
    def on_process_receviers(self):
        self.__run_background_senders()
        while True:
            for receiver in self.receivers:
                payload = self.__on_receiver_callback(receiver)
                if payload is None:
                    continue
                self.__on_payload_callback(payload)

    def init(self, context: Dict[str, Any]):
        raise NotImplementedError

    def sender(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple:
        raise NotImplementedError

    def run(self):
        if self.process.enable_parallel:
            self.on_process_receviers()
        else:
            self.on_solo_receivers()
