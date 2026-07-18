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


class TestLoginUserEndpoint:
    async def test_returns_200_and_token_on_success(self, client):
        async with client:
            await client.post('/users', json=_register_payload())
            response = await client.post(
                '/login', json={'username': 'fabio01', 'password': 'secretpass123'}
            )

        assert response.status_code == 200
        body = response.json()
        assert body['success'] is True
        assert 'token' in body['data']
        assert body['data']['user']['username'] == 'fabio01'

    async def test_response_does_not_expose_password(self, client):
        async with client:
            await client.post('/users', json=_register_payload())
            response = await client.post(
                '/login', json={'username': 'fabio01', 'password': 'secretpass123'}
            )
        body = response.json()
        assert 'password' not in body['data']['user']

    async def test_returns_401_on_wrong_password(self, client):
        async with client:
            await client.post('/users', json=_register_payload())
            response = await client.post(
                '/login', json={'username': 'fabio01', 'password': 'wrongpassword'}
            )
        assert response.status_code == 401
        assert response.json()['success'] is False

    async def test_returns_401_on_unknown_username(self, client):
        async with client:
            response = await client.post(
                '/login', json={'username': 'ghost', 'password': 'secretpass123'}
            )
        assert response.status_code == 401

    async def test_returns_422_on_missing_password(self, client):
        async with client:
            response = await client.post('/login', json={'username': 'fabio01'})
        assert response.status_code == 422
