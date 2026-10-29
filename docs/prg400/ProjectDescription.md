# PRG 400: Advanced Python – Course Project

Welcome to the PRG 400 course project. Over the next few weeks you'll build a **production-grade web application** the way professional teams do: a clean architecture, sensible design patterns, tests, containers and a real deployment.

The point isn't just to get something working. You'll apply **SOLID principles**, the **12-Factor App** methodology and **modular design** so that your app is maintainable and deployable by someone who has never met you.

### At a Glance

| | |
|---|---|
| **What** | A layered Python web API (routes → services → repositories) backed by a database |
| **Framework** | FastAPI (recommended), Flask or Django (see Core Requirements below) |
| **Runs in** | Docker + Docker Compose (app + PostgreSQL) |
| **Timeline** | Weeks 2–8, with a deliverable every week |
| **Tests** | `pytest`, at least 60% overall coverage |
| **Ends with** | A live public URL, a 7–10 minute presentation and a 4–6 page final report |
| **Biggest marks** | SOLID principles in code (20%), repository & service layer (15%), testing (15%) |

---

## Objectives

By the end of this project you will be able to:

- Architect a clean, modular Python web application that follows the **SOLID principles**
- Apply **12-Factor App** practices for configuration, logging and environments
- Build a **RESTful API backend** with **FastAPI** or **Flask**
- Containerise your application with **Docker** and **Docker Compose**
- Write **unit and integration tests** with meaningful coverage
- Deploy your application to a cloud platform
- Document your architecture decisions and reflect on the engineering trade-offs

---

## Core Requirements

Every project **must** include:

| Requirement | Details |
|-------------|---------|
| Web framework | FastAPI (recommended) or Django or Flask |
| Database | PostgreSQL or SQLite (via SQLAlchemy ORM) |
| Containerisation | `Dockerfile` + `docker-compose.yml` |
| Configuration | Environment variables via `.env` (never hardcoded) |
| Testing | Unit tests with `pytest` (minimum 60% coverage) |
| Logging | Structured logging (no bare `print()` statements in production code) |
| Code quality | `ruff` or `flake8` linting, `black` formatting |
| Documentation | `README.md` with setup, architecture and API docs |

---

## SOLID Principles in Your Project

Your project must **visibly apply** all five SOLID principles. You'll be marked on how deliberately and correctly you use each one, not on whether the words appear in your code.

### S: Single Responsibility Principle

> *A class or module should have only one reason to change.*

Each module should own **one concern**. A route handler shouldn't also format data, validate input *and* write to the database. Split those jobs across layers:

```text
app/
├── api/routes/         # HTTP layer only: receives requests, returns responses
├── services/           # Business logic only: applies the domain rules
├── repositories/       # Data access only: talks to the database
├── models/             # Domain entities: data shapes and validation
└── core/               # App-wide concerns: config, logging, exceptions
```

### O: Open/Closed Principle

> *Software entities should be open for extension, but closed for modification.*

Design your core logic so you can add features **without editing existing code**. Abstract base classes, dependency injection and the strategy pattern all help here.

**Example:** a `NotificationService` that works with any `NotificationChannel` (email, SMS, webhook). Adding a new channel means writing a new class; the service itself never changes.


```python
from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> None: ...


class EmailChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> None:
        print(f"[email] to {recipient}: {message}")   # real code would send an email


class SMSChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> None:
        print(f"[sms] to {recipient}: {message}")     # real code would send an SMS


class NotificationService:
    def __init__(self, channel: NotificationChannel):
        self._channel = channel

    def notify(self, recipient: str, message: str) -> None:
        self._channel.send(recipient, message)


NotificationService(EmailChannel()).notify("asha@example.com", "Your order has shipped")
NotificationService(SMSChannel()).notify("+977-9800000000", "Your order has shipped")
```

    [email] to asha@example.com: Your order has shipped
    [sms] to +977-9800000000: Your order has shipped


### L: Liskov Substitution Principle

> *Subtypes must be substitutable for their base types without altering program correctness.*

