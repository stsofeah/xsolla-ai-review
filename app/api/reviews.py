import hashlib
import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import Header

from app.services.llm_provider import review_diff_llm
from app.core.security import require_bearer_token
from app.models.review import ReviewRequest, ReviewResponse
from app.services.job_store import (
    create_job,
    get_job,
    get_cache,
    save_cache,
    set_job_error,
    update_job_result,
    update_job_status,
    idempotency_store,
)
from app.services.mock_provider import review_diff
from app.services.rate_limiter import allow_request

router = APIRouter()

def _build_cache_key(request: ReviewRequest) -> str:
    payload = (
        request.diff
        + request.options.provider
        + str(request.options.maxFindings)
    )

    return hashlib.sha256(payload.encode()).hexdigest()

def _build_usage(request: ReviewRequest, findings: object) -> dict[str, object]:
    return {
        "inputBytes": len(request.diff.encode()),
        "chunks": getattr(findings, "chunk_count", 1),
        "cacheHit": False,
    }


async def _process_review(
    job_id: str,
    request: ReviewRequest,
    cache_key: str,
) -> None:

    update_job_status(job_id, "running")

    try:

        if request.options.provider == "mock":
            findings = review_diff(
                request.diff,
                request.options.maxFindings,
            )

        elif request.options.provider == "llm":
            findings = review_diff_llm(
                request.diff,
                request.options.maxFindings,
            )

        else:
            raise RuntimeError("Unknown provider")

        usage = _build_usage(request, findings)

        update_job_result(
            job_id,
            findings,
            usage,
        )

        save_cache(
            cache_key,
            findings,
            usage,
        )

    except Exception as exc:
        update_job_status(job_id, "failed")
        set_job_error(job_id, str(exc))


@router.post(
    "/v1/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_bearer_token)],
)
def create_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None),
) -> ReviewResponse:
    

    # Validate payload size (1 MiB)
    if len(request.diff.encode("utf-8")) > 1048576:
        return JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "payload_too_large",
                    "message": "Payload exceeds 1 MiB limit",
                }
            },
        )

    # Validate diff
    if not request.diff.strip():
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_diff",
                    "message": "Diff cannot be empty",
                }
            },
        )

    
    # Basic unified diff validation
    if "+++" not in request.diff or "@@" not in request.diff:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_diff",
                    "message": "Invalid unified diff",
                }
            },
        )

    allowed, retry_after = allow_request()

    if not allowed:
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(retry_after)},
            content={"error": {"code": "rate_limited", "message": "Too many requests"}},
        )
    if idempotency_key:

        body_signature = {
            "diff": request.diff,
            "provider": request.options.provider,
            "maxFindings": request.options.maxFindings,
        }

        existing = idempotency_store.get(idempotency_key)

        print("==========")
        print("STORE:", idempotency_store)
        print("KEY:", idempotency_key)
        print("EXISTING:", existing)
        print("==========")

        if existing:

            if existing["body"] != body_signature:
                return JSONResponse(
                    status_code=409,
                    content={
                        "error": {
                            "code": "idempotency_conflict",
                            "message": "Idempotency key already used with different request",
                        }
                    },
                )

            return ReviewResponse(
                jobId=existing["jobId"],
                status=get_job(existing["jobId"])["status"],
            )
    
    # Check cache
    cache_key = _build_cache_key(request)

    cached = get_cache(cache_key)

    if cached:
        job_id = str(uuid.uuid4())
        create_job(job_id, request)

        update_job_result(
            job_id,
            cached["findings"],
            {
                **cached["usage"],
                "cacheHit": True,
            },
        )

        return ReviewResponse(
            jobId=job_id,
            status="done",
        )
    
    job_id = str(uuid.uuid4())
    create_job(job_id, request)

    if idempotency_key:
        idempotency_store[idempotency_key] = {
            "jobId": job_id,
            "body": {
                "diff": request.diff,
                "provider": request.options.provider,
                "maxFindings": request.options.maxFindings,
            },
        }

    background_tasks.add_task(
        _process_review,
        job_id,
        request,
        cache_key,
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
        "error": job.get("error"),
    }


@router.get(
    "/v1/reviews/{job_id}/stream",
    dependencies=[Depends(require_bearer_token)],
)
def stream_review(job_id: str):

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

    def event_generator():

        # Replay status
        yield (
            "event: status\n"
            f"data: {json.dumps({'status': job['status']})}\n\n"
        )

        # Replay every finding
        for finding in job["findings"]:
            yield (
                "event: finding\n"
                f"data: {json.dumps(finding)}\n\n"
            )

        # Done event
        yield (
            "event: done\n"
            f"data: {json.dumps({'total': len(job['findings']), 'usage': job['usage']})}\n\n"
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )