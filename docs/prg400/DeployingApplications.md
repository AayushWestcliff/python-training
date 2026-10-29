# Deploying Applications

> *"An application isn't useful until someone can use it."*

---

### Learning Objectives

By the end of this notebook, you will be able to:

1.  **Explain** how HTTP and REST APIs work and how clients consume them
2.  **Build** a REST API with FastAPI backed by a SQLite database
3.  **Containerise** an application using Docker
4.  **Orchestrate** multiple services using Docker Compose
5.  **Configure** Nginx as a reverse proxy in front of a FastAPI application
6.  **Explain** how DNS A records point a domain name to a server IP

---

### Prerequisites

- Python 3.10+ installed
- Docker Desktop installed and running
- Basic terminal usage
- Familiarity with Python functions and classes

Install Python dependencies before starting Section 3:

```bash
pip install fastapi 'uvicorn[standard]' sqlalchemy
```

---

## Section 0 — What We're Building

By the end of this notebook, every request made by a browser or `curl` will travel through this stack:

```
Browser / curl
      |
      | HTTP  port 80
      v
  [ Nginx ]              <-- reverse proxy, handles incoming connections
      |
      | HTTP  port 8000 (internal Docker network)
      v
  [ FastAPI / uvicorn ]  <-- application server, runs your Python code
      |
      | SQL
      v
  [ SQLite ]             <-- file-based database, persisted as a Docker volume
```

### What Each Layer Does

| Layer | Tool | Responsibility |
|----|----|----|
| Reverse proxy | Nginx | Accepts public traffic, forwards to the app server |
| Application server | FastAPI + uvicorn | Handles business logic, validates input, queries DB |
| Database | SQLite | Stores and retrieves data persistently |
| Container runtime | Docker | Packages each service so it runs identically everywhere |
| Orchestration | Docker Compose | Starts all containers with correct wiring in one command |

### The Running Example: Task Manager API

We will build a REST API for managing tasks. Every section adds one layer to this same application until the full stack is running.

| Method  | Path                   | Action                   |
|---------|------------------------|--------------------------|
| `GET`   | `/tasks`               | List all tasks           |
| `POST`  | `/tasks`               | Create a new task        |
| `PATCH` | `/tasks/{id}/complete` | Mark a task as completed |

---

## Section 1 — REST APIs & HTTP

### What Is an API?

An **API** (Application Programming Interface) is a defined way for one program to communicate with another. A **web API** uses the HTTP protocol — the same protocol your browser uses to load web pages — as the communication channel.

When you open `https://weather.com`, your browser sends an HTTP request and receives an HTML page. When your Python code calls a weather API, it sends the same kind of HTTP request and receives JSON. The protocol is identical; only the response format differs.

### What Is REST?

**REST** (Representational State Transfer) is a set of conventions for designing web APIs:

- Resources are identified by URLs (`/tasks`, `/tasks/42`)
- The HTTP **method** expresses what action to take
- Responses use standard **status codes** to communicate the outcome
- Data is exchanged as **JSON**

An API that follows these conventions is called **RESTful**.

---

### HTTP Methods

| Method   | Meaning                     | Typical use              |
|----------|-----------------------------|--------------------------|
| `GET`    | Retrieve a resource         | List tasks, get one task |
| `POST`   | Create a new resource       | Add a task               |
| `PUT`    | Replace a resource entirely | Replace all task fields  |
| `PATCH`  | Update part of a resource   | Mark a task complete     |
| `DELETE` | Remove a resource           | Delete a task            |

---

### HTTP Status Codes

| Code | Meaning | When it happens |
|----|----|----|
| `200 OK` | Success | GET returned data |
| `201 Created` | Resource created | POST succeeded |
| `204 No Content` | Success, no response body | DELETE succeeded |
| `400 Bad Request` | Client sent invalid data | Missing required field |
| `404 Not Found` | Resource doesn't exist | Task ID not in database |
| `422 Unprocessable Entity` | Validation failed | Wrong data type in body |
| `500 Internal Server Error` | Server crashed | Bug in your code |

> **Rule of thumb:** 2xx = success, 4xx = the client's fault, 5xx = the server's fault.

---

### Anatomy of an HTTP Request and Response

```
REQUEST
--------
POST /tasks HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{"title": "Buy groceries"}


RESPONSE
--------
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 1, "title": "Buy groceries", "completed": false, "created_at": "2026-04-16T10:00:00"}
```

