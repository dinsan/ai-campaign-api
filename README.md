# AI Campaign API — Architecture & Technical Design

## 1. Project Overview

AI Campaign API is a production-style backend application for creating marketing campaigns and generating AI-powered campaign content.

The application is designed to demonstrate modern Python backend engineering, including REST API design, layered architecture, PostgreSQL persistence, authentication, asynchronous processing, and LLM integration.

The system will eventually support AI-generated:

- Keywords
- Advertising headlines
- Advertising descriptions
- Campaign content variations

---

# 2. Technology Stack

## Backend

**Python 3**  
Primary programming language.

**FastAPI**  
REST API framework used for routing, dependency injection, request handling, validation, and OpenAPI documentation.

**Pydantic**  
Used for request and response validation.

**Pydantic Settings**  
Used for environment-based application configuration.

## Database

**PostgreSQL**  
Primary relational database.

**SQLAlchemy 2**  
ORM and database abstraction layer.

**Psycopg**  
PostgreSQL database driver used by SQLAlchemy.

**Alembic**  
Database schema migration management.

## Security

**Argon2 / pwdlib**  
Secure password hashing and verification.

**JWT Authentication**  
Will be used for authenticated API access.

## Background Processing

**Redis**  
Will act as the message broker/cache for asynchronous jobs.

**Celery**  
Will process long-running AI generation tasks outside the HTTP request lifecycle.

## AI

An LLM provider will be integrated through a dedicated AI service layer.

The LLM integration will be responsible for generating campaign keywords, headlines, descriptions, and other marketing content.

## Testing

**Pytest**  
Automated unit and integration testing.

**HTTPX**  
Testing FastAPI HTTP endpoints.

## Infrastructure

**Docker / Docker Compose**  
Containerized local development and deployment.

---

# 3. High-Level Architecture

```text
                     Client
                       │
                       │ HTTP / REST
                       ▼
              ┌─────────────────┐
              │     FastAPI     │
              │     Routes      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Service Layer   │
              │ Business Logic  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Repository      │
              │ Layer           │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   SQLAlchemy    │
              └────────┬────────┘
                       │
                    Psycopg
                       │
                       ▼
              ┌─────────────────┐
              │   PostgreSQL    │
              └─────────────────┘
```

The application follows a layered architecture:

```text
API → Service → Repository → ORM → Database
```

Each layer has a separate responsibility.

---

# 4. Project Structure

```text
ai-campaign-api/
│
├── app/
│   │
│   ├── api/
│   │   ├── __init__.py        # mounts every API version under /api
│   │   └── v1/
│   │       ├── __init__.py    # aggregate router for /api/v1
│   │       ├── auth.py
│   │       ├── categories.py
│   │       ├── products.py
│   │       ├── search.py
│   │       └── users.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   ├── dependencies.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── category.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── repositories/
│   │   ├── category_repository.py
│   │   ├── product_repository.py
│   │   ├── search.py
│   │   └── user_repository.py
│   │
│   ├── schemas/
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── search.py
│   │   └── user.py
│   │
│   ├── services/
│   │   ├── category_service.py
│   │   ├── product_service.py
│   │   ├── search_service.py
│   │   └── user_service.py
│   │
│   └── main.py
│
├── migrations/
│   └── versions/
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

As the project grows, additional modules will be introduced for campaigns, authentication, AI generation and background workers.

---

# 5. Layer Responsibilities

## API Layer

Location:

```text
app/api/
```

Responsibilities:

- Receive HTTP requests
- Validate request data
- Inject dependencies
- Call the appropriate service
- Convert application errors into HTTP responses
- Return response schemas

Example:

```text
POST /api/v1/users
```

The API layer should not directly execute SQL queries or contain complex business logic.

---

## Service Layer

Location:

```text
app/services/
```

Responsibilities:

- Business rules
- Application workflows
- Validation beyond request structure
- Coordinating repositories
- Security operations
- Coordinating external services

Example:

When creating a user:

```text
Check whether email exists
        ↓
