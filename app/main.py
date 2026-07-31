from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.reviews import router as reviews_router
from app.api.spec import router as spec_router

app = FastAPI()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "internal",
                "message": str(exc.detail),
            }
        },
    )


app.include_router(health_router)
app.include_router(spec_router)
app.include_router(reviews_router)