Every HTTP interaction follows this shape: **method + URL + headers + optional body** going out, **status code + headers + optional body** coming back.

---

## Section 2 — Browser Clients & Consuming APIs

### What Is a Client?

A **client** is anything that sends HTTP requests to an API. The API doesn't know or care what type of client is calling it — it only sees an HTTP request.

| Client                       | Typical use                                |
|------------------------------|--------------------------------------------|
| Web browser (via JavaScript) | Loads a web app; `fetch()` calls the API   |
| `curl`                       | Terminal tool for testing APIs manually    |
| Postman                      | GUI tool for building and testing requests |
| Python `requests` / `httpx`  | API calls from scripts and services        |
| Mobile app                   | iOS/Android apps calling a backend         |
| Another server               | Microservices calling each other           |

### How a Browser Consumes an API

When a web page needs data, JavaScript uses the `fetch` API:

```bash
// JavaScript running in the browser
const response = await fetch('http://localhost:8000/tasks');
const tasks = await response.json();
console.log(tasks);
// [{"id": 1, "title": "Buy groceries", "completed": false, ...}]
```

The browser sends an HTTP GET to your FastAPI server and receives JSON. Your Python code never knows whether the caller is a browser, a mobile app, or `curl`.

### Testing with `curl`

`curl` is the fastest way to test an API from the terminal:

```bash
# List all tasks
curl http://localhost:8000/tasks

# Create a new task
curl -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy groceries"}'

# Mark task 1 as completed
curl -X PATCH http://localhost:8000/tasks/1/complete
```

### FastAPI's Built-in Client: Swagger UI

FastAPI automatically generates interactive API documentation at `/docs`. You can send real HTTP requests directly from the browser — no `curl` or Postman required.

Once you start the server in Section 3, visit:

```
http://localhost:8000/docs
```

---

## Section 3 — FastAPI: First Endpoint

### What Is FastAPI?

**FastAPI** is a modern Python web framework for building APIs. Key properties:

- **Automatic validation** — uses Python type hints and Pydantic to validate all incoming data; returns a `422` with a clear message if the data is wrong
- **Auto-generated docs** — Swagger UI at `/docs` with zero extra code
- **Dependency injection** — clean way to share database sessions, auth, and other resources across routes
- **Fast** — one of the fastest Python frameworks, powered by Starlette and uvicorn

### Project Structure

Create this directory structure:

```
taskapi/
├── app/
│   └── main.py
└── requirements.txt
```

### Version 1: In-Memory Task List

Copy the code below into `taskapi/app/main.py`. This version stores tasks in a Python list. There is no database yet — restart the server and all tasks disappear. Section 4 fixes this.


```python
# taskapi/app/main.py  (version 1 — in-memory storage)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

app = FastAPI(title='Task Manager API')

# In-memory storage — replaced with SQLite in Section 4
tasks = []
_next_id = 1


class TaskCreate(BaseModel):
    title: str


class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    created_at: str


@app.get('/tasks', response_model=list[TaskResponse])
def list_tasks():
    return tasks


@app.post('/tasks', response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate):
    global _next_id
    new_task = {
        'id': _next_id,
        'title': task.title,
        'completed': False,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    tasks.append(new_task)
    _next_id += 1
    return new_task


@app.patch('/tasks/{task_id}/complete', response_model=TaskResponse)
def complete_task(task_id: int):
    for task in tasks:
        if task['id'] == task_id:
            task['completed'] = True
            return task
    raise HTTPException(status_code=404, detail='Task not found')
```

### Running the Application

From the `taskapi/` directory:

```bash
uvicorn app.main:app --reload
```

`--reload` restarts the server automatically when you save a file. Visit:

- `http://localhost:8000/tasks` — the raw JSON endpoint
- `http://localhost:8000/docs` — Swagger UI (try the endpoints interactively)

### Testing with curl

```bash
# Create two tasks
curl -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy groceries"}'

curl -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Write tests"}'

# List all tasks
curl http://localhost:8000/tasks

# Complete task 1
curl -X PATCH http://localhost:8000/tasks/1/complete
```

### How FastAPI Handles Validation

Send a bad request — omit the required `title` field:

```bash
curl -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{}'
```

FastAPI returns `422 Unprocessable Entity` with a detailed error — no extra validation code needed:

```json
{
  "detail": [{"loc": ["body", "title"], "msg": "field required", "type": "value_error.missing"}]
}
```