Hash password
        ↓
Create user
```

The service layer decides **what should happen**.

---

## Repository Layer

Location:

```text
app/repositories/
```

Responsibilities:

- Database queries
- Creating database records
- Updating records
- Deleting records
- Retrieving records

Example:

```text
UserRepository.get_by_email()

UserRepository.create()

UserRepository.get_by_id()
```

The repository layer decides **how data is stored and retrieved**.

---

## Model Layer

Location:

```text
app/models/
```

Contains SQLAlchemy database models.

Example:

```text
User
Campaign
Generation
```

These models represent database tables and relationships.

---

## Schema Layer

Location:

```text
app/schemas/
```

Contains Pydantic request and response models.

For example:

```text
UserCreate
UserUpdate
UserResponse
```

This provides a separation between:

```text
API representation
        ↓
Pydantic Schema

Database representation
        ↓
SQLAlchemy Model
```

Database models should not be exposed directly as unrestricted API responses.

---

# 6. Database Architecture

The initial database contains:

```text
users
```

The project will later introduce:

```text
users
   │
   │ 1
   │
   └────────── *
            campaigns
                │
                │ 1
                │
                └────────── *
                         generations
```

Conceptually:

```text
User
 │
 ├── Campaign
 │      │
 │      ├── Generation
 │      ├── Generation
 │      └── Generation
 │
 └── Campaign
        │
        └── Generation
```

A user can therefore have multiple campaigns, and each campaign can have multiple AI generation versions.

---

# 7. Database Migrations

Alembic manages database schema changes.

The workflow is:

```text
Modify SQLAlchemy model
        ↓
Generate migration
        ↓
Review migration
        ↓
Apply migration
        ↓
PostgreSQL updated
```

Example:

```bash
alembic revision --autogenerate -m "create users table"

alembic upgrade head
```

Database tables should not be manually created for application schema changes.

---

# 8. User Registration Flow

Current registration architecture:

```text
Client
  │
  │ POST /api/v1/users
  ▼
FastAPI User Route
  │
  ▼
UserService
  │
  ├──── Check email
  │
  ▼
UserRepository
  │
  ▼
PostgreSQL
```

If the email does not exist:

```text
UserService
    │
    ▼
Hash password
    │
    ▼
Argon2 Hash
    │
    ▼
UserRepository.create()
    │
    ▼
SQLAlchemy
    │
    ▼
PostgreSQL
```

The raw password is never stored.

Only:

```text
password_hash
```

is persisted.

---

# 9. Dependency Injection

FastAPI dependency injection manages database sessions.

```text
HTTP Request
     │
     ▼
get_db()
     │
     ▼
Create SQLAlchemy Session
     │
     ▼
Route
     │
     ▼
Repository
     │
     ▼
Database operation
     │
     ▼
Request finishes
     │
     ▼
Session closed
```

This prevents routes from manually managing database connection lifecycles.

---

# 10. Authentication Flow

JWT authentication will be introduced next.

Expected flow:

```text
POST /api/v1/auth/login
        │
        ▼
Find User
        │
        ▼
Verify Password
        │
        ▼
Create JWT
        │
        ▼
Return Access Token
```

Protected endpoints will then use:

```text
Authorization:
Bearer <JWT>
```

The API will decode the token and determine the authenticated user.

---

# 11. Campaign Flow

After authentication, users will be able to create campaigns.

Example:

```text
POST /api/v1/campaigns

{
    "name": "GreenRide Campaign",
    "product": "Electric bicycle subscription",
    "target_audience": "Professionals in Paris",
    "objective": "Google Ads"
}
```

Flow:

```text
Authenticated User
        │
        ▼
Campaign API
        │
        ▼
CampaignService
        │
        ▼
CampaignRepository
        │
        ▼
