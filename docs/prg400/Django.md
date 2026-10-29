# Django

In this notebook we build a blog platform with Django and Django REST Framework (DRF). We start with one plain JSON view and end with a token-protected REST API, nested comment URLs and a customised admin site.

### Learning Objectives

By the end of this notebook you will be able to:

1. Create a Django project and app from scratch
2. Define models and run database migrations
3. Query the database with the Django ORM
4. Write function-based and class-based views and connect them to URLs
5. Build a REST API with DRF serializers, ViewSets and routers
6. Protect endpoints with token authentication and permissions
7. Manage your data with the Django admin site

### Prerequisites

- Python 3.10 or newer
- The OOP notebook (classes, inheritance, decorators) and some HTTP basics
- The FastAPI notebook is helpful but not required. We compare the two frameworks a few times.

Install everything used in this notebook:

```bash
pip install django djangorestframework drf-nested-routers django-filter
```

### How to Use This Notebook

- Work through it **top to bottom**. Each section adds to the same project, called `blogplatform`.
- The code cells are **not meant to be run inside Jupyter**. Django code has to live inside a project. Each cell tells you where it goes:
    - `# file: blog/models.py` means the cell is the full content of that file. Create (or replace) the file and paste it in.
    - `# add to: blogplatform/settings.py` means paste the cell into the existing file.
    - `# run in: python manage.py shell` means type or paste it into the Django shell.
    - Cells marked *Illustration* are short pieces to read, not to copy.
- Run terminal commands (`python manage.py ...`) from the outer `blogplatform/` folder, the one that contains `manage.py`.
- Try each **Exercise** yourself before opening *Show solution*.
- Each section ends with a **Quick recap**. Read just the recaps when revising.

---

## What We're Building

We will build the **Blog Platform**: a web application with a REST API for blog posts, comments and authors.

```
Browser / curl / Postman
          |
          | HTTP
          v
    [ Django + DRF ]       <-- your Python code
          |
          | ORM
          v
       [ SQLite ]          <-- db.sqlite3
```

### Final Endpoint Table

| Method | Path                          | Auth          | Description               |
|--------|-------------------------------|---------------|---------------------------|
| GET    | `/api/posts/`                 | None          | List all posts            |
| POST   | `/api/posts/`                 | Token         | Create a post             |
| GET    | `/api/posts/{id}/`            | None          | Get one post with comments|
| PUT    | `/api/posts/{id}/`            | Token + Owner | Update a post             |
| DELETE | `/api/posts/{id}/`            | Token + Owner | Delete a post             |
| POST   | `/api/posts/{id}/publish/`    | Token + Owner | Publish a post            |
| POST   | `/api/posts/{id}/unpublish/`  | Token + Owner | Unpublish a post          |
| GET    | `/api/posts/{id}/comments/`   | None          | List comments on a post   |
| POST   | `/api/posts/{id}/comments/`   | Token         | Add a comment             |
| POST   | `/api/auth/register/`         | None          | Register a user           |
| POST   | `/api/auth/token/`            | None          | Get an auth token         |
| DELETE | `/api/auth/token/revoke/`     | Token         | Log out (delete token)    |

### Project Structure

```
blogplatform/
├── manage.py
├── blogplatform/          <- project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── blog/                  <- our app
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── permissions.py
    └── admin.py
```

**Quick recap**

- One Django **project** (`blogplatform`) holds the settings; one **app** (`blog`) holds our code.
- Anyone can read posts and comments. Writing needs a token, and only the author may change their own post.

---

## 1. Setup & First View

### Django vs FastAPI

|  | Django | FastAPI |
|----|----|----|
| Philosophy | Batteries included: ORM, admin, auth and templates built in | Small core, add what you need |
| Data validation | Forms / DRF serializers | Pydantic models |
| Auto docs | Not built in (DRF gives a browsable API) | Swagger UI + ReDoc |
| Async support | Async views since 3.1; ORM mostly sync | Native async/await |
| Best for | Full web apps, content sites, admin-heavy projects | Fast APIs, microservices |

### Creating a Project

```bash
django-admin startproject blogplatform
cd blogplatform
python manage.py startapp blog
```

`startproject` creates the configuration package (settings, root URLs). `startapp` creates one **app**: a self-contained folder with its own models, views and URLs. A Django project is made of one or more apps.

### Registering the App

Open `blogplatform/settings.py` and add DRF and our app to the `INSTALLED_APPS` list that's already there:


```python
# add to: blogplatform/settings.py  (edit the existing INSTALLED_APPS)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',          # <- Django REST Framework
    'rest_framework.authtoken', # <- Token authentication
    'blog',                    # <- our app
]
```

### Running the Development Server

```bash
python manage.py migrate      # apply the built-in migrations (creates db.sqlite3)
python manage.py runserver    # start the dev server at http://127.0.0.1:8000
```

### Your First View

A **view** is a Python function (or class) that receives an `HttpRequest` and returns an `HttpResponse`. `JsonResponse` is an `HttpResponse` that turns a dict into JSON for you.


```python
# file: blog/views.py  (Section 1 checkpoint)
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok", "version": "1.0.0"})
```

Now connect it to a URL. The app gets its own `urls.py`, and the project's `urls.py` includes it under `api/`:


```python
# file: blog/urls.py  (Section 1 checkpoint; create this file)
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health),
]
```


```python
# file: blogplatform/urls.py  (include the app URLs)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('blog.urls')),
]
```

Visit `http://127.0.0.1:8000/api/health/` and Django returns `{"status": "ok", "version": "1.0.0"}`.

