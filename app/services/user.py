from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserAlreadyExistsError
from app.models.user import User
from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)

    async def create_user(self, data: UserCreate) -> User:
        try:
            async with self.session.begin():
                existing = await self.repository.get_by_email(
                    str(data.email)
                )

                if existing is not None:
                    raise UserAlreadyExistsError(
                        "Email already registered 1"
                    )

                hashed_password = hash_password(data.password)

                user = await self.repository.create(
                    email=str(data.email),
                    full_name=data.full_name,
                    hashed_password=hashed_password,
                )

            await self.session.refresh(user)
            return user

        except IntegrityError as exc:
            original = exc.orig
            sqlstate = getattr(original, "sqlstate", None)
            diagnostic = getattr(original, "diag", None)
            constraint = getattr(
                diagnostic,
                "constraint_name",
                None,
            )

            if (
                sqlstate == "23505"
                and constraint == "uq_users_email"
            ):
                raise UserAlreadyExistsError(
                    "Email already registered 2"
                ) from exc
            raise

    async def get_user(self, user_id: int) -> User | None:
        return await self.repository.get_by_id(user_id)
