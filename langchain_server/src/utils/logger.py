import logging
from functools import wraps


def log_on_init(logger_name):
    logger = logging.getLogger(logger_name)

    def decorator(cls):
        # 클래스의 원래 __init__ 메소드를 감싸는 래퍼 함수
        original_init = cls.__init__

        @wraps(original_init)
        def wrapped_init(self, *args, **kwargs):
            memory_address = hex(id(self))
            logger.info(
                f"Creating instance of {cls.__name__} at {memory_address} with args={args}, kwargs={kwargs}"
            )
            original_init(self, *args, **kwargs)  # 원래의 __init__ 호출

        cls.__init__ = wrapped_init
        return cls

    return decorator
