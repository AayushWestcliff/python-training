# FastAPI

In this notebook we build a small travel-booking REST API with FastAPI, one feature at a time. We start with a single file that returns hard-coded JSON and finish with a database, routers, middleware, API keys and JWT login.

### Learning Objectives

By the end of this notebook you will be able to:

1. Build a REST API with FastAPI and run it with uvicorn
2. Read path parameters, query parameters and JSON request bodies
3. Validate input and shape output with Pydantic request/response models
4. Store data in SQLite with SQLAlchemy and FastAPI's `Depends()`
5. Split a growing app into separate files with `APIRouter`
6. Add logging and CORS middleware
7. Protect routes with an API key
8. Add username/password login that issues JWT access tokens with an expiry time

### Prerequisites

- Python 3.10 or newer
- The OOP notebook (classes, type hints) and basic SQL
- Some idea of what HTTP methods (GET, POST, ...) and status codes (200, 404, ...) are

Install everything used in this notebook:

```bash
pip install "fastapi[standard]" sqlalchemy pyjwt bcrypt
```

`fastapi[standard]` also installs uvicorn (the server), httpx (used by `TestClient`) and python-multipart (needed for the login form in Section 8).

### How to Use This Notebook

- Work through it **top to bottom**. Each section adds one feature to the same project, called `travelapi`.
- Most code cells are **files**, not cells to run here. A cell that starts with `# file: travelapi/app/main.py` is the full content of that file: create (or replace) the file and paste it in. Cells marked *Illustration* are short pieces to read, not to copy.
- Sections 1 to 3 also have small cells marked **Runs in the notebook**. They use FastAPI's `TestClient` to call the API without starting a server, so you can try things right here.
- From Section 4 on, run the real server from inside the `travelapi/` folder with `uvicorn app.main:app --reload` and test in the browser at `http://localhost:8000/docs`.
- Try each **Exercise** yourself before opening *Show solution*.
- Each section ends with a **Quick recap**. Read just the recaps when revising.

---

## What We're Building

We will build the **Travel API**: a REST API for browsing destinations, booking trips and managing users.

```
Client (curl / browser / Swagger UI)
          |
          | HTTP
          v
    [ FastAPI + uvicorn ]    <-- your Python code
          |
          | SQL
          v
       [ SQLite ]            <-- travel.db
```

### Final Endpoint Table

| Method | Path                    | Auth    | Description           |
|--------|-------------------------|---------|-----------------------|
| GET    | `/destinations`         | None    | List all destinations |
| GET    | `/destinations/{id}`    | None    | Get one destination   |
| POST   | `/destinations`         | API Key | Create a destination  |
| DELETE | `/destinations/{id}`    | API Key | Delete a destination  |
| GET    | `/trips`                | None    | List all trips        |
| GET    | `/trips/{id}`           | None    | Get one trip          |
| POST   | `/trips`                | API Key | Create a trip         |
| POST   | `/auth/register`        | None    | Register a user       |
| POST   | `/auth/token`           | None    | Get a JWT token       |
| POST   | `/bookings`             | JWT     | Create a booking      |
| GET    | `/bookings/me`          | JWT     | My bookings           |
| PATCH  | `/bookings/{id}/cancel` | JWT     | Cancel a booking      |

### Project Structure

This is where we'll end up. Don't create it all now; each section tells you which file to add.

```
travelapi/
├── app/
│   ├── __init__.py        (empty)
│   ├── main.py
│   ├── database.py
│   ├── dependencies/
│   │   ├── __init__.py    (empty)
│   │   ├── auth.py        (API key)
│   │   └── jwt_auth.py    (JWT)
│   └── routers/
│       ├── __init__.py    (empty)
│       ├── destinations.py
│       ├── trips.py
│       ├── bookings.py
│       └── auth.py
└── requirements.txt
```

**Quick recap**

- We're building one project, `travelapi`, and growing it section by section.
- Public routes let anyone read. Writing destinations and trips needs an API key; bookings need a JWT login.
- Data lives in a SQLite file, `travel.db`, from Section 4 onwards.

---

## 1. First Routes

### What Is FastAPI?

**FastAPI** is a modern Python web framework for building REST APIs. What makes it pleasant to use:

- **Type hints drive everything.** Route parameters, request bodies and response shapes are all declared with ordinary Python types.
- **Validation is automatic.** Pydantic checks every incoming request. Bad data gets a `422` response with a clear message, and your function never runs.
- **Docs for free.** Swagger UI at `/docs` and ReDoc at `/redoc`, with no extra code.
- **It's fast.** It's built on Starlette and runs on uvicorn, and is one of the fastest Python frameworks around.

### Project Setup

Create the project folder:

```bash
mkdir -p travelapi/app
cd travelapi
touch app/__init__.py
```

Create `travelapi/requirements.txt`:

```
fastapi[standard]>=0.115
sqlalchemy>=2.0
pyjwt>=2.8
bcrypt>=4.1
```

Paste the code cell below into `app/main.py`, then start the server from the `travelapi/` folder:

```bash
uvicorn app.main:app --reload
```

`app.main:app` means "in the module `app/main.py`, use the variable `app`". `--reload` restarts the server every time you save a file.

Now visit:

- `http://localhost:8000/` for the raw JSON response
- `http://localhost:8000/docs` for Swagger UI, where you can try every endpoint
- `http://localhost:8000/redoc` for the ReDoc version of the docs

### How a Route Works

```
@app.get("/destinations")      <- HTTP method + URL path
def list_destinations():       <- an ordinary Python function (sync or async)
    return [...]               <- dict or list, FastAPI turns it into JSON
```

The decorator connects a URL to a function. When a GET request arrives at `/destinations`, FastAPI calls `list_destinations()` and sends back whatever it returns as JSON.


