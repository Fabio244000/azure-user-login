from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.logout_user import LogoutUserUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.application.use_cases.request_password_reset import (
    RequestPasswordResetUseCase,
)
from app.application.use_cases.update_password import UpdatePasswordUseCase
from app.domain.ports.output.password_hasher_port import PasswordHasherPort
from app.domain.ports.output.password_reset_code_repository_port import (
    PasswordResetCodeRepositoryPort,
)
from app.domain.ports.output.sms_queue_port import SmsQueuePort
from app.domain.ports.output.token_issuer_port import TokenIssuerPort
from app.domain.ports.output.user_repository_port import UserRepositoryPort
from app.infrastructure.database.repositories.password_reset_code_repository import (
    PasswordResetCodeRepository,
)
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.session import get_session
from app.infrastructure.messaging.azure_sms_queue import AzureSmsQueue
from app.infrastructure.security.argon2_password_hasher import Argon2PasswordHasher
from app.infrastructure.security.jwt_token_issuer import JwtTokenIssuer


def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepositoryPort:
    return UserRepository(session)


def get_jwt_token_issuer() -> TokenIssuerPort:
    return JwtTokenIssuer()


def get_password_hasher() -> PasswordHasherPort:
    return Argon2PasswordHasher()


def get_register_user_use_case(
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    token_issuer: TokenIssuerPort = Depends(get_jwt_token_issuer),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        user_repository=user_repository,
        token_issuer=token_issuer,
        hasher=password_hasher,
    )


def get_login_user_use_case(
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    token_issuer: TokenIssuerPort = Depends(get_jwt_token_issuer),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
) -> LoginUserUseCase:
    return LoginUserUseCase(
        user_repository=user_repository,
        token_issuer=token_issuer,
        hasher=password_hasher,
    )


def get_logout_user_use_case(
    token_issuer: TokenIssuerPort = Depends(get_jwt_token_issuer),
) -> LogoutUserUseCase:
    return LogoutUserUseCase(token_issuer=token_issuer)


def get_password_reset_code_repository(
    session: AsyncSession = Depends(get_session),
) -> PasswordResetCodeRepositoryPort:
    return PasswordResetCodeRepository(session)


def get_sms_queue() -> SmsQueuePort:
    return AzureSmsQueue()


def get_request_password_reset_use_case(
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    reset_code_repository: PasswordResetCodeRepositoryPort = Depends(
        get_password_reset_code_repository
    ),
    sms_queue: SmsQueuePort = Depends(get_sms_queue),
) -> RequestPasswordResetUseCase:
    return RequestPasswordResetUseCase(
        user_repository=user_repository,
        reset_code_repository=reset_code_repository,
        sms_queue=sms_queue,
    )


def get_update_password_use_case(
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    reset_code_repository: PasswordResetCodeRepositoryPort = Depends(
        get_password_reset_code_repository
    ),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
) -> UpdatePasswordUseCase:
    return UpdatePasswordUseCase(
        user_repository=user_repository,
        reset_code_repository=reset_code_repository,
        hasher=password_hasher,
    )