> **Note:** Restart the server and all tasks are gone — the list lives only in memory. Section 4 adds a real database.

---

## Section 4 — SQLite Database

### What Is SQLite?

**SQLite** is a file-based SQL database. The entire database is a single `.db` file — no separate server process, no configuration.

| Property | SQLite |
|----|----|
| Storage | One file (`tasks.db`) |
| Setup | None — works out of the box |
| Suitable for | Development, small-to-medium production apps, embedded systems |
| Not suitable for | High-concurrency write-heavy workloads |

SQLite is the right choice for this course project and for most applications that do not need horizontal scaling.

### SQLAlchemy

**SQLAlchemy** is Python's most widely used ORM (Object-Relational Mapper). It lets you define database tables as Python classes and write queries in Python rather than raw SQL.

```
Python class  ──────────►  database table
class Task        maps to    CREATE TABLE tasks (...)

Python object ──────────►  database row
task = Task(...)  maps to    INSERT INTO tasks ...
```

### Updated Project Structure

Add `database.py` alongside `main.py`:

```
taskapi/
├── app/
│   ├── main.py       <-- updated (connects to database)
│   └── database.py   <-- new (engine, session, ORM model)
└── requirements.txt
```

Copy `database.py` below into `taskapi/app/database.py`:


```python
# taskapi/app/database.py

import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./tasks.db')

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Yield a database session; close it when the request is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
```

Now replace `taskapi/app/main.py` with the version below. The three routes are identical — only the storage layer changes from a Python list to SQLAlchemy queries.


```python
# taskapi/app/main.py  (version 2 — SQLite backend)

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import Task, get_db, create_tables

app = FastAPI(title='Task Manager API')

create_tables()  # creates tasks.db and the tasks table on first run


class TaskCreate(BaseModel):
    title: str


class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    created_at: str


def _task_to_dict(task: Task) -> dict:
    return {
        'id': task.id,
        'title': task.title,
        'completed': task.completed,
        'created_at': task.created_at.isoformat(),
    }


@app.get('/tasks', response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return [_task_to_dict(t) for t in db.query(Task).all()]


@app.post('/tasks', response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(title=task.title)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return _task_to_dict(db_task)


@app.patch('/tasks/{task_id}/complete', response_model=TaskResponse)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    task.completed = True
    db.commit()
    db.refresh(task)
    return _task_to_dict(task)
```

### Running with the Database

```bash
cd taskapi/
uvicorn app.main:app --reload
```

`tasks.db` is created in the `taskapi/` directory the first time the app starts. Restart the server — your tasks are still there.

### Inspecting the Database Directly

```bash
sqlite3 tasks.db

sqlite> .tables
tasks

sqlite> SELECT * FROM tasks;
1|Buy groceries|0|2026-04-16 10:00:00.000000
2|Write tests|0|2026-04-16 10:01:00.000000

sqlite> .quit
```

### Key Concept: `Depends(get_db)`

`Depends(get_db)` is FastAPI's **dependency injection** system. For every incoming request:

1.  FastAPI calls `get_db()` to open a database session
2.  Passes the session to your route function as `db`
3.  After the response is sent, runs the `finally` block in `get_db()` to close the session

This happens automatically — your route function never manages the session lifecycle.

---

## Section 5 — Docker

### Containers vs Virtual Machines

The classic deployment problem: *"It works on my machine."*

A virtual machine solves this by bundling a full OS. A container is lighter — it shares the host OS kernel but packages your app and all its dependencies into an isolated, reproducible unit.

|  | Virtual Machine | Container |
|----|----|----|
| Includes | Full OS + app | App + dependencies only |
| Startup | Minutes | Seconds |
| Size | Gigabytes | Megabytes |
| Isolation | Separate kernel | Process-level (shared kernel) |
| Use case | Running different operating systems | Packaging and deploying apps |

### How Docker Works

```
Dockerfile           docker build          docker run
(instructions)  ──────────────►  Image  ──────────────►  Container
                               (snapshot)              (running instance)
```

- **Dockerfile** — instructions for building your image
- **Image** — an immutable snapshot (like a ZIP file of your app and its environment)
- **Container** — a running instance of an image

### Updated Project Structure

Add `Dockerfile` and `requirements.txt` to the `taskapi/` root:

```
taskapi/
├── app/
│   ├── main.py
│   └── database.py
├── Dockerfile        <-- new
└── requirements.txt  <-- new
```