```python
# file: travelapi/app/main.py  (Section 1 checkpoint)

from fastapi import FastAPI

app = FastAPI(title="Travel API", description="A travel booking system", version="1.0.0")


@app.get("/")
def root():
    return {"message": "Welcome to the Travel API"}


@app.get("/destinations")
def list_destinations():
    return [
        {"id": 1, "name": "Paris", "country": "France", "price_per_day": 150},
        {"id": 2, "name": "Tokyo", "country": "Japan", "price_per_day": 120},
        {"id": 3, "name": "Rome", "country": "Italy", "price_per_day": 100},
    ]


@app.get("/trips")
def list_trips():
    return [
        {"id": 1, "destination_id": 1, "start_date": "2026-06-01", "end_date": "2026-06-07", "spots_available": 10},
        {"id": 2, "destination_id": 2, "start_date": "2026-07-15", "end_date": "2026-07-22", "spots_available": 5},
    ]
```

You can call this app without starting a server. `TestClient` sends fake HTTP requests straight to the `app` object, which is handy for quick checks and for writing tests later. Run the cell above first, then this one.


```python
# Runs in the notebook
from fastapi.testclient import TestClient

client = TestClient(app)

response = client.get("/")
print(response.status_code, response.json())

response = client.get("/destinations")
print(response.status_code, [d["name"] for d in response.json()])
```

    200 {'message': 'Welcome to the Travel API'}
    200 ['Paris', 'Tokyo', 'Rome']


### Exercise 1: Add a Health Check

Add a `GET /health` route that returns `{"status": "ok", "version": "1.0.0"}`. Check that it shows up in Swagger UI at `/docs`.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: travelapi/app/main.py

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
```

</details>

**Quick recap**

- `app = FastAPI()` creates the application; `uvicorn app.main:app --reload` serves it.
- `@app.get("/path")` connects a URL and HTTP method to a function.
- Return a dict or list and FastAPI sends it as JSON.
- Swagger UI at `/docs` is generated for you. Use it to try your endpoints.

---

## 2. Path & Query Parameters

### Path Parameters

A **path parameter** is a variable that is part of the URL itself, like the `1` in `/destinations/1`. Put `{name}` in the path and add a function argument with the same name:


```python
# Illustration (not a complete file)
@app.get("/destinations/{destination_id}")
def get_destination(destination_id: int):
    ...
```

FastAPI turns the text `"1"` from the URL into the Python `int` `1` for you. If the client sends `"abc"`, FastAPI returns `422` before your function is even called.

### Query Parameters

A **query parameter** is anything after the `?` in the URL: `GET /destinations?country=France&max_price=200`.

Declare them as function arguments with default values:

```python
def list_destinations(country: str | None = None, max_price: float | None = None):
```

- If `country` isn't in the URL, it's `None`.
- How does FastAPI know which is which? An argument whose name appears in the path string is a path parameter. Any other simple argument is a query parameter.

### Type Conversion

| URL value | Python type hint | Result                   |
|-----------|------------------|--------------------------|
| `"42"`    | `int`            | `42`                     |
| `"3.14"`  | `float`          | `3.14`                   |
| `"true"`  | `bool`           | `True` (so do `1`, `yes`, `on`) |
| `"abc"`   | `int`            | 422 Unprocessable Entity |

Here is the whole file for this section. It keeps the data in a plain Python list for now.


```python
# file: travelapi/app/main.py  (Section 2 checkpoint)

from fastapi import FastAPI, HTTPException
from typing import Optional

app = FastAPI(title="Travel API", version="1.0.0")

_destinations = [
    {"id": 1, "name": "Paris", "country": "France", "price_per_day": 150.0},
    {"id": 2, "name": "Tokyo", "country": "Japan", "price_per_day": 120.0},
    {"id": 3, "name": "Rome", "country": "Italy", "price_per_day": 100.0},
]


@app.get("/destinations")
def list_destinations(
    country: Optional[str] = None,
    max_price: Optional[float] = None,
):
    result = _destinations
    if country:
        result = [d for d in result if d["country"].lower() == country.lower()]
    if max_price is not None:
        result = [d for d in result if d["price_per_day"] <= max_price]
    return result


@app.get("/destinations/{destination_id}")
def get_destination(destination_id: int):
    for dest in _destinations:
        if dest["id"] == destination_id:
            return dest
    raise HTTPException(status_code=404, detail="Destination not found")


@app.get("/trips")
def list_trips(destination_id: Optional[int] = None):
    trips = [
        {"id": 1, "destination_id": 1, "start_date": "2026-06-01", "end_date": "2026-06-07", "spots_available": 10},
        {"id": 2, "destination_id": 2, "start_date": "2026-07-15", "end_date": "2026-07-22", "spots_available": 5},
    ]
    if destination_id is not None:
        trips = [t for t in trips if t["destination_id"] == destination_id]
    return trips
```

Try a few URLs against it. Notice the `404` comes from our own `HTTPException`, while the `422` comes from FastAPI before our code runs.


```python
# Runs in the notebook
from fastapi.testclient import TestClient

client = TestClient(app)

print(client.get("/destinations", params={"country": "france"}).json())
print(client.get("/destinations", params={"max_price": 120}).json())
print(client.get("/destinations/99").status_code, client.get("/destinations/99").json())
print(client.get("/destinations/abc").status_code)
```

    [{'id': 1, 'name': 'Paris', 'country': 'France', 'price_per_day': 150.0}]
    [{'id': 2, 'name': 'Tokyo', 'country': 'Japan', 'price_per_day': 120.0}, {'id': 3, 'name': 'Rome', 'country': 'Italy', 'price_per_day': 100.0}]
    404 {'detail': 'Destination not found'}
    422


### Exercise 2: Minimum Price Filter

Add an optional `min_price` query parameter to `GET /destinations` that removes destinations cheaper than the given value. Test it with `/destinations?min_price=120` (you should get Paris and Tokyo).

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: travelapi/app/main.py  (replace list_destinations)

@app.get("/destinations")
def list_destinations(
    country: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
):
    result = _destinations
    if country:
        result = [d for d in result if d["country"].lower() == country.lower()]
    if max_price is not None:
        result = [d for d in result if d["price_per_day"] <= max_price]
    if min_price is not None:
        result = [d for d in result if d["price_per_day"] >= min_price]
    return result
```

