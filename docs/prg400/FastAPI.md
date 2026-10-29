# FastAPI

> *"The best API is the one you can understand in five minutes and extend in five more."*

---

### Learning Objectives

By the end of this notebook, you will be able to:

1.  **Build** a REST API with FastAPI from first principles
2.  **Use** path parameters, query parameters, and Pydantic request/response models
3.  **Persist** data with SQLAlchemy and FastAPI's dependency injection system
4.  **Organise** routes into separate files using `APIRouter`
5.  **Add** logging and CORS middleware to a FastAPI application
6.  **Protect** routes with API key authentication
7.  **Implement** JWT OAuth2 authentication with token expiry

---

### Prerequisites

- Python 3.10+ installed
- Familiarity with Pydantic models, type hints, and SQLAlchemy

Install dependencies before starting:

```bash
pip install fastapi==0.111.0 'uvicorn[standard]==0.29.0' sqlalchemy==2.0.30 'python-jose[cryptography]==3.3.0' 'passlib[bcrypt]==1.7.4'
```

---

## Section 0 — What We're Building

We will build the **Travel API** — a REST API for browsing destinations, booking trips, and managing users.

```
Client (curl / browser / Swagger UI)
          |
          | HTTP
          v
    [ FastAPI + uvicorn ]    <-- your Python code
          |
          | SQL
          v
       [ SQLite ]           <-- travel.db
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
| POST   | `/auth/token`           | None    | Get JWT token         |
| POST   | `/bookings`             | JWT     | Create a booking      |
| GET    | `/bookings/me`          | JWT     | My bookings           |
| PATCH  | `/bookings/{id}/cancel` | JWT     | Cancel a booking      |

### Project Structure

```
travelapi/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── dependencies/
│   │   ├── auth.py        (API key)
│   │   └── jwt_auth.py    (JWT)
│   └── routers/
│       ├── destinations.py
│       ├── trips.py
│       ├── bookings.py
│       └── auth.py
└── requirements.txt
```

---

## Section 1 — First Routes

### What Is FastAPI?

**FastAPI** is a modern Python web framework for building REST APIs. Key properties:

- **Type hints drive everything** — route parameters, request bodies, and response shapes are all declared with Python types
- **Automatic validation** — Pydantic validates every incoming request; invalid data returns `422` with a clear message
- **Auto-generated docs** — Swagger UI at `/docs` and ReDoc at `/redoc` with zero extra code
- **Fast** — one of the fastest Python frameworks, built on Starlette and uvicorn

### Project Setup

Create the project directory:

```bash
mkdir -p travelapi/app
cd travelapi
```

Create `travelapi/requirements.txt`:

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

Copy `app/main.py` from the code cell below, then run:

```bash
uvicorn app.main:app --reload
```

Visit: - `http://localhost:8000/` — raw JSON response - `http://localhost:8000/docs` — Swagger UI (try the endpoints interactively) - `http://localhost:8000/redoc` — ReDoc documentation

### How a Route Works

```
@app.get("/destinations")      ← HTTP method + URL path
def list_destinations():       ← Python function (sync or async)
    return [...]               ← dict or list → FastAPI serialises to JSON
```

FastAPI maps the decorator to a URL. When a GET request arrives at `/destinations`, it calls `list_destinations()` and returns the result as JSON.

**🏋️ Mini Challenge:** Add a `GET /health` route that returns `{"status": "ok", "version": "1.0.0"}`. Verify it appears in Swagger UI.


```python
# travelapi/app/main.py  (Section 1 checkpoint)

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

---

## Section 2 — Path & Query Parameters

### Path Parameters

A **path parameter** is a variable embedded in the URL. Declare it in the decorator string with `{name}` and add a matching argument to the function:


```python
@app.get("/destinations/{destination_id}")
def get_destination(destination_id: int):
    ...
