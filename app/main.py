from fastapi import FastAPI

from app.domain.exceptions.user_exceptions import DomainError
from app.infrastructure.api.exception_handlers import domain_exception_handler
from app.infrastructure.api.routes.login import router as login_router
from app.infrastructure.api.routes.logout import router as logout_router
from app.infrastructure.api.routes.password_reset import router as password_reset_router
from app.infrastructure.api.routes.update_password import (
    router as update_password_router,
)
from app.infrastructure.api.routes.user import router as user_router

app = FastAPI(title='TurfBook Login Service')

app.include_router(user_router)
app.include_router(login_router)
app.include_router(logout_router)
app.include_router(password_reset_router)
app.include_router(update_password_router)
app.add_exception_handler(DomainError, domain_exception_handler)
