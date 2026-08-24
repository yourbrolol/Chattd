import pytest
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.testclient import TestClient

from app.core.router import APIRouter, limiter


@pytest.fixture(autouse=True)
def _reset_limiter_storage():
    """Start each test with a clean in-memory rate limit window."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def rate_limited_app():
    """Fresh FastAPI app wired like app.main."""
    router = APIRouter()

    @router.get("/ping")
    async def ping():
        return {"message": "pong"}

    test_app = FastAPI()
    test_app.state.limiter = limiter
    test_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    test_app.add_middleware(SlowAPIMiddleware)
    test_app.include_router(router)
    return test_app


def test_rate_limit_returns_429_after_20_requests(rate_limited_app):
    """The 20 req/s default limit allows 20 requests, then returns 429."""
    with TestClient(rate_limited_app) as client:
        # First 20 requests pass
        for _ in range(20):
            r = client.get("/ping")
            assert r.status_code == 200

        # 21st request is rate limited
        r = client.get("/ping")
        assert r.status_code == 429
        assert "rate limit exceeded" in r.text.lower()
