# Deploying Applications

Writing an app is only half the job; someone has to be able to reach it. In this lab we build a small Task Manager API with FastAPI and SQLite, package it with Docker, run it behind Nginx with Docker Compose, and finish by looking at how a domain name gets pointed at the server.

### Learning Objectives

By the end of this notebook you will be able to:

1. Explain how HTTP and REST APIs work and how clients use them
2. Build a REST API with FastAPI, backed by a SQLite database
3. Package an application into a Docker image
4. Run several services together with Docker Compose
5. Put Nginx in front of a FastAPI app as a reverse proxy
6. Explain how a DNS A record points a domain name at a server

### Prerequisites

- Python 3.10 or newer
- Docker Desktop installed and running (check with `docker --version`)
- Basic terminal use
- Comfortable with Python functions and classes

Install the Python packages before you start Section 3:

```bash
pip install fastapi 'uvicorn[standard]' sqlalchemy
```

### How to Use This Notebook

- Sections 1 and 2 are background. From Section 3 on it's a **step-by-step lab**: work through the numbered steps in order, because each one builds on the last.
- Cells that start with `%%writefile` save a file for you when you run them (into a `taskapi/` folder next to this notebook). For the other files (`Dockerfile`, `nginx.conf`, ...) create the file in your editor and paste in the contents shown.
- Commands in `bash` blocks are for your **terminal**, run from inside the `taskapi/` folder unless the step says otherwise.
- After the important steps there's a **Checkpoint** telling you what you should see. If you don't see it, fix that step before moving on.
- Try the practice tasks and the challenge yourself before opening *Show solution*. Each section ends with a **Quick recap** for revision.

---

## The Big Picture: What We're Building

By the end of the lab, every request from a browser or `curl` travels through this stack:

```text
Browser / curl
      |
      | HTTP, port 80
      v
  [ Nginx ]              <-- reverse proxy, accepts incoming connections
      |
      | HTTP, port 8000 (internal Docker network)
      v
  [ FastAPI / uvicorn ]  <-- application server, runs your Python code
      |
      | SQL
      v
  [ SQLite ]             <-- file-based database, kept in a Docker volume
```

### What Each Layer Does

| Layer | Tool | Job |
|----|----|----|
| Reverse proxy | Nginx | Accepts public traffic and forwards it to the app server |
| Application server | FastAPI + uvicorn | Runs the business logic, validates input, queries the database |
| Database | SQLite | Stores the data so it survives restarts |
| Container runtime | Docker | Packages each service so it runs the same everywhere |
| Orchestration | Docker Compose | Starts all the containers, wired together, with one command |

### The Running Example: a Task Manager API

We build one REST API for managing tasks. Each section adds one layer to the same app until the full stack is running.

| Method | Path | Action |
|---------|------------------------|--------------------------|
| `GET` | `/tasks` | List all tasks |
| `POST` | `/tasks` | Create a new task |
| `PATCH` | `/tasks/{id}/complete` | Mark a task as completed |

---

## 1. REST APIs and HTTP

### What Is an API?

An **API** (Application Programming Interface) is an agreed way for one program to talk to another. A **web API** uses HTTP, the same protocol your browser uses to load web pages.

When you open `https://weather.com`, your browser sends an HTTP request and gets back an HTML page. When your Python code calls a weather API, it sends the same kind of request and gets back JSON. Same protocol, different response format.

### What Is REST?

**REST** (Representational State Transfer) is a set of conventions for designing web APIs:

- Each resource has a URL (`/tasks`, `/tasks/42`).
- The HTTP **method** says what you want to do with it.
- The response's **status code** says how it went.
- Data goes back and forth as **JSON**.

An API that follows these conventions is called **RESTful**.

### HTTP Methods

| Method | Meaning | Typical use |
|----------|-----------------------------|--------------------------|
| `GET` | Read a resource | List tasks, get one task |
| `POST` | Create a new resource | Add a task |
| `PUT` | Replace a resource completely | Replace all of a task's fields |
| `PATCH` | Update part of a resource | Mark a task complete |
| `DELETE` | Remove a resource | Delete a task |

### HTTP Status Codes