### `requirements.txt`

Copy into `taskapi/requirements.txt`:

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
```

### `Dockerfile`

This uses a **multi-stage build**: the builder stage installs dependencies into a virtual environment; the runtime stage copies only what is needed, producing a lean final image with no build tools.

Copy into `taskapi/Dockerfile`:

```bash
# Stage 1: Builder — install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Runtime — lean final image, no build tools
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run as a non-root user — security best practice
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Commands

Run all commands from the `taskapi/` directory.

**Build the image:**

```bash
docker build -t taskapi .
```

**Run a container from the image:**

```bash
docker run -p 8000:8000 taskapi
```

`-p 8000:8000` maps port 8000 on your machine to port 8000 inside the container.

Visit `http://localhost:8000/tasks` — the app is now running inside a container.

**Other useful Docker commands:**

```bash
# List running containers
docker ps

# View container logs
docker logs <container-id>

# Open a shell inside a running container
docker exec -it <container-id> /bin/sh

# Stop a container
docker stop <container-id>

# List all images
docker images

# Remove an image
docker rmi taskapi
```

> **Note:** The SQLite database is created inside the container's filesystem. When the container is stopped and removed, the data is lost. Section 6 solves this with a Docker volume.

---

## Section 6 — Docker Compose

### What Is Docker Compose?

Docker Compose lets you define and run multiple containers together using a single YAML file. Instead of running a long `docker run` command with flags, you describe your services in `docker-compose.yml` and start everything with one command.

```
docker-compose.yml
       |
       v
 docker compose up --build
       |
       ├── starts container: app  (your FastAPI service)
       └── (more services added in Section 7)
```

### `docker-compose.yml` — Version 1

Add this file at `taskapi/docker-compose.yml`:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:////app/data/tasks.db
```

**What each field does:**

| Field | Purpose |
|----|----|
| `build: .` | Build the image from the Dockerfile in the current directory |
| `ports` | Map host port 8000 to container port 8000 |
| `volumes` | Mount `./data` on your machine to `/app/data` inside the container — the database file survives container restarts |
| `environment` | Set `DATABASE_URL` so the app writes `tasks.db` into the mounted volume |

> The four slashes in `sqlite:////app/data/tasks.db` are correct: `sqlite://` (scheme) + `//app/data/tasks.db` (absolute path).

### Docker Compose Commands

```bash
# Build images and start all services (runs in foreground)
docker compose up --build

# Run in the background
docker compose up --build -d

# View logs
docker compose logs -f

# Stop and remove containers
docker compose down

# Stop and also remove named volumes
docker compose down -v
```

Visit `http://localhost:8000/tasks` — same app, now with a persistent database.

---

## Section 7 — Nginx as Reverse Proxy

### What Is a Reverse Proxy?

A **reverse proxy** is a server that sits in front of your application and forwards incoming requests to it.

```
Without Nginx:
  Browser ──► FastAPI :8000

With Nginx:
  Browser ──► Nginx :80 ──► FastAPI :8000 (internal)
```

Why add this layer?

| Benefit | Explanation |
|----|----|
| Standard port | Users connect on port 80 (HTTP) or 443 (HTTPS) instead of `:8000` |
| SSL termination | Nginx handles HTTPS; your app only ever sees plain HTTP internally |
| Static files | Nginx serves static files (images, CSS) directly without hitting Python |
| Load balancing | Nginx can distribute traffic across multiple app instances |

For this course, we use Nginx purely as a reverse proxy on port 80.

### Updated Project Structure

```
taskapi/
├── app/
│   ├── main.py
│   └── database.py
├── nginx/
│   └── nginx.conf    <-- new
├── Dockerfile
├── docker-compose.yml  <-- updated
└── requirements.txt
```

### `nginx.conf`

Copy into `taskapi/nginx/nginx.conf`:

```bash
upstream taskapi {
    server app:8000;
}

server {
    listen 80;

    location / {
        proxy_pass         http://taskapi;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    }
}
```

**Key parts explained:**

| Directive | Meaning |
|----|----|
| `upstream taskapi` | Names the group of app servers to proxy to. `app` is the Docker Compose service name — Docker's internal DNS resolves it to the container's IP. |
| `listen 80` | Accept connections on port 80 |
| `proxy_pass http://taskapi` | Forward all requests to the upstream group |
| `proxy_set_header` | Pass the original client IP and host to the app so it can log them |

