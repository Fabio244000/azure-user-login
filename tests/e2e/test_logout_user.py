import pytest
from httpx import ASGITransport, AsyncClient

from app.infrastructure.database.session import get_session
from app.main import app


def _register_payload(**overrides):
    data = {
        'first_name': 'fabio',
        'last_name': 'nunez garcia',
        'cellphone': '+51 987654321',
        'username': 'fabio01',
        'password': 'secretpass123',
        'email': 'fabio@mail.com',
    }
    data.update(overrides)
    return data


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url='http://test')
    app.dependency_overrides.clear()


class TestLogoutUserEndpoint:
    async def test_returns_204_with_valid_token(self, client):
        async with client:
            await client.post('/users', json=_register_payload())
            login_response = await client.post(
                '/login', json={'username': 'fabio01', 'password': 'secretpass123'}
            )
            token = login_response.json()['data']['token']

            response = await client.post(
                '/logout', headers={'Authorization': f'Bearer {token}'}
            )

        assert response.status_code == 204
        assert response.content == b''

    async def test_returns_401_with_invalid_token(self, client):
        async with client:
            response = await client.post(
                '/logout', headers={'Authorization': 'Bearer not-a-real-token'}
            )
        assert response.status_code == 401

    async def test_returns_401_without_token(self, client):
        async with client:
            response = await client.post('/logout')
        assert response.status_code == 401
