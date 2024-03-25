class CoralException(Exception):
    pass


class CoralSenderException(CoralException):
    "coral 发送数据出错异常"
    pass


class CoralSenderIgnoreException(CoralSenderException):
    "coral 发送数据忽略的一场"
    pass