</details>

**Quick recap**

- Path parameters: `{name}` in the path plus an argument with the same name.
- Query parameters: any other argument, usually with a default such as `None`.
- Type hints do the conversion. Bad values get a `422` automatically.
- Raise `HTTPException(status_code=404, ...)` when something isn't found.

---

## 3. Request & Response Models

### Why Two Models?

FastAPI uses Pydantic models to describe the data going in and out:

- **Request model** (`DestinationCreate`): what the client sends. It can contain things you never want to send back, like a password.
- **Response model** (`DestinationResponse`): what the API returns. It can contain things the client never sends, like the `id` the server assigns.

Keeping them separate means you can change one direction without affecting the other.

### `response_model`

Passing `response_model=DestinationResponse` to the decorator tells FastAPI to:

1. Validate your return value against the model
2. Drop any fields that aren't in the model (so you can't leak data by accident)
3. Show the response shape in Swagger UI

### Field Validation

`Field()` from Pydantic adds rules directly on the model:

| Constraint       | Meaning                               |
|------------------|---------------------------------------|
| `min_length=1`   | String must not be empty              |
| `max_length=100` | String must not exceed 100 characters |
| `gt=0`           | Number must be greater than 0         |
| `ge=0`           | Number must be ≥ 0                    |
| `le=500`         | Number must be ≤ 500                  |

If a rule is broken, the client gets `422 Unprocessable Entity` with a message saying which field failed. You don't write any validation code in the route.

### Testing Validation with curl

```bash
# Missing required fields
curl -X POST http://localhost:8000/destinations \
  -H 'Content-Type: application/json' \
  -d '{"name": "Berlin"}'
# -> 422: country, description and price_per_day are required

# price_per_day = 0 (breaks gt=0)
curl -X POST http://localhost:8000/destinations \
  -H 'Content-Type: application/json' \
  -d '{"name": "Berlin", "country": "Germany", "description": "A vibrant European capital", "price_per_day": 0}'
# -> 422: price_per_day must be greater than 0
```


```python
# file: travelapi/app/main.py  (Section 3 checkpoint)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="Travel API", version="1.0.0")


class DestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10)
    price_per_day: float = Field(gt=0)


class DestinationResponse(BaseModel):
    id: int
    name: str
    country: str
    description: str
    price_per_day: float


class TripCreate(BaseModel):
    destination_id: int
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    spots_available: int = Field(gt=0)


class TripResponse(BaseModel):
    id: int
    destination_id: int
    start_date: str
    end_date: str
    spots_available: int


_destinations: list[dict] = []
_trips: list[dict] = []
_dest_id = 1
_trip_id = 1


@app.get("/destinations", response_model=list[DestinationResponse])
def list_destinations(country: Optional[str] = None):
    if country:
        return [d for d in _destinations if d["country"].lower() == country.lower()]
    return _destinations


@app.get("/destinations/{destination_id}", response_model=DestinationResponse)
def get_destination(destination_id: int):
    for dest in _destinations:
        if dest["id"] == destination_id:
            return dest
    raise HTTPException(status_code=404, detail="Destination not found")


@app.post("/destinations", response_model=DestinationResponse, status_code=201)
def create_destination(destination: DestinationCreate):
    global _dest_id
    record = {"id": _dest_id, **destination.model_dump()}
    _destinations.append(record)
    _dest_id += 1
    return record


@app.get("/trips", response_model=list[TripResponse])
def list_trips():
    return _trips


@app.post("/trips", response_model=TripResponse, status_code=201)
def create_trip(trip: TripCreate):
    global _trip_id
    record = {"id": _trip_id, **trip.model_dump()}
    _trips.append(record)
    _trip_id += 1
    return record
```

Here are the same two curl tests, plus a valid request, sent from the notebook:


```python
# Runs in the notebook
from fastapi.testclient import TestClient

client = TestClient(app)

good = {"name": "Berlin", "country": "Germany",
        "description": "A vibrant European capital", "price_per_day": 90}
r = client.post("/destinations", json=good)
print(r.status_code, r.json())

r = client.post("/destinations", json={"name": "Berlin"})
print(r.status_code, [err["loc"][-1] for err in r.json()["detail"]])

r = client.post("/destinations", json={**good, "price_per_day": 0})
print(r.status_code, r.json()["detail"][0]["msg"])
```

    201 {'id': 1, 'name': 'Berlin', 'country': 'Germany', 'description': 'A vibrant European capital', 'price_per_day': 90.0}
    422 ['country', 'description', 'price_per_day']
    422 Input should be greater than 0


**What just happened?** The first request passed validation, got an `id` and came back with `201 Created`. The second listed every missing field. The third failed the `gt=0` rule. In the last two cases `create_destination` never ran.

### Exercise 3: Tags

Add a `tags` field (a list of strings, empty by default) to `DestinationCreate` and `DestinationResponse`. Each tag must be at most 20 characters. Check that `["beach", "culture"]` is accepted and `["a" * 21]` is rejected with `422`.

**Hint:** `Annotated[str, Field(max_length=20)]` puts a rule on each item of the list.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: travelapi/app/main.py

from typing import Annotated

Tag = Annotated[str, Field(max_length=20)]


class DestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10)
    price_per_day: float = Field(gt=0)
    tags: list[Tag] = []


class DestinationResponse(BaseModel):
    id: int
    name: str
    country: str
    description: str
    price_per_day: float
    tags: list[str] = []

