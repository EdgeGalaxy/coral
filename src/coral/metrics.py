import os
import json
from typing import Union, Dict

import paho.mqtt.client as mqtt
from loguru import logger


COMMON_CONFIG_FP = os.environ.get("CORAL_COMMON_CONFIG_PATH", f"{os.environ['HOME']}/.coral/common-config.json")


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
        if not enable:
            return
        self.cfg = self.get_common_config()
        self.organization_id = self.cfg.get('organization_id', 'coral-user')
        self.gateway_id = self.cfg.get('gateway_id', 'coral-gateway')
        self.topic_prefix = self._topic_prefix()
        self.mqtt_client = init_mqtt(self.cfg.get('mqtt', {}))
    
    def get_common_config(self) -> Dict:
        with open(COMMON_CONFIG_FP, 'r') as f:
            return json.load(f)
    
    def _topic_prefix(self):
        prefix = f"/organization/{self.organization_id}/gateway/{self.gateway_id}/pipeline/{self.pipeline_id}/node/{self.node_id}"
        logger.info(f"node: {self.node_id} topic prefix: {prefix}")
        return prefix
    
    def publish(self, topic: str, topic_type: str, message: dict):
        mqtt_topic = f'{self.topic_prefix}/{topic}/{topic_type}'
        return self.mqtt_client.publish(mqtt_topic, json.dumps(message))

    def count_process_frames(self, value: int = 1):
        return self.system_set('process_frames_count', value)

    def count_full_drop_frames(self, value: int = 1):
        return self.system_set('drop_frames_count', value)

    def count_skip_drop_frames(self, value: int = 1):
        return self.system_set('skip_frames_count', value)

    def cost_process_frames(self, value: float):
        return self.system_set('process_frames_cost', round(value, 4))

    def cost_pendding_frames(self, value: float):
        return self.system_set('pendding_frames_cost', round(value, 4))

    def system_set(
        self,
        topic: str,
        value: Union[int, float],
    ):
        if not self.enable:
            return
        self.publish(topic, 'system', {"value": value})
    
    def business_set(
        self,
        topic: str,
        value: Union[int, float],
    ):
        if not self.enable:
            return
        self.publish(topic, 'business', {"value": value})
        

def init_mqtt(cfg: dict) -> mqtt.Client:
    # 获取必要的配置
    mqtt_broker = cfg.pop("broker")
    mqtt_port = cfg.pop("port")
    mqtt_username = cfg.pop("username", None)
    mqtt_password = cfg.pop("password", None)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="coral-node-mqtt")
    if mqtt_username and mqtt_password:
        client.username_pw_set(mqtt_username, mqtt_password)

    # MQTT连接回调函数
    def on_connect(*args, **kwargs):
        if kwargs.get('rc', -1) == 0:
            logger.info("Connected to MQTT Broker!")
        else:
            logger.error("Failed to connect, return code %d\n", kwargs.get('rc'))

    # MQTT断开连接回调函数
    def on_disconnect(*args, **kwargs):
        logger.error("Disconnected from MQTT Broker!!")

    # MQTT设置回调函数
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    # 连接MQTT服务器
    client.connect(host=mqtt_broker, port=mqtt_port, **cfg)
    return client