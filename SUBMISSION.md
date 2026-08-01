# SUBMISSION

## Candidate

**Name:** Siti Sofeah binti Suharzelim

---

# Architecture

This project is implemented as a FastAPI REST service.

The application is organized into separate modules:

- `api/` – API endpoints
- `models/` – Pydantic request and response models
- `services/` – business logic including the mock provider, job storage, caching, and rate limiting
- `core/` – authentication and security
- `tests/` – automated unit and API tests

Review requests are submitted through `POST /v1/reviews`.

Each request creates an asynchronous background job. The job is stored in memory, processed by the selected provider, and later retrieved through the polling endpoint or replayed through the SSE endpoint.

---

# Provider Design

The review pipeline supports two providers behind the same interface.

## Mock Provider

The mock provider performs deterministic rule-based analysis of unified diffs.

It detects:

- eval()
- hardcoded secrets
- SQL string concatenation
- swallowed exceptions
- loose null comparison
- JSON deep clone
- console.log()
- TODO/FIXME markers
- prompt injection patterns

The mock provider is deterministic and is used for the assessment scoring.

---

## LLM Provider

The service exposes an `llm` provider path.

If an LLM provider is not configured, the job fails gracefully instead of crashing.

Example response:

```json
{
  "status": "failed",
  "error": "LLM provider is not configured."
}
```

This demonstrates graceful degradation while keeping the API available.

---

# Verification of Cross-Cutting Behaviors

The following behaviors were manually verified using Swagger UI and automated tests where applicable.

## Authentication

Verified that all `/v1/*` endpoints require a valid Bearer token.

Invalid or missing tokens correctly return HTTP 401.

---

## Idempotency

Verified that:

- identical request body with the same `Idempotency-Key` returns the same `jobId`
- different request body with the same key returns HTTP 409

---

## Response Caching

Verified that submitting an identical request returns:

```json
"cacheHit": true
```

without reprocessing the review.

---

## Server-Sent Events (SSE)

Verified that:

- status events are emitted
- finding events are replayed
- completed jobs replay the full event stream correctly

---

## Rate Limiting

Verified that:

- the first 30 POST requests within one minute succeed
- subsequent requests return HTTP 429
- the `Retry-After` header is included

---

## Chunking

The mock provider reports chunk usage through the response usage object.

Chunk counting behavior was verified using automated tests.

---

# Testing

Automated tests were implemented using Pytest.

The test suite covers:

- mock provider rules
- API endpoints
- chunk counting
- rate limiting

Current result:

```
12 passed
```

---

# AI Tools Used

- ChatGPT
  - Architecture planning
  - Debugging
  - API design discussions
  - Test development
  - Documentation

- Cursor AI
  - Code review
  - Code generation
  - Refactoring suggestions
  - Implementation verification

- GitHub
  - Version control

- Render
  - Application deployment

---

# AI Suggestion Rejected

One AI-generated suggestion was to simplify the implementation by removing the asynchronous processing flow and handling reviews synchronously.

I rejected this suggestion because the assessment explicitly requires asynchronous job processing. Keeping the background task implementation better matches the required API contract and job lifecycle.

---

# Future Improvements

Given additional development time, the following improvements would be implemented:

- integrate a real LLM provider using environment-based API credentials
- persistent database storage instead of in-memory storage
- Redis-backed caching
- asynchronous task queue (Celery or similar)
- improved concurrent job scheduling
- expanded automated integration tests
- container orchestration for production deployment

---

# Repository

The repository contains:

- complete FastAPI implementation
- Docker support
- automated tests
- README documentation
- this submission document

The project is deployable using Docker or a standard Python environment.