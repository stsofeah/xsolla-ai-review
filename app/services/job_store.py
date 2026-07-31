from app.models.review import ReviewRequest

jobs: dict[str, dict[str, object]] = {}

MAX_CONCURRENT = 4
processing_jobs = 0
waiting_jobs: list[str] = []

def create_job(job_id: str, request: ReviewRequest) -> dict[str, object]:
    job = {
        "jobId": job_id,
        "status": "queued",
        "findings": [],
        "usage": {},
        "diff": request.diff,
        "provider": request.options.provider,
        "maxFindings": request.options.maxFindings,
    }
    jobs[job_id] = job
    return job


def get_job(job_id: str) -> dict[str, object] | None:
    return jobs.get(job_id)


def update_job_status(job_id: str, status: str) -> dict[str, object] | None:
    job = jobs.get(job_id)
    if job is None:
        return None
    job["status"] = status
    return job


def update_job_result(
    job_id: str,
    findings: list[dict[str, object]],
    usage: dict[str, object],
) -> dict[str, object] | None:
    job = jobs.get(job_id)
    if job is None:
        return None
    job["status"] = "done"
    job["findings"] = findings
    job["usage"] = usage
    return job