### `docker-compose.yml` — Version 2

Replace `taskapi/docker-compose.yml` with this version, which adds the `nginx` service:

```yaml
services:
  app:
    build: .
    expose:
      - "8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:////app/data/tasks.db

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - app
```

**What changed from version 1:**

| Change | Reason |
|----|----|
| `ports` → `expose` on app | The app is no longer directly reachable from outside; only Nginx talks to it |
| Added `nginx` service | Runs the official `nginx:alpine` image |
| `ports: 80:80` on nginx | Only Nginx is exposed to the outside world |
| `depends_on: app` | Docker Compose starts `app` before starting `nginx` |

### Testing Through Nginx

```bash
docker compose up --build

# Nginx is now on port 80 — no port number needed
curl http://localhost/tasks

curl -X POST http://localhost/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Test through Nginx"}'
```

---

## Section 8 — Putting It All Together

### Final Project Structure

```
taskapi/
├── app/
│   ├── main.py          # FastAPI routes, Pydantic models
│   └── database.py      # SQLAlchemy engine, session, ORM model
├── nginx/
│   └── nginx.conf       # Reverse proxy config
├── data/                # Created automatically; holds tasks.db
├── Dockerfile           # Multi-stage build for the FastAPI app
├── docker-compose.yml   # Orchestrates app + nginx
└── requirements.txt     # Python dependencies
```

### Starting the Full Stack From Scratch

```bash
cd taskapi/

# Build images and start both services
docker compose up --build
```

That's it. Docker Compose builds the FastAPI image, pulls the Nginx image, creates the network, mounts volumes, and starts both containers.

### Request Trace: What Happens When You Call `curl http://localhost/tasks`

```
1. curl sends:  GET /tasks HTTP/1.1  to  127.0.0.1:80

2. Nginx receives the request on port 80
   Reads nginx.conf: location / → proxy_pass http://taskapi
   Forwards:  GET /tasks HTTP/1.1  to  app:8000  (Docker internal DNS)

3. FastAPI (uvicorn) receives the request on port 8000
   Matches route:  @app.get('/tasks')
   Opens a SQLAlchemy session via Depends(get_db)
   Queries:  SELECT * FROM tasks
   Returns JSON response with status 200

4. Nginx receives the JSON response from FastAPI
   Forwards it back to curl unchanged

5. curl prints the JSON
```

### Component Responsibilities Summary

| Question | Answer |
|----|----|
| Who accepts the public connection? | Nginx |
| Who runs the Python code? | uvicorn (inside the FastAPI container) |
| Who validates the request body? | FastAPI + Pydantic |
| Who talks to the database? | SQLAlchemy (inside the FastAPI container) |
| Who persists data across restarts? | Docker volume mounted to `./data` |
| Who wires everything together? | Docker Compose |

---

## Section 9 — DNS & Domain Names

### What Is DNS?

Every server on the internet has an **IP address** — a numeric identifier like `203.0.113.42`. DNS (Domain Name System) is the internet's naming system: it translates human-readable domain names like `tasks.example.com` into IP addresses that computers can connect to.

Without DNS, you would need to type `http://203.0.113.42/tasks` instead of `http://tasks.example.com/tasks`.

### How DNS Resolution Works

When you type `tasks.example.com` into a browser, this happens:

```
Browser
  |
  | 1. Check browser cache (visited recently?)
  v
Operating System
  |
  | 2. Check OS cache / /etc/hosts
  v
Recursive Resolver  (provided by your ISP or 8.8.8.8)
  |
  | 3. Ask: who handles .com?
  v
Root Name Server
  |
  | 4. Returns: TLD server for .com
  v
TLD Name Server  (.com)
  |
  | 5. Returns: authoritative NS for example.com
  v
Authoritative Name Server  (your DNS provider)
  |
  | 6. Returns: tasks.example.com → 203.0.113.42
  v
Browser connects to 203.0.113.42:80
```

The result is **cached** at each level so this lookup only happens once (until the TTL expires).

### A Records

An **A record** (Address record) maps a hostname to an IPv4 address. It is the most fundamental DNS record type.

| Type | Name                | Value          | TTL    |
|------|---------------------|----------------|--------|
| A    | `tasks.example.com` | `203.0.113.42` | `3600` |
| A    | `www.example.com`   | `203.0.113.42` | `3600` |
| A    | `example.com`       | `203.0.113.42` | `3600` |

