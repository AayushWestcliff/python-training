# Vibe Coding: Using AI Tools and Agents in Python Development

AI assistants can now write a lot of code for you. This notebook shows how to use them well: how to ask, how to check what comes back, and where you still have to do the thinking yourself.

> "The best programmers aren't the ones who know the most. They're the ones who know how to find good answers, and AI is now one of the places to look."

### Learning Objectives

By the end of this notebook you will be able to:

1. Explain what "vibe coding" means and where the term comes from
2. Write clear, targeted prompts for tools like GitHub Copilot, ChatGPT and Claude
3. Review AI-generated code critically and spot bugs, security holes and hallucinations
4. Scaffold FastAPI and Django code faster with AI help
5. Generate Dockerfiles and `docker-compose.yml` files with AI, and check them
6. Explain what an AI agent is and how it differs from autocomplete
7. Follow a responsible workflow: generate, review, refine, test, own

### Prerequisites

- Python 3.10 or newer
- The FastAPI, Django and Deploying Applications notebooks from this course (we reuse their ideas)
- Access to at least one AI coding tool (Copilot Chat, ChatGPT, Claude or similar) for the exercises

### How to Use This Notebook

- Run the code cells **from top to bottom**. None of them call a real AI service, so they work offline and need no API keys.
- Several cells hold AI-generated code **as a string** so you can read it without installing Django or Docker. To try it for real, copy it into a file.
- Exercises ask you to write prompts or review code. Try first, then open *Show solution* to compare with an example answer.
- Each section ends with a **Quick recap**. Read just the recaps when revising.

---

## 1. What is Vibe Coding?

### Where the Term Comes From

Andrej Karpathy (a co-founder of OpenAI and former head of AI at Tesla) coined the phrase **vibe coding** in a post in February 2025:

> "There's a new kind of coding I call 'vibe coding', where you fully give in to the vibes, embrace exponentials, and forget that the code even exists. It's possible because the LLMs (e.g. Cursor Composer w Sonnet) are getting too good."

He was describing a way of working where you:

- describe what you want in plain English
- let the AI write the code
- accept its suggestions without always reading them closely
- fix things by sending another prompt rather than editing the code yourself

He was mostly talking about quick throwaway projects. For anything you have to maintain, the "forget the code exists" part is where the trouble starts, and most of this notebook is about that.

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

Most working developers sit somewhere in the middle. They let AI speed things up, but they still understand the code and take responsibility for it.

### Why This Matters Now

| Year | Milestone |
|------|-----------|
| 2021 | GitHub Copilot preview: AI autocomplete arrives in the editor |
| 2022 | ChatGPT released: you can *chat* about code |
| 2023 | GPT-4 and Claude 2: much stronger reasoning about code |
| 2024 | Copilot Workspace, Cursor and similar tools start editing whole projects |
| 2025 | Agent tools (Copilot agent mode, Claude Code, Codex and others) can edit files, run tests and iterate on their own |

### Class Discussion (3 minutes)

- Have you used GitHub Copilot, ChatGPT or Claude to help write code?
- What worked well? What didn't?
- Do you think AI will replace programmers? Why or why not?

**Quick recap**

- "Vibe coding" (Karpathy, Feb 2025) means describing what you want and letting the AI write it, often without reading it closely.
- In practice it's a spectrum, from hand-written code to fully AI-written code.
- Professional work sits in the middle: AI drafts, you understand and own the result.

---

## 2. The AI Developer Toolkit

### Common AI Coding Tools

This list changes every few months, so treat it as a snapshot rather than a ranking.

| Tool | Type | Good for |
|------|------|----------|
| GitHub Copilot | IDE plugin + agent | Autocomplete in the editor, chat, PR review, agent mode |
| Cursor | AI-first editor (a VS Code fork) | Working with the whole codebase as context, multi-file edits |
| Claude (Anthropic) | Chat, API and the Claude Code CLI agent | Long code generation, talking through design, terminal-based agent work |
| ChatGPT (OpenAI) | Chat + API | Explanations, debugging, general coding questions |
| Gemini Code Assist | IDE plugin | Development on Google Cloud |
| Amazon Q Developer | IDE plugin | Development on AWS |
| Aider | CLI tool | Pair programming in the terminal, commits to git for you |

### How These Tools Work (High Level)

```
Your prompt + code context
         │
         ▼
  ┌──────────────────────────────────┐
  │        Large Language Model      │
  │   (trained on huge amounts of    │
  │    code from GitHub, docs,       │
  │    Stack Overflow, papers...)    │
  └──────────────────────────────────┘
         │
         ▼
   Generated tokens  →  code output
```

Four ideas worth knowing:

- **Context window**: how much text the model can "see" at once. This ranges from a few thousand tokens in older models to hundreds of thousands (or more) today.
- **Temperature**: how random the output is. Lower means more predictable code.
- **Training cutoff**: the model doesn't know about libraries or versions released after it was trained.
- **Hallucination**: the model confidently writes code that looks right but isn't, for example calling a function that doesn't exist.

### GitHub Copilot in VS Code

| Feature | What it does |
|---------|--------------|
| Inline suggestions | Grey "ghost text" as you type; press Tab to accept |
| Copilot Chat | Ask questions about your code in a side panel |
| `/explain` | Explain the selected code |
| `/fix` | Suggest a fix for a bug in the selection |
| `/tests` | Generate unit tests |
| `/doc` | Generate docstrings / comments |
| Agent mode | Carry out multi-step tasks across files on its own |

**Quick recap**

- Tools range from autocomplete (Copilot inline) to chat (ChatGPT, Claude) to agents (Copilot agent mode, Claude Code, Aider).
- Under the hood they're all large language models predicting the next tokens.
- Remember the limits: context window, training cutoff and hallucination.

---

## 3. The Art of Prompting

What you get out of an AI tool depends heavily on what you put in. Of everything in this notebook, prompting is the skill you'll use every day.

### What a Good Code Prompt Contains

