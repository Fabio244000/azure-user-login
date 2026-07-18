from datetime import UTC, datetime
from uuid import UUID

from app.domain.constants import (
    PASSWORD_PATTERN,
    PASSWORD_RESET_MAX_VERIFICATION_ATTEMPTS,
)
from app.domain.entities.password_reset_code import PasswordResetCode
from app.domain.exceptions import (
    InvalidPasswordError,
    InvalidPasswordResetCodeError,
    PasswordResetAttemptsExceededError,
    UserNotFoundError,
)
from app.domain.ports.output.password_hasher_port import PasswordHasherPort
from app.domain.ports.output.password_reset_code_repository_port import (
    PasswordResetCodeRepositoryPort,
)
from app.domain.ports.output.user_repository_port import UserRepositoryPort


class UpdatePasswordUseCase:
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        reset_code_repository: PasswordResetCodeRepositoryPort,
        hasher: PasswordHasherPort,
    ) -> None:
        self._user_repository = user_repository
        self._reset_code_repository = reset_code_repository
        self._hasher = hasher

    async def execute(self, cellphone: str, code: str, new_password: str) -> None:
        user = await self._user_repository.find_by_cellphone(cellphone)
        if user is None:
            raise UserNotFoundError('no existe un usuario con ese número registrado.')

        reset_code = await self._get_verifiable_reset_code(user.uuid)
        await self._verify_code(reset_code, code)
        self._validate_password(new_password)

        hashed_password = self._hasher.hash(new_password)
        await self._user_repository.update_password(user.uuid, hashed_password)
        reset_code.consumed_at = datetime.now(UTC)
        await self._reset_code_repository.update(reset_code)

    async def _get_verifiable_reset_code(self, user_uuid: UUID) -> PasswordResetCode:
        reset_code = await self._reset_code_repository.find_latest_by_user(user_uuid)
        if reset_code is None or reset_code.consumed_at is not None:
            raise InvalidPasswordResetCodeError(
                'no hay un código de recuperación activo, solicita uno nuevo.'
            )
        if reset_code.expires_at is not None and reset_code.expires_at <= datetime.now(
            UTC
        ):
            raise InvalidPasswordResetCodeError('el código expiró, solicita uno nuevo.')
        if reset_code.attempts_used >= PASSWORD_RESET_MAX_VERIFICATION_ATTEMPTS:
            raise PasswordResetAttemptsExceededError(
                'se agotaron los intentos, solicita un nuevo código.'
            )
        return reset_code

    async def _verify_code(self, reset_code: PasswordResetCode, code: str) -> None:
        if reset_code.code != code:
            reset_code.attempts_used += 1
            await self._reset_code_repository.update(reset_code)
            raise InvalidPasswordResetCodeError('código incorrecto.')

    def _validate_password(self, new_password: str) -> None:
        if not PASSWORD_PATTERN.match(new_password):
            raise InvalidPasswordError('password is invalid.')
