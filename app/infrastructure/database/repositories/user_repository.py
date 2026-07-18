from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import UserAlreadyExistsError
from app.domain.ports.output.user_repository_port import UserRepositoryPort
from app.infrastructure.database.models import UserModel


class UserRepository(UserRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> User:
        model = self._to_model(user)
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise UserAlreadyExistsError(
                'A user already exist with unique fields.'
            ) from error
        return user

    async def find_by_username(self, username: str) -> User | None:
        query = select(UserModel).where(UserModel.username == username)
        data = await self._session.execute(query)
        model = data.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_cellphone(self, cellphone: str) -> User | None:
        query = select(UserModel).where(UserModel.cellphone == cellphone)
        data = await self._session.execute(query)
        model = data.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update_password(self, user_uuid: UUID, hashed_password: str) -> None:
        query = (
            update(UserModel)
            .where(UserModel.uuid == user_uuid)
            .values(password=hashed_password, updated_at=datetime.now(UTC))
        )
        await self._session.execute(query)
        await self._session.commit()

    async def exists_by_username(self, username: str) -> bool:
        query = select(UserModel).where(UserModel.username == username)
        data = await self._session.execute(query)
        return data.scalar_one_or_none() is not None

    async def exists_by_cellphone(self, cellphone: str) -> bool:
        query = select(UserModel).where(UserModel.cellphone == cellphone)
        data = await self._session.execute(query)
        return data.scalar_one_or_none() is not None

    async def exists_by_email(self, email: str) -> bool:
        query = select(UserModel).where(UserModel.email == email)
        data = await self._session.execute(query)
        return data.scalar_one_or_none() is not None

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            uuid=user.uuid,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            password=user.password,
            facebook_token=user.facebook_token,
            gmail_token=user.gmail_token,
            cellphone=user.cellphone,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _to_entity(self, model: UserModel) -> User:
        # __post_init__ validates password against the plain-text pattern, which a
        # stored hash never matches, so it's assigned after construction — the same
        # bypass RegisterUserUseCase uses when it hashes the password post-init.
        user = User(
            first_name=model.first_name,
            last_name=model.last_name,
            cellphone=model.cellphone,
            username=model.username,
            password='placeholder' if model.password else None,
            email=model.email,
            facebook_token=model.facebook_token,
            gmail_token=model.gmail_token,
            created_at=model.created_at,
            updated_at=model.updated_at,
            uuid=model.uuid,
        )
        user.password = model.password
        return user
