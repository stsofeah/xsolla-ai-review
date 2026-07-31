from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.reviews import router as reviews_router
from app.api.spec import router as spec_router

app = FastAPI()
app.include_router(health_router)
app.include_router(spec_router)
app.include_router(reviews_router)
