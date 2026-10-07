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

## Run Locally

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at http://127.0.0.1:8000.

For interactive API docs, visit http://127.0.0.1:8000/docs.
