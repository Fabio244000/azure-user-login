import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.domain.constants import (
    CELLPHONE_PATTERN,
    PASSWORD_RESET_CODE_GENERATION_RETRIES,
    PASSWORD_RESET_DAILY_LIMIT_HOURS,
)
from app.domain.entities.password_reset_code import PasswordResetCode
from app.domain.exceptions import (
    InvalidCellphoneError,
    InvalidPasswordResetCodeError,
    PasswordResetAlreadyRequestedError,
    UserNotFoundError,
)
from app.domain.ports.output.password_reset_code_repository_port import (
    PasswordResetCodeRepositoryPort,
)
from app.domain.ports.output.sms_queue_port import SmsQueuePort
from app.domain.ports.output.user_repository_port import UserRepositoryPort


class RequestPasswordResetUseCase:
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        reset_code_repository: PasswordResetCodeRepositoryPort,
        sms_queue: SmsQueuePort,
    ) -> None:
        self._user_repository = user_repository
        self._reset_code_repository = reset_code_repository
        self._sms_queue = sms_queue

    async def execute(self, cellphone: str) -> None:
        self._validate_cellphone(cellphone)
        user = await self._user_repository.find_by_cellphone(cellphone)
        if user is None:
            raise UserNotFoundError('no existe un usuario con ese número registrado.')

        await self._verify_daily_limit(user.uuid)
        code = await self._generate_unique_code()

        reset_code = PasswordResetCode(user_uuid=user.uuid, code=code)
        await self._reset_code_repository.save(reset_code)
        await self._sms_queue.publish_verification_code(
            cellphone=user.cellphone, code=code
        )

    def _validate_cellphone(self, cellphone: str) -> None:
        if not CELLPHONE_PATTERN.match(cellphone):
            raise InvalidCellphoneError('cellphone format is invalid.')

    async def _verify_daily_limit(self, user_uuid: UUID) -> None:
        last_code = await self._reset_code_repository.find_latest_by_user(user_uuid)
        limit_window = timedelta(hours=PASSWORD_RESET_DAILY_LIMIT_HOURS)
        if last_code and datetime.now(UTC) - last_code.created_at < limit_window:
            raise PasswordResetAlreadyRequestedError(
                'ya solicitaste un código hoy, inténtalo más tarde.'
            )

    async def _generate_unique_code(self) -> str:
        for _ in range(PASSWORD_RESET_CODE_GENERATION_RETRIES):
            candidate = f'{secrets.randbelow(1_000_000):06d}'
            if not await self._reset_code_repository.exists_active_code(candidate):
                return candidate
        raise InvalidPasswordResetCodeError(
            'could not generate a unique verification code.'
        )
