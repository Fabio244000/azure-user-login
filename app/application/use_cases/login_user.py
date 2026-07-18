from app.domain.entities.user import User
from app.domain.exceptions import InvalidCredentialsError
from app.domain.ports.output.password_hasher_port import PasswordHasherPort
from app.domain.ports.output.token_issuer_port import TokenIssuerPort
from app.domain.ports.output.user_repository_port import UserRepositoryPort


class LoginUserUseCase:
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        hasher: PasswordHasherPort,
        token_issuer: TokenIssuerPort,
    ) -> None:
        self._user_repository = user_repository
        self._hasher = hasher
        self._token_issuer = token_issuer

    async def execute(self, username: str, password: str) -> tuple[User, str]:
        user = await self._user_repository.find_by_username(username)
        if user is None or not user.password:
            raise InvalidCredentialsError('invalid username or password.')

        if not self._hasher.verify(password, user.password):
            raise InvalidCredentialsError('invalid username or password.')

        session_token = self._token_issuer.issue(user.uuid)
        return user, session_token
