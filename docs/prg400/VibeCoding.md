# Vibe Coding: Using AI Tools and Agents in Modern Python Development

> *"The best programmers are not those who know the most, but those who know how to find the best answers — and now AI is part of that toolkit."*

---

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Explain** what "vibe coding" is and where the term comes from
2.  **Use** AI coding assistants (GitHub Copilot, ChatGPT, Claude) effectively with targeted prompts
3.  **Evaluate** AI-generated code critically — spotting bugs, security issues, and hallucinations
4.  **Scaffold** FastAPI and Django projects faster using AI-assisted workflows
5.  **Generate** Dockerfiles and docker-compose configurations with AI guidance
6.  **Understand** what AI agents are and how they differ from simple autocomplete
7.  **Apply** a responsible AI workflow: generate → review → refine → own

---

## Sections

| #  | Topic                                 |
|-----|---------------------------------------|
| 1   | What is Vibe Coding?                  |
| 2   | The AI Developer Toolkit              |
| 3   | The Art of Prompting                  |
| 4   | AI-Assisted FastAPI Development       |
| 5   | AI-Assisted Django Development        |
| 6   | AI for Infrastructure: Docker & Nginx |
| 7   | AI Agents in Development              |
| 8   | Pitfalls, Hallucinations & Security   |
| 9   | What AI Cannot Replace                |
| 10  | Best Practices & Responsible Workflow |

---

## Section 1 — What is Vibe Coding?

### The Term's Origin

The phrase **"vibe coding"** was coined by **Andrej Karpathy** (co-founder of OpenAI, former Tesla AI director) in February 2025. His tweet read:

> *"There's a new kind of coding I call 'vibe coding', where you fully give in to the vibes, embrace exponentials, and forget that the code even exists. It's possible because LLMs are getting good enough."*

He described a workflow where developers: - Describe what they want in natural language - Let the AI generate the code - Accept suggestions without always reading them deeply - Iterate quickly through prompts rather than through manual edits

---

### The Spectrum of AI-Assisted Development

```
TRADITIONAL                                              PURE VIBE
CODING                                                   CODING
  |--------------------------------------------------------|
  |                                                        |
  Write every   Use AI for     Use AI for    Use AI for   Let AI write
  line by hand  autocomplete   boilerplate   full drafts  everything
                               and snippets  you review
```

**Most professional developers today operate in the middle** — using AI to accelerate work while retaining full understanding and responsibility for the code.

---

### Why This Matters Now

| Year | Milestone                                            |
|------|------------------------------------------------------|
| 2021 | GitHub Copilot beta — AI autocomplete arrives        |
| 2022 | ChatGPT released — conversational code generation    |
| 2023 | GPT-4, Claude 2 — near-human reasoning on code       |
| 2024 | Copilot Workspace, Cursor IDE — agentic coding tools |
| 2025 | AI agents write, test, deploy code autonomously      |

---

### 💬 Class Discussion (3 minutes)

> - Have you used GitHub Copilot, ChatGPT, or Claude to help write code?
> - What worked well? What didn't?
> - Do you think AI will replace programmers? Why or why not?

---

## Section 2 — The AI Developer Toolkit

### Major AI Coding Tools in 2025

| Tool | Type | Best For |
|----|----|----|
| **GitHub Copilot** | IDE plugin + agent | In-editor autocomplete, PR review, workspace agents |
| **Cursor** | AI-native IDE | Full codebase context, multi-file edits |
| **Claude (Anthropic)** | Chat + API | Long code generation, architecture discussion |
| **ChatGPT (OpenAI)** | Chat + API | Explanation, debugging, general coding tasks |
| **Gemini Code Assist** | IDE plugin | Google Cloud / GCP-integrated development |
| **Amazon Q** | IDE plugin | AWS-integrated development |
| **Aider** | CLI tool | Terminal-based AI pair programming with git |

---

### How These Tools Actually Work (High Level)

```
Your Prompt / Code Context
         │
         ▼
  ┌─────────────────────────────────┐
  │        Large Language Model      │
  │   (Trained on billions of lines  │
  │    of code from GitHub, docs,    │
  │    Stack Overflow, papers...)    │
  └─────────────────────────────────┘
         │
         ▼
    Generated Tokens  →  Code Output
```

**Key concepts to understand:**

- **Context window**: The amount of text the model can "see" at once (8K → 200K+ tokens)
- **Temperature**: Controls randomness — lower = more deterministic code
- **Training cutoff**: The model doesn't know about libraries released after its training date
- **Hallucination**: The model confidently generates plausible-but-wrong code

---