```

FastAPI automatically converts the URL string `"1"` to the Python `int` `1`. If the client sends `"abc"`, FastAPI returns `422` before your function is called.

### Query Parameters

A **query parameter** is anything after `?` in the URL: `GET /destinations?country=France&max_price=200`.

Declare them as function arguments with default values:

```bash
def list_destinations(country: str = None, max_price: float = None):
```

- If `country` is not in the URL, it is `None`
- FastAPI distinguishes path params (in the path string) from query params (function args not in the path string) automatically

### Type Coercion Table

| URL value | Python type hint | Result                   |
|-----------|------------------|--------------------------|
| `"42"`    | `int`            | `42`                     |
| `"3.14"`  | `float`          | `3.14`                   |
| `"true"`  | `bool`           | `True`                   |
| `"abc"`   | `int`            | 422 Unprocessable Entity |

**🏋️ Mini Challenge:** Add an optional `min_price: float = None` query parameter to `GET /destinations` that filters out destinations cheaper than the given value. Test it at `/destinations?min_price=120`.


```python
# travelapi/app/main.py  (Section 2 checkpoint)

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

---

## Section 3 — Request & Response Models

### Why Two Models?

FastAPI uses Pydantic models to define:

- **Request model** (`DestinationCreate`) — what the client sends. May include passwords, raw fields, things you never want to return.
- **Response model** (`DestinationResponse`) — what the API returns. May include `id`, computed fields, things never sent by the client.

Keeping them separate gives you control over each direction independently.

### `response_model`

Passing `response_model=DestinationResponse` to the decorator tells FastAPI to: 1. Validate the return value against the model 2. Strip any fields not declared in the response model (security benefit) 3. Document the response shape in Swagger UI

### Field Validation

`Field()` from Pydantic adds constraints directly to the model:

| Constraint       | Meaning                               |
|------------------|---------------------------------------|
| `min_length=1`   | String must not be empty              |
| `max_length=100` | String must not exceed 100 characters |
| `gt=0`           | Number must be greater than 0         |
| `ge=0`           | Number must be ≥ 0                    |
| `le=500`         | Number must be ≤ 500                  |

Violating any constraint returns `422 Unprocessable Entity` with a field-level error message — no validation code needed in your route function.

### Testing Validation

```bash
# Missing required field
curl -X POST http://localhost:8000/destinations \
  -H 'Content-Type: application/json' \
  -d '{"name": "Berlin"}'
# → 422: country, description, price_per_day are required

# price_per_day = 0 (violates gt=0)
curl -X POST http://localhost:8000/destinations \
  -H 'Content-Type: application/json' \
  -d '{"name": "Berlin", "country": "Germany", "description": "A vibrant European capital", "price_per_day": 0}'
# → 422: price_per_day must be greater than 0
```

**🏋️ Mini Challenge:** Add a `tags: list[str] = []` field to `DestinationCreate` and `DestinationResponse`. Add `Field(max_length=20)` to each tag. Test that `["beach", "culture"]` is accepted and `["a" * 21]` is rejected.


```python
# travelapi/app/main.py  (Section 3 checkpoint)

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

---

## Section 4 — SQLAlchemy Integration

### Why Move to a Database?

The in-memory lists from Section 3 lose all data on server restart. SQLAlchemy maps Python classes to database tables and handles sessions automatically via FastAPI's dependency injection.

### `Depends(get_db)` — How It Works


```python
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

For every request FastAPI calls `get_db()`, passes the session as `db`, and closes it after the response — your route never manages the session lifecycle.

### Project Structure

Create two files:

```
travelapi/app/
├── database.py    ← engine, session factory, ORM models, get_db
└── main.py        ← FastAPI app, routes
```

Copy `database.py` from the first code cell and `main.py` from the second, then restart uvicorn.

```bash
uvicorn app.main:app --reload
```

### Inspecting the Database

```bash
sqlite3 travel.db

sqlite> .tables
bookings  destinations  trips  users

sqlite> SELECT * FROM destinations;
1|Paris|France|The city of light|150.0

sqlite> .quit
```