PostgreSQL
```

A campaign belongs to the authenticated user and can contain multiple generation records.

---

# 12. API Versioning

All endpoints are served under a version prefix:

```text
/api/v1/...
```

Only `/health` is unversioned; it reports the versions currently available:

```json
{ "status": "ok", "service": "ai-campaign-api", "api_versions": ["v1"] }
```

How it is wired:

```text
app.main
   │
   └── app.api.router              prefix /api
          │
          └── app.api.v1.router    prefix /v1
                 ├── auth
                 ├── users
                 ├── products
                 ├── categories
                 └── search
```

Rules:

- Backwards-compatible changes (new endpoints, new optional fields) go into
  the current version.
- Breaking changes (renamed/removed fields, changed status codes, different
  behaviour) require a new version. Add an `app/api/v2/` package with its own
  aggregate router, register it in `app/api/__init__.py`, and leave `v1`
  untouched so existing clients keep working.
- Business logic stays in the service and repository layers, which are shared
  by all versions. A new version normally only adds new route modules and
  schemas.

---

# 13. Product API

Authenticated users can manage their own products through `/api/v1/products`. Product
records include a required name and optional description, website, and
`category_id`. A user can only list, retrieve, update, or delete products they
own.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/products` | Create a product |
| `GET` | `/api/v1/products` | List the authenticated user's products |
| `GET` | `/api/v1/products/{product_id}` | Retrieve an owned product |
| `PUT` | `/api/v1/products/{product_id}` | Replace an owned product's details |
| `DELETE` | `/api/v1/products/{product_id}` | Delete an owned product |

Requests use a Bearer access token. The `products` table is created by the
Alembic migration `a8c2d91f4b63_create_products_table.py`.

A product can optionally be linked to one of the owner's categories by sending
its id as `category_id`. The category must belong to the authenticated user;
otherwise the request is rejected with `400 Bad Request`. Sending
`"category_id": null` unlinks the product.

---

# 14. Category API

Authenticated users can organise their products into categories through
`/api/v1/categories`. A category has a required name (unique per user) and an optional
description. A user can only list, retrieve, update, or delete categories they
own.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/categories` | Create a category (`409` if the name is already used) |
| `GET` | `/api/v1/categories` | List the authenticated user's categories |
| `GET` | `/api/v1/categories/{category_id}` | Retrieve an owned category |
| `PUT` | `/api/v1/categories/{category_id}` | Replace an owned category's details |
| `DELETE` | `/api/v1/categories/{category_id}` | Delete an owned category |

Relationship with products:

```text
User
 │
 ├── Category ──── * Product
 │
 └── Product (no category)
```

Deleting a category does **not** delete its products; their `category_id` is
reset to `null` (`ON DELETE SET NULL`).

The `categories` table and the `products.category_id` column are created by the
Alembic migration `c4e7f3a9d215_create_categories_table.py`. That migration
also converts any existing free-text `products.category` values into real
category rows before dropping the old column, so no data is lost on upgrade.

---

# 15. Search API

Authenticated users can search their own products and categories in one call.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/search?q=<text>` | Find products and categories whose name contains `q` |

Matching is case-insensitive and partial (`bik` matches `Electric Bike`), and
`%`/`_` in the query are treated literally. A blank `q` is rejected with `422`.

The response has two sections. Matched products carry their linked category;
matched categories carry their linked products:

```json
{
  "query": "bike",
  "products": [
    {
      "id": 1,
      "name": "Electric Bike",
      "description": null,
      "website": "https://bikes.example.com/",
      "category": { "id": 1, "name": "Transport", "description": "Ways to get around" }
    }
  ],
  "categories": [
    {
      "id": 1,
      "name": "Bikes",
      "description": null,
      "products": [
        { "id": 1, "name": "Electric Bike", "description": null, "website": "https://bikes.example.com/" }
      ]
    }
  ]
}
```

Flow:

```text
GET /api/v1/search?q=bike
        │
        ▼
SearchService
        │
        ├──── ProductRepository.search_by_name()   (category preloaded)
        │
        └──── CategoryRepository.search_by_name()  (products preloaded)
```

No schema change is required; search only reads the existing `products` and
`categories` tables.
