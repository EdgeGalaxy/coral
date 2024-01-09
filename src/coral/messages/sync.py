


class TimeSyncMessagesFilter:
    def __init__(self, receivers, receiver_func, callback_func, timeout=0.5) -> None:
        self.receivers = receivers
        self.receiver_func = receiver_func
        self.callback_func = callback_func

    def start(self):
        while True:
            for receiver in self.receivers:
                payload = self.receiver_func(receiver)
                if payload is None:
                    continue
                # TODO: 此处后续做多个receivers的消息在一段时间内同步的逻辑
                self.callback_func(payload)


