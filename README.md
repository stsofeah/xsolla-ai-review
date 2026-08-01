# AI Diff Review Service

A lightweight AI-powered code review service built with FastAPI for the **Xsolla AI-First Engineering Internship Technical Assessment**.

The service accepts a unified Git diff, performs asynchronous AI-style code review using a deterministic mock provider, and returns structured review findings through a REST API.

---

# Features

- Review unified Git diffs
- Asynchronous review processing
- Rule-based mock code review provider
- Security, correctness, performance and style findings
- Prompt injection detection
- Path and line number tracking
- Chunk counting
- In-memory job storage
- Response caching
- Idempotency support
- Server-Sent Events (SSE) streaming
- Rate limiting (30 requests per minute)
- Swagger API documentation
- Unit tests using pytest
- Docker support

---

# Tech Stack

- Python 3.14
- FastAPI
- Pydantic
- Uvicorn
- Pytest
- HTTPX
- Docker
- Git

---

# Project Structure

```text
app/
├── api/
│   └── reviews.py
├── core/
│   └── security.py
├── models/
│   └── review.py
├── services/
│   ├── job_store.py
│   ├── mock_provider.py
│   └── rate_limiter.py
└── main.py

tests/
├── test_mock_provider.py
└── test_reviews_api.py

Dockerfile
README.md
requirements.txt
```

---

# Installation

Clone the repository.

```bash
git clone https://github.com/stsofeah/xsolla-ai-review.git
cd xsolla-ai-review
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate the virtual environment.

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

---

# Run the Application

```bash
uvicorn app.main:app --reload
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Authentication

All protected endpoints require a Bearer token.

Example:

```http
Authorization: Bearer sofeah-xsolla-2026-review
```

The API token is configured using the environment variable:

```text
API_TOKEN
```

Example (PowerShell):

```powershell
$env:API_TOKEN="sofeah-xsolla-2026-review"
```

---

# Run with Docker

Build the Docker image.

```bash
docker build -t xsolla-ai-review .
```

Run the container.

```bash
docker run -p 8000:8000 -e API_TOKEN=sofeah-xsolla-2026-review xsolla-ai-review
```

---

# Run Tests

```bash
python -m pytest
```

Current automated tests cover:

- Mock provider rules
- Review API endpoints
- Authentication
- Job retrieval
- Path tracking
- Line tracking
- Chunk counting

---

# API Endpoints

## Create Review

```http
POST /v1/reviews
```

Returns:

```http
202 Accepted
```

Example response:

```json
{
  "jobId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "queued"
}
```

---

## Get Review

```http
GET /v1/reviews/{jobId}
```

Returns:

```http
200 OK
```

or

```http
404 Not Found
```

Example response:

```json
{
  "jobId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "done",
  "findings": [],
  "usage": {
    "inputBytes": 120,
    "chunks": 1,
    "cacheHit": false
  }
}
```

---

## Stream Review Progress (SSE)

```http
GET /v1/reviews/{jobId}/stream
```

Returns a **Server-Sent Events (SSE)** stream containing review progress and the final review result.

---

# Mock Detection Rules

| Rule ID | Description |
|----------|-------------|
| MOCK-001 | Detects use of `eval()` |
| MOCK-002 | Detects hardcoded API keys or secrets |
| MOCK-003 | Detects SQL string concatenation |
| MOCK-004 | Detects swallowed exceptions |
| MOCK-005 | Detects loose null comparison |
| MOCK-006 | Detects JSON deep clone pattern |
| MOCK-007 | Detects leftover `console.log()` statements |
| MOCK-008 | Detects unresolved `TODO` / `FIXME` comments |
| MOCK-INJ | Detects prompt injection attempts |

---

# Project Status

Implemented features:

- ✅ REST API with FastAPI
- ✅ Asynchronous review processing
- ✅ In-memory job storage
- ✅ Mock review provider
- ✅ Multiple detection rules
- ✅ Path tracking
- ✅ Line number tracking
- ✅ Chunk counting
- ✅ Response caching
- ✅ Idempotency support
- ✅ Server-Sent Events (SSE)
- ✅ Rate limiting
- ✅ Swagger API documentation
- ✅ Unit tests
- ✅ API endpoint tests
- ✅ Docker support

---

# Notes

This project was developed as part of the **Xsolla AI-First Engineering Internship Technical Assessment**.

The service was implemented using the deterministic mock provider specified in the assessment and includes support for response caching, idempotency, asynchronous processing, Server-Sent Events (SSE), and rate limiting.