
from unittest.mock import AsyncMock

import pytest

from app.api.dependencies import get_login_rate_limiter
from app.core.rate_limit import RateLimitExceeded
from app.main import app


@pytest.mark.asyncio
async def test_login_rate_limit_returns_429(client):
    limiter = AsyncMock()
    limiter.check_login.side_effect = RateLimitExceeded(
        retry_after=60
    )

    app.dependency_overrides[get_login_rate_limiter] = (
        lambda: limiter
    )

    try:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePassword123!",
            },
        )

        assert response.status_code == 429
        assert response.headers["retry-after"] == "60"

        limiter.check_login.assert_awaited_once()

    finally:
        app.dependency_overrides.pop(
            get_login_rate_limiter,
            None,
        )