| Part | Example |
|------|---------|
| Role | "You are a senior Python backend developer." |
| Context | "I'm building a FastAPI app with PostgreSQL." |
| Task | "Create a user registration endpoint." |
| Specifics | "Use Pydantic v2 and hash passwords with bcrypt." |
| Constraints | "Follow REST conventions and add error handling." |
| Format | "Include type hints and docstrings." |

You won't need all six every time, but the more of them you include, the less the AI has to guess.

### Weak Prompt vs. Strong Prompt

**Weak:**

```text
make a login api
```

**Strong:**

```text
You are a senior Python developer. I'm building a FastAPI application.

Create a POST /auth/login endpoint that:
- Accepts email and password in the request body (use Pydantic v2 BaseModel)
- Queries a SQLAlchemy User model (assume it has id, email, hashed_password fields)
- Verifies the password using passlib bcrypt
- Returns a JWT access token (use python-jose)
- Raises HTTPException 401 if credentials are invalid
- Includes type hints and a brief docstring

Do not create the full app — just the router function and the Pydantic schemas.
```

The weak prompt leaves the AI to guess the framework, the database, the password hashing and the response format. The strong one answers all of those up front, and the last line stops it from generating a whole app you didn't ask for.

### Prompting Patterns for Developers

| Pattern | When to use | Example |
|---------|-------------|---------|
| Scaffolding | Starting a new project or module | "Create a FastAPI project structure for a blog API" |
| Completion | Filling in a function body | "Complete this function that parses CSV and returns a list of dicts" |
| Refactoring | Improving existing code | "Refactor this to use async/await and add error handling" |
| Debugging | Finding bugs | "This function raises KeyError on line 12. Here's the traceback: [...]" |
| Testing | Writing tests | "Write pytest tests for this endpoint covering the happy path and 4xx errors" |
| Documentation | Adding docs | "Add OpenAPI descriptions and Pydantic field descriptions to this model" |
| Translation | Converting code | "Convert this Django ORM query to SQLAlchemy 2.0" |

### Live Demo: Weak vs. Better Prompt

The cell below shows the kind of code you typically get back from each prompt.


```python
# Prompt 1 (weak): "make a function to validate email"
# Typical AI output: minimal, no edge cases
def validate_email_weak(email):
    return "@" in email


# Prompt 2 (better): "Write a Python function that validates an email address
# using a regex. Return True if valid, False otherwise. Add type hints."
# Typical AI output: more careful
import re

def validate_email(email: str) -> bool:
    """Validate an email address using a regex pattern."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


test_emails = [
    "student@kings.edu.np",
    "not-an-email",
    "missing@domain",
    "valid.user+tag@example.co.uk",
    "@nodomain.com",
]

print(f"{'email':<30} {'weak':<8} better")
print("-" * 46)
for email in test_emails:
    print(f"{email:<30} {str(validate_email_weak(email)):<8} {validate_email(email)}")
```

    email                          weak     better
    ----------------------------------------------
    student@kings.edu.np           True     True
    not-an-email                   False    False
    missing@domain                 True     False
    valid.user+tag@example.co.uk   True     True
    @nodomain.com                  True     False


The weak version accepts `missing@domain` and `@nodomain.com`. The better prompt asked for something specific, so it got something specific.

### Critical Thinking: Review an AI-Generated Function

The AI also produced this password checker. Read it carefully before you run it. What would you change?


```python
def check_password_strength(password: str) -> str:
    """
    AI-generated function. Review before trusting!
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

    print(f"Checking password: {password}")

    if score <= 1:
        return "weak"
    elif score <= 3:
        return "medium"
    else:
        return "strong"


print("Strength:", check_password_strength("Secret1!"))
print("Strength:", check_password_strength("Ab1!"))   # only 4 characters
```

    Checking password: Secret1!
    Strength: strong
    Checking password: Ab1!
    Strength: medium


### Exercise 1: Spot the Problems

List at least three problems with `check_password_strength`. Look at the output above for one big hint.

<details markdown="1">
<summary>Show solution</summary>

```text
1. It prints the password to stdout. Passwords must never end up in logs
   (OWASP A09, Security Logging and Monitoring Failures).
2. Length is just one point out of four, so a 4-character password like
   "Ab1!" still scores 3 and is rated "medium".
3. The minimum length is 8. Current guidance (e.g. NIST) is to encourage
   longer passwords; 12+ is a common recommendation.
4. Lowercase letters are never checked, and the "special character" list
   is very short (no "-", "_", "?", ...).
5. It only scores character classes. It doesn't reject common passwords
   such as "Password1!".
```

</details>

### Exercise 2: Fix It

Write `check_password_strength_fixed(password)` that:

- never prints the password
- returns `"weak"` for anything shorter than 12 characters, whatever else it contains
- otherwise counts lowercase, uppercase, digit and "anything else" (symbol), and returns `"strong"` if all four are present, `"medium"` otherwise


```python
# Exercise 2: your code here
def check_password_strength_fixed(password: str) -> str:
    ...

# Tests (uncomment when ready):
# assert check_password_strength_fixed("Ab1!") == "weak"
# assert check_password_strength_fixed("abcdefghijkl") == "medium"
# assert check_password_strength_fixed("Correct-Horse-9") == "strong"
# print("Exercise 2 passed")
```

<details markdown="1">
<summary>Show solution</summary>

```python
def check_password_strength_fixed(password: str) -> str:
    if len(password) < 12:
        return "weak"
    checks = [
        any(c.islower() for c in password),
        any(c.isupper() for c in password),
        any(c.isdigit() for c in password),
        any(not c.isalnum() for c in password),
    ]
    return "strong" if all(checks) else "medium"


assert check_password_strength_fixed("Ab1!") == "weak"
assert check_password_strength_fixed("abcdefghijkl") == "medium"
assert check_password_strength_fixed("Correct-Horse-9") == "strong"
print("Exercise 2 passed")
```

</details>

**Quick recap**

