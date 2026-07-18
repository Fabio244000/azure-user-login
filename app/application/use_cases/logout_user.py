from app.domain.ports.output.token_issuer_port import TokenIssuerPort


class LogoutUserUseCase:
    def __init__(self, token_issuer: TokenIssuerPort) -> None:
        self._token_issuer = token_issuer

    async def execute(self, token: str) -> None:
        self._token_issuer.decode(token)