### GitHub Copilot in VS Code — Key Features

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Copilot Features                                 │
│                                                          │
│  ① Inline Suggestions    — Tab to accept as you type    │
│  ② Copilot Chat          — Ask questions about code     │
│  ③ /explain              — Explain selected code        │
│  ④ /fix                  — Fix a bug in selection       │
│  ⑤ /tests                — Generate unit tests         │
│  ⑥ /doc                  — Generate docstrings         │
│  ⑦ Agent Mode            — Multi-step autonomous tasks │
└─────────────────────────────────────────────────────────┘
```

---

## Section 3 — The Art of Prompting

The quality of AI output is **directly proportional to the quality of your prompt**. This is the most important skill to develop.

### The Anatomy of a Great Code Prompt

```
┌────────────────────────────────────────────────────────────────┐
│  ROLE       — "You are a senior Python backend developer"       │
│  CONTEXT    — "I'm building a FastAPI app with PostgreSQL"      │
│  TASK       — "Create a user registration endpoint"            │
│  SPECIFICS  — "Use Pydantic v2, hash passwords with bcrypt"    │
│  CONSTRAINTS— "Follow RESTful conventions, add error handling" │
│  FORMAT     — "Include type hints and docstrings"              │
└────────────────────────────────────────────────────────────────┘
```

### Bad Prompt vs. Good Prompt

**❌ Weak prompt:**

    make a login api

**✅ Strong prompt:**

    You are a senior Python developer. I'm building a FastAPI application.

    Create a POST /auth/login endpoint that:
    - Accepts email and password in the request body (use Pydantic v2 BaseModel)
    - Queries a SQLAlchemy User model (assume it has id, email, hashed_password fields)
    - Verifies the password using passlib bcrypt
    - Returns a JWT access token (use python-jose)
    - Raises HTTPException 401 if credentials are invalid
    - Includes type hints and a brief docstring

    Do not create the full app — just the router function and the Pydantic schemas.

---

### Prompting Patterns for Developers

| Pattern | When to Use | Example |
|----|----|----|
| **Scaffolding** | Starting a new project/module | "Create a FastAPI project structure for a blog API" |
| **Completion** | Filling in a function body | "Complete this function that parses CSV and returns a list of dicts" |
| **Refactoring** | Improving existing code | "Refactor this to use async/await and add error handling" |
| **Debugging** | Finding bugs | "This function raises KeyError on line 12. Here's the traceback: [...]" |
| **Testing** | Writing tests | "Write pytest tests for this endpoint covering happy path and 4xx errors" |
| **Documentation** | Adding docs | "Add OpenAPI descriptions and Pydantic field descriptions to this model" |
| **Translation** | Converting code | "Convert this Django ORM query to raw SQLAlchemy 2.0" |


```python
# ──────────────────────────────────────────────────────────────
# LIVE DEMO: Simulating what AI tools produce
# We'll look at a progression of prompts and the kind of output
# a tool like GitHub Copilot or Claude would generate.
# ──────────────────────────────────────────────────────────────

# Prompt 1 (weak): "make a function to validate email"
# Typical AI output — minimal, no edge cases:

def validate_email_weak(email):
    return "@" in email


# Prompt 2 (better): "Write a Python function that validates an email address
# using a regex. Return True if valid, False otherwise. Add type hints."
# Typical AI output — more robust:

import re