- A good prompt gives role, context, task, specifics, constraints and format.
- Vague prompts get vague code; specific prompts get specific code.
- Always read AI output: the password checker looked fine but leaked passwords and rated `Ab1!` as medium.

---

## 4. AI-Assisted FastAPI Development

### The Workflow in Practice

```
  You describe             AI generates            You review
  what you want    ──►    the scaffold     ──►    and refine
       │                                               │
       │◄──────────── iterate until correct ───────────┘
```

### Example Prompt Sent to an AI

```text
Build a FastAPI application for a simple task manager with:

- SQLite database using SQLAlchemy 2.0 (async not required)
- A Task model with: id, title, description, completed (bool), created_at
- CRUD endpoints: GET /tasks, POST /tasks, GET /tasks/{id},
  PATCH /tasks/{id}, DELETE /tasks/{id}
- Pydantic v2 request/response schemas
- Proper 404 handling when a task doesn't exist
- Keep everything in a single file for simplicity
```

### What the AI Generated (After Review)

Below is the AI's output **after** we reviewed it and fixed one problem (the `created_at` default, see the table after the code). It is stored in a string so the cell runs without starting a server. To run it for real, save the string as `main.py` and run `uvicorn main:app --reload`.


```python
# AI-generated + human-reviewed: Task Manager FastAPI app.
# An AI produces a scaffold like this in seconds. Your job is to
# understand every line of it.

code = '''
# main.py — AI-assisted scaffold, human-reviewed

from datetime import datetime, timezone
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
    # Reviewed: AI used datetime.utcnow (deprecated since Python 3.12)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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

print("Task Manager API scaffold (AI-generated, human-reviewed)")
print("Character count:", len(code))
print("\nPatterns you need to understand before you can trust it:")
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

    Task Manager API scaffold (AI-generated, human-reviewed)
    Character count: 3500
    
    Patterns you need to understand before you can trust it:
      1. SQLAlchemy 2.0 DeclarativeBase (not the old declarative_base())
      2. Pydantic v2 model_config = {'from_attributes': True}
      3. Dependency injection with Depends(get_db)
      4. model_dump(exclude_unset=True) for partial updates
      5. HTTPException for consistent error responses
      6. status_code=201 for POST, 204 for DELETE


### What the AI Got Right, and What Needed Fixing

| Aspect | AI output | Verdict |
|--------|-----------|---------|
| SQLAlchemy setup | Used the 2.0 `DeclarativeBase` | Correct |
| Model columns | Used `Column(...)` and `db.query(...)` | Works, but SQLAlchemy 2.0 prefers `Mapped[...]`/`mapped_column()` and `select()`. Fine for a demo. |
| Pydantic schemas | Used `model_config` (v2 style) | Correct |
| PATCH endpoint | Used `exclude_unset=True` | Correct |
| `check_same_thread` | Added for SQLite | Correct |
| Field validation | Added `min_length`, `max_length` | Correct |
| `created_at` default | Used `datetime.utcnow` (deprecated in Python 3.12+) | **Fixed** above to `datetime.now(timezone.utc)` |
| Authentication | None | Fine for a demo, not for production |
| Pagination | Returns every task | Would need `skip`/`limit` at scale |

Most of the scaffold was right. The useful work, and the part you can't hand to the AI, is spotting the handful of things that weren't.

### Exercise 3: Prompt and Review (10 minutes)

Send this prompt to your AI tool of choice and review what comes back:

```text
Add a GET /tasks/search endpoint to the Task Manager API above.
It should accept a query parameter `q` and return tasks where
the title contains the search string (case-insensitive).
Use SQLAlchemy's ilike() for the filter.
```

Check:

1. Does it use `ilike()` correctly?
2. What happens when `q` is empty or missing?
3. Is the route registered **before** `/tasks/{task_id}`? If not, FastAPI matches `/tasks/search` against `/tasks/{task_id}` first and returns a 422 error because `"search"` isn't an integer.

<details markdown="1">
<summary>Show solution</summary>

```python
from fastapi import Query

# Must be defined ABOVE @app.get("/tasks/{task_id}")
@app.get("/tasks/search", response_model=list[TaskResponse])
def search_tasks(
    q: str = Query(..., min_length=1, description="Text to search for in titles"),
    db: Session = Depends(get_db),
):
    """Return tasks whose title contains q (case-insensitive)."""
    return db.query(Task).filter(Task.title.ilike(f"%{q}%")).all()

# q is required and must be at least 1 character, so an empty or missing
# q returns a 422 validation error instead of every task.
```

</details>

**Quick recap**

- Give the AI a precise spec (database, models, endpoints, versions) and it can produce a working scaffold quickly.
- Then review it line by line: we found a deprecated `datetime.utcnow` and missing auth/pagination.
- Route order matters in FastAPI: fixed paths like `/tasks/search` go before `/tasks/{task_id}`.

---

## 5. AI-Assisted Django Development

### When to Use Django vs. FastAPI

| Criteria | Django | FastAPI |
|----------|--------|---------|
| Full-stack web app (pages, forms, templates) | Best choice | Not designed for it |
| Admin panel | Built in | You build it yourself |
| High-performance async API | Possible, but heavier | Built for this |
| Rapid prototyping with a database | Migrations + ORM included | Also good (with SQLAlchemy + Alembic) |
| Authentication | Complete system built in | You add it yourself |
| API documentation | Needs DRF + drf-spectacular | Automatic Swagger UI |

### Generating Models with AI

Prompt sent to the AI:

```text
Create Django models for a blog platform with:
- User profile (extends Django's built-in User with bio and avatar_url)
- Post model (title, content, author FK to User, published_at, is_published, slug)
- Tag model (name, slug) with ManyToMany to Post
- Comment model (post FK, author FK, body, created_at)

Use __str__ methods, Meta classes with ordering, and include
a custom manager on Post that returns only published posts.
```


```python
# AI-generated Django models for a blog platform, with our review notes.

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
    "What the AI got right": [
        "Used OneToOneField (not ForeignKey) for UserProfile",
        "Custom manager correctly overrides get_queryset()",
        "auto_now_add vs auto_now used correctly",
        "ManyToManyField with blank=True (not null=True)",
        "on_delete=CASCADE on all ForeignKeys",
        "Auto-sets published_at when first published",
    ],
    "Things to discuss": [
        "Slug auto-generation: what happens with duplicate titles?",
        "No max_length on TextField fields (fine, but intentional?)",
        "No signal to auto-create UserProfile on User creation",
        "published_at ordering may show unpublished posts oddly",
    ]
}