| Code | Meaning | When it happens |
|----|----|----|
| `200 OK` | Success | A GET returned data |
| `201 Created` | Resource created | A POST succeeded |
| `204 No Content` | Success, no response body | A DELETE succeeded |
| `400 Bad Request` | The server won't accept the request | e.g. a business rule fails, like a duplicate username |
| `404 Not Found` | The resource doesn't exist | Task ID not in the database |
| `422 Unprocessable Entity` | Validation failed | Missing field or wrong type in the body (FastAPI's default for bad input) |
| `500 Internal Server Error` | The server crashed | A bug in your code |

**Rule of thumb:** 2xx means success, 4xx means the client got something wrong, 5xx means the server got something wrong.

### What a Request and Response Look Like

```http
POST /tasks HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{"title": "Buy groceries"}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 1, "title": "Buy groceries", "completed": false, "created_at": "2026-04-16T10:00:00"}
```

Every HTTP exchange has this shape. Going out: **method + URL + headers + optional body**. Coming back: **status code + headers + optional body**.

**Quick recap**

- A web API lets programs talk over HTTP, usually exchanging JSON.
- REST: URLs name resources, methods (GET/POST/PATCH/DELETE) say what to do.
- Status codes: 2xx success, 4xx client error, 5xx server error.

---

## 2. Clients: Who Calls Your API?

A **client** is anything that sends HTTP requests to your API. The API doesn't know or care what kind of client it is; it only sees the request.

| Client | Typical use |
|------------------------------|--------------------------------------------|
| Web browser (JavaScript) | A web page calls the API with `fetch()` |
| `curl` | Testing APIs by hand in the terminal |
| Postman | GUI tool for building and testing requests |
| Python `requests` / `httpx` | Calling APIs from scripts and other services |
| Mobile app | iOS/Android apps talking to their backend |
| Another server | Microservices calling each other |

### How a Browser Uses an API

When a web page needs data, its JavaScript calls `fetch`:

```javascript
// JavaScript running in the browser
const response = await fetch('http://localhost:8000/tasks');
const tasks = await response.json();
console.log(tasks);
// [{"id": 1, "title": "Buy groceries", "completed": false, ...}]
```

The browser sends a GET request to your FastAPI server and gets JSON back. Your Python code can't tell whether the caller was a browser, a mobile app or `curl`.

One catch: if the web page comes from a *different* address than the API (say `localhost:3000` calling `localhost:8000`), the browser blocks the response unless the API allows it with **CORS** headers. FastAPI has a `CORSMiddleware` for this. We won't need it here, but it's the first thing to check when `fetch` fails in the browser and `curl` works fine.

### Testing with `curl`

`curl` is the quickest way to try an API from the terminal. Here's a preview of the commands we'll use once the server is running:

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

**Windows users:** the single quotes and `\` line breaks above work in Git Bash and WSL, but not in Command Prompt or PowerShell. Use Git Bash, or use the Swagger UI described next.

### FastAPI's Built-in Client: Swagger UI

FastAPI automatically builds interactive documentation at `/docs`. You can send real requests straight from the browser, with no `curl` or Postman needed. Once the server is running (Section 3), open:

```text
http://localhost:8000/docs
```

**Quick recap**

- Any program that sends HTTP requests is a client: browsers, `curl`, Postman, Python scripts, apps.
- Browsers call APIs with `fetch()`; a different origin needs CORS on the API side.
- `curl` and Swagger UI (`/docs`) are the two quickest ways to test your API.

---

## 3. FastAPI: Your First Endpoints

### What Is FastAPI?

**FastAPI** is a modern Python framework for building APIs. What makes it nice to work with:

- **Automatic validation.** It uses your type hints (through Pydantic) to check incoming data, and replies with a `422` and a clear message when the data is wrong.
- **Free documentation.** Swagger UI at `/docs`, with no extra code.
- **Dependency injection.** A clean way to share things like database sessions across routes.
- **Speed.** It's one of the fastest Python frameworks, built on Starlette and uvicorn.

### Step 1: Create the Project Folder

We'll end up with this structure (more files get added in later sections):

```text
taskapi/
└── app/
    └── main.py
```

Run the cell below to create the folders, or create them yourself in your editor.


```python
from pathlib import Path

Path("taskapi/app").mkdir(parents=True, exist_ok=True)
print("Created taskapi/app/")
```

    Created taskapi/app/


### Step 2: Write `main.py` (Version 1, In-Memory)

This first version keeps tasks in a plain Python list. There's no database yet, so restarting the server wipes everything. Section 4 fixes that.

Run the cell to save it as `taskapi/app/main.py`.


```python
%%writefile taskapi/app/main.py
# taskapi/app/main.py  (version 1: in-memory storage)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

app = FastAPI(title='Task Manager API')

# In-memory storage. Replaced with SQLite in Section 4.
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

    Overwriting taskapi/app/main.py


**What just happened?** We saved the file; nothing is running yet. A few things to notice in the code:

- `TaskCreate` describes what a client must **send** (just a `title`). `TaskResponse` describes what we **send back**.
- `@app.post('/tasks', ..., status_code=201)` connects a URL and method to a function and sets the success code.
- `task_id: int` in the PATCH route is read from the URL, and FastAPI converts it to an `int` for us.
- `raise HTTPException(status_code=404, ...)` is how you return an error.

### Step 3: Start the Server

In a terminal, go into the `taskapi/` folder and run:

```bash
uvicorn app.main:app --reload
```

`app.main:app` means "in the module `app/main.py`, use the object called `app`". The `--reload` flag restarts the server whenever you save a file.

**Checkpoint:** the terminal shows `Uvicorn running on http://127.0.0.1:8000`. Opening `http://localhost:8000/tasks` in a browser shows `[]` (an empty list), and `http://localhost:8000/docs` shows the Swagger UI.

Leave the server running and open a **second** terminal for the next step.

### Step 4: Try It with `curl`

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

**Checkpoint:** the list shows two tasks with ids `1` and `2`, and after the PATCH, task 1 comes back with `"completed": true`. Try `curl -X PATCH http://localhost:8000/tasks/99/complete` too: you should get `{"detail":"Task not found"}`.

### Step 5: See Validation in Action

Send a bad request that leaves out the required `title`:

```bash
curl -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{}'
```

FastAPI replies with `422 Unprocessable Entity` and explains exactly what's wrong. We didn't write any validation code for this:

```json
{
  "detail": [
    {"type": "missing", "loc": ["body", "title"], "msg": "Field required", "input": {}}
  ]
}
```

`loc` tells you where the problem is (the `title` field in the request body).

Now stop the server (`Ctrl+C`) and start it again. Run `curl http://localhost:8000/tasks`: the list is empty again, because the tasks only lived in memory.

**Quick recap**

- A FastAPI route is a function with a decorator like `@app.get('/tasks')`.
- Pydantic models (`TaskCreate`, `TaskResponse`) define what comes in and goes out; bad input gets a `422`.
- `uvicorn app.main:app --reload` runs the app; `/docs` gives you a free test UI.
- In-memory data disappears on every restart, so we need a database.

---

## 4. Adding a SQLite Database

### What Is SQLite?

**SQLite** is a SQL database that lives in a single file. There's no separate database server to install or configure.

| Property | SQLite |
|----|----|
| Storage | One file (`tasks.db`) |
| Setup | None, it works out of the box (it's built into Python) |
| Good for | Development, small-to-medium apps, embedded systems |
| Not good for | Lots of users writing at the same time |

It's a good fit for this course project and for many apps that never need more than one server.

### SQLAlchemy

**SQLAlchemy** is the most widely used ORM (Object-Relational Mapper) for Python. You describe tables as Python classes and write queries in Python instead of raw SQL:

```text
Python class   ---->  database table
class Task      maps to   CREATE TABLE tasks (...)

Python object  ---->  database row
Task(...)       maps to   INSERT INTO tasks ...
```

We'll add one new file, `database.py`, next to `main.py`:

```text
taskapi/
└── app/
    ├── main.py       <-- updated (uses the database)
    └── database.py   <-- new (engine, session, ORM model)
```

### Step 6: Write `database.py`


```python
%%writefile taskapi/app/database.py
# taskapi/app/database.py

import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./tasks.db')

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)


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

    Overwriting taskapi/app/database.py


**What just happened?** This file sets up three things:

- `engine` is the connection to the database. The URL comes from the `DATABASE_URL` environment variable, or falls back to `sqlite:///./tasks.db` (a file called `tasks.db` in the current folder). We'll use that environment variable later with Docker.
- `SessionLocal` creates **sessions**, which are like a conversation with the database for one request.
- `Task` is the table: each class attribute becomes a column.

`check_same_thread=False` is a SQLite-only setting. FastAPI may handle one request across different threads, and SQLite blocks that by default.

### Step 7: Update `main.py` (Version 2, SQLite)

Replace `main.py` with the version below. The three routes do exactly the same job as before; only the storage changes from a Python list to SQLAlchemy queries.


```python
%%writefile taskapi/app/main.py
# taskapi/app/main.py  (version 2: SQLite backend)

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

    Overwriting taskapi/app/main.py


### Step 8: Run It and Check the Data Survives

```bash
cd taskapi/
uvicorn app.main:app --reload
```

The first time the app starts, it creates `tasks.db` in the `taskapi/` folder. Create a couple of tasks with the `curl` commands from Step 4, then stop and restart the server.

**Checkpoint:** after the restart, `curl http://localhost:8000/tasks` still shows your tasks.

### Looking Inside the Database

If you have the `sqlite3` command-line tool installed, you can look at the file directly:

```bash
sqlite3 tasks.db

sqlite> .tables
tasks

sqlite> SELECT * FROM tasks;
1|Buy groceries|0|2026-04-16 10:00:00.000000
2|Write tests|0|2026-04-16 10:01:00.000000

sqlite> .quit
```

SQLite stores `True`/`False` as `1`/`0`.

### How `Depends(get_db)` Works

`Depends(get_db)` is FastAPI's **dependency injection**. For every request:

1. FastAPI calls `get_db()`, which opens a database session.
2. It passes that session into your route function as `db`.
3. After the response is sent, it runs the `finally` block in `get_db()`, which closes the session.

Your route functions never have to open or close sessions themselves.

**Quick recap**

- SQLite is a whole database in one file; SQLAlchemy lets you use it through Python classes.
- `DATABASE_URL` comes from an environment variable, with a local `tasks.db` as the default.
- `Depends(get_db)` gives each request its own session and closes it afterwards.
- Data now survives a server restart.

---

## 5. Docker

### Containers vs Virtual Machines

The classic deployment problem: *"It works on my machine."*

A virtual machine solves this by shipping a whole operating system. A container is lighter: it shares the host's OS kernel but packages your app and everything it needs into an isolated unit that runs the same everywhere.

| | Virtual Machine | Container |
|----|----|----|
| Includes | Full OS + app | App + dependencies only |
| Starts in | Minutes | Seconds |
| Size | Gigabytes | Megabytes |
| Isolation | Separate kernel | Separate process (shared kernel) |
| Use case | Running a different operating system | Packaging and deploying apps |

### How Docker Works

```text
Dockerfile      docker build              docker run
(recipe)     --------------->  Image  --------------->  Container
                             (snapshot)               (running instance)
```

- **Dockerfile**: the recipe for building an image.
- **Image**: a read-only snapshot of your app and its environment. Think of it as a ZIP file you can run.
- **Container**: a running copy of an image. You can start many containers from one image.

We'll add two files to the project root:

```text
taskapi/
├── app/
│   ├── main.py
│   └── database.py
├── Dockerfile        <-- new
└── requirements.txt  <-- new
```

### Step 9: Create `requirements.txt`

This lists the exact package versions the container will install. Create `taskapi/requirements.txt`:

```text
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
```

Pinning exact versions (`==`) means the image you build next month gets the same packages as the one you build today.

### Step 10: Create the `Dockerfile`

This Dockerfile uses a **multi-stage build**. The first stage (`builder`) installs the dependencies into a virtual environment. The second stage (`runtime`) copies only that environment and your code, so the final image doesn't carry any build leftovers.

Create `taskapi/Dockerfile` (no file extension):

```dockerfile
# Stage 1: builder - install dependencies into a virtual environment
FROM python:3.12-slim AS builder

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: runtime - lean final image, no build tools
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run as a non-root user (security best practice).
# The user needs a folder it can write the database into.
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/data \
    && chown appuser /app/data
ENV DATABASE_URL=sqlite:////app/data/tasks.db
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**What's going on in the last few lines?** The app runs as an ordinary user called `appuser`, not as `root`, so a bug in the app can't take over the whole container. But an ordinary user can't write into `/app`, which belongs to root. So we create `/app/data`, hand it to `appuser`, and point `DATABASE_URL` at it. Without this, the app would crash on start-up with `unable to open database file`.

### Step 11: Build the Image and Run a Container

Run these from the `taskapi/` folder. Stop the uvicorn server from Step 8 first, because both use port 8000.

Build the image (the `.` means "use the Dockerfile in this folder"):

```bash
docker build -t taskapi .
```

Run a container from it:

```bash
docker run -p 8000:8000 taskapi
```

`-p 8000:8000` connects port 8000 on your machine to port 8000 inside the container.

**Checkpoint:** the build finishes without errors, the container prints `Uvicorn running on http://0.0.0.0:8000`, and `curl http://localhost:8000/tasks` returns `[]`. The app is now running inside a container. (It's an empty list because the container has its own fresh database.)

### Other Useful Docker Commands

```bash
docker ps                          # list running containers
docker logs <container-id>         # show a container's output
docker exec -it <container-id> sh  # open a shell inside a running container
docker stop <container-id>         # stop a container
docker images                      # list images
docker rmi taskapi                 # remove the image
```

Note that the database file lives inside the container's own filesystem. If you remove the container, the data goes with it. Section 6 fixes this with a Docker volume.

**Quick recap**

- An image is a snapshot built from a Dockerfile; a container is a running copy of an image.
- A multi-stage build keeps the final image small.
- Run as a non-root user, and give that user a folder it can write to.
- `docker build -t name .` builds, `docker run -p host:container name` runs.

---

## 6. Docker Compose

### What Is Docker Compose?

Docker Compose lets you describe one or more containers in a YAML file and start them all with one command. Instead of remembering a long `docker run` command full of flags, you write the settings down once in `docker-compose.yml`.

```text
docker-compose.yml
       |
       v
 docker compose up --build
       |
       ├── starts container: app  (your FastAPI service)
       └── (an nginx container joins it in Section 7)
```

### Step 12: Create `docker-compose.yml` (Version 1)

Create `taskapi/docker-compose.yml`:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - taskdata:/app/data
    environment:
      - DATABASE_URL=sqlite:////app/data/tasks.db

volumes:
  taskdata:
```

What each part does:

| Field | Purpose |
|----|----|
| `build: .` | Build the image from the Dockerfile in this folder |
| `ports` | Connect port 8000 on your machine to port 8000 in the container |
| `volumes` | Store `/app/data` in a Docker **volume** called `taskdata`, so `tasks.db` survives when the container is removed |
| `environment` | Set `DATABASE_URL` so the app writes `tasks.db` into that volume |
| top-level `volumes:` | Declares the `taskdata` volume |

The four slashes in `sqlite:////app/data/tasks.db` are correct: `sqlite:///` is the start of the URL, and `/app/data/tasks.db` is an absolute path.

**Why a named volume and not a folder on your machine?** You'll often see `./data:/app/data` instead, which uses a folder on your computer. That works on Docker Desktop, but on a Linux server the folder is created as `root` and our non-root `appuser` can't write to it. A named volume avoids that problem everywhere.

### Step 13: Start the Stack

```bash
docker compose up --build
```

**Checkpoint:** create a task with `curl` (Step 4 commands), then stop everything with `Ctrl+C` followed by `docker compose down`. Run `docker compose up` again and list the tasks: your task is still there, because it lives in the `taskdata` volume.

To peek at the database inside the running container (the slim image has no `sqlite3` tool, but it has Python):

```bash
docker compose exec app python -c "import sqlite3; print(sqlite3.connect('/app/data/tasks.db').execute('SELECT * FROM tasks').fetchall())"
```

### Docker Compose Commands

```bash
docker compose up --build      # build images and start everything (in the foreground)
docker compose up --build -d   # same, but in the background
docker compose logs -f         # follow the logs
docker compose down            # stop and remove the containers (volumes are kept)
docker compose down -v         # ...and delete the volumes too (this deletes your data!)
```

**Quick recap**

- `docker-compose.yml` describes your containers; `docker compose up --build` starts them.
- A named volume keeps `tasks.db` safe when containers are removed.
- `docker compose down` keeps your data; `docker compose down -v` deletes it.

---

## 7. Nginx as a Reverse Proxy

### What Is a Reverse Proxy?

A **reverse proxy** is a server that sits in front of your app and passes incoming requests on to it.

```text
Without Nginx:
  Browser --> FastAPI :8000

With Nginx:
  Browser --> Nginx :80 --> FastAPI :8000 (internal only)
```

Why add another layer?

| Benefit | Explanation |
|----|----|
| Standard ports | Users connect on port 80 (HTTP) or 443 (HTTPS) instead of `:8000` |
| HTTPS | Nginx handles the encryption; your app only ever sees plain HTTP inside |
| Static files | Nginx serves images and CSS directly, without bothering Python |
| Load balancing | Nginx can share traffic between several copies of your app |

In this course we only use the first one: Nginx as a reverse proxy on port 80.

The project gets a new folder:

```text
taskapi/
├── app/
│   ├── main.py
│   └── database.py
├── nginx/
│   └── nginx.conf      <-- new
├── Dockerfile
├── docker-compose.yml  <-- updated
└── requirements.txt
```

### Step 14: Create `nginx/nginx.conf`

Create the folder `taskapi/nginx/` and the file `taskapi/nginx/nginx.conf`:

```nginx
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

| Directive | Meaning |
|----|----|
| `upstream taskapi` | Names the group of app servers to forward to. `app` is the service name from `docker-compose.yml`; Docker's built-in DNS turns it into the container's IP address. |
| `listen 80` | Accept connections on port 80 |
| `proxy_pass http://taskapi` | Forward every request to the `taskapi` upstream |
| `proxy_set_header` | Pass along the original host and client IP so the app can log them |

### Step 15: Update `docker-compose.yml` (Version 2)

Replace `taskapi/docker-compose.yml` with this version, which adds the `nginx` service:

```yaml
services:
  app:
    build: .
    expose:
      - "8000"
    volumes:
      - taskdata:/app/data
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

volumes:
  taskdata:
```

What changed from version 1:

| Change | Reason |
|----|----|
| `ports` became `expose` on `app` | The app is no longer reachable from outside; only Nginx can talk to it |
| New `nginx` service | Runs the official `nginx:alpine` image |
| `ports: "80:80"` on `nginx` | Nginx is now the only way in |
| Our config mounted into Nginx | Replaces Nginx's default site with our `nginx.conf` |
| `depends_on: app` | Compose starts `app` before `nginx` |

### Step 16: Test Through Nginx

```bash
docker compose up --build
```

In a second terminal (note: no port number, because port 80 is the default for HTTP):

```bash
curl http://localhost/tasks

curl -X POST http://localhost/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Test through Nginx"}'
```

**Checkpoint:** both commands work, and the task you created in Step 13 is still in the list (same volume). Run `curl -i http://localhost/tasks` to see the response headers: there's a `Server: nginx/...` line, which proves the request went through Nginx. And `curl http://localhost:8000/tasks` should now **fail**, because the app is no longer exposed directly.

If port 80 is already in use on your machine, change `"80:80"` to `"8080:80"` and use `http://localhost:8080` instead.

**Quick recap**

- A reverse proxy accepts public traffic and forwards it to your app.
- In Compose, services find each other by name (`server app:8000`).
- `expose` keeps the app internal; only Nginx publishes a port (`80:80`).

---

## 8. Putting It All Together

### Final Project Structure

```text
taskapi/
├── app/
│   ├── main.py          # FastAPI routes, Pydantic models
│   └── database.py      # SQLAlchemy engine, session, ORM model
├── nginx/
│   └── nginx.conf       # reverse proxy config
├── Dockerfile           # multi-stage build for the FastAPI app
├── docker-compose.yml   # runs app + nginx, declares the taskdata volume
└── requirements.txt     # pinned Python dependencies
```

(The `tasks.db` file from Step 8 may also be sitting in `taskapi/`. It's only used when you run uvicorn directly; the containers use the `taskdata` volume.)

### Starting the Full Stack From Scratch

```bash
cd taskapi/
docker compose up --build
```

That one command builds the FastAPI image, pulls the Nginx image, creates a private network and the volume, and starts both containers.

### Following One Request: `curl http://localhost/tasks`

```text
1. curl sends  GET /tasks HTTP/1.1  to  127.0.0.1:80

2. Nginx receives the request on port 80.
   nginx.conf says: location /  ->  proxy_pass http://taskapi
   Nginx forwards  GET /tasks  to  app:8000  (found with Docker's internal DNS)

3. uvicorn receives the request on port 8000.
   FastAPI matches the route @app.get('/tasks').
   Depends(get_db) opens a SQLAlchemy session.
   SQLAlchemy runs  SELECT ... FROM tasks  on /app/data/tasks.db.
   FastAPI returns JSON with status 200.

4. Nginx passes the JSON response back to curl unchanged.

5. curl prints the JSON.
```

### Who Does What?

| Question | Answer |
|----|----|
| Who accepts the public connection? | Nginx |
| Who runs the Python code? | uvicorn, inside the `app` container |
| Who validates the request body? | FastAPI + Pydantic |
| Who talks to the database? | SQLAlchemy, inside the `app` container |
| Who keeps the data across restarts? | The `taskdata` Docker volume |
| Who wires everything together? | Docker Compose |

**Quick recap**

- One `docker compose up --build` starts the whole stack.
- A request goes curl -> Nginx (:80) -> uvicorn/FastAPI (:8000) -> SQLite, and back.
- Each layer has one job, so you can change one without touching the others.

---

## 9. DNS and Domain Names

So far everything ran on `localhost`. To put the app on the internet, you'd run the same `docker compose up` on a server, then point a domain name at that server. This section explains that last part. You don't need a server or a domain to follow along.

### What Is DNS?

Every server on the internet has an **IP address**, a number like `203.0.113.42`. **DNS** (Domain Name System) is the internet's phone book: it turns names like `tasks.example.com` into IP addresses that computers can connect to.

Without DNS, you'd type `http://203.0.113.42/tasks` instead of `http://tasks.example.com/tasks`.

### How a Name Gets Looked Up

When you type `tasks.example.com` into a browser:

```text
Browser
  |
  | 1. Check the browser's cache (visited recently?)
  v
Operating system
  |
  | 2. Check the OS cache and the hosts file (/etc/hosts)
  v
Recursive resolver  (from your ISP, or a public one like 8.8.8.8)
  |
  | 3. Ask: who handles .com?
  v
Root name server
  |
  | 4. Answers: ask the .com TLD server
  v
TLD name server  (.com)
  |
  | 5. Answers: ask example.com's authoritative name server
  v
Authoritative name server  (your DNS provider)
  |
  | 6. Answers: tasks.example.com -> 203.0.113.42
  v
Browser connects to 203.0.113.42 on port 80
```

The answer is **cached** along the way, so the full lookup only happens again once the cached copy expires (its TTL runs out).

### A Records

An **A record** (Address record) maps a hostname to an IPv4 address. It's the most basic DNS record.

| Type | Name | Value | TTL |
|------|---------------------|----------------|--------|
| A | `tasks.example.com` | `203.0.113.42` | `3600` |
| A | `www.example.com` | `203.0.113.42` | `3600` |
| A | `example.com` | `203.0.113.42` | `3600` |

**TTL** (Time To Live) is how many seconds resolvers may cache the record. `3600` is one hour. A low TTL means changes spread faster; a high TTL means fewer lookups.

### Other Common Record Types

| Type | Purpose | Example |
|----|----|----|
| `A` | Hostname -> IPv4 address | `tasks.example.com -> 203.0.113.42` |
| `AAAA` | Hostname -> IPv6 address | `tasks.example.com -> 2001:db8::1` |
| `CNAME` | Alias: hostname -> another hostname | `www.example.com -> example.com` |
| `MX` | Mail server for the domain | `example.com -> mail.example.com` |
| `TXT` | Free text, used for domain verification, SPF, etc. | `"v=spf1 include:..."` |

### What a Zone File Looks Like

A **zone file** holds all the records for a domain. Most DNS providers hide it behind a web form, but underneath it looks like this:

```text
; Zone file for example.com
$TTL 3600

@     IN  A   203.0.113.42   ; example.com       -> server IP
www   IN  A   203.0.113.42   ; www.example.com   -> server IP
tasks IN  A   203.0.113.42   ; tasks.example.com -> server IP
```

`@` means the domain itself (`example.com`).

### Pointing a Domain at Your Server, Step by Step

1. **Buy a domain** from a registrar such as Namecheap, Porkbun or Cloudflare.
2. **Find your server's public IP address**: the IP of the machine running `docker compose up`.
3. **Log in to your DNS provider** (often the same company as the registrar, or Cloudflare).
4. **Add an A record:**
    - Name: `tasks` (or `@` for the bare domain)
    - Type: `A`
    - Value: `203.0.113.42` (your server's IP)
    - TTL: `3600`
5. **Wait for the change to spread.** It usually takes 1 to 30 minutes, and up to 48 hours if old records were cached with long TTLs.

You can check the result from your terminal with `nslookup tasks.example.com` (or `dig tasks.example.com` on macOS/Linux).

### How This Connects to Our Stack

```text
Browser types:   http://tasks.example.com
                        |
                        | DNS: tasks.example.com -> 203.0.113.42
                        v
              Your server at 203.0.113.42
                        |
                        | port 80
                        v
                    [ Nginx ]     <-- receives the request
                        |
                        v
                    [ FastAPI ]   <-- handles it
                        |
                        v
                    [ SQLite ]    <-- stores the data
```

Nginx is the one listening on port 80. As soon as DNS points your domain at the server, real traffic flows through exactly the stack you built in this lab.

**What about HTTPS?** In production you'd also have Nginx listen on port 443 with a certificate, for example a free one from Let's Encrypt using Certbot. That only changes the Nginx layer; FastAPI and SQLite stay the same.

**Quick recap**

- DNS turns names into IP addresses; answers are cached for the record's TTL.
- An A record maps a hostname to an IPv4 address; CNAME is an alias, MX is for mail.
- To go live: run the stack on a server, then add an A record pointing your domain at its IP.

---

## 10. Practice

Short tasks to check your understanding. Try each one before opening the solution.

### Task 1: Pick the status code

Which status code should the API return in each case?

1. `GET /tasks/7` and task 7 exists.
2. `POST /tasks` with the body `{}`. And with `{"title": 123}`?
3. `PATCH /tasks/999/complete` and there is no task 999.
4. `DELETE /tasks/7` succeeded.

<details markdown="1">
<summary>Show solution</summary>

1. **`200 OK`**.
2. Both give **`422 Unprocessable Entity`**. `{}` is missing `title` (`"Field required"`), and Pydantic v2 doesn't turn the number `123` into a string (`"Input should be a valid string"`).
3. **`404 Not Found`**.
4. **`204 No Content`**.

</details>

### Task 2: Get one task

Add a `GET /tasks/{task_id}` route to the SQLite version of `main.py` that returns a single task, or `404` if it doesn't exist.

<details markdown="1">
<summary>Show solution</summary>

```python
@app.get('/tasks/{task_id}', response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    return _task_to_dict(task)
```

</details>

### Task 3: Move Nginx to port 8080

Port 80 is already taken on your laptop. What do you change so the stack is reachable at `http://localhost:8080/tasks`? Do you need to change `nginx.conf`?

<details markdown="1">
<summary>Show solution</summary>

Only the **host** side of the port mapping in `docker-compose.yml` changes:

```yaml
  nginx:
    ports:
      - "8080:80"
```

`nginx.conf` stays the same: inside the container Nginx still listens on port 80. Run `docker compose up -d` again to apply the change.

</details>

### Task 4: Add a DNS record

You own `example.com`, and your server's IP is `198.51.100.7`. Write the record that makes `api.example.com` point to the server.

<details markdown="1">
<summary>Show solution</summary>

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | `api` | `198.51.100.7` | `3600` |

In zone-file form: `api IN A 198.51.100.7`

</details>

---

## Challenge: Add a Delete Endpoint

Extend the Task Manager API with a **delete endpoint**.

### Requirements

1. Add `DELETE /tasks/{task_id}` to `app/main.py`.
2. Return `204 No Content` on success (no response body).
3. Return `404 Not Found` if the task doesn't exist.
4. Rebuild the Docker image and bring the stack back up.
5. Check it with `curl`:

```bash
# Create a task and note the "id" in the response
curl -X POST http://localhost/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Delete me"}'

# Delete it (replace 1 with the id you got back)
curl -i -X DELETE http://localhost/tasks/1

# Confirm it's gone
curl http://localhost/tasks
```

<details markdown="1">
<summary>Show solution</summary>

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

There's no `return`: with `status_code=204` FastAPI sends an empty body.

Rebuild and restart:

```bash
docker compose up --build
```

`curl -i` should show `HTTP/1.1 204 No Content`. Deleting the same id again gives `404`.

</details>

---

## Summary & Cheat Sheet

| Concept | Remember this |
|----|----|
| REST / HTTP | Methods + URLs + status codes + JSON are the language of web APIs |
| FastAPI | Type hints + Pydantic give you validation and docs for free |
| SQLAlchemy | Maps Python classes to tables; `Depends(get_db)` manages sessions |
| Docker | Packages your app and its environment into an image that runs anywhere |
| Docker Compose | One YAML file starts several containers, wired together, with a volume for data |
| Nginx | Sits in front of your app on port 80 (later 443 for HTTPS) |
| DNS / A records | Map a domain name to your server's IP address |

### Commands You'll Use Most

```bash
uvicorn app.main:app --reload     # run the app locally while developing
docker build -t taskapi .         # build an image
docker run -p 8000:8000 taskapi   # run a single container
docker compose up --build -d      # build and start the whole stack in the background
docker compose logs -f            # watch the logs
docker compose down               # stop the stack (keeps the data volume)
curl -i http://localhost/tasks    # test through Nginx, showing headers
```

### Further Reading

- [FastAPI documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Docker getting started guide](https://docs.docker.com/get-started/)
- [Nginx beginner's guide](https://nginx.org/en/docs/beginners_guide.html)
- [The Twelve-Factor App](https://12factor.net): principles behind production-ready applications

### What's Next

The next notebook, **Vibe Coding**, looks at building software with AI assistants. Keep this Task Manager handy: it's a good, realistic project to practise on, and you now know every layer it runs on.
