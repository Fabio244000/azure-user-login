from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.use_cases.logout_user import LogoutUserUseCase
from app.domain.exceptions import InvalidTokenError
from app.infrastructure.api.dependencies import get_logout_user_use_case

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    use_case: LogoutUserUseCase = Depends(get_logout_user_use_case),
) -> None:
    if credentials is None:
        raise InvalidTokenError('missing session token.')
    await use_case.execute(credentials.credentials)
