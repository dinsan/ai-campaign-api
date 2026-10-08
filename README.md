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
│   │   └── users.py
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
│   │   └── user.py
│   │
│   ├── repositories/
│   │   └── user_repository.py
│   │
│   ├── schemas/
│   │   └── user.py
│   │
│   ├── services/
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
POST /users
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
  │ POST /users
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
POST /auth/login
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
POST /campaigns

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

A campaign belongs to the