for category, points in review_points.items():
    print(f"\n{category}:")
    for point in points:
        print(f"  - {point}")
```

    Django models generated by AI
    ==================================================
    
    What the AI got right:
      - Used OneToOneField (not ForeignKey) for UserProfile
      - Custom manager correctly overrides get_queryset()
      - auto_now_add vs auto_now used correctly
      - ManyToManyField with blank=True (not null=True)
      - on_delete=CASCADE on all ForeignKeys
      - Auto-sets published_at when first published
    
    Things to discuss:
      - Slug auto-generation: what happens with duplicate titles?
      - No max_length on TextField fields (fine, but intentional?)
      - No signal to auto-create UserProfile on User creation
      - published_at ordering may show unpublished posts oddly


### Exercise 4: Fix the Duplicate Slug Problem

One of the review points above asks what happens when two posts have the same title. `slugify("Hello World")` gives `hello-world` both times, and the second save fails because `slug` is `unique=True`.

Write a plain-Python helper `unique_slug(title, existing)` that returns `slugify(title)` if it's free, otherwise adds `-2`, `-3`, ... until it finds an unused slug. Use the simple `slugify` below so you don't need Django installed.


```python
import re

def slugify(text: str) -> str:
    """Simplified version of django.utils.text.slugify."""
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", text)


# Exercise 4: your code here
def unique_slug(title: str, existing: set[str]) -> str:
    ...

# Tests (uncomment when ready):
# assert unique_slug("Hello World", set()) == "hello-world"
# assert unique_slug("Hello World", {"hello-world"}) == "hello-world-2"
# assert unique_slug("Hello World", {"hello-world", "hello-world-2"}) == "hello-world-3"
# print("Exercise 4 passed")
```

<details markdown="1">
<summary>Show solution</summary>

```python
def unique_slug(title: str, existing: set[str]) -> str:
    base = slugify(title)
    slug, n = base, 2
    while slug in existing:
        slug = f"{base}-{n}"
        n += 1
    return slug


assert unique_slug("Hello World", set()) == "hello-world"
assert unique_slug("Hello World", {"hello-world"}) == "hello-world-2"
assert unique_slug("Hello World", {"hello-world", "hello-world-2"}) == "hello-world-3"
print("Exercise 4 passed")

# In the real Post.save(), "existing" would come from the database:
#   set(Post.objects.filter(slug__startswith=base).values_list("slug", flat=True))
```

</details>

### AI-Generated Django Admin Configuration

Django admin setup is a great job for AI: it's repetitive, full of boilerplate, and easy to check by opening the admin page.


```python
# Prompt: "Generate Django admin.py for the blog models above.
#          Include list_display, search_fields, list_filter,
#          prepopulated_fields for slugs, and inline for comments."

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
print("\nThis is where AI saves real time: it knows the admin API well.")
print("But you still need to know what each option does to check it.")
```

    Django admin.py — AI-generated output
    --------------------------------------------------
    Time to generate manually: ~15-20 minutes
    Time with AI:              ~30 seconds
    
    This is where AI saves real time: it knows the admin API well.
    But you still need to know what each option does to check it.


**Quick recap**

- Pick Django for full-stack apps with admin and auth; pick FastAPI for lean, async APIs.
- AI is very good at Django boilerplate: models, managers, `admin.py`.
- Review the design questions it skips, like duplicate slugs or auto-creating a `UserProfile`.

---

## 6. AI for Infrastructure: Docker & Nginx

### Why AI Is Good at Infrastructure Files

Docker configuration is:

- **pattern-heavy**: every app of the same type looks much the same
- **easy to get slightly wrong**: a missing port, volume or healthcheck
- **slow to look up** from scratch every time

That makes it a good fit for AI generation, as long as you check the result.

### Prompt for a Full-Stack Docker Setup

```text
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
# AI-generated Docker Compose, Nginx config and Dockerfile, with review notes.

