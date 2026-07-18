from fastapi import APIRouter, Depends, status

from app.application.use_cases.login_user import LoginUserUseCase
from app.infrastructure.api.dependencies import get_login_user_use_case
from app.infrastructure.api.schemas.api_response import ApiResponse
from app.infrastructure.api.schemas.login_schema import LoginData, LoginRequest
from app.infrastructure.api.schemas.user_schema import UserResponse

router = APIRouter()


@router.post(
    '/login',
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[LoginData],
)
async def login(
    request: LoginRequest,
    use_case: LoginUserUseCase = Depends(get_login_user_use_case),
) -> ApiResponse[LoginData]:
    user, token = await use_case.execute(
        username=request.username,
        password=request.password,
    )
    data = LoginData(user=UserResponse.model_validate(user), token=token)
    return ApiResponse(success=True, data=data)
