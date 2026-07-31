from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str | int]:
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptimeSeconds": 0,
    }
