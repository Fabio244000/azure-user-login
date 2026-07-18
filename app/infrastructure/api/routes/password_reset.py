from fastapi import APIRouter, Depends, status

from app.application.use_cases.request_password_reset import (
    RequestPasswordResetUseCase,
)
from app.infrastructure.api.dependencies import get_request_password_reset_use_case
from app.infrastructure.api.schemas.api_response import ApiResponse
from app.infrastructure.api.schemas.password_reset_schema import (
    RequestPasswordResetRequest,
)

router = APIRouter()


@router.post(
    '/password/reset-request',
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[None],
)
async def request_password_reset(
    request: RequestPasswordResetRequest,
    use_case: RequestPasswordResetUseCase = Depends(
        get_request_password_reset_use_case
    ),
) -> ApiResponse[None]:
    await use_case.execute(request.cellphone)
    return ApiResponse(success=True, message='código enviado')
