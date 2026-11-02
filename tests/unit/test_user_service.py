
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import UserAlreadyExistsError
from app.schemas.user import UserCreate
from app.services.user import UserService


@pytest.mark.asyncio
async def test_create_user_with_duplicate_email():
    session = MagicMock()
    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock()
    transaction.__aexit__ = AsyncMock(return_value=False)
    session.begin.return_value = transaction

    service = UserService(session)

    service.repository.get_by_email = AsyncMock(
        return_value=object()
    )

    service.repository.create = AsyncMock()

    data = UserCreate(
        email="test@example.com",
        full_name="Test User",
    )

    with pytest.raises(UserAlreadyExistsError):
        await service.create_user(data)

    service.repository.create.assert_not_awaited()