The full URL is the two pieces joined: `api/` from the project's `urls.py` plus `health/` from the app's `urls.py`.

### Exercise 1: Ping

Add a `GET /api/ping/` view that returns `{"message": "pong", "timestamp": <current UTC time as a string>}`. Use `datetime` from Python's standard library.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/views.py
from datetime import datetime, timezone


def ping(request):
    return JsonResponse({
        "message": "pong",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# add to: blog/urls.py  (inside urlpatterns)
# path('ping/', views.ping),
```

</details>

**Quick recap**

- `startproject` makes the config package; `startapp` makes an app. Add the app to `INSTALLED_APPS`.
- A view takes a request and returns a response. `JsonResponse(dict)` returns JSON.
- URLs are split: the project's `urls.py` uses `include()` to hand a prefix over to the app's `urls.py`.

---

## 2. Models & Migrations

### What Is a Django Model?

A **model** is a Python class that maps to a database table. Each class attribute is a column. Django's ORM turns Python code into SQL for you.


```python
# Illustration: the smallest possible model
from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=200)
    body  = models.TextField()
```

Django names the table `blog_post`: app name plus model name, in lowercase.

### Common Field Types

| Field | Python type | SQL type |
|----|----|----|
| `CharField(max_length=N)` | `str` | VARCHAR(N) |
| `TextField()` | `str` | TEXT |
| `IntegerField()` | `int` | INTEGER |
| `FloatField()` | `float` | REAL |
| `BooleanField()` | `bool` | BOOLEAN |
| `DateTimeField(auto_now_add=True)` | `datetime` | DATETIME (set once, on create) |
| `DateTimeField(auto_now=True)` | `datetime` | DATETIME (set on every save) |
| `ForeignKey(Model, on_delete=...)` | the related object | INTEGER + foreign key constraint |

### Relationships


```python
# Illustration (fields shortened)
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    # CASCADE: deleting a Post also deletes all its Comments
    # related_name: lets you do post.comments.all()
```

### The Migration Workflow

```
Edit models.py
      |
      v
python manage.py makemigrations   <- writes a migration file in blog/migrations/
      |
      v
python manage.py migrate          <- runs it against the database
```

Run both commands every time you change a model. Don't edit migration files by hand unless you really know what you're doing.

### Inspecting the Schema

```bash
python manage.py sqlmigrate blog 0001
# prints the SQL Django will run. Great for learning what the ORM does.
```

Here is the full `models.py` for the project:


```python
# file: blog/models.py  (Section 2 checkpoint)

from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    title      = models.CharField(max_length=200)
    slug       = models.SlugField(unique=True)
    body       = models.TextField()
    published  = models.BooleanField(default=False)
    author     = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']   # newest first by default

    def __str__(self):
        return self.title


class Comment(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author} on "{self.post}"'
```

**What just happened?**

- `author` links each post to Django's built-in `User` model, so we get user accounts and passwords for free.
- `related_name='posts'` means you can write `alice.posts.all()`. Likewise `post.comments.all()` for comments.
- `class Meta: ordering = ['-created_at']` makes every query return the newest posts first unless you ask otherwise.
- `__str__` controls how a post is shown in the shell and the admin site.

Now create the tables:

```bash
python manage.py makemigrations blog
python manage.py migrate
```

### Exercise 2: Slug and Published Flag

Suppose your `Post` model started without `slug` and `published`. Add a `slug` field (`SlugField(unique=True)`) and a `published` boolean field (default `False`), run `makemigrations` and `migrate`, and check the new columns with `sqlmigrate`.

(The checkpoint above already includes both, so compare your answer with it.)

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/models.py  (inside class Post)
slug      = models.SlugField(unique=True)
published = models.BooleanField(default=False)

# Then in the terminal:
#   python manage.py makemigrations blog
#   python manage.py migrate
#   python manage.py sqlmigrate blog 0002    # the number of your new migration
#
# If the table already has rows, makemigrations asks for a default for `slug`.
# A unique field can't share one default, so the easiest fix while learning is
# to delete db.sqlite3 and the files in blog/migrations/ (keep __init__.py)
# and start again.
```

</details>

**Quick recap**

- A model is a class; each field is a column. Django adds an `id` primary key for you.
- `ForeignKey(..., on_delete=models.CASCADE, related_name='...')` links tables and gives you a reverse lookup.
- Changed a model? `makemigrations`, then `migrate`. Every time.

---

## 3. Django ORM

All the code in this section runs in the **Django shell**, a Python prompt with your project already loaded:

```bash
python manage.py shell
```

Start with this session. It creates the user `alice` and a first post, which the later examples use. Run it only once: creating `alice` a second time fails because usernames are unique.

Since Django 5.2 the shell imports your models automatically. The `import` lines in the cells are still there so the code also works in older versions and in plain scripts.


```python
# run in: python manage.py shell

# Only needed if you run this as a plain script instead of in the shell:
# import django, os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogplatform.settings')
# django.setup()

from django.contrib.auth.models import User
from blog.models import Post, Comment

# Create a user (only needed once)
alice = User.objects.create_user(username='alice', password='secret123')

# CREATE
post = Post.objects.create(
    title='Getting Started with Python',
    slug='getting-started-python',
    body='Python is a versatile language...',
    author=alice,
    published=True,
)

# READ
all_posts    = Post.objects.all()
pub_posts    = Post.objects.filter(published=True)
alice_posts  = Post.objects.filter(author__username='alice').select_related('author')

# UPDATE
post.title = 'Getting Started with Python (Revised)'
post.save()

```

### The QuerySet

Every ORM query returns a **QuerySet**: a lazy, chainable list of model objects. "Lazy" means Django doesn't run any SQL until you actually need the results, for example when you loop over it, slice it or call `list()` on it.


```python
# run in: python manage.py shell
# Nothing hits the DB yet:
qs = Post.objects.filter(published=True)

# DB query fires here:
for post in qs:
    print(post.title)
```

### CRUD Operations

Here are create, read, update and delete side by side. Note the last two lines delete data; that's fine on a practice database.


```python
# run in: python manage.py shell
from blog.models import Post
from django.contrib.auth.models import User

author = User.objects.get(username='alice')

# CREATE
post = Post.objects.create(
    title='Hello Django',
    slug='hello-django',
    body='My first post.',
    author=author,
    published=True,
)

# READ: all
Post.objects.all()

# READ: filter
Post.objects.filter(published=True)
Post.objects.filter(author__username='alice')   # <- double-underscore traverses FK

# READ: single record (raises DoesNotExist if missing)
post = Post.objects.get(slug='hello-django')

# UPDATE
post.title = 'Hello Django (Updated)'
post.save()

# Bulk UPDATE (no .save() needed)
Post.objects.filter(published=False).update(published=True)

# DELETE
post.delete()
Post.objects.filter(published=False).delete()
```

### Lookups (Filtering)

| Lookup | Example | Meaning |
|----|----|----|
| `exact` (default) | `filter(title='Hello')` | `title = 'Hello'` |
| `icontains` | `filter(title__icontains='django')` | case-insensitive `LIKE` |
| `gt` / `gte` / `lt` / `lte` | `filter(id__gt=5)` | `>`, `>=`, `<`, `<=` |
| `in` | `filter(id__in=[1, 2, 3])` | `id IN (1, 2, 3)` |
| `isnull` | `filter(slug__isnull=True)` | `IS NULL` |
| Related field | `filter(author__username='alice')` | JOIN through the foreign key |

### `select_related` and `prefetch_related`

The **N+1 problem**: you load N posts with one query, then touching `post.author` runs one more query *per post*. These two methods fix it:


```python
# run in: python manage.py shell
# BAD (the N+1 problem): one query per post to fetch the author
for post in Post.objects.all():
    print(post.author.username)

# GOOD: single JOIN query
for post in Post.objects.select_related('author').all():
    print(post.author.username)

# For many-to-many or reverse FK (e.g., all comments per post)
posts = Post.objects.prefetch_related('comments').all()
```

Rule of thumb: `select_related` for a foreign key you follow *forwards* (post -> author, one object). `prefetch_related` for the *reverse* side or many-to-many (post -> comments, many objects).

### Exercise 3: Recent Python Posts

Write one QuerySet that returns the 5 most recently created **published** posts whose title contains `"python"` (any case). Chain the methods together.

<details markdown="1">
<summary>Show solution</summary>

```python
# run in: python manage.py shell
recent_python = (
    Post.objects
    .filter(published=True, title__icontains='python')
    .order_by('-created_at')[:5]
)
print(list(recent_python))
```

</details>

**Quick recap**

- `Model.objects` gives you QuerySets: `all()`, `filter()`, `exclude()`, `get()`, `order_by()`.
- QuerySets are lazy and chainable. SQL runs only when you use the results.
- Double underscores do lookups (`title__icontains`) and follow relations (`author__username`).
- Use `select_related` / `prefetch_related` to avoid the N+1 query problem.

---

## 4. Views & URL Patterns

Before we bring in DRF, let's see how far plain Django gets us. This helps you appreciate what DRF does for you in the next section.

### Function-Based Views (FBVs)

A function-based view can handle several HTTP methods in one function. Check `request.method` to decide what to do.


```python
# Illustration (blog/views.py)
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import Post

@csrf_exempt
@require_http_methods(['GET', 'POST'])
def post_list(request):
    if request.method == 'GET':
        posts = list(Post.objects.values('id', 'title', 'slug', 'published'))
        return JsonResponse(posts, safe=False)

    elif request.method == 'POST':
        data = json.loads(request.body)
        post = Post.objects.create(author=request.user, **data)
        return JsonResponse({'id': post.id}, status=201)
```

Two things to notice:

- **`@csrf_exempt`**: Django protects every POST, PUT and DELETE against CSRF attacks by default. That check expects a token that only Django's own HTML forms send, so a JSON request from curl gets `403 Forbidden`. We switch the check off for these demo views. DRF handles this properly for us later.
- **`author=request.user`**: every post needs an author. `request.user` is the logged-in user (or `AnonymousUser` if nobody is logged in, which is why the checkpoint below checks first).

### URL Patterns


```python
# Illustration (blog/urls.py)
from django.urls import path
from . import views

urlpatterns = [
    path('posts/',       views.post_list),   # /api/posts/
    path('posts/<int:pk>/', views.post_detail),  # /api/posts/42/
]
```

URL converters:

| Converter     | Matches                   | Example                |
|---------------|---------------------------|------------------------|
| `<int:pk>`    | digits                    | `/posts/42/` gives `pk=42` |
| `<str:slug>`  | anything except `/`       | `/posts/hello-world/`  |
| `<slug:slug>` | letters, digits, `-`, `_` | `/posts/hello-world/`  |
| `<uuid:id>`   | a UUID                    | `/items/550e8400-.../` |

### `get_object_or_404`


```python
# Illustration
from django.shortcuts import get_object_or_404

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)  # returns 404 if not found
    return JsonResponse({'id': post.id, 'title': post.title, 'body': post.body})
```

### Class-Based Views (CBVs)

With a class-based view, each HTTP method is its own method on the class. Django calls `get()` for GET requests, `delete()` for DELETE, and so on:


```python
# Illustration
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

class PostDetailView(View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        return JsonResponse({'id': post.id, 'title': post.title})

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.delete()
        return HttpResponse(status=204)   # 204 means "no content", so no body
```


```python
# Illustration (blog/urls.py)
path('posts/<int:pk>/', PostDetailView.as_view()),
```

### Exercise 4: A Post Detail View

Write a `post_detail` function-based view that handles:

- `GET`: return the post as JSON
- `PUT`: update `title` and `body` from the JSON request body
- `DELETE`: delete the post

Use `get_object_or_404`.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/views.py
@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'GET':
        return JsonResponse({'id': post.id, 'title': post.title, 'body': post.body})

    if request.method == 'PUT':
        data = json.loads(request.body)
        post.title = data.get('title', post.title)
        post.body = data.get('body', post.body)
        post.save()
        return JsonResponse({'id': post.id, 'title': post.title})

    post.delete()   # DELETE
    return HttpResponse(status=204)
```

</details>

Here is the full `views.py` and `urls.py` for this section. Compare how much code it takes; we'll replace all of it with a few lines of DRF in Section 6.


```python
# file: blog/views.py  (Section 4 checkpoint: plain Django views)

import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Post


def health(request):
    return JsonResponse({"status": "ok", "version": "1.0.0"})


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def post_list(request):
    if request.method == 'GET':
        posts = list(
            Post.objects.filter(published=True)
                        .select_related('author')
                        .values('id', 'title', 'slug', 'author__username', 'created_at')
        )
        return JsonResponse(posts, safe=False)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'login required'}, status=401)
        data = json.loads(request.body)
        post = Post.objects.create(
            title=data['title'],
            slug=data['slug'],
            body=data['body'],
            author=request.user,
        )
        return JsonResponse({'id': post.id, 'title': post.title}, status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'GET':
        return JsonResponse({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'body': post.body,
            'author': post.author.username,
            'published': post.published,
        })

    elif request.method == 'PUT':
        data = json.loads(request.body)
        post.title = data.get('title', post.title)
        post.body  = data.get('body', post.body)
        post.save()
        return JsonResponse({'id': post.id, 'title': post.title})

    elif request.method == 'DELETE':
        post.delete()
        return HttpResponse(status=204)
```


```python
# file: blog/urls.py  (Section 4 checkpoint)
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health),
    path('posts/', views.post_list),              # /api/posts/
    path('posts/<int:pk>/', views.post_detail),   # /api/posts/42/
]
```

**What just happened?** `post_list` only lists *published* posts, and it uses `.values(...)` to get plain dicts that `JsonResponse` can serialise. A model object can't be turned into JSON directly, which is why `post_detail` builds its dict by hand. `safe=False` is needed because we return a list rather than a dict.

**Quick recap**

- Function-based views branch on `request.method`; class-based views have one method per HTTP verb.
- `path('posts/<int:pk>/', view)` captures part of the URL and passes it to the view.
- `get_object_or_404` saves you the try/except for missing objects.
- Plain Django views mean manual JSON, manual validation and dealing with CSRF yourself. DRF fixes all three.

---

## 5. Django REST Framework: Serializers

### Why DRF?

Plain Django views work, but you write the JSON parsing, validation and serialisation by hand. **Django REST Framework (DRF)** gives you:

- **Serializers**: declare the fields once and get validation and JSON conversion
- **Generic views / ViewSets**: full CRUD in a few lines
- **Browsable API**: a clickable HTML page for every endpoint
- **Authentication & permissions**: ready-made classes you plug in

### ModelSerializer

A `ModelSerializer` builds its fields from a model. It plays the same role as the Pydantic `...Create` / `...Response` models in FastAPI, in one class:


```python
# Illustration (blog/serializers.py)
from rest_framework import serializers
from .models import Post, Comment

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'body', 'published', 'author', 'created_at']
        read_only_fields = ['id', 'created_at', 'author']
