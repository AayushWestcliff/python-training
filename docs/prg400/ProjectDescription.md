# PRG 400: Advanced Python – Course Project

Welcome to the **PRG 400: Advanced Python** course project!

This project challenges you to engineer a **production-grade web application** using professional software development practices — from architecture and design patterns to containerization and deployment.

You will apply **SOLID principles**, **12-Factor App methodology**, and **modular software design** to build something real, maintainable, and deployable.

---

## Objective

By the end of this project, you will:

- Architect a clean, modular Python web application following **SOLID principles**
- Apply **12-Factor App** practices for configuration, logging, and environment management
- Build a **RESTful API backend** using **FastAPI** or **Flask**
- Containerize your application using **Docker** and **Docker Compose**
- Write **unit and integration tests** with meaningful coverage
- Deploy your application to a cloud platform
- Document your architecture decisions and reflect on engineering tradeoffs

---

## Core Requirements

Every project **must** include:

| Requirement | Details |
|----|----|
| Web Framework | FastAPI (recommended) or Django or Flask |
| Database | PostgreSQL or SQLite (via SQLAlchemy ORM) |
| Containerization | `Dockerfile` + `docker-compose.yml` |
| Configuration | Environment variables via `.env` (never hardcoded) |
| Testing | Unit tests with `pytest` (minimum 60% coverage) |
| Logging | Structured logging (no bare `print()` statements in production code) |
| Code Quality | `ruff` or `flake8` linting, `black` formatting |
| Documentation | `README.md` with setup, architecture, and API docs |

---

## SOLID Principles — Applied

Your project must **demonstrably apply** all five SOLID principles. You will be evaluated on how intentionally and correctly each is used — not just whether the terms appear in your code.

### S — Single Responsibility Principle

> *A class or module should have only one reason to change.*

Each module in your project should own **one concern**. A route handler should not also format data, validate input, AND write to the database. Split responsibilities across layers.

**Example in your project:**

    app/
    ├── api/routes/         # HTTP layer only — receives requests, returns responses
    ├── services/           # Business logic only — orchestrates domain rules
    ├── repositories/       # Data access only — talks to the database
    ├── models/             # Domain entities — data shapes and validation
    └── core/               # App-wide concerns — config, logging, exceptions

### O — Open/Closed Principle

> *Software entities should be open for extension, but closed for modification.*

Design your core logic so new features can be added **without editing existing code**. Use abstract base classes, dependency injection, and strategy patterns.

**Example:** An `NotificationService` that accepts any `NotificationChannel` (email, SMS, webhook) without its core logic ever changing:

```bash
from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> None: ...

class EmailChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> None:
        # send email

class SMSChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> None:
        # send SMS

class NotificationService:
    def __init__(self, channel: NotificationChannel):
        self._channel = channel

    def notify(self, recipient: str, message: str) -> None:
        self._channel.send(recipient, message)
```

### L — Liskov Substitution Principle

> *Subtypes must be substitutable for their base types without altering program correctness.*

If you use inheritance or abstract classes, any subclass must honour the full contract of its parent. A subclass should never **weaken preconditions**, **strengthen postconditions**, or raise unexpected exceptions.

**What to watch for:** If you find yourself writing `if isinstance(obj, SubclassX)` inside shared logic, LSP is likely violated.

### I — Interface Segregation Principle

> *Clients should not be forced to depend on interfaces they do not use.*

Prefer many small, focused interfaces over one large "god" interface. If a class only needs read access to a repository, it should depend on a `ReadableRepository`, not a full `CRUDRepository`.


```python
from typing import Protocol

class Readable(Protocol):
    def get(self, id: int): ...

class Writable(Protocol):
    def save(self, entity): ...
    def delete(self, id: int): ...

class ReadWriteRepository(Readable, Writable): ...
```

### D — Dependency Inversion Principle

> *High-level modules should not depend on low-level modules. Both should depend on abstractions.*

Your service layer should **never import** a concrete database class directly. Inject dependencies through constructors or FastAPI's `Depends()` system.


```python
# Bad — high-level service knows about low-level detail
class UserService:
    def __init__(self):
        self.db = PostgresUserRepository()   # ❌ tightly coupled

# Good — depends on abstraction, injected from outside
class UserService:
    def __init__(self, repo: UserRepository):  # ✅ abstraction injected
        self.repo = repo
```

---

## 12-Factor App Methodology

