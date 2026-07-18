from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.password_reset_code import PasswordResetCode
from app.domain.ports.output.password_reset_code_repository_port import (
    PasswordResetCodeRepositoryPort,
)
from app.infrastructure.database.models import PasswordResetCodeModel


class PasswordResetCodeRepository(PasswordResetCodeRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, reset_code: PasswordResetCode) -> PasswordResetCode:
        model = self._to_model(reset_code)
        self._session.add(model)
        await self._session.commit()
        return reset_code

    async def update(self, reset_code: PasswordResetCode) -> PasswordResetCode:
        query = (
            update(PasswordResetCodeModel)
            .where(PasswordResetCodeModel.uuid == reset_code.uuid)
            .values(
                attempts_used=reset_code.attempts_used,
                consumed_at=reset_code.consumed_at,
            )
        )
        await self._session.execute(query)
        await self._session.commit()
        return reset_code

    async def find_latest_by_user(self, user_uuid: UUID) -> PasswordResetCode | None:
        query = (
            select(PasswordResetCodeModel)
            .where(PasswordResetCodeModel.user_uuid == user_uuid)
            .order_by(PasswordResetCodeModel.created_at.desc())
            .limit(1)
        )
        data = await self._session.execute(query)
        model = data.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists_active_code(self, code: str) -> bool:
        now = datetime.now(UTC)
        query = select(PasswordResetCodeModel).where(
            PasswordResetCodeModel.code == code,
            PasswordResetCodeModel.expires_at > now,
            PasswordResetCodeModel.consumed_at.is_(None),
        )
        data = await self._session.execute(query)
        return data.scalar_one_or_none() is not None

    def _to_model(self, reset_code: PasswordResetCode) -> PasswordResetCodeModel:
        return PasswordResetCodeModel(
            uuid=reset_code.uuid,
            user_uuid=reset_code.user_uuid,
            code=reset_code.code,
            attempts_used=reset_code.attempts_used,
            consumed_at=reset_code.consumed_at,
            created_at=reset_code.created_at,
            expires_at=reset_code.expires_at,
        )

    def _to_entity(self, model: PasswordResetCodeModel) -> PasswordResetCode:
        return PasswordResetCode(
            uuid=model.uuid,
            user_uuid=model.user_uuid,
            code=model.code,
            attempts_used=model.attempts_used,
            consumed_at=model.consumed_at,
            created_at=model.created_at,
            expires_at=model.expires_at,
        )