```

The inner `Meta` class connects the serializer to a model. `fields` lists the columns to include; `read_only_fields` are sent back to the client but can't be set by it.

### Validation

Add `validate_<field>` methods for checks on one field, and `validate` for checks that involve several fields:


```python
# Illustration (blog/serializers.py)
class PostSerializer(serializers.ModelSerializer):
    title = serializers.CharField(min_length=5, max_length=200)

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'body', 'published', 'author', 'created_at']
        read_only_fields = ['id', 'created_at', 'author']

    def validate_slug(self, value):
        """Field-level validator."""
        if ' ' in value:
            raise serializers.ValidationError('Slug must not contain spaces.')
        return value

    def validate(self, data):
        """Object-level validator (runs after all fields pass)."""
        if data.get('published') and not data.get('body'):
            raise serializers.ValidationError('A published post must have a body.')
        return data
```

When a check fails, DRF answers `400 Bad Request` with the error message under the field name, for example `{"slug": ["Slug must not contain spaces."]}`.

### Nested Serializers

A serializer can be used as a field inside another one. Here each post includes its full list of comments:


```python
# Illustration (blog/serializers.py)
class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'body', 'author_username', 'created_at']
        read_only_fields = ['id', 'created_at', 'author_username']


class PostDetailSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)  # inline nested objects
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'body', 'published',
                  'author_username', 'created_at', 'comments']