**TTL** (Time To Live) is how long resolvers cache this record, in seconds. `3600` = 1 hour. Lower TTL means faster propagation of changes; higher TTL means fewer DNS lookups.

### Other Common Record Types

| Type | Purpose | Example |
|----|----|----|
| `A` | Maps hostname → IPv4 address | `tasks.example.com → 203.0.113.42` |
| `AAAA` | Maps hostname → IPv6 address | `tasks.example.com → 2001:db8::1` |
| `CNAME` | Alias — maps hostname → another hostname | `www.example.com → example.com` |
| `MX` | Mail server for a domain | `example.com → mail.example.com` |
| `TXT` | Arbitrary text (used for domain verification, SPF) | `"v=spf1 include:..."` |

### DNS Zone File (What It Looks Like)

A DNS zone file is the authoritative record for a domain. Most DNS providers hide this behind a GUI, but the underlying format looks like this:

```
; Zone file for example.com
$TTL 3600

@   IN  A     203.0.113.42      ; example.com → server IP
www IN  A     203.0.113.42      ; www.example.com → server IP
tasks IN A    203.0.113.42      ; tasks.example.com → server IP
```

### Pointing a Domain to Your Server: Step by Step

1.  **Buy a domain** from a registrar (Namecheap, GoDaddy, Google Domains, etc.)
2.  **Find your server's IP address** — this is the public IP of the machine running Docker
3.  **Log in to your DNS provider** (often the same as your registrar, or Cloudflare)
4.  **Add an A record:**
5.  Name: `tasks` (or `@` for the root domain)
6.  Type: `A`
7.  Value: `203.0.113.42` (your server's IP)
8.  TTL: `3600`
9.  **Wait for propagation** — changes typically take 1–30 minutes (up to 48 hours if old records were cached with high TTLs)

### How This Connects to Our Stack

Once DNS is configured:

```
Browser types:   http://tasks.example.com
                        |
                        | DNS resolves tasks.example.com → 203.0.113.42
                        v
              Your server at 203.0.113.42
                        |
                        | port 80
                        v
                    [ Nginx ]          <-- receives the request
                        |
                        v
                    [ FastAPI ]        <-- processes it
                        |
                        v
                    [ SQLite ]         <-- queries the database
```

Nginx is what listens on port 80. The moment DNS resolves your domain name to the server IP, real HTTP traffic starts flowing through the exact stack you built in this notebook.

> **HTTPS:** For production, you would configure Nginx to also listen on port 443 and obtain an SSL certificate (e.g., via Let's Encrypt / Certbot). That adds TLS termination at the Nginx layer — the rest of the stack remains unchanged.

---

## Section 10 — Challenge

Extend the Task Manager API with a **delete endpoint**.

### Requirements

1.  Add `DELETE /tasks/{id}` to `app/main.py`
2.  Return `204 No Content` on success (no response body)
3.  Return `404 Not Found` if the task does not exist
4.  Rebuild the Docker image and bring the stack back up
5.  Verify with `curl`:

```bash
# Create a task
curl -X POST http://localhost/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Delete me"}'

# Delete task 1
curl -X DELETE http://localhost/tasks/1

# Confirm it is gone
curl http://localhost/tasks
```

---

<details>
<summary>Solution</summary>

Add this route to `app/main.py`:


```python
@app.delete('/tasks/{task_id}', status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    db.delete(task)
    db.commit()
```


Rebuild and restart:


```bash
docker compose up --build
```

</details>

---

## Summary

| Concept | Key Takeaway |
|----|----|
| **REST / HTTP** | Standard methods + status codes + JSON form the language of web APIs |
| **FastAPI** | Type hints + Pydantic give you validation and docs for free |
| **SQLAlchemy** | Maps Python classes to database tables; `Depends(get_db)` manages sessions |
| **Docker** | Packages your app and its environment into a portable, reproducible image |
| **Docker Compose** | One YAML file orchestrates multiple containers with correct wiring |
| **Nginx** | Sits in front of your app; handles port 80, connection management, and later SSL |
| **DNS / A records** | Maps a human domain name to your server's IP address |

### Further Reading

- [FastAPI documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Docker getting started guide](https://docs.docker.com/get-started/)
- [Nginx reverse proxy guide](https://nginx.org/en/docs/beginners_guide.html)
- [12-Factor App](https://12factor.net) — principles behind production-grade applications
