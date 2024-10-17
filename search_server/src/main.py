import os

import sentry_sdk
from config import lifespan
from fastapi import FastAPI
from routes.api_endpoints import router as main_router
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration


def traces_sampler(sampling_context):
    # Extract the ASGI scope and then the path from it
    asgi_scope = sampling_context.get("asgi_scope", {})
    path = asgi_scope.get("path", "")  # Extracting the 'path'

    # Ignore root URL ("/")
    if path == "/":
        return 0  # Drop transaction for the root path
    return 1.0  # Default sample rate for other paths


if os.getenv("ENVIRONMENT", "dev") == "prod":
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
        traces_sampler=traces_sampler,
    )
app = FastAPI(lifespan=lifespan)

# 라우트 추가
app.include_router(main_router)