docker_compose = '''
# docker-compose.yml (AI-generated, reviewed)
# Reviewed: removed the AI's `version: "3.9"` line. Compose v2 ignores it
# and prints a warning that it is obsolete.

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
# nginx/nginx.conf (AI-generated)

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
# Dockerfile (AI-generated multi-stage build)

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
    "Host and X-Forwarded-* headers passed on, so Django sees the real host and client IP",
    "Static files served by Nginx, not gunicorn",
]
for d in decisions:
    print(f"  [ok]    {d}")

print("\nWhat AI missed (always check):")
missed = [
    "HTTPS/TLS configuration (needs certbot or cert volume)",
    "Django migration command on startup",
    "Rate limiting in Nginx",
    "Log rotation configuration",
    "Prompt asked Nginx to proxy only /api/; the config proxies everything at /",
    "collectstatic runs at build time, so settings must import without real secrets",
    "Dockerfile runs as root (no USER line) and has no CMD of its own",
]
for m in missed:
    print(f"  [check] {m}")
```

    Infrastructure files generated by AI:
    ==================================================
      docker-compose.yml        (58 lines)
      nginx/nginx.conf          (26 lines)
      Dockerfile                (14 lines)
    
    Key decisions AI made correctly:
      [ok]    postgres:16-alpine (not latest — pinned version)
      [ok]    healthcheck with condition: service_healthy (not just depends_on)
      [ok]    Secrets via environment variables, not hardcoded
      [ok]    Named volumes (not bind mounts) for production data
      [ok]    Multi-stage Dockerfile (builder → final) reduces image size
      [ok]    Host and X-Forwarded-* headers passed on, so Django sees the real host and client IP
      [ok]    Static files served by Nginx, not gunicorn
    
    What AI missed (always check):
      [check] HTTPS/TLS configuration (needs certbot or cert volume)
      [check] Django migration command on startup
      [check] Rate limiting in Nginx
      [check] Log rotation configuration
      [check] Prompt asked Nginx to proxy only /api/; the config proxies everything at /
      [check] collectstatic runs at build time, so settings must import without real secrets
      [check] Dockerfile runs as root (no USER line) and has no CMD of its own


### Exercise 5: Write a Follow-Up Prompt

The review found several gaps (no migrations on startup, root user in the Dockerfile, `/api/` vs `/` proxying). Write **one** follow-up prompt that asks the AI to fix the Dockerfile and the Nginx config without rewriting the parts that were already fine.

<details markdown="1">
<summary>Show solution</summary>

```text
Here are the Dockerfile and nginx.conf you generated earlier: [paste both].

Please make these changes and keep everything else the same:

1. Dockerfile: create a non-root user and switch to it before the app runs.
   Install packages into a virtual environment (/opt/venv) instead of
   /root/.local so the non-root user can use them.
2. Dockerfile: add a CMD that starts gunicorn on 0.0.0.0:8000.
3. nginx.conf: proxy only /api/ (and /admin/) to Django. Keep serving
   /static/ directly.

Show the full updated files, then list each change in one line so I can
review it.
```

</details>

**Quick recap**

- Infrastructure files follow strong patterns, so AI drafts them well.
- Check the details: pinned image versions, healthchecks, secrets in `.env`, non-root users.
- Compare the output with your prompt: here the AI proxied `/` when we asked for `/api/`.
- Follow-up prompts work best when you list exact changes and say "keep everything else".

---

## 7. AI Agents in Development

### From Autocomplete to Agents

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

### What Makes Something an "Agent"?

An **AI agent** is a system that loops through four steps:

1. **Perceive** its environment (read files, browse docs, run commands)
2. **Reason** about what to do next (the LLM picks the next step)
3. **Act** using tools (write files, run code, call APIs)
4. **Observe** the result and **iterate** (read the error output, try again)

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
         Done (or loop again)
```

### Agent Tools for Developers

| Tool | What it does | Kind |
|------|--------------|------|
| GitHub Copilot agent mode | Works across your whole VS Code workspace | Coding agent |
| Cursor (agent / Composer) | Multi-file editing agent inside the editor | Coding agent |
| Claude Code | Terminal agent that reads, edits and runs code in your repo | Coding agent |
| Aider | CLI agent that reads/writes files and commits to git | Coding agent |
| Devin | Commercial "autonomous software engineer" | Experimental agent |
| LangChain / LangGraph | Build your own agents in Python | Framework |
| CrewAI | Multi-agent orchestration | Framework |
| AutoGen (Microsoft) | Multi-agent conversation framework | Framework |

### Demo: An Agent Loop in Plain Python

The cell below fakes the LLM part (the steps are written in advance) so you can see the loop itself. In a real agent, the LLM would choose each step after reading the previous result.


```python
# A simple agent loop, simulated in pure Python (no AI library needed).

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
    print(f"AGENT GOAL: {goal}")
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
            print(f"  Result: ERROR - unknown tool '{tool_name}'")

    print("\n" + "=" * 60)
    print("Agent finished all steps")


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

    AGENT GOAL: Add a health check endpoint to the FastAPI app
    ============================================================
    
    Step 1: [read_file]
      Reason: Read existing code to understand current structure
      Args:   {"path": "main.py"}
      Result: from fastapi import FastAPI
    app = FastAPI()
    
    
    Step 2: [write_file]
      Reason: Write updated main.py with health endpoint added
      Args:   {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health_check():\n    return {'status': 'ok'}\n"}
      Result: SUCCESS: Wrote 113 bytes to main.py
    
    Step 3: [run_tests]
      Reason: Verify nothing is broken after the change
      Args:   {"test_path": "test_main.py"}
      Result: PASSED: 3 tests passed in 0.42s
    
    ============================================================
    Agent finished all steps


### Exercise 6: Give the Agent a New Tool

Add a `list_files` tool that returns the names of the mock files (`main.py`, `requirements.txt`) as a comma-separated string. Register it in `TOOLS` and run `simulate_agent` with a plan whose **first** step is `list_files`.


```python
# Exercise 6: your code here

```

<details markdown="1">
<summary>Show solution</summary>

```python
MOCK_FILES = ["main.py", "requirements.txt"]

def list_files_tool() -> str:
    """Simulated directory listing."""
    return ", ".join(MOCK_FILES)

TOOLS["list_files"] = list_files_tool

simulate_agent(
    goal="Find out what the project contains",
    planned_steps=[
        {"tool": "list_files", "args": {}, "reason": "See which files exist"},
        {"tool": "read_file", "args": {"path": "requirements.txt"},
         "reason": "Check which libraries are used"},
    ],
)
```

</details>

**Quick recap**

- Autocomplete suggests a line, chat answers a question, an agent carries out a multi-step task.
- An agent is an LLM in a loop: perceive, reason, act with tools, observe, repeat.
- The tools are ordinary functions; the LLM just decides which one to call next.

---

## 8. Pitfalls, Hallucinations & Security

### The Five Biggest Risks of Vibe Coding

| Risk | What happens |
|------|--------------|
| 1. Hallucinations | The AI invents functions, parameters or libraries that don't exist. It sounds confident. It's wrong. |
| 2. Outdated code | Training has a cutoff. You may get Pydantic v1 code when you use v2, or old Django patterns. |
| 3. Security holes | SQL injection, hardcoded secrets, missing permission checks. |
| 4. Skill atrophy | If you accept code you don't understand, you stop learning and come to depend on the tool. |
| 5. Licensing / IP | The AI may reproduce copyrighted code from its training data. Know your organisation's AI policy. |

### Hallucination Examples

Each snippet below contains a mistake an AI really does make. Try to spot it before reading the comment.


```python
# Spot the hallucinations: each snippet contains a typical AI mistake.

print("=" * 60)
print("HALLUCINATION EXAMPLES: spot the bug")
print("=" * 60)

# Example 1: non-existent FastAPI parameter
example_1 = '''
# AI generated this. What's wrong?
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
async def get_items(limit: int = Query(default=10, max_value=100)):
    ...  # Bug: FastAPI's Query uses `le=` not `max_value=`
         # Correct: Query(default=10, le=100)
         # (Query is also never imported.)
