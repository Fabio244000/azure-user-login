import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.infrastructure.database.models import PasswordResetCodeModel
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


async def _register_and_request_code(client):
    await client.post('/users', json=_register_payload())
    await client.post('/password/reset-request', json={'cellphone': '+51 987654321'})


async def _latest_reset_code(session):
    query = (
        select(PasswordResetCodeModel)
        .order_by(PasswordResetCodeModel.created_at.desc())
        .limit(1)
    )
    result = await session.execute(query)
    return result.scalar_one().code


class TestUpdatePasswordEndpoint:
    async def test_returns_200_and_updates_password_on_correct_code(
        self, client, session
    ):
        async with client:
            await _register_and_request_code(client)
            code = await _latest_reset_code(session)

            response = await client.post(
                '/password/reset',
                json={
                    'cellphone': '+51 987654321',
                    'code': code,
                    'new_password': 'newsecret123',
                },
            )
            login_response = await client.post(
                '/login',
                json={'username': 'fabio01', 'password': 'newsecret123'},
            )

        assert response.status_code == 200
        assert response.json()['message'] == 'Contraseña actualizada'
        assert login_response.status_code == 200

    async def test_returns_400_on_wrong_code(self, client):
        async with client:
            await _register_and_request_code(client)
            response = await client.post(
                '/password/reset',
                json={
                    'cellphone': '+51 987654321',
                    'code': '000000',
                    'new_password': 'newsecret123',
                },
            )
        assert response.status_code == 400
        assert response.json()['success'] is False

    async def test_returns_429_after_three_wrong_attempts(self, client):
        async with client:
            await _register_and_request_code(client)
            for _ in range(3):
                response = await client.post(
                    '/password/reset',
                    json={
                        'cellphone': '+51 987654321',
                        'code': '000000',
                        'new_password': 'newsecret123',
                    },
                )
            fourth = await client.post(
                '/password/reset',
                json={
                    'cellphone': '+51 987654321',
                    'code': '000000',
                    'new_password': 'newsecret123',
                },
            )
        assert response.status_code == 400
        assert fourth.status_code == 429

    async def test_returns_400_on_invalid_new_password_format(self, client):
        async with client:
            await _register_and_request_code(client)
            response = await client.post(
                '/password/reset',
                json={
                    'cellphone': '+51 987654321',
                    'code': '000000',
                    'new_password': 'short',
                },
            )
        assert response.status_code == 400

    async def test_returns_400_when_no_code_was_requested(self, client):
        async with client:
            await client.post('/users', json=_register_payload())
            response = await client.post(
                '/password/reset',
                json={
                    'cellphone': '+51 987654321',
                    'code': '123456',
                    'new_password': 'newsecret123',
                },
            )
        assert response.status_code == 400

    async def test_returns_404_on_unregistered_cellphone(self, client):
        async with client:
            response = await client.post(
                '/password/reset',
                json={
                    'cellphone': '+51 900000000',
                    'code': '123456',
                    'new_password': 'newsecret123',
                },
            )
        assert response.status_code == 404

    async def test_returns_422_on_missing_fields(self, client):
        async with client:
            response = await client.post(
                '/password/reset', json={'cellphone': '+51 987654321'}
            )
        assert response.status_code == 422