```

`source='author.username'` reads a value through the relation, so the API shows `"alice"` instead of the author's id.

### Exercise 5: Comment Count

Add a `comment_count` field to `PostSerializer` that returns how many comments each post has. Use `serializers.SerializerMethodField` and write a `get_comment_count` method.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/serializers.py  (inside PostSerializer)
comment_count = serializers.SerializerMethodField()

def get_comment_count(self, obj):
    return obj.comments.count()

# and add 'comment_count' to Meta.fields
```

</details>

Here is the full `serializers.py`, including the exercise. `PostDetailSerializer` inherits from `PostSerializer` and just adds the comments, so the two never get out of step.


```python
# file: blog/serializers.py  (Section 5 checkpoint)

from rest_framework import serializers
from .models import Post, Comment


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'body', 'author_username', 'created_at']
        read_only_fields = ['id', 'created_at', 'author_username']


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    comment_count   = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'body', 'published',
            'author_username', 'created_at', 'comment_count',
        ]
        read_only_fields = ['id', 'created_at', 'author_username', 'comment_count']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def validate_slug(self, value):
        if ' ' in value:
            raise serializers.ValidationError('Slug must not contain spaces.')
        return value


class PostDetailSerializer(PostSerializer):
    """Extends PostSerializer with full comment list for detail views."""
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['comments']
```

