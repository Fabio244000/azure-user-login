from app.domain.exceptions.user_exceptions import DomainError


class InvalidPasswordResetCodeError(DomainError):
    pass


class PasswordResetAlreadyRequestedError(DomainError):
    pass


class PasswordResetAttemptsExceededError(DomainError):
    pass