def validate_email(email: str) -> bool:
    """Validate an email address using a regex pattern."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# Test it
test_emails = [
    "student@kings.edu.np",
    "not-an-email",
    "missing@domain",
    "valid.user+tag@example.co.uk",
    "@nodomain.com",
]

print("Email Validation Results:")
print("-" * 40)
for email in test_emails:
    result = "✓ Valid" if validate_email(email) else "✗ Invalid"
    print(f"  {result}: {email}")
```


```python
# ──────────────────────────────────────────────────────────────
# CRITICAL THINKING EXERCISE
# The AI also generated this password checker. Can you spot
# what's wrong with it before running it?
# ──────────────────────────────────────────────────────────────

def check_password_strength(password: str) -> str:
    """
    AI-generated function — review before trusting!
    Returns 'weak', 'medium', or 'strong' based on password rules.
    """
    score = 0

    if len(password) >= 8:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*" for c in password):
        score += 1

    # BUG: The thresholds don't account for the max score being 4
    # Also: printing the password is a security anti-pattern!
    print(f"Checking password: {password}")  # ← NEVER DO THIS IN PRODUCTION

    if score <= 1:
        return "weak"
    elif score <= 3:   # ← 'medium' catches score 2 and 3
        return "medium"
    else:
        return "strong"


# Discussion: What are the problems?
# 1. Logging the password to stdout (OWASP A09 - Security Logging failure)
# 2. No protection against extremely short passwords (score=1 still passes 'medium')
# 3. Only 8 chars minimum — modern standards recommend 12+
# This is exactly the kind of code that requires human review!

print("Strength:", check_password_strength("Secret1!"))
```

---

## Section 4 — AI-Assisted FastAPI Development

### The Workflow in Practice

```
  You describe             AI generates            You review
  what you want    ──►    the scaffold     ──►    and refine
       │                                               │
       │◄──────────── iterate until correct ───────────┘
```

### Example Prompt Sent to an AI

```
Build a FastAPI application for a simple task manager with:

- SQLite database using SQLAlchemy 2.0 (async not required)
- A Task model with: id, title, description, completed (bool), created_at
- CRUD endpoints: GET /tasks, POST /tasks, GET /tasks/{id},
  PATCH /tasks/{id}, DELETE /tasks/{id}
- Pydantic v2 request/response schemas
- Proper 404 handling when a task doesn't exist
- Keep everything in a single file for simplicity
```

### What the AI Generated (and what we reviewed)

The following code is a **reviewed and corrected** version of AI output:


```python
# ──────────────────────────────────────────────────────────────
# AI-Generated + Human-Reviewed: Task Manager FastAPI App
# This is the kind of scaffold an AI produces in ~10 seconds.
# We walk through it to understand EVERY part.
# ──────────────────────────────────────────────────────────────

# NOTE: This cell shows the code structure. To actually run this,
# you would save it as main.py and run: uvicorn main:app --reload

code = '''
# main.py — AI-assisted scaffold, human-reviewed

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ── Database Setup ─────────────────────────────────────────────
DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = "tasks"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(String(1000), default="")
    completed   = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ── Pydantic Schemas ───────────────────────────────────────────
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}  # Pydantic v2

# ── Dependency ─────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── App & Routes ───────────────────────────────────────────────
app = FastAPI(title="Task Manager API", version="1.0.0")

@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """Return all tasks."""
    return db.query(Task).all()

@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Fetch a single task by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Partially update a task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
'''

print("Task Manager API scaffold generated by AI.")
print("Character count:", len(code))
print("\nKey patterns used (that YOU need to understand):")
patterns = [
    "SQLAlchemy 2.0 DeclarativeBase (not the old declarative_base())",
    "Pydantic v2 model_config = {'from_attributes': True}",
    "Dependency injection with Depends(get_db)",
    "model_dump(exclude_unset=True) for partial updates",
    "HTTPException for consistent error responses",
    "status_code=201 for POST, 204 for DELETE",
]
for i, p in enumerate(patterns, 1):
    print(f"  {i}. {p}")
```

### What the AI Got Right — and What Needed Fixing

| Aspect | AI Output | Human Fix Needed? |
|----|----|----|
| SQLAlchemy setup | Used modern `DeclarativeBase` | ✅ Correct |
| Pydantic schemas | Used `model_config` (v2 style) | ✅ Correct |
| PATCH endpoint | Used `exclude_unset=True` | ✅ Correct |
| `check_same_thread` | Added for SQLite | ✅ Correct |
| Field validation | Added `min_length`, `max_length` | ✅ AI did it |
| `datetime.utcnow` | Used (deprecated in Python 3.12+) | ⚠️ Should use `datetime.now(timezone.utc)` |
| No auth layer | No authentication | ⚠️ Fine for demo, not for production |
| No pagination | Returns all tasks | ⚠️ Would need `skip`/`limit` at scale |

**Lesson:** AI gets 80-90% right. Your job is to spot the remaining 10-20%.

---

### ✍️ Exercise: Prompt-and-Review (10 minutes)

Using your AI tool of choice (GitHub Copilot Chat / ChatGPT / Claude), send this prompt and review the output:

```
Add a GET /tasks/search endpoint to the Task Manager API above.
It should accept a query parameter `q` and return tasks where
the title contains the search string (case-insensitive).
Use SQLAlchemy's ilike() for the filter.
```

Check: 1. Does it use `ilike()` correctly? 2. Does it handle the case where `q` is empty? 3. Is the route registered before `/tasks/{task_id}` to avoid conflict?

---

## Section 5 — AI-Assisted Django Development

### When to Use Django vs FastAPI

| Criteria | Django | FastAPI |
|----|----|----|
| Full-stack web app | ✅ Best choice | ❌ Not designed for it |
| Admin panel needed | ✅ Built-in | ❌ Must build manually |
| High-performance async API | ⚠️ Possible but heavier | ✅ Built for this |
| Rapid prototyping with DB | ✅ Migrations + ORM | ✅ Also good |
| Built-in auth system | ✅ Complete | ❌ Must add yourself |
| API documentation | ⚠️ Needs DRF + drf-spectacular | ✅ Automatic with Swagger UI |

---

### AI-Assisted Django: Generating Models

**Prompt sent to AI:**

```
Create Django models for a blog platform with:
- User profile (extends Django's built-in User with bio and avatar_url)
- Post model (title, content, author FK to User, published_at, is_published, slug)
- Tag model (name, slug) with ManyToMany to Post
- Comment model (post FK, author FK, body, created_at)

Use __str__ methods, Meta classes with ordering, and include
a custom manager on Post that returns only published posts.
```


```python
# ──────────────────────────────────────────────────────────────
# AI-Generated Django Models — Blog Platform
# Display the generated code and annotate the key decisions
# ──────────────────────────────────────────────────────────────

django_models_code = '''
# models.py — AI-generated, human-reviewed

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone


class UserProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio        = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class PublishedManager(models.Manager):
    """Custom manager that returns only published posts."""
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class Post(models.Model):
    title        = models.CharField(max_length=300)
    slug         = models.SlugField(max_length=300, unique=True)
    content      = models.TextField()
    author       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    tags         = models.ManyToManyField(Tag, blank=True, related_name="posts")
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    objects   = models.Manager()        # default manager
    published = PublishedManager()      # custom manager

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-published_at"]


class Comment(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    class Meta:
        ordering = ["created_at"]
'''

print("Django models generated by AI")
print("=" * 50)

review_points = {
    "✅ AI got right": [
        "Used OneToOneField (not ForeignKey) for UserProfile",
        "Custom manager correctly overrides get_queryset()",
        "auto_now_add vs auto_now used correctly",
        "ManyToManyField with blank=True (not null=True)",
        "on_delete=CASCADE on all ForeignKeys",
        "Auto-sets published_at when first published",
    ],
    "⚠️ Things to discuss": [
        "Slug auto-generation: what happens with duplicate titles?",
        "No max_length on TextField fields (fine, but intentional?)",
        "No signal to auto-create UserProfile on User creation",
        "published_at ordering may show unpublished posts oddly",
    ]
}

for category, points in review_points.items():
    print(f"\n{category}:")
    for point in points:
        print(f"  • {point}")
```

### AI-Generated Django Admin Configuration

One of the most powerful AI-assisted tasks is configuring Django Admin. It's repetitive, boilerplate-heavy, and AI excels at it:


```python
# ──────────────────────────────────────────────────────────────
# Prompt: "Generate Django admin.py for the blog models above.
#          Include list_display, search_fields, list_filter,
#          prepopulated_fields for slugs, and inline for comments."
# ──────────────────────────────────────────────────────────────

admin_code = '''
# admin.py — AI-generated in ~3 seconds

from django.contrib import admin
from .models import UserProfile, Post, Tag, Comment


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "bio")
    search_fields = ("user__username", "user__email")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("author", "created_at")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display  = ("title", "author", "is_published", "published_at", "created_at")
    list_filter   = ("is_published", "tags", "created_at")
    search_fields = ("title", "content", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal   = ("tags",)
    inlines = [CommentInline]
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ("author", "post", "created_at")
    search_fields = ("author__username", "body")
    list_filter   = ("created_at",)
'''

print("Django admin.py — AI-generated output")
print("-" * 50)
print("Time to generate manually: ~15-20 minutes")
print("Time with AI:              ~30 seconds")
print("\nThis is the productivity multiplier.")
print("The AI knows Django admin's API better than most developers.")
print("\nBut YOU need to know what it means to verify it!")
```

---

## Section 6 — AI for Infrastructure: Docker & Nginx

### Infrastructure as Code — AI's Comfort Zone

Docker configurations are: - Pattern-heavy (same structure for every app type) - Easy to forget details (exposed ports, volume mounts, healthchecks) - Time-consuming to look up from scratch

This makes them a **perfect target for AI generation**.

---

### Prompt for Full Stack Docker Setup

```
Generate a production-ready docker-compose.yml for a Django application with:
- Django app running with gunicorn (web service)
- PostgreSQL 16 database (db service)
- Nginx as reverse proxy (nginx service)
- Redis for caching (redis service)

Requirements:
- Use named volumes for postgres data and static files
- Django reads DB config from environment variables
- Nginx serves static files directly and proxies /api/ to gunicorn
- Include a healthcheck for the database
- Use a .env file for secrets (do not hardcode passwords)
```


```python
# ──────────────────────────────────────────────────────────────
# AI-Generated Docker Compose — Reviewed & Annotated
# ──────────────────────────────────────────────────────────────

docker_compose = '''
# docker-compose.yml — AI-generated, production-ready pattern

version: "3.9"

services:

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB:       ${POSTGRES_DB}
      POSTGRES_USER:     ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  web:
    build: .
    command: gunicorn blogplatform.wsgi:application --bind 0.0.0.0:8000 --workers 3
    volumes:
      - static_files:/app/staticfiles
    environment:
      DATABASE_URL:  postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db/${POSTGRES_DB}
      REDIS_URL:     redis://redis:6379/0
      SECRET_KEY:    ${DJANGO_SECRET_KEY}
      DEBUG:         "False"
      ALLOWED_HOSTS: ${ALLOWED_HOSTS}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_files:/app/staticfiles:ro
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  static_files:
'''

nginx_conf = '''
# nginx/nginx.conf — AI-generated Nginx config

upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name _;

    # Serve static files directly
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy everything else to Django
    location / {
        proxy_pass         http://django;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
'''

dockerfile = '''
# Dockerfile — AI-generated multi-stage build

FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
RUN python manage.py collectstatic --no-input
EXPOSE 8000
'''

files = {
    "docker-compose.yml": docker_compose,
    "nginx/nginx.conf": nginx_conf,
    "Dockerfile": dockerfile,
}

print("Infrastructure files generated by AI:")
print("=" * 50)
for filename, content in files.items():
    lines = len(content.strip().splitlines())
    print(f"  {filename:<25} ({lines} lines)")

print("\nKey decisions AI made correctly:")
decisions = [
    "postgres:16-alpine (not latest — pinned version)",
    "healthcheck with condition: service_healthy (not just depends_on)",
    "Secrets via environment variables, not hardcoded",
    "Named volumes (not bind mounts) for production data",
    "Multi-stage Dockerfile (builder → final) reduces image size",
    "X-Forwarded-For headers set in Nginx for Django ALLOWED_HOSTS",
    "Static files served by Nginx, not gunicorn",
]
for d in decisions:
    print(f"  ✅ {d}")

print("\nWhat AI missed (always check):")
missed = [
    "HTTPS/TLS configuration (needs certbot or cert volume)",
    "Django migration command on startup",
    "Rate limiting in Nginx",
    "Log rotation configuration",
]
for m in missed:
    print(f"  ⚠️  {m}")
```

---

## Section 7 — AI Agents in Development

### From Autocomplete to Agents

There's an important spectrum to understand:

```
AUTOCOMPLETE          CHAT            AGENT
     │                 │               │
  Single line     Multi-turn       Multi-step
  suggestion      conversation     autonomous
                                   task execution
     │                 │               │
"completes       "answers your    "reads files,
  your code"      question"        writes code,
                                   runs tests,
                                   fixes errors"
```

---

### What Makes Something an "Agent"?

An **AI agent** is a system that:

1.  **Perceives** its environment (reads files, browses docs, runs commands)
2.  **Reasons** about what to do next (LLM decides the next step)
3.  **Acts** using tools (writes files, runs code, calls APIs)
4.  **Observes** the result and **iterates** (reads error output, tries again)

```
       Goal: "Add pagination to the FastAPI endpoint"
              │
              ▼
    ┌─────────────────────────────┐
    │   LLM (the "brain")         │
    └─────────────────────────────┘
              │  decides to use tools:
     ┌────────┼────────┬──────────┐
     ▼        ▼        ▼          ▼
 read_file  write_    run_       search_
            file      tests      docs
     │        │        │          │
     └────────┴────────┴──────────┘
              │  results feed back
              ▼
    ┌─────────────────────────────┐
    │   LLM decides next step     │
    └─────────────────────────────┘
              │
              ▼
           Done! (or iterate)
```

---

### Real AI Agent Tools for Developers

| Tool | What It Does | Agent Capability |
|----|----|----|
| **GitHub Copilot Agent Mode** | Works across your whole VS Code workspace | High |
| **Cursor Composer** | Multi-file editing agent | High |
| **Aider** | CLI agent that reads/writes files and commits to git | High |
| **Devin** | Fully autonomous software engineer | Experimental |
| **LangChain/LangGraph** | Build your own agents in Python | Framework |
| **CrewAI** | Multi-agent orchestration framework | Framework |
| **AutoGen (Microsoft)** | Multi-agent conversation framework | Framework |


```python
# ──────────────────────────────────────────────────────────────
# DEMO: Building a simple AI agent loop from scratch
# This illustrates HOW agents work under the hood.
# (Uses no external AI library — pure Python simulation)
# ──────────────────────────────────────────────────────────────

import json
from typing import Callable


# ── Tool definitions (functions the "agent" can call) ──────────
def read_file_tool(path: str) -> str:
    """Simulated file reader."""
    mock_files = {
        "main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "requirements.txt": "fastapi==0.111.0\nuvicorn==0.29.0\n",
    }
    return mock_files.get(path, f"ERROR: File '{path}' not found")


def write_file_tool(path: str, content: str) -> str:
    """Simulated file writer."""
    return f"SUCCESS: Wrote {len(content)} bytes to {path}"


def run_tests_tool(test_path: str) -> str:
    """Simulated test runner."""
    # In reality, this would call subprocess.run(["pytest", test_path])
    return "PASSED: 3 tests passed in 0.42s"


# ── Agent loop (simplified) ────────────────────────────────────
TOOLS: dict[str, Callable] = {
    "read_file": read_file_tool,
    "write_file": write_file_tool,
    "run_tests": run_tests_tool,
}


def simulate_agent(goal: str, planned_steps: list[dict]) -> None:
    """
    Simulates an agent loop.
    In production, each step would be decided by the LLM
    based on the previous tool output.
    """
    print(f"🤖 AGENT GOAL: {goal}")
    print("=" * 60)

    for step_num, step in enumerate(planned_steps, 1):
        tool_name = step["tool"]
        args = step["args"]
        reason = step["reason"]

        print(f"\nStep {step_num}: [{tool_name}]")
        print(f"  Reason: {reason}")
        print(f"  Args:   {json.dumps(args)}")

        if tool_name in TOOLS:
            result = TOOLS[tool_name](**args)
            print(f"  Result: {result}")
        else:
            print(f"  Result: ERROR — unknown tool '{tool_name}'")

    print("\n" + "=" * 60)
    print("✅ Agent completed task")


# Simulated agent execution plan (in reality, the LLM decides each step)
simulate_agent(
    goal="Add a health check endpoint to the FastAPI app",
    planned_steps=[
        {
            "tool": "read_file",
            "args": {"path": "main.py"},
            "reason": "Read existing code to understand current structure"
        },
        {
            "tool": "write_file",
            "args": {
                "path": "main.py",
                "content": (
                    "from fastapi import FastAPI\n"
                    "app = FastAPI()\n\n"
                    "@app.get('/health')\n"
                    "def health_check():\n"
                    "    return {'status': 'ok'}\n"
                )
            },
            "reason": "Write updated main.py with health endpoint added"
        },
        {
            "tool": "run_tests",
            "args": {"test_path": "test_main.py"},
            "reason": "Verify nothing is broken after the change"
        },
    ]
)
```

---

## Section 8 — Pitfalls, Hallucinations & Security

### The 5 Biggest Risks of Vibe Coding

```
 ┌─────────────────────────────────────────────────────────────┐
 │  RISK 1: HALLUCINATIONS                                      │
 │  AI invents functions, parameters, and libraries that don't  │
 │  exist. It sounds confident. It is wrong.                    │
 ├─────────────────────────────────────────────────────────────┤
 │  RISK 2: OUTDATED CODE                                       │
 │  AI training has a cutoff. It may generate Pydantic v1 code  │
 │  when you're using v2, or deprecated Django patterns.        │
 ├─────────────────────────────────────────────────────────────┤
 │  RISK 3: SECURITY VULNERABILITIES                            │
 │  AI may generate code with SQL injection, hardcoded secrets, │
 │  or missing authentication guards.                           │
 ├─────────────────────────────────────────────────────────────┤
 │  RISK 4: SKILL ATROPHY                                       │
 │  Accepting AI output without understanding it prevents you   │
 │  from growing. You become dependent on the tool.             │
 ├─────────────────────────────────────────────────────────────┤
 │  RISK 5: LICENSING / IP ISSUES                               │
 │  AI may reproduce copyrighted code from training data.       │
 │  Know your organization's AI use policy.                     │
 └─────────────────────────────────────────────────────────────┘
```

---

### Hallucination Examples


```python
# ──────────────────────────────────────────────────────────────
# SPOT THE HALLUCINATIONS
# Each of these snippets contains an AI hallucination.
# Can you find what's wrong before running the code?
# ──────────────────────────────────────────────────────────────

print("=" * 60)
print("HALLUCINATION EXAMPLES — Spot the Bug")
print("=" * 60)

# ── Example 1: Non-existent FastAPI parameter ──────────────────
example_1 = '''
# AI generated this. What's wrong?
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
async def get_items(limit: int = Query(default=10, max_value=100)):
    ...  # Bug: FastAPI's Query uses `le=` not `max_value=`
         # Correct: Query(default=10, le=100)
'''

# ── Example 2: Invented Django ORM method ─────────────────────
example_2 = '''
# AI generated this. What's wrong?
# "Use the .recent() manager method to get the latest 5 posts."

posts = Post.objects.recent(5)  # Bug: .recent() does not exist!
                                 # Correct: Post.objects.order_by('-created_at')[:5]
'''

# ── Example 3: Invented Pydantic feature ──────────────────────
example_3 = '''
# AI generated this Pydantic v2 code. What's wrong?
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

    @validator("age")      # Bug: @validator is Pydantic v1!
    def age_must_be_positive(cls, v):
        ...                # Correct v2: use @field_validator
'''

# ── Example 4: Security hallucination ─────────────────────────
example_4 = '''
# AI said: "Here's how to hash a password securely"
import hashlib

def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()  # WRONG!
    # MD5 is cryptographically broken.
    # Never use MD5 or SHA1 for passwords.
    # Correct: use bcrypt, argon2, or scrypt.
'''

examples = [
    ("FastAPI — wrong Query parameter name", "max_value= doesn't exist → use le="),
    ("Django ORM — invented method", ".recent() doesn't exist → use .order_by()"),
    ("Pydantic v2 — wrong decorator", "@validator is v1 → use @field_validator"),
    ("Security — broken hash function", "MD5 is broken for passwords → use bcrypt"),
]

print("\nHallucination Summary:")
print("-" * 60)
for i, (category, fix) in enumerate(examples, 1):
    print(f"  {i}. {category}")
    print(f"     Fix: {fix}")
    print()
```


```python
# ──────────────────────────────────────────────────────────────
# OWASP TOP 10 ISSUES IN AI-GENERATED CODE
# Demonstrating common security pitfalls
# ──────────────────────────────────────────────────────────────

print("Common OWASP Issues in AI-Generated Python Code")
print("=" * 60)

security_issues = [
    {
        "owasp": "A01 - Broken Access Control",
        "ai_code": "@app.delete('/users/{user_id}')\ndef delete_user(user_id: int, db=Depends(get_db)):\n    # No check if current user == user_id or is admin!",
        "fix": "Always verify current_user.id == user_id or current_user.is_admin",
    },
    {
        "owasp": "A02 - Cryptographic Failures",
        "ai_code": "token = base64.b64encode(user.id.encode()).decode()  # NOT a token!",
        "fix": "Use python-jose with JWT or a dedicated secrets library",
    },
    {
        "owasp": "A03 - Injection",
        "ai_code": "cursor.execute(f\"SELECT * FROM users WHERE name = '{name}'\")",
        "fix": "Use parameterized queries: cursor.execute('...WHERE name = %s', (name,))",
    },
    {
        "owasp": "A05 - Security Misconfiguration",
        "ai_code": "SECRET_KEY = 'dev-secret-key-12345'  # Hardcoded in settings.py",
        "fix": "SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # From env vars",
    },
    {
        "owasp": "A09 - Security Logging",
        "ai_code": "print(f'Login attempt: {username} / {password}')",
        "fix": "Never log passwords. Log: 'Login attempt for user {username}'",
    },
]

for issue in security_issues:
    print(f"\n⚠️  {issue['owasp']}")
    print(f"   AI Generated: {issue['ai_code'].splitlines()[0]}")
    print(f"   ✅ Fix:       {issue['fix']}")
```

---

## Section 9 — What AI Cannot Replace

### The Human Edge

Despite rapid improvements, AI coding assistants consistently struggle with:

```
┌───────────────────────────────────────────────────────────┐
│                                                           │
│  🧠 PROBLEM UNDERSTANDING                                 │
│     AI doesn't know what your business actually needs.    │
│     It optimizes for the prompt, not the real problem.    │
│                                                           │
│  🏗️  SYSTEM ARCHITECTURE                                  │
│     Choosing between microservices vs monolith,           │
│     event-driven vs request-response, requires            │
│     domain knowledge and long-term thinking.              │
│                                                           │
│  🔍 DEBUGGING COMPLEX SYSTEMS                             │
│     Race conditions, distributed tracing, memory leaks,   │
│     and intermittent failures require human intuition.    │
│                                                           │
│  🤝 COMMUNICATION & REQUIREMENTS                          │
│     Translating fuzzy stakeholder needs into precise      │
│     technical specifications is deeply human.             │
│                                                           │
│  ⚖️  ETHICAL & PRODUCT JUDGMENT                           │
│     "Should we build this feature?"                       │
│     "Is this data usage appropriate?"                     │
│     AI cannot answer these questions responsibly.         │
│                                                           │
│  🔐 SECURITY REVIEW                                       │
│     Threat modeling, penetration testing, and             │
│     understanding business risk require deep expertise.   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

### The Fundamentals Amplify AI's Value

| Programmer Type | AI Value Gained | Risk |
|----|----|----|
| **Strong fundamentals** | Very high — AI accelerates expert intuition | Low — can spot mistakes |
| **Intermediate skills** | High — fills knowledge gaps quickly | Medium — may miss subtle issues |
| **Beginner (weak fundamentals)** | Low — can't evaluate correctness | High — blind trust in wrong code |

> **The paradox of vibe coding**: AI is most valuable to those who need it least, and most dangerous to those who need it most.

---

### 💬 Class Discussion (5 minutes)

> 1.  Think of a project you've worked on. Which parts would AI have helped most? Which parts would have been dangerous to delegate?
> 2.  If AI can write code, what should computer science education focus on?
> 3.  How do you verify that AI-generated code is correct?

---

## Section 10 — Best Practices & Responsible Workflow

### The Professional AI-Assisted Development Workflow

```
         YOU define the goal
         and break it into tasks
                  │
                  ▼
         ┌────────────────┐
    ┌────►   GENERATE     │  ← Write clear, specific prompt
    │    └────────────────┘
    │             │
    │             ▼
    │    ┌────────────────┐
    │    │    REVIEW      │  ← Read every line. Understand it.
    │    └────────────────┘
    │             │
    │             ▼
    │    ┌────────────────┐
    │    │    REFINE      │  ← Edit, fix, improve
    │    └────────────────┘
    │             │
    │             ▼
    │    ┌────────────────┐
    └────┤   TEST         │  ← Write tests, run them
         └────────────────┘
                  │
                  ▼
             OWN IT ✅
         (You are responsible
          for this code now)
```

---

### The Golden Rules

1.  **Never accept code you don't understand.** If you can't explain what a function does line by line, keep asking the AI to explain until you can.

2.  **Always run the code.** AI-generated code may look correct and fail silently. Test with real inputs.

3.  **Security-review everything.** Especially: authentication, database queries, input validation, and secret handling.

4.  **Pin your library versions.** AI may generate for a different version than you're using.

5.  **Iterate with feedback.** Paste error messages back to the AI. The best prompts often include the actual error.

6.  **Use AI for what it's best at.** Boilerplate, documentation, test generation, refactoring — not system design.

7.  **Keep building your fundamentals.** The more you know, the more effective your AI collaboration becomes.


```python
# ──────────────────────────────────────────────────────────────
# DEMO: Effective AI-assisted debugging workflow
# This simulates the feedback loop developers use with AI
# ──────────────────────────────────────────────────────────────

print("Debugging Workflow with AI Assistance")
print("=" * 60)

# Step 1: You encounter a bug
buggy_code = """
def calculate_discount(price: float, discount_pct: float) -> float:
    return price - (price * discount_pct)  # Bug: discount_pct is 0-100 not 0-1