**Quick recap**

- A `ModelSerializer` turns model objects into JSON and validates incoming JSON.
- `Meta.fields` picks the columns; `read_only_fields` are output-only.
- `validate_<field>()` for one field, `validate()` for several. Raise `serializers.ValidationError`.
- `source='author.username'` and `SerializerMethodField` add computed fields.

---

## 6. DRF Views & Routers

### APIView

`APIView` is DRF's version of Django's `View`: one method per HTTP verb. On top of that, DRF parses JSON for you (`request.data`), turns `Response` objects into JSON, and runs authentication and permission checks.


```python
# Illustration (blog/views.py)
from .models import Post
from .serializers import PostSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class PostListView(APIView):
    def get(self, request):
        posts = Post.objects.filter(published=True)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### ModelViewSet

A **ViewSet** puts all the operations for one resource in one class. A **ModelViewSet** gives you `list`, `create`, `retrieve`, `update`, `partial_update` and `destroy` without writing any of them:


```python
# Illustration (blog/views.py)
from rest_framework import viewsets

class PostViewSet(viewsets.ModelViewSet):
    queryset            = Post.objects.select_related('author').all()
    serializer_class    = PostSerializer
```

### DRF Router

Give the ViewSet to a `DefaultRouter` and it creates all the URL patterns:


```python
# Illustration (blog/urls.py)
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet, basename='post')

urlpatterns = router.urls
```

That one `register` call creates:

| URL                | Method | Action           |
|--------------------|--------|------------------|
| `/api/posts/`      | GET    | `list`           |
| `/api/posts/`      | POST   | `create`         |
| `/api/posts/{pk}/` | GET    | `retrieve`       |
| `/api/posts/{pk}/` | PUT    | `update`         |
| `/api/posts/{pk}/` | PATCH  | `partial_update` |
| `/api/posts/{pk}/` | DELETE | `destroy`        |

### Custom Actions with `@action`

For anything that isn't plain CRUD, add a method with `@action`. `detail=True` means it works on one object, so the URL includes the `pk`:


```python
# Illustration (blog/views.py)
from rest_framework.decorators import action

class PostViewSet(viewsets.ModelViewSet):
    queryset         = Post.objects.all()
    serializer_class = PostSerializer

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """POST /api/posts/{pk}/publish/ marks a post as published."""
        post = self.get_object()
        post.published = True
        post.save()
        return Response({'status': 'published'})
```

### Exercise 6: Unpublish

Add an `@action` called `unpublish` (`detail=True`, `methods=['post']`) that sets `post.published = False`. Both `/publish/` and `/unpublish/` should work on the same ViewSet.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/views.py  (inside PostViewSet)
@action(detail=True, methods=['post'], url_path='unpublish')
def unpublish(self, request, pk=None):
    post = self.get_object()
    post.published = False
    post.save()
    return Response({'status': 'unpublished'})
```

</details>

### Section 6 Checkpoint

Replace `blog/views.py` and `blog/urls.py` with the two cells below. The comments live under each post (`/api/posts/1/comments/`), which needs the `drf-nested-routers` package from the install command.

**Heads-up:** until we add authentication in Section 7, you can *read* through the API but not create posts. `perform_create` saves `self.request.user` as the author, and an anonymous user can't be one, so a POST ends in a server error. That's exactly what the next section fixes.


```python
# file: blog/views.py  (Section 6 checkpoint: DRF ViewSets)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Post, Comment
from .serializers import PostSerializer, PostDetailSerializer, CommentSerializer


def health(request):
    return JsonResponse({"status": "ok", "version": "1.0.0"})


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author').prefetch_related('comments').all()

    def get_serializer_class(self):
        # Use the detailed serializer (with comments) for single-object views
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer

    def perform_create(self, serializer):
        # Automatically set the author to the authenticated user
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        post = self.get_object()
        post.published = True
        post.save()
        return Response({'status': 'published'})

    @action(detail=True, methods=['post'], url_path='unpublish')
    def unpublish(self, request, pk=None):
        post = self.get_object()
        post.published = False
        post.save()
        return Response({'status': 'unpublished'})


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        # Scope comments to the parent post
        return Comment.objects.filter(
            post_id=self.kwargs['post_pk']
        ).select_related('author').order_by('created_at')   # oldest first

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)
```