# Note: `= []` is safe here. Pydantic copies the default for every
# new object, unlike a plain function default argument.
```

</details>

**Quick recap**

- Use one Pydantic model for input (`...Create`) and another for output (`...Response`).
- `response_model=` validates the output and hides fields that aren't declared.
- `Field(min_length=..., gt=...)` adds rules; breaking one gives a `422`.
- Use `status_code=201` on routes that create something.

---

## 4. SQLAlchemy Integration

### Why Move to a Database?

The lists from Section 3 are emptied every time the server restarts. SQLAlchemy maps Python classes to database tables, and FastAPI's dependency system hands each request its own database session.

### How `Depends(get_db)` Works


```python
# Illustration (the real version is in database.py below)
def get_db():
    db = SessionLocal()
    try:
        yield db        # ← session handed to the route function
    finally:
        db.close()      # ← always runs after the response is sent

@app.get("/destinations")
def list_destinations(db: Session = Depends(get_db)):
    ...
```

For every request, FastAPI calls `get_db()`, passes the session in as `db`, and runs the `finally` block (closing the session) after the response is sent. Your route never has to open or close a session itself.

### Files for This Section

```
travelapi/app/
├── __init__.py    (empty, from Section 1)
├── database.py    <- engine, session factory, ORM models, get_db
└── main.py        <- FastAPI app and routes
```

Paste the first cell below into `app/database.py` and the second into `app/main.py` (replacing the old version). The server reloads by itself; if it isn't running, start it from the `travelapi/` folder:

```bash
uvicorn app.main:app --reload
```

The imports say `from app.database import ...`, so always run uvicorn from the `travelapi/` folder, not from inside `app/`.


```python
# file: travelapi/app/database.py

import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price_per_day = Column(Float, nullable=False)
    trips = relationship("Trip", back_populates="destination")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    spots_available = Column(Integer, nullable=False)
    destination = relationship("Destination", back_populates="trips")
    bookings = relationship("Booking", back_populates="trip")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=True)
    bookings = relationship("Booking", back_populates="user")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    trip = relationship("Trip", back_populates="bookings")
    user = relationship("User", back_populates="bookings")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
```

Two small things in `database.py`:

- `check_same_thread=False` is a SQLite-only setting. FastAPI may use the session from a different thread than the one that created it, and SQLite would complain without it.
- `created_at` uses `datetime.now(timezone.utc)`. The older `datetime.utcnow()` is deprecated since Python 3.12.


```python
# file: travelapi/app/main.py  (Section 4 checkpoint)

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import Destination, Trip, get_db, create_tables

app = FastAPI(title="Travel API", version="1.0.0")
create_tables()


class DestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10)
    price_per_day: float = Field(gt=0)


class DestinationResponse(BaseModel):
    id: int
    name: str
    country: str
    description: str
    price_per_day: float

    model_config = {"from_attributes": True}


class TripCreate(BaseModel):
    destination_id: int
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    spots_available: int = Field(gt=0)


class TripResponse(BaseModel):
    id: int
    destination_id: int
    start_date: str
    end_date: str
    spots_available: int

    model_config = {"from_attributes": True}


@app.get("/destinations", response_model=list[DestinationResponse])
def list_destinations(db: Session = Depends(get_db)):
    return db.query(Destination).all()


@app.get("/destinations/{destination_id}", response_model=DestinationResponse)
def get_destination(destination_id: int, db: Session = Depends(get_db)):
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    return dest


@app.post("/destinations", response_model=DestinationResponse, status_code=201)
def create_destination(destination: DestinationCreate, db: Session = Depends(get_db)):
    db_dest = Destination(**destination.model_dump())
    db.add(db_dest)
    db.commit()
    db.refresh(db_dest)
    return db_dest


@app.delete("/destinations/{destination_id}", status_code=204)
def delete_destination(destination_id: int, db: Session = Depends(get_db)):
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    if dest.trips:
        raise HTTPException(status_code=409, detail="Delete this destination's trips first")
    db.delete(dest)
    db.commit()


@app.get("/trips", response_model=list[TripResponse])
def list_trips(db: Session = Depends(get_db)):
    return db.query(Trip).all()


@app.post("/trips", response_model=TripResponse, status_code=201)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    db_trip = Trip(**trip.model_dump())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip
```

**What just happened?** The routes look almost the same as before. The differences:

- Each route takes `db: Session = Depends(get_db)` and uses `db.query(...)` instead of a list.
- To save something: `db.add(obj)`, `db.commit()`, then `db.refresh(obj)` to load the `id` the database assigned.
- `model_config = {"from_attributes": True}` lets Pydantic read a SQLAlchemy object (`dest.name`) instead of only dicts (`dest["name"]`).
- `delete_destination` refuses (`409 Conflict`) to delete a destination that still has trips. Without that check SQLAlchemy would try to set those trips' `destination_id` to `NULL`, the database would reject it, and the client would get a `500` error.

### Inspecting the Database

```bash
sqlite3 travel.db

sqlite> .tables
bookings  destinations  trips  users

sqlite> SELECT * FROM destinations;
1|Paris|France|The city of light|150.0

sqlite> .quit
```

All four tables exist already because `create_tables()` creates every model in `database.py`, even the ones we haven't used yet.

### Exercise 4: Get One Trip

`main.py` can fetch one destination but not one trip. Add `GET /trips/{trip_id}` that returns `404` if the trip doesn't exist. Test with a valid ID and with `999`.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: travelapi/app/main.py

@app.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip
```

</details>

**Quick recap**

- `database.py` holds the engine, `SessionLocal`, the models and `get_db()`.
- `db: Session = Depends(get_db)` gives each request its own session, closed automatically.
- Create = `add` + `commit` + `refresh`. Read = `db.query(Model).filter(...).first()` or `.all()`.
- Add `model_config = {"from_attributes": True}` to response models that read ORM objects.

---

## 5. Routers

### The Problem With One Big `main.py`

As the API grows, one `main.py` with every route in it gets hard to find your way around. `APIRouter` lets you put related routes in their own file, each with its own URL prefix and Swagger tag, and plug them all into `main.py`.

### How `APIRouter` Works


