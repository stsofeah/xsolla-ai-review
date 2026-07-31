from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_review():
    response = client.post(
        "/v1/reviews",
        json={
            "diff": "+++ b/test.js\n@@ -1,0 +1 @@\n+eval(userInput)"
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert "jobId" in data
    assert data["status"] == "queued"


def test_get_review():
    create_response = client.post(
        "/v1/reviews",
        json={
            "diff": "+++ b/test.js\n@@ -1,0 +1 @@\n+eval(userInput)"
        },
    )

    job_id = create_response.json()["jobId"]

    response = client.get(f"/v1/reviews/{job_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "done"
    assert len(data["findings"]) == 1
    assert data["findings"][0]["ruleId"] == "MOCK-001"


def test_get_review_not_found():
    response = client.get("/v1/reviews/not-found")

    assert response.status_code == 404

    data = response.json()

    assert data["error"]["code"] == "not_found"