If you use inheritance or abstract classes, every subclass must honour the full contract of its parent. A subclass should never **demand more** from its callers (stricter preconditions), **promise less** (weaker postconditions), or raise exceptions the parent wouldn't.

**What to watch for:** if you find yourself writing `if isinstance(obj, SubclassX)` inside shared logic, you're probably breaking LSP.

### I: Interface Segregation Principle

> *Clients should not be forced to depend on interfaces they do not use.*

Prefer several small, focused interfaces over one large "god" interface. If a class only needs to read from a repository, it should depend on something like `Readable`, not on a full CRUD repository.


```python
from typing import Protocol

class Readable(Protocol):
    def get(self, id: int): ...

class Writable(Protocol):
    def save(self, entity): ...
    def delete(self, id: int): ...

class ReadWriteRepository(Readable, Writable, Protocol): ...
```

### D: Dependency Inversion Principle

> *High-level modules should not depend on low-level modules. Both should depend on abstractions.*

Your service layer should **never import** a concrete database class directly. Pass dependencies in through the constructor or FastAPI's `Depends()` system.


```python
from typing import Protocol


class UserRepository(Protocol):            # the abstraction
    def get(self, user_id: int) -> dict: ...


class PostgresUserRepository:              # a concrete, low-level detail
    def get(self, user_id: int) -> dict:
        return {"id": user_id, "source": "postgres"}


# Bad: the high-level service creates its own low-level dependency
class UserServiceBad:
    def __init__(self):
        self.repo = PostgresUserRepository()   # tightly coupled


# Good: the service depends on the abstraction, injected from outside
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo


service = UserService(PostgresUserRepository())   # or a fake repo in your tests
print(service.repo.get(1))
```

    {'id': 1, 'source': 'postgres'}


---

## 12-Factor App Methodology

