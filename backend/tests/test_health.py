import asyncio

import httpx

from backend.app.main import app


def test_health_reports_database_readiness() -> None:
    async def request() -> httpx.Response:
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.get("/api/health")

    response = asyncio.run(request())

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ready"