```python
# file: blog/urls.py  (Section 6 checkpoint: nested router)

from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers  # pip install drf-nested-routers
from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet, basename='post')

# Nested: /api/posts/{post_pk}/comments/
posts_router = nested_routers.NestedDefaultRouter(router, 'posts', lookup='post')
posts_router.register('comments', views.CommentViewSet, basename='post-comments')

urlpatterns = [path('health/', views.health)] + router.urls + posts_router.urls
```

**What just happened?**

- `get_serializer_class()` picks the serializer per action: the detailed one (with comments) for a single post, the short one for lists.
- `perform_create()` is a hook DRF calls when saving a new object. We use it to fill in fields the client must not choose, like `author`.
- `NestedDefaultRouter(router, 'posts', lookup='post')` puts the comments URLs under a post, and passes the post's id to the view as `self.kwargs['post_pk']`.
- `CommentViewSet` uses `get_object_or_404`, so commenting on a post that doesn't exist gives `404` rather than a server error. It also sorts the comments (`order_by('created_at')`); `Comment` has no default ordering, and paginating an unsorted list makes DRF print a warning.

**Quick recap**

- `APIView`: one method per verb, with `request.data` and `Response` doing the JSON work.
- `ModelViewSet` + `DefaultRouter` = full CRUD and all its URLs in a few lines.
- `@action(detail=True, methods=['post'])` adds extra endpoints like `/publish/`.
- Override `get_queryset`, `get_serializer_class` and `perform_create` to customise a ViewSet.

---

## 7. Authentication & Permissions

### DRF Authentication Classes

| Class | How the client proves who it is |
|----|----|
| `SessionAuthentication` | Django session cookie (logging in through a browser) |
| `BasicAuthentication` | HTTP Basic: username and password on every request. Testing only. |
| `TokenAuthentication` | `Authorization: Token <token>` header |
| `JWTAuthentication` (from `djangorestframework-simplejwt`) | `Authorization: Bearer <jwt>` header |

We'll use `TokenAuthentication`. It's like the API key from the FastAPI notebook: a random string stored in the database, one per user.

### Setting Up Token Authentication

Add this to the bottom of `settings.py`:


```python
# add to: blogplatform/settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}
```

Then run `python manage.py migrate` again. `rest_framework.authtoken` (which we added to `INSTALLED_APPS` in Section 1) brings its own table, `authtoken_token`.

DRF also ships a ready-made view that swaps a username and password for a token. Add it to `blogplatform/urls.py`:


```python
# Illustration (blogplatform/urls.py; the final version is in Section 9)
from rest_framework.authtoken import views as drf_auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('blog.urls')),
    path('api/auth/token/', drf_auth_views.obtain_auth_token),  # POST {username, password}
]
```

### Built-in Permission Classes

| Permission                  | Effect                                 |
|-----------------------------|----------------------------------------|
| `AllowAny`                  | Everyone, logged in or not             |
| `IsAuthenticated`           | Must send a valid token / session      |
| `IsAuthenticatedOrReadOnly` | Anonymous users may only read (GET, HEAD, OPTIONS) |
| `IsAdminUser`               | `request.user.is_staff` must be `True` |

### Custom Object-Level Permission

Only a post's author should be able to edit or delete it. Built-in classes can't know that, so we write our own:


```python
# file: blog/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Write access only to the object's owner; read access for everyone."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
```

`has_object_permission` runs when the view loads one specific object (retrieve, update, delete and our `publish` action). `SAFE_METHODS` is the tuple `('GET', 'HEAD', 'OPTIONS')`, the methods that don't change anything.

Apply it to the ViewSet. DRF checks every class in the list, and all of them must agree:


```python
# Illustration (blog/views.py)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsOwnerOrReadOnly

class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    ...
```

### User Registration View

DRF has no sign-up endpoint, so we write a small one. It creates the user and gives back a token straight away:


```python
# Illustration (blog/views.py; the full file is below)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

class RegisterView(APIView):
    permission_classes = []   # public endpoint

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'username and password required'}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'username already taken'}, status=400)
        user  = User.objects.create_user(username=username, password=password)
        token = Token.objects.create(user=user)
        return Response({'token': token.key}, status=201)
```

`permission_classes = []` overrides the default from `settings.py`, so anyone may call it. Otherwise nobody could register without already having a token.

### Exercise 7: Log Out

Add a `DELETE /api/auth/token/revoke/` endpoint that deletes the current user's token, so they have to log in again. It must require `IsAuthenticated`.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/views.py
from rest_framework.permissions import IsAuthenticated


class RevokeTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        request.user.auth_token.delete()
        return Response(status=204)


# add to: blogplatform/urls.py  (inside urlpatterns)
# path('api/auth/token/revoke/', RevokeTokenView.as_view()),
```

</details>

Here is the complete `views.py` with everything from Sections 6 and 7. Besides the new auth views, `CommentViewSet` now also uses `IsOwnerOrReadOnly`. Without it, any logged-in user could delete anyone else's comment.


```python
# file: blog/views.py  (Section 7 checkpoint: full file)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .models import Post, Comment
from .serializers import PostSerializer, PostDetailSerializer, CommentSerializer
from .permissions import IsOwnerOrReadOnly


def health(request):
    return JsonResponse({"status": "ok", "version": "1.0.0"})