'''

# Example 2: invented Django ORM method
example_2 = '''
# AI generated this. What's wrong?
# "Use the .recent() manager method to get the latest 5 posts."

posts = Post.objects.recent(5)  # Bug: .recent() does not exist!
                                 # Correct: Post.objects.order_by('-created_at')[:5]
'''

# Example 3: outdated Pydantic API
example_3 = '''
# AI generated this Pydantic v2 code. What's wrong?
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

    @validator("age")      # Bug: @validator is the Pydantic v1 API
    def age_must_be_positive(cls, v):
        ...                # (deprecated in v2, and not imported here)
                           # Correct v2: @field_validator("age") + @classmethod
'''

# Example 4: insecure advice
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
    ("FastAPI - wrong Query parameter name", "max_value= doesn't exist -> use le="),
    ("Django ORM - invented method", ".recent() doesn't exist -> use .order_by()"),
    ("Pydantic v2 - outdated decorator", "@validator is the v1 API -> use @field_validator"),
    ("Security - broken hash function", "MD5 is broken for passwords -> use bcrypt or argon2"),
]

print("\nHallucination Summary:")
print("-" * 60)
for i, (category, fix) in enumerate(examples, 1):
    print(f"  {i}. {category}")
    print(f"     Fix: {fix}")
    print()
```

    ============================================================
    HALLUCINATION EXAMPLES: spot the bug
    ============================================================
    
    Hallucination Summary:
    ------------------------------------------------------------
      1. FastAPI - wrong Query parameter name
         Fix: max_value= doesn't exist -> use le=
    
      2. Django ORM - invented method
         Fix: .recent() doesn't exist -> use .order_by()
    
      3. Pydantic v2 - outdated decorator
         Fix: @validator is the v1 API -> use @field_validator
    
      4. Security - broken hash function
         Fix: MD5 is broken for passwords -> use bcrypt or argon2
    


### Common Security Issues in AI-Generated Code

These map to categories from the [OWASP Top 10](https://owasp.org/www-project-top-ten/) (2021 numbering).


```python
# OWASP Top 10 issues that show up in AI-generated code.

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
        "ai_code": "token = base64.b64encode(str(user.id).encode()).decode()  # NOT a token!",
        "fix": "Use a signed JWT (e.g. PyJWT) or secrets.token_urlsafe() for random tokens",
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
        "owasp": "A09 - Security Logging and Monitoring Failures",
        "ai_code": "print(f'Login attempt: {username} / {password}')",
        "fix": "Never log passwords. Log: 'Login attempt for user {username}'",
    },
]

for issue in security_issues:
    print(f"\n{issue['owasp']}")
    print(f"   AI Generated: {issue['ai_code'].splitlines()[0]}")
    print(f"   Fix:          {issue['fix']}")
```

    Common OWASP Issues in AI-Generated Python Code
    ============================================================
    
    A01 - Broken Access Control
       AI Generated: @app.delete('/users/{user_id}')
       Fix:          Always verify current_user.id == user_id or current_user.is_admin
    
    A02 - Cryptographic Failures
       AI Generated: token = base64.b64encode(str(user.id).encode()).decode()  # NOT a token!
       Fix:          Use a signed JWT (e.g. PyJWT) or secrets.token_urlsafe() for random tokens
    
    A03 - Injection
       AI Generated: cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
       Fix:          Use parameterized queries: cursor.execute('...WHERE name = %s', (name,))
    
    A05 - Security Misconfiguration
       AI Generated: SECRET_KEY = 'dev-secret-key-12345'  # Hardcoded in settings.py
       Fix:          SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # From env vars
    
    A09 - Security Logging and Monitoring Failures
       AI Generated: print(f'Login attempt: {username} / {password}')
       Fix:          Never log passwords. Log: 'Login attempt for user {username}'


### Exercise 7: Fix the SQL Injection

The function below is the A03 example in runnable form, using an in-memory SQLite database. Pass it the name `x' OR '1'='1` and it returns **every** user. Rewrite it with a parameterised query so that input returns nothing.


```python
import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (name TEXT, email TEXT)")
conn.executemany("INSERT INTO users VALUES (?, ?)",
                 [("alice", "alice@example.com"), ("bob", "bob@example.com")])

def find_user_unsafe(name: str):
    return conn.execute(f"SELECT * FROM users WHERE name = '{name}'").fetchall()

print(find_user_unsafe("alice"))
print(find_user_unsafe("x' OR '1'='1"))   # leaks every row


# Exercise 7: your code here
def find_user_safe(name: str):
    ...

# Tests (uncomment when ready):
# assert find_user_safe("alice") == [("alice", "alice@example.com")]
# assert find_user_safe("x' OR '1'='1") == []
# print("Exercise 7 passed")
```

    [('alice', 'alice@example.com')]
    [('alice', 'alice@example.com'), ('bob', 'bob@example.com')]


<details markdown="1">
<summary>Show solution</summary>

```python
def find_user_safe(name: str):
    # The ? placeholder sends name as data, never as part of the SQL text.
    return conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall()


assert find_user_safe("alice") == [("alice", "alice@example.com")]
assert find_user_safe("x' OR '1'='1") == []
print("Exercise 7 passed")
```

</details>

**Quick recap**

- The big five risks: hallucinations, outdated code, security holes, skill atrophy, licensing.
- Hallucinations look plausible: `max_value=`, `.recent()`, `@validator` in v2.
- Check AI code against the OWASP list: access control, crypto, injection, config, logging.
- Parameterised queries, hashed passwords (bcrypt/argon2) and secrets from env vars are non-negotiable.

---

## 9. What AI Cannot Replace

### The Human Edge

AI assistants keep getting better, but they still struggle with these:

| Area | Why it still needs you |
|------|------------------------|
| Problem understanding | The AI doesn't know what your users or business actually need. It optimises for the prompt, not the real problem. |
| System architecture | Monolith or microservices? Event-driven or request-response? These need domain knowledge and long-term thinking. |
| Debugging complex systems | Race conditions, memory leaks and intermittent failures in distributed systems need careful investigation and intuition. |
| Communication & requirements | Turning fuzzy stakeholder wishes into a precise spec is a human conversation. |
| Ethical & product judgement | "Should we build this?" "Is this use of data appropriate?" The AI can't answer these responsibly. |
| Security review | Threat modelling, penetration testing and understanding business risk need real expertise. |

### Fundamentals Make AI More Useful

| Programmer | How much AI helps | Risk |
|------------|-------------------|------|
| Strong fundamentals | A lot: it speeds up what they already know how to do | Low: they spot mistakes |
| Intermediate | Quite a lot: it fills knowledge gaps quickly | Medium: may miss subtle issues |
| Beginner (weak fundamentals) | Less than you'd think: they can't tell if it's right | High: blind trust in wrong code |

> **The paradox of vibe coding:** AI is most valuable to those who need it least, and most dangerous to those who need it most.

### Class Discussion (5 minutes)

1. Think of a project you've worked on. Which parts would AI have helped with most? Which parts would have been dangerous to hand over?
2. If AI can write code, what should computer science education focus on?
3. How do you check that AI-generated code is correct?

**Quick recap**

- AI can't understand your users, choose your architecture, or make ethical calls for you.
- Hard debugging and security review still need human expertise.
- Strong fundamentals are what make AI useful; without them, AI is a risk.

---

## 10. Best Practices & Responsible Workflow

### The Professional AI-Assisted Workflow

```
         YOU define the goal
         and break it into tasks
                  │
                  ▼
         ┌────────────────┐
    ┌───►│   GENERATE     │  ← Write a clear, specific prompt
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
    └────┤     TEST       │  ← Write tests, run them
         └────────────────┘
                  │
                  ▼
               OWN IT
         (You are responsible
          for this code now)
```

### The Golden Rules

1. **Never accept code you don't understand.** If you can't explain a function line by line, keep asking the AI to explain it until you can.
2. **Always run the code.** AI code can look right and still be wrong. Test it with real inputs.
3. **Security-review everything**, especially authentication, database queries, input validation and secret handling.
4. **Pin your library versions.** The AI may be writing for a different version than the one you have installed.
5. **Iterate with feedback.** Paste the actual error message back to the AI. The best follow-up prompts include it.
6. **Use AI for what it's good at:** boilerplate, documentation, tests and refactoring. Keep system design for yourself.
7. **Keep building your fundamentals.** The more you know, the better you'll be at working with AI.

### Demo: Debugging with AI

Here's rule 5 in action. We find a bug, write a good prompt about it, apply the fix and test it.


```python
# Simulating the debug -> prompt -> fix -> test loop with an AI assistant.

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
print(f"  Got:      ${result:.2f}  <- wrong: 20 was treated as 2000%")

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
print("  - the actual code")
print("  - the inputs used")
print("  - the expected output")
print("  - the actual output received")

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
    status = "PASS" if passed else "FAIL"
    print(f"  {status} discount({price}, {pct}%) = ${result:.3f} (expected ${expected:.3f})")
    if not passed:
        all_pass = False

print(f"\nAll tests passed: {all_pass}")
```

    Debugging Workflow with AI Assistance
    ============================================================
    
    Step 1: Observe unexpected behaviour
      Price: $100, Discount: 20%
      Expected: $80.00
      Got:      $-1900.00  <- wrong: 20 was treated as 2000%
    
    Step 2: Craft a precise prompt to AI
    ----------------------------------------
    Good prompt includes:
      - the actual code
      - the inputs used
      - the expected output
      - the actual output received
    
    Step 3: AI Response (simulated)
    ----------------------------------------
    The bug: discount_pct should be divided by 100 if passed as
    a percentage (0-100) rather than a fraction (0.0-1.0).
    
    Step 4: Apply and verify the fix
    ----------------------------------------
      PASS discount(100.0, 20%) = $80.000 (expected $80.000)
      PASS discount(200.0, 50%) = $100.000 (expected $100.000)
      PASS discount(99.99, 10%) = $89.991 (expected $89.991)
      PASS discount(0.0, 100%) = $0.000 (expected $0.000)
    
    All tests passed: True


### Exercise 8: Prompt Engineering Challenge

For each task, write the prompt you would send to Copilot Chat or Claude. Use the checklist from Section 3 (role, context, task, specifics, constraints, format). Then compare with the example prompt, and if you have time, share your best one with the class.

#### Challenge 1: Django REST Framework ViewSet

Create a DRF ViewSet for the `Post` model from our blog app. It should support list, retrieve, create, update and destroy. Only authenticated users can create, update or delete.

*Hint:* mention the DRF version, permission classes and serializer requirements.

<details markdown="1">
<summary>Show solution</summary>

```text
You are an experienced Django developer. I'm using Django 5 and
Django REST Framework 3.15.

Using the Post model below [paste models.py], create:
- a PostSerializer (ModelSerializer) exposing id, title, slug, content,
  author (read-only, username), tags, is_published, published_at
- a PostViewSet (ModelViewSet) supporting list, retrieve, create,
  update, partial_update and destroy
- permission_classes = [IsAuthenticatedOrReadOnly] so anyone can read
  but only logged-in users can write
- perform_create() that sets author to request.user
- the router registration for urls.py

Use type hints where they make sense. Don't change the model.
```

</details>

#### Challenge 2: FastAPI Middleware for Request Timing

Add middleware to the FastAPI app that logs the HTTP method, path, status code and response time for every request.

*Hint:* mention Python's `logging` module (not `print()`) and async middleware.

<details markdown="1">
<summary>Show solution</summary>

```text
I have a FastAPI app (FastAPI 0.115, Python 3.12) in main.py.

Write an HTTP middleware using @app.middleware("http") that, for every
request, logs one line with:
- HTTP method
- path
- response status code
- response time in milliseconds (use time.perf_counter())

Requirements:
- Use the standard logging module with a logger named "app.requests",
  not print()
- The middleware must be async and must not change the response
- Also log (at ERROR level) if the handler raises, then re-raise

Show only the middleware function and the logging setup.
```

</details>

#### Challenge 3: Docker Multi-Stage Build for FastAPI

Write a Dockerfile that uses a multi-stage build to produce a minimal FastAPI production image under 200 MB.

*Hint:* mention `python:3.12-slim`, `pip install --user` and copying from the builder stage.

<details markdown="1">
<summary>Show solution</summary>

```text
Write a multi-stage Dockerfile for a FastAPI app.

Project layout: app/main.py contains `app = FastAPI()`; dependencies are
in requirements.txt (fastapi, uvicorn[standard], sqlalchemy).

Requirements:
- Builder stage: python:3.12-slim, install dependencies with
  pip install --user --no-cache-dir
- Final stage: python:3.12-slim, copy only the installed packages
  from the builder and the app/ folder
- Run as a non-root user
- PYTHONUNBUFFERED=1 and PYTHONDONTWRITEBYTECODE=1
- EXPOSE 8000 and CMD running uvicorn on 0.0.0.0:8000
- Final image must be under 200 MB

Add a short comment above each step explaining why it's there.
```

</details>

#### Challenge 4: Pytest Fixtures for FastAPI

Write pytest fixtures for testing the Task Manager API. Use an in-memory SQLite database that resets between tests.

*Hint:* mention `TestClient`, overriding the `get_db` dependency, and `scope="function"`.

<details markdown="1">
<summary>Show solution</summary>

```text
I'm testing the FastAPI Task Manager app below [paste main.py].
It uses SQLAlchemy 2.0 and a get_db() dependency.

Write a conftest.py with pytest fixtures that:
- create an in-memory SQLite engine (sqlite:// with StaticPool and
  check_same_thread=False so all connections share one database)
- create all tables before each test and drop them after
  (scope="function", so every test starts empty)
- override the get_db dependency with app.dependency_overrides
- provide a `client` fixture using fastapi.testclient.TestClient

Then write two example tests using the client: creating a task returns
201, and getting a missing task returns 404.
```

</details>

**Quick recap**

- Follow the loop: generate, review, refine, test, own.
- Never accept code you can't explain, and always run it.
- When debugging with AI, give it the code, the input, the expected output and the actual output.
- Good prompts name versions, constraints and exactly what you want back.

---

## Summary & Cheat Sheet

| Topic | Remember this |
|-------|---------------|
| Vibe coding | It's a spectrum. Professionals use AI as a collaborator, not a replacement. |
| AI toolkit | Copilot, Cursor, Claude, Aider: each has its place. Know your tools and their limits. |
| Prompting | Be specific. Context + constraints = better output. |
| FastAPI | AI scaffolds most of an API correctly. You find and fix the rest. |
| Django | AI is great at models and admin. Business rules need you. |
| Docker | Infrastructure files are pattern-heavy, so AI drafts them well. Check every detail. |
| Agents | An LLM in a loop, using tools to finish multi-step tasks. |
| Pitfalls | Hallucinations, outdated APIs, security holes. Always review. |
| Human edge | Architecture, hard debugging, ethics and communication stay with you. |
| Workflow | Generate → Review → Refine → Test → Own. Never skip review. |

### The Mindset

> Think of AI as a very fast junior developer who never sleeps and has read every framework's docs, but who sometimes makes things up with total confidence and has no idea what your business needs.
>
> Your job is to be the senior developer who reviews, guides, corrects and takes responsibility.

### Recommended Resources

| Resource | Link |
|----------|------|
| GitHub Copilot docs | https://docs.github.com/en/copilot |
| Andrej Karpathy (origin of "vibe coding") | https://x.com/karpathy |
| Aider (CLI AI coding) | https://aider.chat |
| LangChain docs | https://python.langchain.com |
| OWASP Top 10 | https://owasp.org/www-project-top-ten/ |
| Prompt Engineering Guide | https://www.promptingguide.ai |

### Assignment Preview

Using AI assistance, build a **REST API** on a topic of your choice using **FastAPI** or **Django REST Framework**.

Requirements:

- At least 3 models with relationships
- Full CRUD for at least one resource
- JWT authentication
- A `Dockerfile` and `docker-compose.yml` that run the app
- A `PROMPTS.md` file documenting the prompts you used and what you changed in the AI output

**`PROMPTS.md` is the most important deliverable.** It shows that you reviewed, understood and improved the AI's work.

### Self-Assessment

Answer each question in your head (or on paper) before opening the answers.

1. What is the most important thing to do with AI-generated code?
2. What is a hallucination in the context of AI coding tools?
3. Name two things that make a prompt more effective.
4. What is the difference between AI autocomplete and an AI agent?
5. Why are developers with strong fundamentals more effective at using AI?

<details markdown="1">
<summary>Show answers</summary>

```text
1. Read and understand every line before using it.
2. When the AI confidently generates code that uses functions, parameters
   or APIs that don't exist.
3. Specific context (framework, versions, constraints) and a clear task.
4. An agent takes multi-step actions with tools (reads files, writes code,
   runs tests) and reacts to the results; autocomplete only suggests the
   next bit of code.
5. They can judge the AI's output, spot its mistakes and steer it toward
   a correct solution.
```

</details>

### What's Next

Next up is the **Project Description (PRG400)**. You're allowed to use AI tools on the course project, but you must be able to explain every line you submit, so put this notebook's workflow into practice there.
