from fastapi import APIRouter, Depends, status

from app.application.use_cases.update_password import UpdatePasswordUseCase
from app.infrastructure.api.dependencies import get_update_password_use_case
from app.infrastructure.api.schemas.api_response import ApiResponse
from app.infrastructure.api.schemas.password_reset_schema import UpdatePasswordRequest

router = APIRouter()


@router.post(
    '/password/reset',
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[None],
)
async def update_password(
    request: UpdatePasswordRequest,
    use_case: UpdatePasswordUseCase = Depends(get_update_password_use_case),
) -> ApiResponse[None]:
    await use_case.execute(
        cellphone=request.cellphone,
        code=request.code,
        new_password=request.new_password,
    )
    return ApiResponse(success=True, message='Contraseña actualizada')
