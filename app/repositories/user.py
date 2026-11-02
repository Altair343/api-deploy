from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)

        result = await self.session.scalar(statement)

        return result

    async def create(
        self,
        email: str,
        full_name: str,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
        )

        self.session.add(user)

        await self.session.flush()

        return user
