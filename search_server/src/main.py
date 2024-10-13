import os

import sentry_sdk
from config import lifespan
from fastapi import FastAPI
from routes.api_endpoints import router as main_router
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration


def before_send(event, hint):
    # 이벤트가 트랜잭션일 경우, 해당 트랜잭션의 요청 경로가 `/`이면 무시
    if "transaction" in event:
        request = event.get("request", {})
        if request.get("url", "").endswith("/"):
            return None  # 트랜잭션 무시
    return event


sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    integrations=[
        StarletteIntegration(
            transaction_style="endpoint",
            failed_request_status_codes={403, *range(500, 599)},
            http_methods_to_capture=("GET",),
        ),
        FastApiIntegration(
            transaction_style="endpoint",
            failed_request_status_codes={403, *range(500, 599)},
            http_methods_to_capture=("GET",),
        ),
    ],
    before_send=before_send,  # before_send 콜백 설정
)
app = FastAPI(lifespan=lifespan)

# 라우트 추가
app.include_router(main_router)