"""

# Step 2: You run it and see unexpected output
def calculate_discount_buggy(price: float, discount_pct: float) -> float:
    return price - (price * discount_pct)

print("\nStep 1: Observe unexpected behaviour")
result = calculate_discount_buggy(100, 20)  # Expecting $80, passing 20%
print(f"  Price: $100, Discount: 20%")
print(f"  Expected: $80.00")
print(f"  Got:      ${result:.2f}  ← WRONG! (treated 20 as 2000%!)")

# Step 3: Good prompt to AI (include context + error)
prompt_to_ai = '''
My Python function returns wrong results. Here's the code:

    def calculate_discount(price: float, discount_pct: float) -> float:
        return price - (price * discount_pct)

When I call calculate_discount(100, 20), I expect $80.00 (20% off).
But I get -1900.0.

What's wrong and how do I fix it?
'''

print("\nStep 2: Craft a precise prompt to AI")
print("-" * 40)
print("Good prompt includes:")
print("  ✅ The actual code")
print("  ✅ The inputs used")
print("  ✅ The expected output")
print("  ✅ The actual output received")

# Step 4: AI explains and provides fix
print("\nStep 3: AI Response (simulated)")
print("-" * 40)
print("The bug: discount_pct should be divided by 100 if passed as")
print("a percentage (0-100) rather than a fraction (0.0-1.0).")

# Step 5: Apply and verify the fix
def calculate_discount_fixed(price: float, discount_pct: float) -> float:
    """Calculate price after discount. discount_pct is 0-100 (e.g., 20 = 20%)."""
    if not (0 <= discount_pct <= 100):
        raise ValueError(f"discount_pct must be between 0 and 100, got {discount_pct}")
    return price * (1 - discount_pct / 100)

print("\nStep 4: Apply and verify the fix")
print("-" * 40)
test_cases = [
    (100.0, 20, 80.0),
    (200.0, 50, 100.0),
    (99.99, 10, 89.991),
    (0.0, 100, 0.0),
]
all_pass = True
for price, pct, expected in test_cases:
    result = calculate_discount_fixed(price, pct)
    passed = abs(result - expected) < 0.001
    status = "✅" if passed else "❌"
    print(f"  {status} discount({price}, {pct}%) = ${result:.3f} (expected ${expected:.3f})")
    if not passed:
        all_pass = False

print(f"\nAll tests passed: {all_pass}")
```


```python
# ──────────────────────────────────────────────────────────────
# FINAL EXERCISE: Prompt Engineering Challenge
# Write prompts for each of the following tasks.
# Share your best prompt with the class.
# ──────────────────────────────────────────────────────────────

print("Prompt Engineering Challenge")
print("=" * 60)
print()
print("For each task below, write a prompt you would send to")
print("GitHub Copilot Chat or Claude to get the best result.")
print()

challenges = [
    {
        "num": 1,
        "task": "Django REST Framework viewset",
        "description": (
            "Create a DRF ViewSet for the Post model from our blog app. "
            "It should support list, retrieve, create, update, destroy. "
            "Only authenticated users can create/update/delete."
        ),
        "hint": "Mention: DRF version, permission classes, serializer requirements",
    },
    {
        "num": 2,
        "task": "FastAPI middleware for request timing",
        "description": (
            "Add middleware to the FastAPI app that logs the HTTP method, "
            "path, status code, and response time for every request."
        ),
        "hint": "Mention: use Python's logging module, not print(); async middleware",
    },
    {
        "num": 3,
        "task": "Docker multi-stage build for FastAPI",
        "description": (
            "Write a Dockerfile that uses a multi-stage build to produce "
            "a minimal FastAPI production image under 200MB."
        ),
        "hint": "Mention: python:3.12-slim, pip install --user, copy from builder",
    },
    {
        "num": 4,
        "task": "Pytest fixtures for FastAPI",
        "description": (
            "Write pytest fixtures for testing the Task Manager API. "
            "Use an in-memory SQLite database that resets between tests."
        ),
        "hint": "Mention: TestClient, override_dependency for get_db, scope='function'",
    },
]

for challenge in challenges:
    print(f"Challenge {challenge['num']}: {challenge['task']}")
    print(f"  Task: {challenge['description']}")
    print(f"  Hint: {challenge['hint']}")
    print()
    print(f"  Your prompt:")
    print(f"  " + "_" * 50)
    print()
    print()
```

---

## Lecture Summary

### What We Covered

| Section | Key Takeaway |
|----|----|
| Vibe Coding | It's a spectrum. Professionals use AI as a collaborator, not a replacement. |
| AI Toolkit | Copilot, Cursor, Claude, Aider — each has a role. Know your tools. |
| Prompting | Specificity is everything. Context + constraints = better output. |
| FastAPI | AI scaffolds 80-90% correctly. You identify and fix the rest. |
| Django | AI excels at models, admin, migrations. Business logic needs you. |
| Docker | Infrastructure config is pattern-heavy — AI's comfort zone. |
| Agents | Agents combine LLMs with tools for multi-step autonomous tasks. |
| Pitfalls | Hallucinations, outdated code, security flaws. Always review. |
| Human Edge | Architecture, debugging, ethics, and communication remain human. |
| Workflow | Generate → Review → Refine → Test → Own. Never skip review. |

---

### The Mindset

> **AI is a junior developer who is very fast, never sleeps, knows every framework's docs, but sometimes confidently makes things up and has no idea what your business needs.**
>
> **Your job is to be the senior developer who reviews, guides, corrects, and takes responsibility.**

---

### Recommended Resources

| Resource                       | Link                                   |
|--------------------------------|----------------------------------------|
| GitHub Copilot Docs            | https://docs.github.com/en/copilot     |
| Andrej Karpathy on vibe coding | https://x.com/karpathy                 |
| Aider (CLI AI coding)          | https://aider.chat                     |
| LangChain Docs                 | https://python.langchain.com           |
| OWASP Top 10                   | https://owasp.org/www-project-top-ten/ |
| Prompt Engineering Guide       | https://www.promptingguide.ai          |

---

### Assignment Preview

> Using AI assistance, build a **REST API** for a topic of your choice using **FastAPI** or **Django REST Framework**.
>
> Requirements: - At least 3 models with relationships - Full CRUD for at least one resource - JWT authentication - A `Dockerfile` and `docker-compose.yml` that runs the app - A `PROMPTS.md` file documenting the prompts you used and what changes you made to the AI output
>
> **The `PROMPTS.md` file is the most important deliverable** — it shows you reviewed, understood, and improved the AI's work.


```python
# ──────────────────────────────────────────────────────────────
# End of Lecture — Quick Self-Assessment
# ──────────────────────────────────────────────────────────────

quiz = [
    {
        "q": "What is the most important thing to do with AI-generated code?",
        "a": "Read and understand every line before using it.",
    },
    {
        "q": "What is a hallucination in the context of AI coding tools?",
        "a": "When AI confidently generates code that uses non-existent functions or APIs.",
    },
    {
        "q": "Name two things that make a prompt more effective.",
        "a": "Specific context (framework, version, constraints) and a clear task definition.",
    },
    {
        "q": "What is the difference between an AI autocomplete and an AI agent?",
        "a": "An agent can take multi-step actions using tools (read files, run tests, write code) autonomously.",
    },
    {
        "q": "Why are developers with strong fundamentals more effective at using AI?",
        "a": "They can evaluate AI output, spot mistakes, and guide the AI toward correct solutions.",
    },
]

print("Self-Assessment Questions")
print("=" * 60)
print("Think through each answer before revealing it.")
print()

for i, item in enumerate(quiz, 1):
    print(f"Q{i}: {item['q']}")
    print(f"  → {item['a']}")
    print()

print("=" * 60)
print("Great work today. Keep building. Keep thinking critically.")
print("The best AI-assisted developers are the best developers.")
```