```python
# Illustration: routers/destinations.py
from fastapi import APIRouter

router = APIRouter(prefix="/destinations", tags=["Destinations"])

@router.get("")         # matches GET /destinations
def list_destinations():
    ...

@router.get("/{id}")    # matches GET /destinations/{id}
def get_destination(id: int):
    ...
```


```python
# Illustration: main.py
from app.routers import destinations
app.include_router(destinations.router)
```

| `APIRouter` parameter | Effect |
|----|----|
| `prefix="/destinations"` | Adds `/destinations` in front of every route in this router |
| `tags=["Destinations"]` | Groups these routes under one heading in Swagger UI |

**Why `""` and not `"/"`?** With a prefix, `@router.get("/")` would create the URL `/destinations/` (with a trailing slash). A request to `/destinations` then gets a `307` redirect. Browsers follow that silently, but `curl -X POST` does not, so your POST would seem to do nothing. Using `""` keeps the URLs exactly as in the endpoint table.

### Updated Project Structure

```
travelapi/app/
├── __init__.py
├── main.py
├── database.py
└── routers/
    ├── __init__.py        (empty)
    ├── destinations.py
    ├── trips.py
    └── bookings.py        (stub, finished in Section 9)
```

Create `app/routers/__init__.py` (empty) and the four files from the cells below, then restart uvicorn. Every endpoint still works the same; only the file layout changed.


```python
# file: travelapi/app/routers/destinations.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import Destination, get_db

router = APIRouter(prefix="/destinations", tags=["Destinations"])


class DestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10)
    price_per_day: float = Field(gt=0)


class DestinationResponse(BaseModel):
    id: int
    name: str
    country: str
    description: str
    price_per_day: float

    model_config = {"from_attributes": True}


@router.get("", response_model=list[DestinationResponse])
def list_destinations(db: Session = Depends(get_db)):
    return db.query(Destination).all()


@router.get("/{destination_id}", response_model=DestinationResponse)
def get_destination(destination_id: int, db: Session = Depends(get_db)):
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    return dest


@router.post("", response_model=DestinationResponse, status_code=201)
def create_destination(destination: DestinationCreate, db: Session = Depends(get_db)):
    db_dest = Destination(**destination.model_dump())
    db.add(db_dest)
    db.commit()
    db.refresh(db_dest)
    return db_dest


@router.delete("/{destination_id}", status_code=204)
def delete_destination(destination_id: int, db: Session = Depends(get_db)):
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    if dest.trips:
        raise HTTPException(status_code=409, detail="Delete this destination's trips first")
    db.delete(dest)
    db.commit()
```


```python
# file: travelapi/app/routers/trips.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import Trip, get_db

router = APIRouter(prefix="/trips", tags=["Trips"])


class TripCreate(BaseModel):
    destination_id: int
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    spots_available: int = Field(gt=0)


class TripResponse(BaseModel):
    id: int
    destination_id: int
    start_date: str
    end_date: str
    spots_available: int

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TripResponse])
def list_trips(db: Session = Depends(get_db)):
    return db.query(Trip).all()


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("", response_model=TripResponse, status_code=201)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    db_trip = Trip(**trip.model_dump())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip
```


```python
# file: travelapi/app/routers/bookings.py  (stub, finished in Section 9)

from fastapi import APIRouter

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("")
def list_bookings():
    return []

```


```python
# file: travelapi/app/main.py  (Section 5 checkpoint)

from fastapi import FastAPI
from app.database import create_tables
from app.routers import destinations, trips, bookings

app = FastAPI(title="Travel API", description="A travel booking system", version="1.0.0")
create_tables()

app.include_router(destinations.router)
app.include_router(trips.router)
app.include_router(bookings.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Travel API"}
```

### Exercise 5: A Reviews Router

Add `routers/reviews.py` with prefix `/reviews` and a single `GET` route that returns `{"reviews": []}`. Include it in `main.py` and check that it appears in Swagger UI under a "Reviews" heading.

<details markdown="1">
<summary>Show solution</summary>

```python
# file: travelapi/app/routers/reviews.py

from fastapi import APIRouter

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("")
def list_reviews():
    return {"reviews": []}


# add to: travelapi/app/main.py
# from app.routers import destinations, trips, bookings, reviews
# app.include_router(reviews.router)
```

</details>

**Quick recap**

- `router = APIRouter(prefix=..., tags=[...])` in its own file, then `app.include_router(router)` in `main.py`.
- Use `@router.get("")` for the collection URL so there's no trailing-slash redirect.
- Every folder you import from (`app/`, `app/routers/`) gets an empty `__init__.py`.

---

## 6. Middleware

### What Is Middleware?

Middleware is code that runs **before** every request reaches a route and **after** every response leaves it. It wraps the whole request/response cycle.

```
Request  ->  [Middleware 1]  ->  [Middleware 2]  ->  Route Function
Response <-  [Middleware 1]  <-  [Middleware 2]  <-  Route Function
```

Common uses: logging, CORS, authentication checks, rate limiting, adding response headers.

### `BaseHTTPMiddleware`


```python
# Illustration (imports left out)
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Code here runs BEFORE the route
        response = await call_next(request)
        # Code here runs AFTER the route
        return response
```

`call_next(request)` passes the request on to the next middleware (or the route) and gives you back its response. Anything before that line runs on the way in; anything after it runs on the way out.

### CORS Middleware

Browsers block JavaScript `fetch()` calls to a different origin (for example from a React app on port 3000 to our API on port 8000) unless the server says it's allowed. FastAPI ships with `CORSMiddleware` for this:


```python
# Illustration (imports left out)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)
```

During development `allow_origins=["*"]` (any origin) is fine. In production, list the real frontend URLs instead.

### Middleware Order

The middleware you add **last** becomes the **outermost** layer, so it sees the request first and the response last. In the file below `LoggingMiddleware` is added after `CORSMiddleware`, which means:

- it logs every request, including the `OPTIONS` "preflight" requests browsers send for CORS, and
- the time it measures includes the work done by the CORS layer.


```python
# file: travelapi/app/main.py  (Section 6 checkpoint)

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import create_tables
from app.routers import destinations, trips, bookings


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        print(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
        response.headers["X-Process-Time"] = f"{duration:.3f}"
        return response


app = FastAPI(title="Travel API", description="A travel booking system", version="1.0.0")
create_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(destinations.router)
app.include_router(trips.router)
app.include_router(bookings.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Travel API"}
```

### Exercise 6: Request IDs

Extend `LoggingMiddleware` so every response also has an `X-Request-ID` header containing `str(uuid.uuid4())`. Check it with `curl -i http://localhost:8000/destinations` (`-i` prints the response headers).

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: travelapi/app/main.py  (replace LoggingMiddleware)

import uuid


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        print(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
        response.headers["X-Process-Time"] = f"{duration:.3f}"
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        return response
```

</details>

**Quick recap**

- Middleware wraps every request: code before `await call_next(request)` runs on the way in, code after runs on the way out.
- `CORSMiddleware` lets browser apps on other origins call your API.
- The last middleware added is the outermost one.

---

## 7. API Key Authentication

### What Is API Key Auth?

An **API key** is a secret string the client sends in a request header. The server looks it up in its database before allowing the request. It's simple to build and works well for server-to-server calls.

```
Client                        Server
  |                              |
  |  POST /trips                 |
  |  X-API-Key: abc123  ──────►  |  Look up abc123 in users table
  |                              |  Found -> carry on
  |  201 Created        ◄──────  |
```

### `APIKeyHeader`


```python
# Illustration
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
```

`auto_error=False` means FastAPI won't reject a request with no header by itself. Our own dependency does that instead, so we choose the error message.

### Dependency Injection for Auth

`get_api_key` (below) is a FastAPI dependency. Add it to any route that needs protecting:

```python
@router.post("", status_code=201)
def create_trip(
    trip: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_api_key),   # <- protects the route
):
```

If `get_api_key` raises an `HTTPException`, FastAPI sends that response straight away and the route function is never called.

### Files for This Section

Create an empty `app/dependencies/__init__.py` (so `dependencies/` is a package), then add `app/dependencies/auth.py` from the first cell and replace `app/routers/trips.py` with the second.


```python
# file: travelapi/app/dependencies/auth.py

from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.database import User, get_db

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    if not api_key:
        raise HTTPException(status_code=403, detail="API key required. Send it in the X-API-Key header")
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return user
```


```python
# file: travelapi/app/routers/trips.py  (Section 7: POST protected by API key)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import Trip, User, get_db
from app.dependencies.auth import get_api_key

router = APIRouter(prefix="/trips", tags=["Trips"])


class TripCreate(BaseModel):
    destination_id: int
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    spots_available: int = Field(gt=0)


class TripResponse(BaseModel):
    id: int
    destination_id: int
    start_date: str
    end_date: str
    spots_available: int

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TripResponse])
def list_trips(db: Session = Depends(get_db)):
    return db.query(Trip).all()


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("", response_model=TripResponse, status_code=201)
def create_trip(
    trip: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_api_key),
):
    db_trip = Trip(**trip.model_dump())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip
```

### How to Get an API Key

There's no way to create a user yet. In Section 8 we add `POST /auth/register`, which returns an `api_key`. Once you have one, send it with every protected request:

```bash
curl -X POST http://localhost:8000/trips \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key-here' \
  -d '{"destination_id": 1, "start_date": "2026-08-01", "end_date": "2026-08-07", "spots_available": 20}'
```

### Exercise 7: Protect the Destinations Router

The endpoint table says creating and deleting destinations needs an API key, but `routers/destinations.py` doesn't check yet. Protect `POST /destinations` and `DELETE /destinations/{id}` with `Depends(get_api_key)`. Without the header you should get `403`; with a valid key, `201` and `204`.

<details markdown="1">
<summary>Show solution</summary>

```python
# file: travelapi/app/routers/destinations.py  (Section 7: writes protected by API key)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import Destination, User, get_db
from app.dependencies.auth import get_api_key

router = APIRouter(prefix="/destinations", tags=["Destinations"])


class DestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10)
    price_per_day: float = Field(gt=0)


class DestinationResponse(BaseModel):
    id: int
    name: str
    country: str
    description: str
    price_per_day: float

    model_config = {"from_attributes": True}


@router.get("", response_model=list[DestinationResponse])
def list_destinations(db: Session = Depends(get_db)):
    return db.query(Destination).all()


@router.get("/{destination_id}", response_model=DestinationResponse)
def get_destination(destination_id: int, db: Session = Depends(get_db)):
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    return dest


@router.post("", response_model=DestinationResponse, status_code=201)
def create_destination(
    destination: DestinationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_api_key),
):
    db_dest = Destination(**destination.model_dump())
    db.add(db_dest)
    db.commit()
    db.refresh(db_dest)
    return db_dest


@router.delete("/{destination_id}", status_code=204)
def delete_destination(
    destination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_api_key),
):
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    if dest.trips:
        raise HTTPException(status_code=409, detail="Delete this destination's trips first")
    db.delete(dest)
    db.commit()