**🏋️ Mini Challenge:** Add `GET /destinations/{id}` to `main.py` that returns `404` if the destination does not exist. Test with a valid ID and an invalid ID (e.g., `999`).


```python
# travelapi/app/database.py

import os
from datetime import datetime
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
    created_at = Column(DateTime, default=datetime.utcnow)
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


```python
# travelapi/app/main.py  (Section 4 checkpoint)

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

---

## Section 5 — Routers

### The Problem With One Big `main.py`

As the API grows, putting every route in `main.py` becomes hard to navigate. FastAPI's `APIRouter` lets you split routes into separate files — each with its own prefix and tags — and mount them all in `main.py`.

### How `APIRouter` Works


```python
# routers/destinations.py
from fastapi import APIRouter

router = APIRouter(prefix="/destinations", tags=["Destinations"])

@router.get("/")        # matches GET /destinations
def list_destinations():
    ...

@router.get("/{id}")    # matches GET /destinations/{id}
def get_destination(id: int):
    ...
```


```python
# main.py
from app.routers import destinations
app.include_router(destinations.router)
```

| `APIRouter` parameter | Effect |
|----|----|
| `prefix="/destinations"` | Prepends `/destinations` to all routes in this router |
| `tags=["Destinations"]` | Groups routes under this heading in Swagger UI |

### Updated Project Structure

```
travelapi/app/
├── main.py
├── database.py
└── routers/
    ├── __init__.py        (empty)
    ├── destinations.py
    ├── trips.py
    └── bookings.py        (stub — completed in Section 9)
```

Create the four files from the code cells below, then restart uvicorn. All endpoints still work identically — only the file layout changed.

**🏋️ Mini Challenge:** Add a `routers/reviews.py` router with prefix `/reviews` and a single `GET /` route returning `{"reviews": []}`. Include it in `main.py`. Verify it appears in Swagger UI under a "Reviews" tag.


```python
# travelapi/app/routers/destinations.py

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


@router.get("/", response_model=list[DestinationResponse])
def list_destinations(db: Session = Depends(get_db)):
    return db.query(Destination).all()


@router.get("/{destination_id}", response_model=DestinationResponse)
def get_destination(destination_id: int, db: Session = Depends(get_db)):
    dest = db.query(Destination).filter(Destination.id == destination_id).first()
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    return dest


@router.post("/", response_model=DestinationResponse, status_code=201)
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
    db.delete(dest)
    db.commit()
```


```python
# travelapi/app/routers/trips.py

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


@router.get("/", response_model=list[TripResponse])
def list_trips(db: Session = Depends(get_db)):
    return db.query(Trip).all()


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/", response_model=TripResponse, status_code=201)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    db_trip = Trip(**trip.model_dump())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip
```


```python
# travelapi/app/routers/bookings.py  (stub — completed in Section 9)

from fastapi import APIRouter

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/")
def list_bookings():
    return []


# ─────────────────────────────────────────────────────────────
# travelapi/app/main.py  (Section 5 checkpoint)

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

---

## Section 6 — Middleware

### What Is Middleware?

Middleware is code that runs **before** every request reaches a route function and **after** every response leaves it. It wraps the entire request/response cycle.

```
Request  →  [Middleware 1]  →  [Middleware 2]  →  Route Function
Response ←  [Middleware 1]  ←  [Middleware 2]  ←  Route Function
```

Common uses: logging, CORS, authentication checks, rate limiting, adding response headers.

### `BaseHTTPMiddleware`


```python
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Code here runs BEFORE the route
        response = await call_next(request)
        # Code here runs AFTER the route
        return response
```

`call_next(request)` passes the request to the next middleware or route and returns the response.

### CORS Middleware

Browsers block JavaScript `fetch()` calls to a different origin unless the server explicitly allows it. FastAPI ships with `CORSMiddleware`:


```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For development, `allow_origins=["*"]` allows all origins. Never use `["*"]` in production.

