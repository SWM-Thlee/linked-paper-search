from fastapi import FastAPI
from routes.api_endpoints import router as main_router

from config import lifespan

app = FastAPI(lifespan=lifespan)

# 라우트 추가
app.include_router(main_router)