class PostViewSet(viewsets.ModelViewSet):
    queryset           = Post.objects.select_related('author').prefetch_related('comments').all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        post = self.get_object()
        post.published = True
        post.save()
        return Response({'status': 'published'})

    @action(detail=True, methods=['post'], url_path='unpublish')
    def unpublish(self, request, pk=None):
        post = self.get_object()
        post.published = False
        post.save()
        return Response({'status': 'unpublished'})


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class   = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    http_method_names  = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return Comment.objects.filter(
            post_id=self.kwargs['post_pk']
        ).select_related('author').order_by('created_at')   # oldest first

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)


class RegisterView(APIView):
    permission_classes = []   # public: anyone can register

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'username and password required'}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'username already taken'}, status=400)
        user  = User.objects.create_user(username=username, password=password)
        token = Token.objects.create(user=user)
        return Response({'token': token.key}, status=201)


class RevokeTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        request.user.auth_token.delete()
        return Response(status=204)
```

**Quick recap**

- Authentication answers "who are you?"; permissions answer "are you allowed?".
- Set defaults in `REST_FRAMEWORK` in `settings.py`; override per view with `permission_classes`.
- Clients send `Authorization: Token <key>`. Get the key from `/api/auth/token/` or `/api/auth/register/`.
- Object-level rules ("only the author") go in `has_object_permission`.

---

## 8. Django Admin

### What Is the Admin?

Django comes with a complete web admin site at `/admin/`. You don't write any frontend code; you just register your models.

```bash
python manage.py createsuperuser   # creates an admin user
python manage.py runserver
# open http://127.0.0.1:8000/admin/
```

### Basic Registration


```python
# Illustration (blog/admin.py, simplest version)
from django.contrib import admin
from .models import Post, Comment

admin.site.register(Post)
admin.site.register(Comment)
```

That's enough to get list, add, edit and delete pages for both models.

### Customising the Admin

A `ModelAdmin` class controls the columns, filters, search box and more. An *inline* shows related objects (here, a post's comments) on the same page:


```python
# Illustration (blog/admin.py)
from django.contrib import admin
from .models import Post, Comment


class CommentInline(admin.TabularInline):
    model   = Comment
    extra   = 0        # don't show blank rows by default
    readonly_fields = ['author', 'created_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display    = ['title', 'author', 'published', 'created_at']
    list_filter     = ['published', 'created_at']
    search_fields   = ['title', 'body', 'author__username']
    prepopulated_fields = {'slug': ('title',)}   # auto-fills slug from title
    inlines         = [CommentInline]
    actions         = ['make_published']

    @admin.action(description='Mark selected posts as published')
    def make_published(self, request, queryset):
        queryset.update(published=True)
```

`@admin.action(description=...)` is the current way to name a bulk action. Older code sets `make_published.short_description = ...` after the function, which still works.

### Common `ModelAdmin` Options

| Option                | Effect                                     |
|-----------------------|--------------------------------------------|
| `list_display`        | Columns shown in the list of objects       |
| `list_filter`         | Filter panel in the sidebar                |
| `search_fields`       | Adds a search box (uses `LIKE` queries)    |
| `ordering`            | Default sort order                         |
| `prepopulated_fields` | Fills one field from another as you type   |
| `inlines`             | Shows related objects on the same page     |
| `actions`             | Bulk actions in the list view              |
| `readonly_fields`     | Fields shown but not editable              |

### Exercise 8: Comment Admin

Register `Comment` with a `CommentAdmin` that shows `post`, `author` and `created_at` as columns, can be filtered by `created_at`, and can be searched by `body` and `author__username`. (Remove the plain `admin.site.register(Comment)` line, since a model can only be registered once.)

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/admin.py
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ['post', 'author', 'created_at']
    list_filter   = ['created_at']
    search_fields = ['body', 'author__username']
```

</details>


```python
# file: blog/admin.py  (Section 8 checkpoint)

from django.contrib import admin
from .models import Post, Comment


class CommentInline(admin.TabularInline):
    model           = Comment
    extra           = 0
    readonly_fields = ['author', 'created_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display        = ['title', 'author', 'published', 'created_at']
    list_filter         = ['published', 'created_at']
    search_fields       = ['title', 'body', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    inlines             = [CommentInline]
    actions             = ['make_published']

    @admin.action(description='Mark selected posts as published')
    def make_published(self, request, queryset):
        queryset.update(published=True)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ['post', 'author', 'created_at']
    list_filter   = ['created_at']
    search_fields = ['body', 'author__username']
```

**Quick recap**

- `python manage.py createsuperuser`, then log in at `/admin/`.
- `@admin.register(Model)` + a `ModelAdmin` class to customise the pages.
- `list_display`, `list_filter`, `search_fields` and `inlines` cover most needs.

---

## 9. Final `settings.py` & `urls.py`

Time to put all the pieces together in the project's config files.

### `blogplatform/settings.py`

These are only the parts we changed. Leave everything else that `startproject` generated as it is. Compared with Section 7 we've added `SessionAuthentication` (so you can log in to the browsable API) and pagination.


```python
# add to: blogplatform/settings.py  (final version of the parts we changed)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third-party
    'rest_framework',
    'rest_framework.authtoken',
    # local
    'blog',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
```

### `blogplatform/urls.py`


```python
# file: blogplatform/urls.py  (final)

from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views as drf_auth_views
from blog.views import RegisterView, RevokeTokenView

urlpatterns = [
    path('admin/',                   admin.site.urls),
    path('api/',                     include('blog.urls')),
    path('api/auth/register/',       RegisterView.as_view()),
    path('api/auth/token/',          drf_auth_views.obtain_auth_token),
    path('api/auth/token/revoke/',   RevokeTokenView.as_view()),
    path('api-auth/',                include('rest_framework.urls')),
]
```

### Testing with curl

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "secret123"}'
# -> {"token": "abc123..."}