### Middleware Order

Middleware is applied **last-added, first-executed**. Add `LoggingMiddleware` after `CORSMiddleware` so logging sees the real request, not a preflight.

**🏋️ Mini Challenge:** Extend `LoggingMiddleware` to add an `X-Request-ID` header to every response using `str(uuid.uuid4())`. Verify the header appears in the curl response with `curl -I http://localhost:8000/destinations`.


```python
# travelapi/app/main.py  (Section 6 checkpoint)

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

---

## Section 7 — API Key Authentication

### What Is API Key Auth?

An **API key** is a secret token sent in a request header. The server validates it against its database before allowing access. Simple to implement, good for server-to-server communication.

```
Client                        Server
  |                              |
  |  POST /trips                 |
  |  X-API-Key: abc123  ──────►  |  Look up abc123 in users table
  |                              |  Found → proceed
  |  201 Created        ◄──────  |
```

### `APIKeyHeader`


```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
```

`auto_error=False` means FastAPI won't automatically reject requests without the header — your dependency function handles that, giving you control over the error message.

### Dependency Injection for Auth

The `get_api_key` function is a FastAPI dependency. Add it to any route that needs protection:

```bash
@router.post("/", status_code=201)
def create_trip(
    trip: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_api_key),   ← protects the route
):
```

If `get_api_key` raises `HTTPException`, FastAPI returns that response immediately — the route function is never called.

### How to Get an API Key

After registering (Section 8), the `/auth/register` endpoint returns an `api_key`. Send it in every protected request:

```bash
curl -X POST http://localhost:8000/trips \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key-here' \
  -d '{"destination_id": 1, "start_date": "2026-08-01", "end_date": "2026-08-07", "spots_available": 20}'
```

**🏋️ Mini Challenge:** Protect `DELETE /destinations/{id}` with `Depends(get_api_key)`. Try deleting without the header (expect `403`) and with a valid key (expect `204`).


```python
# travelapi/app/dependencies/__init__.py
# (empty file — makes dependencies/ a Python package)

# ─────────────────────────────────────────────────────────────
# travelapi/app/dependencies/auth.py

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
        raise HTTPException(status_code=403, detail="API key required — include X-API-Key header")
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return user
```


```python
# travelapi/app/routers/trips.py  (Section 7 — POST protected by API key)

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


@router.get("/", response_model=list[TripResponse])
def list_trips(db: Session = Depends(get_db)):
    return db.query(Trip).all()


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/", response_model=TripResponse, status_code=201)
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

---

## Section 8 — JWT Authentication

### API Key vs JWT

|  | API Key | JWT |
|----|----|----|
| Storage | Database lookup per request | Stateless — server decodes the token |
| Expiry | Must be manually revoked | Built-in `exp` claim |
| Contents | Opaque string | Signed payload (username, roles, expiry) |
| Use case | Server-to-server, simple auth | User-facing apps, standard auth |

### JWT Structure

A JWT has three base64url-encoded parts separated by `.`:

```
eyJhbGciOiJIUzI1NiJ9          ← header  (algorithm)
.eyJzdWIiOiJhbHBoYSJ9         ← payload (claims: sub, exp, ...)
.SflKxwRJSMeKKF2QT4fwpMeJf36P ← signature (HMAC-SHA256 of header + payload)
```

The server signs the token with a secret key. It can verify any token without a database lookup — just re-sign the header+payload and compare.

### OAuth2 Password Flow

```
1. Client sends username + password to POST /auth/token
2. Server verifies credentials against the database
3. Server returns {"access_token": "<jwt>", "token_type": "bearer"}
4. Client sends the token in the Authorization header on subsequent requests:
   Authorization: Bearer <jwt>
5. Server decodes the token, extracts the username, loads the User
```

### Token Expiry