```

</details>

**Quick recap**

- An API key is a secret sent in a header (`X-API-Key`) and checked against the database.
- Write the check once as a dependency, then add `Depends(get_api_key)` to each route that needs it.
- Raising `HTTPException` inside a dependency stops the request before the route runs.

---

## 8. JWT Authentication

### API Key vs JWT

|  | API Key | JWT |
|----|----|----|
| Storage | Database lookup on every request | Stateless: the server just checks the token's signature |
| Expiry | Lasts until someone revokes it | Built-in `exp` (expiry) claim |
| Contents | Random string with no meaning | Signed data (username, expiry, ...) |
| Typical use | Server-to-server, simple scripts | Apps where people log in |

### JWT Structure

A JWT (JSON Web Token) is three base64url-encoded parts joined by dots:

```
eyJhbGciOiJIUzI1NiJ9          <- header    (which algorithm)
.eyJzdWIiOiJhbHBoYSJ9         <- payload   (claims: sub, exp, ...)
.SflKxwRJSMeKKF2QT4fwpMeJf36P <- signature (HMAC-SHA256 of header + payload)
```

The server signs the token with a secret key. Later it can check any token without touching the database: sign the header and payload again and compare with the signature. Anyone can *read* the payload, so never put secrets in it.

### OAuth2 Password Flow

1. The client sends a username and password to `POST /auth/token`.
2. The server checks them against the database.
3. The server returns `{"access_token": "<jwt>", "token_type": "bearer"}`.
4. The client sends the token on later requests in the header `Authorization: Bearer <jwt>`.
5. The server decodes the token, reads the username and loads the `User`.

### Token Expiry

The `exp` claim in the payload is a Unix timestamp. `jwt.decode()` checks it for us and raises `ExpiredSignatureError` once that time has passed. We catch that and return `401 Unauthorized` with the message `"Token has expired, please log in again"`.

### Libraries

We use two small libraries:

- **PyJWT** (`import jwt`) to create and check tokens
- **bcrypt** to hash passwords, so the database never stores the real password

Older tutorials (and older versions of this notebook) use `python-jose` and `passlib`. `passlib` no longer works with current `bcrypt` releases, and the FastAPI docs have moved to PyJWT, so we follow them.

### Files for This Section

Add `app/dependencies/jwt_auth.py` and `app/routers/auth.py` from the cells below, then replace `app/main.py`.


```python
# file: travelapi/app/dependencies/jwt_auth.py

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session
from app.database import User, get_db

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-a-long-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def hash_password(password: str) -> str:
    # bcrypt only looks at the first 72 bytes of a password
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode()[:72], hashed.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired, please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exc

    username = payload.get("sub")
    if username is None:
        raise credentials_exc
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exc
    return user
```

**What just happened?**

- `hash_password` turns `"secret123"` into a long random-looking string. `verify_password` checks a login attempt against it. The real password is never stored.
- `create_access_token` adds an `exp` time to the data and signs it.
- `get_current_user` is a dependency, just like `get_api_key`. `OAuth2PasswordBearer` pulls the token out of the `Authorization: Bearer ...` header. Then we decode it, catching the expired case **before** the general invalid-token case, because `ExpiredSignatureError` is a kind of `InvalidTokenError`.


```python
# file: travelapi/app/routers/auth.py

