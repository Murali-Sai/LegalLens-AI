import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "collections" in data
    assert "mock_mode" in data


@pytest.mark.asyncio
async def test_upload_rejects_invalid_extension(client):
    response = await client.post(
        "/api/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF and DOCX" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_missing_file(client):
    response = await client.post("/api/upload")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_analysis_not_found(client):
    response = await client.get("/api/analysis/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_analyses_empty(client):
    response = await client.get("/api/analyses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_stats_empty(client):
    response = await client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_analyses"] >= 0
    assert "high_risk_total" in data


@pytest.mark.asyncio
async def test_evaluate_requires_complete_metric_group(client):
    response = await client.post(
        "/api/evaluate",
        json={"precision": 0.9},  # Missing recall and f1
    )
    assert response.status_code == 400
    assert "No complete metric groups" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evaluate_clause_detection(client):
    response = await client.post(
        "/api/evaluate",
        json={"precision": 0.88, "recall": 0.85, "f1": 0.86},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "precision" in data["metrics_logged"]