The `exp` claim in the payload is a Unix timestamp. When the token expires: - The server decodes successfully but finds `exp < now` - Returns `401 Unauthorized` with `"Token has expired — please log in again"`

### Testing the Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "secret123"}'

# 2. Get token
curl -X POST http://localhost:8000/auth/token \
  -d 'username=alice&password=secret123'
# → {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Use token (copy the access_token value)
curl http://localhost:8000/bookings/me \
  -H 'Authorization: Bearer eyJ...'
```

**🏋️ Mini Challenge:** Change `ACCESS_TOKEN_EXPIRE_MINUTES = 1` in `jwt_auth.py`, get a token, wait 70 seconds, then call a protected endpoint. Confirm you receive `401` with `"Token has expired — please log in again"`. Reset back to `30` when done.


```python
# travelapi/app/dependencies/jwt_auth.py

import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.database import User, get_db

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-a-long-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
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
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exc
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired — please log in again",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise credentials_exc
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exc
    return user
```


```python
# travelapi/app/routers/auth.py

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


```python
# travelapi/app/main.py  (Section 8 checkpoint — final main.py)

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

---

## Section 9 — Final Challenge

Build the complete **Bookings** feature by replacing the stub `routers/bookings.py` with a full implementation.

### Requirements

1.  `POST /bookings` — JWT-protected. Creates a booking for the authenticated user.

2.  Return `404` if the trip does not exist

3.  Return `400` if `spots_available <= 0`

4.  Decrement `spots_available` by 1 on success

5.  Return the booking with status `"confirmed"`

6.  `GET /bookings/me` — JWT-protected. Returns all bookings for the authenticated user.

7.  `PATCH /bookings/{id}/cancel` — JWT-protected. Cancels one of the user's bookings.

8.  Return `404` if the booking does not belong to the current user

9.  Return `400` if the booking is already cancelled

10. Restore `spots_available` by 1 on success

### Verify With Swagger UI

Start the server and open `http://localhost:8000/docs`.

1.  Register a user via `POST /auth/register`
2.  Get a token via `POST /auth/token` — click **Authorize** in Swagger and paste the token
3.  Create a destination and a trip (use the API key from step 1)
4.  Create a booking — confirm `spots_available` decreased by 1
5.  Cancel the booking — confirm `spots_available` restored by 1
6.  Try cancelling the same booking again — confirm `400 Bad Request`

<details>
<summary>Solution</summary>

```python
# travelapi/app/routers/bookings.py

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


@router.post("/", response_model=BookingResponse, status_code=201)
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

---

## Summary

| Concept | Key Takeaway |
|----|----|
| **First Routes** | `@app.get` / `@app.post` + return a dict → FastAPI serialises to JSON |
| **Path & Query Params** | Declare in function signature; FastAPI coerces types automatically |
| **Pydantic Models** | Separate request/response models; `Field()` adds validation for free |
| **SQLAlchemy + Depends** | `get_db()` dependency manages session lifecycle automatically |
| **Routers** | `APIRouter` splits routes into focused files; `app.include_router()` mounts them |
| **Middleware** | `BaseHTTPMiddleware` wraps every request; add CORS with `CORSMiddleware` |
| **API Key Auth** | `APIKeyHeader` + a dependency that validates the key against the database |
| **JWT Auth** | OAuth2 password flow; `python-jose` signs tokens; `passlib` hashes passwords |

### Further Reading

- [FastAPI documentation](https://fastapi.tiangolo.com)
- [Pydantic v2 documentation](https://docs.pydantic.dev/latest/)
- [python-jose documentation](https://python-jose.readthedocs.io)
- [passlib documentation](https://passlib.readthedocs.io)
- [OAuth2 explained](https://oauth.net/2/)


```python
# travelapi/app/routers/bookings.py  (Section 9 complete solution)

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


@router.post("/", response_model=BookingResponse, status_code=201)
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