# Create a post (logged in)
curl -X POST http://127.0.0.1:8000/api/posts/ \
  -H 'Authorization: Token abc123...' \
  -H 'Content-Type: application/json' \
  -d '{"title": "Hello Django", "slug": "hello-django", "body": "My first post!"}'

# List posts (no login needed)
curl http://127.0.0.1:8000/api/posts/

# Publish a post (only its author can)
curl -X POST http://127.0.0.1:8000/api/posts/1/publish/ \
  -H 'Authorization: Token abc123...'

# Log out
curl -X DELETE http://127.0.0.1:8000/api/auth/token/revoke/ \
  -H 'Authorization: Token abc123...'
```

Because pagination is switched on, the list endpoint now wraps the posts: `{"count": 1, "next": null, "previous": null, "results": [...]}`.

You can also open `http://127.0.0.1:8000/api/posts/` in the browser to use the browsable API. Log in with the link in the top-right corner (that's what `api-auth/` is for).

**Quick recap**

- `INSTALLED_APPS` lists DRF, the token app and our app; `REST_FRAMEWORK` sets auth, permission and pagination defaults.
- The project's `urls.py` mounts the admin, the app's API and the auth endpoints.
- With pagination on, list responses look like `{count, next, previous, results}`.

---

## Extra Practice

Three small features for the finished project. Each needs only a few lines.

### Practice 1: Filter Posts

Let clients filter the post list with `?published=true` and `?author__username=alice`, using the **django-filter** package (already in the install command).

**Hint:** add `'django_filters'` to `INSTALLED_APPS`, set `DEFAULT_FILTER_BACKENDS` in `REST_FRAMEWORK`, and give `PostViewSet` a `filterset_fields` list.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blogplatform/settings.py
INSTALLED_APPS += ['django_filters']

REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'] = [
    'django_filters.rest_framework.DjangoFilterBackend',
]


# add to: blog/views.py  (inside PostViewSet)
filterset_fields = ['published', 'author__username']
```

</details>

### Practice 2: Search and Sort

Add `?search=django` (searches title and body) and `?ordering=title` / `?ordering=-created_at` to the post list, using DRF's `SearchFilter` and `OrderingFilter`.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

# inside PostViewSet
filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
search_fields = ['title', 'body']
ordering_fields = ['created_at', 'title']

# Setting filter_backends on the view replaces the default list from settings,
# which is why DjangoFilterBackend is listed again here.
```

</details>

### Practice 3: My Posts

Add `GET /api/posts/mine/` that returns only the logged-in user's posts, including unpublished ones. Anonymous users should get `401`.

**Hint:** `@action(detail=False, ...)` makes an action on the collection, so there's no `pk` in the URL.

<details markdown="1">
<summary>Show solution</summary>

```python
# add to: blog/views.py  (inside PostViewSet)
@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
def mine(self, request):
    posts = self.get_queryset().filter(author=request.user)
    page = self.paginate_queryset(posts)
    serializer = self.get_serializer(page, many=True)
    return self.get_paginated_response(serializer.data)
```

</details>

**Quick recap**

- `filterset_fields` (django-filter) gives exact-match filters with one line.
- `SearchFilter` and `OrderingFilter` add `?search=` and `?ordering=`.
- `@action(detail=False)` adds endpoints on the collection, like `/api/posts/mine/`.

---

## Summary & Cheat Sheet

| Topic | Remember this |
|----|----|
| Project vs app | A project is the configuration; apps hold the code. One project, many apps. |
| Models | Classes that map to tables. Fields are columns. |
| Migrations | `makemigrations` writes the change, `migrate` applies it. Always both. |
| ORM | Lazy, chainable QuerySets. `select_related` / `prefetch_related` avoid N+1 queries. |
| Views | Functions or classes that take an `HttpRequest` and return an `HttpResponse`. |
| DRF serializers | Declare fields once; get validation and JSON in both directions. |
| `ModelViewSet` | One class = full CRUD. Pair it with `DefaultRouter` for the URLs. |
| `@action` | Extra endpoints on a ViewSet (`/publish/`, `/unpublish/`). |
| Permissions | `IsAuthenticatedOrReadOnly` + a custom `IsOwnerOrReadOnly` protect writes. |
| Admin | Register models and customise with `ModelAdmin` for a free management UI. |

### Useful Commands

```bash
django-admin startproject blogplatform    # new project
python manage.py startapp blog            # new app
python manage.py makemigrations           # after changing models
python manage.py migrate                  # apply migrations
python manage.py createsuperuser          # admin login
python manage.py shell                    # Python prompt with the project loaded
python manage.py runserver                # dev server on port 8000
```

### Further Reading

- [Django documentation](https://docs.djangoproject.com/)
- [Django REST Framework documentation](https://www.django-rest-framework.org/)
- [QuerySet API reference](https://docs.djangoproject.com/en/stable/ref/models/querysets/)
- [drf-nested-routers](https://github.com/alanjds/drf-nested-routers): nested URLs for related resources
- [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/): JWT authentication for DRF

### What's Next

The next notebook, **Deploying Applications**, shows how to take a project like this one (or the FastAPI one) off your laptop and run it on a real server.