Your application must follow the [12-Factor App](https://12factor.net/) principles. Below is how each factor maps to your project.

| Factor | What You Must Do |
|----|----|
| **I. Codebase** | One Git repo, one app. No sharing code between apps via copy-paste. |
| **II. Dependencies** | All dependencies declared in `requirements.txt` or `pyproject.toml`. Nothing assumed to be pre-installed. |
| **III. Config** | All config (DB URLs, secrets, ports) loaded from environment variables. Use `python-dotenv` locally. Never commit `.env`. |
| **IV. Backing Services** | Treat your database, cache, or email provider as attached resources — swappable via config, not code changes. |
| **V. Build, Release, Run** | Dockerfile separates build from run. `docker-compose` manages release and run stages. |
| **VI. Processes** | Your app must be stateless. No in-memory session state. Store state in the database or cache. |
| **VII. Port Binding** | Your app exposes itself on a port (e.g., `8000`) defined by environment variable, not hardcoded. |
| **VIII. Concurrency** | Design so multiple workers can run in parallel. Avoid global mutable state. |
| **IX. Disposability** | App starts fast, shuts down gracefully. Handle `SIGTERM` for clean shutdown. |
| **X. Dev/Prod Parity** | Docker Compose ensures local dev mirrors production. No "works on my machine." |
| **XI. Logs** | Log to `stdout`/`stderr` as structured events (JSON preferred). Never write log files manually. |
| **XII. Admin Processes** | DB migrations run as one-off tasks (e.g., `alembic upgrade head`) not embedded in app startup. |

---

## Required Project Structure

Your repository **must** follow this structure (you may add to it, but not remove required parts):

```
your-project/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # App entry point, FastAPI/Flask app factory
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/              # Route handlers (one file per resource)
│   │   │   ├── __init__.py
│   │   │   └── items.py
│   │   └── dependencies.py      # FastAPI Depends() injections
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic BaseSettings — loads from env
│   │   ├── logging.py           # Structured logger setup
│   │   └── exceptions.py        # Custom exception classes
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain.py            # Pure domain entities (Pydantic / dataclasses)
│   │   └── orm.py               # SQLAlchemy ORM models
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract base repository (interface)
│   │   └── item_repository.py   # Concrete implementation
│   │
│   └── services/
│       ├── __init__.py
│       └── item_service.py      # Business logic, depends on repository interface
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures, test DB setup
│   ├── unit/
│   │   └── test_item_service.py
│   └── integration/
│       └── test_item_routes.py
│
├── migrations/                  # Alembic migration scripts
│   ├── env.py
│   └── versions/
│
├── .env.example                 # Template for env vars — committed to repo
├── .env                         # Actual secrets — NEVER committed (in .gitignore)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── docker-compose.test.yml      # Separate compose for running tests
├── requirements.txt
├── pyproject.toml               # Linting, formatting, test config
├── alembic.ini
└── README.md                    # Your project's own README
```

---

## Dockerfile Requirements

Your `Dockerfile` must use a **multi-stage build**:

```bash
# Stage 1: Builder — install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Runtime — lean final image
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy only the venv and app code — no build tools in production image
COPY --from=builder /opt/venv /opt/venv
COPY ./app ./app

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run as non-root user (security best practice)
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Your `docker-compose.yml` must define at minimum: - An `app` service (your web application) - A `db` service (PostgreSQL) - Proper use of `environment`, `depends_on`, `volumes`, and `healthcheck`

---

## Configuration — The Right Way

Use **Pydantic `BaseSettings`** to load all configuration from environment variables:


```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My App"
    database_url: str
    secret_key: str
    debug: bool = False
    port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
```

Your `.env.example` (committed) should list every variable with placeholder values:

```
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
SECRET_KEY=changeme
DEBUG=false
PORT=8000
```

Your `.env` (never committed) holds the real values for local development.

---

## Project Timeline

### Week 2: Architecture Design & Proposal

- Choose your project domain (see ideas below)
- Define your data models, API endpoints, and service boundaries
- Sketch your layered architecture (routes → services → repositories)
- Identify which SOLID principles apply where

**Deliverable:** - 1–2 page Architecture Proposal - Entity-Relationship Diagram (ERD) - Endpoint design table (method, path, description, auth required)

---

### Week 3: Literature & Technical Review

- Review 2–3 open-source Python web applications on GitHub
- Evaluate their architecture: Do they follow SRP? Are services testable? Is config handled properly?
- Identify what you will do differently or improve upon

**Deliverable:** - Technical Review Report (2–3 pages) - Annotated links to reviewed repositories with critique notes

---

### Week 4: Project Scaffold & Core Models

- Initialize your repository with the required folder structure
- Set up `Dockerfile`, `docker-compose.yml`, and `.env.example`
- Implement domain models and ORM models
- Configure Alembic and create your first migration

**Deliverable:** - Running Docker Compose stack (app + db) - At least one Alembic migration applied - `GET /health` endpoint returning `{"status": "ok"}`

---

### Week 5: Repository & Service Layer

- Implement abstract base repository and at least one concrete repository
- Implement service layer with dependency injection
- Write unit tests for service layer using mock repositories
- Demonstrate Dependency Inversion and Open/Closed principles in code

**Deliverable:** - Working service + repository layer with tests - Test coverage report showing ≥ 50% coverage on service layer

---

### Week 6: API Layer & Integration

- Implement all API routes using FastAPI/Flask
- Connect routes → services → repositories through dependency injection
- Add request validation (Pydantic schemas)
- Add structured logging to all service operations

**Deliverable:** - All planned endpoints implemented and manually testable via Swagger UI or Postman - Integration tests for at least 3 endpoints

---

### Week 7: Hardening, Testing & Documentation

- Achieve ≥ 60% overall test coverage
- Add error handling (custom exceptions, proper HTTP status codes)
- Write your project's own `README.md` with: setup guide, environment variables, how to run tests, API reference
- Run linter (`ruff`/`flake8`) and formatter (`black`) — zero errors

**Deliverable:** - Test coverage report (HTML output from `pytest --cov`) - Clean linting output - Complete project `README.md`

---

### Week 8: Deployment, Demo & Submission

- Deploy using one of: **Railway**, **Render**, **Fly.io**, or **a VPS with Docker**
- Live application must be accessible via public URL
- Present your application (7–10 minutes) — demo, architecture walkthrough, and reflection
- Submit final report

**Deliverables:** - Live Deployment URL - Final Project Report (4–6 pages) — see report structure below - Presentation Slides - Final GitHub repository (clean commit history, no secrets committed)

---

## Final Project Report Structure

Your report must cover:

1.  **Project Overview** — What does your app do? Who is it for?
2.  **Architecture Diagram** — Layered diagram showing routes, services, repositories, DB
3.  **SOLID Principles Applied** — One section per principle: where it appears, why you used it, what problem it solves
4.  **12-Factor Compliance** — Which factors you implemented and how
5.  **Testing Strategy** — What you tested, how, and your coverage results
6.  **Deployment** — Platform chosen, deployment steps, any challenges
7.  **Reflection** — What you would do differently; what you learned

---

## Sample Project Ideas

Choose a domain that interests you. The technical requirements are the same regardless of domain.

| Domain           | Project Idea                                     |
|------------------|--------------------------------------------------|
| Healthcare       | Patient appointment scheduling API               |
| Finance          | Personal budget tracker with category analysis   |
| Education        | Course enrollment and grade management system    |
| E-Commerce       | Product catalog and order management API         |
| Productivity     | Task manager with priority queues and deadlines  |
| IoT / Monitoring | Sensor data ingestion and threshold alerting API |
| HR               | Employee leave request and approval workflow     |
| Library          | Book lending and reservation management system   |

---

## Recommended Tools & Libraries

| Purpose | Recommended |
|----|----|
| Web Framework | FastAPI (preferred), Flask |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Testing | pytest, pytest-cov, httpx (for FastAPI) |
| Mocking | pytest-mock, unittest.mock |
| Config | pydantic-settings, python-dotenv |
| Logging | Python `logging` module with JSON formatter (`python-json-logger`) |
| Linting | ruff |
| Formatting | black |
| Containerization | Docker, Docker Compose |
| API Docs | Swagger UI (built into FastAPI), Postman |
| Deployment | Railway, Render, Fly.io |
| Diagramming | draw.io, Lucidchart, Mermaid (in Markdown) |

---

## Evaluation Criteria

| Component | Weight | Key Rubric Points |
|----|----|----|
| Architecture Proposal & ERD | 10% | Clarity of design, layer separation, endpoint planning |
| Technical Review Report | 5% | Depth of analysis, actionable takeaways |
| SOLID Principles (in code) | 20% | Correct and intentional application of all 5 principles |
| 12-Factor Compliance | 10% | Config from env, stateless design, Docker parity, structured logs |
| Repository & Service Layer | 15% | Abstraction quality, dependency injection, testability |
| API Layer & Functionality | 10% | Correctness, validation, error handling, HTTP semantics |
| Testing & Coverage | 15% | Coverage ≥ 60%, meaningful tests (not just happy path) |
| Deployment & Presentation | 10% | Live app, clear demo, architecture explanation |
| Final Report | 5% | Completeness, reflection quality, accuracy |
| **Total** | **100%** |  |

---

## Academic Integrity

- All code must be your own work
- You may use libraries, documentation, and AI tools as references — but you must be able to explain every line of your code
- Copying code from other students or repositories without attribution is a violation of academic policy
- If you use an AI coding assistant, note it in your report and describe how you used it

---

## Getting Started

Once you accept this GitHub Classroom assignment, clone your repository and begin:

```bash
# Clone your repo
git clone https://github.com/your-org/your-repo.git
cd your-repo

# Copy the example env file
cp .env.example .env
# Edit .env with your local values

# Build and start the stack
docker compose up --build

# In a separate terminal — run migrations
docker compose exec app alembic upgrade head

# Run tests
docker compose -f docker-compose.test.yml run --rm test
```

Your app will be available at `http://localhost:8000`\
API documentation: `http://localhost:8000/docs`

---

> *Good engineers do not just write code that works. They write code that is readable, testable, maintainable, and deployable by someone who has never met them.*