import secrets
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import User, get_db
from app.dependencies.jwt_auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    api_key: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    db_user = User(
        username=user.username,
        hashed_password=hash_password(user.password),
        api_key=secrets.token_urlsafe(32),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
```

`OAuth2PasswordRequestForm` reads the username and password from a **form** (not JSON), because that's what the OAuth2 standard says. That's why the curl call below uses `-d 'username=...&password=...'`, and why python-multipart has to be installed. It also makes the **Authorize** button in Swagger UI work.


```python
# file: travelapi/app/main.py  (Section 8 checkpoint: final main.py)

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import create_tables
from app.routers import destinations, trips, bookings, auth as auth_router


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        print(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
        response.headers["X-Process-Time"] = f"{duration:.3f}"
        return response


app = FastAPI(title="Travel API", description="A travel booking system", version="1.0.0")
create_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(auth_router.router)
app.include_router(destinations.router)
app.include_router(trips.router)
app.include_router(bookings.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Travel API"}
```

### Testing the Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "secret123"}'

# 2. Get a token
curl -X POST http://localhost:8000/auth/token \
  -d 'username=alice&password=secret123'
# -> {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Use the token (paste your access_token value)
curl http://localhost:8000/bookings/me \
  -H 'Authorization: Bearer eyJ...'
```

Step 3 only checks the token once Section 9 is done. Until then `/bookings/me` doesn't exist yet.

### Exercise 8: Watch a Token Expire

Make a token that is already expired and confirm that a protected endpoint returns `401` with `"Token has expired, please log in again"`.

The slow way: set `ACCESS_TOKEN_EXPIRE_MINUTES = 1`, get a token, wait 70 seconds, call a protected endpoint, then set it back to `30`. The quick way is in the solution.

<details markdown="1">
<summary>Show solution</summary>

```python
# Run from the travelapi/ folder (python, or a test file).
# Do Section 9 first so /bookings/me exists and checks the token.
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.jwt_auth import create_access_token

client = TestClient(app)
client.post("/auth/register", json={"username": "alice", "password": "secret123"})

expired = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-1))
r = client.get("/bookings/me", headers={"Authorization": f"Bearer {expired}"})
print(r.status_code, r.json())
# 401 {'detail': 'Token has expired, please log in again'}
```

</details>

**Quick recap**

- Passwords are stored as bcrypt hashes, never as plain text.
- `POST /auth/token` checks the password and returns a signed JWT with an `exp` time.
- Clients send `Authorization: Bearer <token>`; `Depends(get_current_user)` checks it and loads the user.
- Catch `ExpiredSignatureError` before `InvalidTokenError` if you want a separate "expired" message.

---

## 9. Final Challenge: Bookings

Build the complete **Bookings** feature by replacing the stub `routers/bookings.py` with a full version.

### Requirements

1. `POST /bookings` (JWT-protected) creates a booking for the logged-in user.
    - Return `404` if the trip doesn't exist.
    - Return `400` if `spots_available <= 0`.
    - Decrease the trip's `spots_available` by 1.
    - Return the booking with status `"confirmed"`.
2. `GET /bookings/me` (JWT-protected) returns all bookings of the logged-in user.
3. `PATCH /bookings/{id}/cancel` (JWT-protected) cancels one of the user's bookings.
    - Return `404` if the booking doesn't exist **or belongs to someone else**.
    - Return `400` if it's already cancelled.
    - Give the spot back: increase `spots_available` by 1.

### Check It With Swagger UI

Start the server and open `http://localhost:8000/docs`.

1. Register a user with `POST /auth/register`. Copy the `api_key` from the response.
2. Click **Authorize** and log in with the same username and password. Swagger calls `/auth/token` and remembers the token for you.
3. Create a destination and a trip. Use the API key from step 1 in the `X-API-Key` field.
4. Create a booking and check that the trip's `spots_available` went down by 1.
5. Cancel the booking and check that `spots_available` went back up.
6. Cancel the same booking again and check you get `400 Bad Request`.

<details markdown="1">
<summary>Show solution</summary>

```python
# file: travelapi/app/routers/bookings.py  (Section 9 solution)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import Booking, Trip, User, get_db
from app.dependencies.jwt_auth import get_current_user

router = APIRouter(prefix="/bookings", tags=["Bookings"])


class BookingCreate(BaseModel):
    trip_id: int


class BookingResponse(BaseModel):
    id: int
    trip_id: int
    user_id: int
    status: str

    model_config = {"from_attributes": True}


@router.post("", response_model=BookingResponse, status_code=201)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.spots_available <= 0:
        raise HTTPException(status_code=400, detail="No spots available for this trip")
    db_booking = Booking(trip_id=booking.trip_id, user_id=current_user.id, status="confirmed")
    trip.spots_available -= 1
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


@router.get("/me", response_model=list[BookingResponse])
def my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Booking).filter(Booking.user_id == current_user.id).all()


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == current_user.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking is already cancelled")
    booking.status = "cancelled"
    trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
    if trip:
        trip.spots_available += 1
    db.commit()
    db.refresh(booking)
    return booking
```

</details>

Notice the cancel query filters on **both** `Booking.id` and `Booking.user_id`. That one line is what stops Bob from cancelling Alice's booking just by guessing its id. We answer `404` rather than `403` so we don't even reveal that the booking exists.

**Quick recap**

- A route can use several dependencies at once: `Depends(get_db)` and `Depends(get_current_user)`.
- Always filter by the current user when reading or changing "my" data.
- Change related rows (the trip's spots) in the same `commit()` as the booking.

---

## Extra Practice

A few more small features to try on the finished project. Each one only touches one file.

### Practice 1: Update a Destination with PATCH

Add `PATCH /destinations/{destination_id}` (API-key protected). The client may send any of the fields; only the ones sent should change. Return `404` if the destination doesn't exist.

**Hint:** make a `DestinationUpdate` model where every field is optional, and use `model_dump(exclude_unset=True)` to get only the fields the client actually sent.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: travelapi/app/routers/destinations.py

from typing import Optional


class DestinationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    country: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=10)
    price_per_day: Optional[float] = Field(default=None, gt=0)


@router.patch("/{destination_id}", response_model=DestinationResponse)
def update_destination(
    destination_id: int,
    changes: DestinationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_api_key),
):
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(dest, field, value)
    db.commit()
    db.refresh(dest)
    return dest
```

</details>

### Practice 2: Filter Trips

Let `GET /trips` take two optional query parameters: `destination_id` (only trips to that destination) and `min_spots` (only trips with at least that many free spots). For example `/trips?destination_id=1&min_spots=5`.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: travelapi/app/routers/trips.py  (replace list_trips)

from typing import Optional


@router.get("", response_model=list[TripResponse])
def list_trips(
    destination_id: Optional[int] = None,
    min_spots: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Trip)
    if destination_id is not None:
        query = query.filter(Trip.destination_id == destination_id)
    if min_spots is not None:
        query = query.filter(Trip.spots_available >= min_spots)
    return query.all()
```

</details>

### Practice 3: Who Am I?

Add `GET /auth/me` (JWT-protected) that returns the logged-in user's `id` and `username`. It must **not** return the password hash.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: travelapi/app/routers/auth.py

from app.dependencies.jwt_auth import get_current_user


class MeResponse(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}


@router.get("/me", response_model=MeResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user   # response_model drops hashed_password and api_key
```

</details>

**Quick recap**

- PATCH = partial update: optional fields plus `model_dump(exclude_unset=True)`.
- Build a SQLAlchemy query step by step, adding `.filter()` only for the parameters that were sent.
- A response model is the easiest way to make sure secrets never leave the API.

---

## Summary & Cheat Sheet

| Topic | Remember this |
|----|----|
| First routes | `@app.get` / `@app.post` + return a dict; FastAPI sends JSON. Run with `uvicorn app.main:app --reload`. |
| Path & query params | `{id}` in the path = path param; other arguments = query params. Type hints convert and validate. |
| Pydantic models | Separate `...Create` (input) and `...Response` (output) models. `Field()` adds rules; failures give `422`. |
| SQLAlchemy + `Depends` | `get_db()` yields a session per request and closes it afterwards. `add`, `commit`, `refresh`. |
| Routers | `APIRouter(prefix=..., tags=...)` per file; `app.include_router()` in `main.py`. |
| Middleware | `BaseHTTPMiddleware.dispatch` wraps every request; `CORSMiddleware` for browser clients. |
| API key auth | `APIKeyHeader` + a dependency that looks the key up in the database. |
| JWT auth | OAuth2 password flow; bcrypt hashes passwords; PyJWT signs tokens with an `exp` time. |
| Testing | `TestClient(app)` calls your API without starting a server. |

### Further Reading

- [FastAPI documentation](https://fastapi.tiangolo.com)
- [Pydantic documentation](https://docs.pydantic.dev/latest/)
- [SQLAlchemy ORM tutorial](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [PyJWT documentation](https://pyjwt.readthedocs.io)
- [OAuth2 explained](https://oauth.net/2/)

### What's Next

The next notebook, **Django**, builds a similar REST API (a blog) with Django and Django REST Framework. Watch how much FastAPI made you write by hand that Django gives you out of the box, like the admin site, user accounts and migrations.
