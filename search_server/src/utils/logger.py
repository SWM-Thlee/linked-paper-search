import logging
import os
from functools import wraps

# 환경 변수를 가져옴, 기본값은 "dev"
environment = os.getenv("ENVIRONMENT", "dev")

# 로거 생성
logger = logging.getLogger("uvicorn.info")
haystack_logger = logging.getLogger("haystack")


# 환경에 따라 uvicorn.info 로거의 로깅 레벨 설정
if environment == "dev":
    logger.setLevel(logging.DEBUG)  # 개발 환경에서는 디버깅 로깅
    haystack_logger.setLevel(logging.DEBUG)  # haystack도 디버그 레벨로 설정

elif environment == "prod":
    logger.setLevel(logging.WARNING)  # 프로덕션에서는 경고 이상만 로깅
    haystack_logger.setLevel(logging.WARNING)  # haystack도 경고 레벨로 설정

else:
    logger.setLevel(logging.INFO)  # 기본값으로 INFO 설정
    haystack_logger.setLevel(logging.INFO)  # haystack도 INFO 레벨로 설정


def log_on_init():
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
