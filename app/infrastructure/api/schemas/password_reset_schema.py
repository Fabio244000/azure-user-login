from pydantic import BaseModel


class RequestPasswordResetRequest(BaseModel):
    cellphone: str


class UpdatePasswordRequest(BaseModel):
    cellphone: str
    code: str
    new_password: str
