import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.security import require_bearer_token
from app.models.review import ReviewRequest, ReviewResponse
from app.services.job_store import create_job, get_job, update_job_result
from app.services.mock_provider import review_diff
from app.services.rate_limiter import allow_request

router = APIRouter()


@router.post(
    "/v1/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_bearer_token)],
)
def create_review(request: ReviewRequest) -> ReviewResponse:

    allowed, retry_after = allow_request()

    if not allowed:
        return JSONResponse(
            status_code=429,
            headers={
                "Retry-After": str(retry_after)
            },
            content={
                "error": {
                    "code": "rate_limited",
                    "message": "Too many requests"
                }
            },
        )

    job_id = str(uuid.uuid4())
    create_job(job_id, request)

    findings = review_diff(
        request.diff,
        request.options.maxFindings,
    )

    update_job_result(
        job_id,
        findings,
        {
            "inputBytes": len(request.diff.encode()),
            "chunks": findings.chunk_count,
            "cacheHit": False,
        },
    )

    return ReviewResponse(
        jobId=job_id,
        status="queued",
    )


@router.get(
    "/v1/reviews/{job_id}",
    dependencies=[Depends(require_bearer_token)],
)
def get_review(job_id: str):

    job = get_job(job_id)

    if job is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "not_found",
                    "message": "Job not found",
                }
            },
        )

    return {
        "jobId": job.get("jobId"),
        "status": job.get("status"),
        "findings": job.get("findings"),
        "usage": job.get("usage"),
    }