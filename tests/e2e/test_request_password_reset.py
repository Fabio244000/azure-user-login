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


class TestRequestPasswordResetEndpoint:
    async def test_returns_200_and_message_on_success(self, client):
        async with client:
            await client.post('/users', json=_register_payload())
            response = await client.post(
                '/password/reset-request', json={'cellphone': '+51 987654321'}
            )

        assert response.status_code == 200
        body = response.json()
        assert body['success'] is True
        assert body['message'] == 'código enviado'

    async def test_returns_429_on_second_request_same_day(self, client):
        async with client:
            await client.post('/users', json=_register_payload())
            await client.post(
                '/password/reset-request', json={'cellphone': '+51 987654321'}
            )
            response = await client.post(
                '/password/reset-request', json={'cellphone': '+51 987654321'}
            )

        assert response.status_code == 429
        assert response.json()['success'] is False

    async def test_returns_404_on_unregistered_cellphone(self, client):
        async with client:
            response = await client.post(
                '/password/reset-request', json={'cellphone': '+51 900000000'}
            )
        assert response.status_code == 404

    async def test_returns_400_on_malformed_cellphone(self, client):
        async with client:
            response = await client.post(
                '/password/reset-request', json={'cellphone': '123'}
            )
        assert response.status_code == 400

    async def test_returns_422_on_missing_cellphone(self, client):
        async with client:
            response = await client.post('/password/reset-request', json={})
        assert response.status_code == 422
