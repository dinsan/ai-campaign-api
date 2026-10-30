# AI Campaign API

## Activate Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure

Copy `.env.example` to `.env` and fill in the values. `JWT_SECRET_KEY` must be
at least 32 characters; generate one with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Then apply the database migrations:

```bash
alembic upgrade head
```

## Run Locally

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at http://127.0.0.1:8000.

For interactive API docs, visit http://127.0.0.1:8000/docs.

All endpoints are versioned, e.g. http://127.0.0.1:8000/api/v1/products.
Only the health check is unversioned: http://127.0.0.1:8000/health.

## First Administrator

New accounts are read-only `viewer`s. After running the migrations, promote
your own account once so you can manage users and roles through the API:

```sql
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

## Run Tests

```bash
python -m pytest
```