Your application must follow the [12-Factor App](https://12factor.net/) principles. Here's what each factor means for your project.

| Factor | What you must do |
|--------|------------------|
| **I. Codebase** | One Git repo, one app. No sharing code between apps by copy-paste. |
| **II. Dependencies** | Declare every dependency in `requirements.txt` or `pyproject.toml`. Assume nothing is pre-installed. |
| **III. Config** | Load all config (DB URLs, secrets, ports) from environment variables. Use `python-dotenv` locally. Never commit `.env`. |
| **IV. Backing Services** | Treat your database, cache or email provider as attached resources, swappable through config rather than code changes. |
| **V. Build, Release, Run** | The Dockerfile separates build from run. `docker compose` manages the release and run stages. |
| **VI. Processes** | Your app must be stateless. No in-memory session state; keep state in the database or cache. |
| **VII. Port Binding** | Your app exposes itself on a port (e.g. `8000`) set by an environment variable, not hardcoded. |
| **VIII. Concurrency** | Design so that several workers can run in parallel. Avoid global mutable state. |
| **IX. Disposability** | The app starts fast and shuts down gracefully. Handle `SIGTERM` for a clean shutdown. |
| **X. Dev/Prod Parity** | Docker Compose keeps local development close to production. No "works on my machine". |
| **XI. Logs** | Log to `stdout`/`stderr` as structured events (JSON preferred). Don't write log files yourself. |
| **XII. Admin Processes** | Run DB migrations as one-off tasks (e.g. `alembic upgrade head`), not as part of app startup. |

---

## Required Project Structure

Your repository **must** follow this structure. You may add to it, but don't remove any of the required parts.

```text
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

Your `Dockerfile` must use a **multi-stage build**, like this one:

```dockerfile
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

Your `docker-compose.yml` must define at least:

- an `app` service (your web application)
- a `db` service (PostgreSQL)
- proper use of `environment`, `depends_on`, `volumes` and `healthcheck`

---

## Configuration: The Right Way

Use **Pydantic `BaseSettings`** (from the `pydantic-settings` package) to load all configuration from environment variables:

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "My App"
    database_url: str
    secret_key: str
    debug: bool = False
    port: int = 8000


settings = Settings()
```

Your `.env.example` (committed) should list every variable with a placeholder value:

```text
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
SECRET_KEY=changeme
DEBUG=false
PORT=8000
```

Your `.env` (never committed) holds the real values for local development.

---

## Project Timeline

### Milestones at a Glance

| Week | Focus | Deliverables |
|------|-------|--------------|
| 2 | Architecture design & proposal | Architecture proposal (1–2 pages), ERD, endpoint design table |
| 3 | Literature & technical review | Technical review report (2–3 pages), annotated links to reviewed repos |
| 4 | Project scaffold & core models | Running Compose stack (app + db), one Alembic migration applied, `GET /health` |
| 5 | Repository & service layer | Working service + repository layer with tests, ≥ 50% coverage on the service layer |
| 6 | API layer & integration | All planned endpoints testable in Swagger UI/Postman, integration tests for ≥ 3 endpoints |
| 7 | Hardening, testing & documentation | HTML coverage report, clean linting output, complete `README.md` |
| 8 | Deployment, demo & submission | Live URL, final report (4–6 pages), slides, final GitHub repo |

The details for each week are below.

### Week 2: Architecture Design & Proposal

- Choose your project domain (see Sample Project Ideas below)
- Define your data models, API endpoints and service boundaries
- Sketch your layered architecture (routes → services → repositories)
- Identify which SOLID principles apply where

**Deliverables:**

- 1–2 page Architecture Proposal
- Entity-Relationship Diagram (ERD)
- Endpoint design table (method, path, description, auth required)

### Week 3: Literature & Technical Review

- Review 2–3 open-source Python web applications on GitHub
- Evaluate their architecture: Do they follow SRP? Are the services testable? Is config handled properly?
- Identify what you'll do differently or improve on

**Deliverables:**

- Technical Review Report (2–3 pages)
- Annotated links to the reviewed repositories, with critique notes

### Week 4: Project Scaffold & Core Models

- Initialise your repository with the required folder structure
- Set up `Dockerfile`, `docker-compose.yml` and `.env.example`
- Implement the domain models and ORM models
- Configure Alembic and create your first migration

**Deliverables:**

- Running Docker Compose stack (app + db)
- At least one Alembic migration applied
- `GET /health` endpoint returning `{"status": "ok"}`

### Week 5: Repository & Service Layer

- Implement an abstract base repository and at least one concrete repository
- Implement the service layer with dependency injection
- Write unit tests for the service layer using mock repositories
- Demonstrate the Dependency Inversion and Open/Closed principles in code

**Deliverables:**

- Working service + repository layer with tests
- Test coverage report showing ≥ 50% coverage on the service layer

### Week 6: API Layer & Integration

- Implement all API routes using FastAPI/Flask
- Connect routes → services → repositories through dependency injection
- Add request validation (Pydantic schemas)
- Add structured logging to all service operations

**Deliverables:**

- All planned endpoints implemented and testable by hand in Swagger UI or Postman
- Integration tests for at least 3 endpoints

### Week 7: Hardening, Testing & Documentation

- Reach ≥ 60% overall test coverage
- Add error handling (custom exceptions, correct HTTP status codes)
- Write your project's own `README.md`: setup guide, environment variables, how to run tests, API reference
- Run the linter (`ruff`/`flake8`) and formatter (`black`) with zero errors

**Deliverables:**

- Test coverage report (HTML output from `pytest --cov`)
- Clean linting output
- Complete project `README.md`

### Week 8: Deployment, Demo & Submission

- Deploy using one of: **Railway**, **Render**, **Fly.io** or **a VPS with Docker**
- The live application must be reachable at a public URL
- Present your application (7–10 minutes): demo, architecture walkthrough and reflection
- Submit the final report

**Deliverables:**

- Live deployment URL
- Final Project Report (4–6 pages), see the structure below
- Presentation slides
- Final GitHub repository (clean commit history, no secrets committed)

---

## Final Project Report Structure

Your report must cover:

1. **Project Overview**: What does your app do? Who is it for?
2. **Architecture Diagram**: A layered diagram showing routes, services, repositories and the DB
3. **SOLID Principles Applied**: One section per principle: where it appears, why you used it, what problem it solves
4. **12-Factor Compliance**: Which factors you implemented and how
5. **Testing Strategy**: What you tested, how, and your coverage results
6. **Deployment**: The platform you chose, the deployment steps, any challenges
7. **Reflection**: What you'd do differently, and what you learned

---

## Sample Project Ideas

Pick a domain that interests you. The technical requirements are the same whichever you choose.

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
|---------|-------------|
| Web framework | FastAPI (preferred), Flask |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Testing | pytest, pytest-cov, httpx (for FastAPI) |
| Mocking | pytest-mock, unittest.mock |
| Config | pydantic-settings, python-dotenv |
| Logging | Python `logging` module with a JSON formatter (`python-json-logger`) |
| Linting | ruff |
| Formatting | black |
| Containerisation | Docker, Docker Compose |
| API docs | Swagger UI (built into FastAPI), Postman |
| Deployment | Railway, Render, Fly.io |
| Diagramming | draw.io, Lucidchart, Mermaid (in Markdown) |

---

## Evaluation Criteria

| Component | Weight | Key Rubric Points |
|-----------|--------|-------------------|
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

- All code must be your own work.
- You may use libraries, documentation and AI tools as references, but you must be able to explain every line of your code.
- Copying code from other students or repositories without attribution is a violation of academic policy.
- If you use an AI coding assistant, say so in your report and describe how you used it.

---

## Frequently Asked Questions

**Can I use AI tools like Copilot or ChatGPT?**
Yes, as references. You must be able to explain every line, and you must mention the AI use in your report (see Academic Integrity above).

**Which database should I use?**
PostgreSQL or SQLite, through the SQLAlchemy ORM. Your `docker-compose.yml` must include a PostgreSQL `db` service.

**Do I commit my `.env` file?**
No. Commit `.env.example` with placeholder values; keep `.env` out of Git via `.gitignore`.

**What coverage do I need?**
At least 50% on the service layer by Week 5, and at least 60% overall by Week 7.

**Where can I deploy?**
Railway, Render, Fly.io or a VPS running Docker. The app must be reachable at a public URL.

**How long is the presentation?**
7–10 minutes: a demo, an architecture walkthrough and your reflection.

---

## Getting Started

Once you accept the GitHub Classroom assignment, clone your repository and get the stack running:

```bash
# Clone your repo
git clone https://github.com/your-org/your-repo.git
cd your-repo

# Copy the example env file, then edit .env with your local values
cp .env.example .env

# Build and start the stack
docker compose up --build

# In a separate terminal: run migrations
docker compose exec app alembic upgrade head

# Run tests
docker compose -f docker-compose.test.yml run --rm test
```

Your app will be at `http://localhost:8000`, and the API docs at `http://localhost:8000/docs`.

---

## Submission Checklist

Tick these off before your final submission in Week 8.

**Code & repository**

- [ ] Repository follows the required project structure
- [ ] All five SOLID principles applied deliberately (and explained in the report)
- [ ] Config loaded from environment variables; `.env.example` committed, `.env` not committed
- [ ] Structured logging, no bare `print()` in production code
- [ ] `ruff`/`flake8` and `black` run with zero errors
- [ ] Clean commit history with no secrets committed

**Containers & deployment**

- [ ] Multi-stage `Dockerfile`
- [ ] `docker-compose.yml` with `app` and `db` services, using `environment`, `depends_on`, `volumes` and `healthcheck`
- [ ] Alembic migrations run as a one-off task
- [ ] App deployed and reachable at a public URL

**Testing**

- [ ] Unit tests for the service layer using mock repositories
- [ ] Integration tests for at least 3 endpoints
- [ ] At least 60% overall coverage, with the HTML coverage report

**Documents**

- [ ] Project `README.md`: setup, environment variables, how to run tests, API reference
- [ ] Final report (4–6 pages) covering all seven sections
- [ ] Presentation slides for a 7–10 minute demo

---

> *Good engineers don't just write code that works. They write code that is readable, testable, maintainable and deployable by someone who has never met them.*
