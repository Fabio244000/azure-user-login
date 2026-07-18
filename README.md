# TurfBook — Login

Login microservice for TurfBook, a synthetic grass court booking platform.
Handles authentication: login, logout, and password reset. Built with FastAPI
following hexagonal architecture, designed to run serverless on AWS Lambda
and deployed to Azure.

## Exposed API

| Method | Endpoint                        | Description                                    |
|--------|----------------------------------|-------------------------------------------------|
| POST   | `/users`                        | Register a new user                              |
| POST   | `/login`                        | Authenticate a user with username/password       |
| POST   | `/logout`                       | Invalidate a session token (`Authorization: Bearer <token>`) |
| POST   | `/password/reset-request`       | Request a 6-digit SMS verification code (cellphone) |
| POST   | `/password/reset`               | Verify the code and set a new password (cellphone, code, new_password) |

Password reset rules: the code is 6 digits, expires after 10 minutes, allows
3 verification attempts before it's locked (a new code must be requested),
and can only be requested once every 24 hours per user. The SMS itself is
sent asynchronously by a worker subscribed to a queue (`app/worker.py`), not
by the API request itself.

## Tech stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- Azure Storage Queue (emulated locally with Azurite)
- Docker / Docker Compose
- Azure (target deployment)

## Getting started

### 1. Create the virtual environment

```bash
conda create -n login-app-env python=3.12
conda activate login-app-env
pip install -r requirements/local.txt
```

### 2. Set environment variables

Copy the example file and adjust if needed:

```bash
cp .env.example .env
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

This starts the API, Postgres, an Azurite container (local emulator for
Azure Storage Queue), and the `sms-worker` service that consumes the queue
and logs the mocked SMS send — the local stand-in for the Azure Function
that will do this in production.

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

## Development

Run code quality checks:

```bash
pre-commit run --all-files
```

Run tests (inside the `app` container, against `TEST_DATABASE_URL`):

```bash
docker compose exec app pytest
```
