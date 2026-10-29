# Django

> *"The web framework for perfectionists with deadlines."*

---

### Learning Objectives

By the end of this notebook, you will be able to:

1.  **Create** a Django project and app from scratch
2.  **Define** models and run database migrations
3.  **Query** the database using the Django ORM
4.  **Write** function-based and class-based views
5.  **Build** a REST API using Django REST Framework serializers and ViewSets
6.  **Protect** endpoints using authentication and permissions
7.  **Register** models with the Django admin interface

---

### Prerequisites

- Python 3.10+ installed
- Familiarity with Python classes, decorators, and HTTP basics

Install dependencies before starting:

```bash
pip install django==5.0.6 djangorestframework==3.15.2 django-filter==24.2
```

---

## Section 0 — What We're Building

We will build the **Blog Platform** — a web application with a REST API for managing blog posts, comments, and authors.

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

| Method | Path                        | Auth          | Description             |
|--------|-----------------------------|---------------|-------------------------|
| GET    | `/api/posts/`               | None          | List all posts          |
| POST   | `/api/posts/`               | Token         | Create a post           |
| GET    | `/api/posts/{id}/`          | None          | Retrieve a post         |
| PUT    | `/api/posts/{id}/`          | Token + Owner | Update a post           |
| DELETE | `/api/posts/{id}/`          | Token + Owner | Delete a post           |
| GET    | `/api/posts/{id}/comments/` | None          | List comments on a post |
| POST   | `/api/posts/{id}/comments/` | Token         | Add a comment           |
| POST   | `/api/auth/register/`       | None          | Register a user         |
| POST   | `/api/auth/token/`          | None          | Obtain auth token       |

### Project Structure

```
blogplatform/
├── manage.py
├── blogplatform/          ← project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── blog/                  ← our app
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── permissions.py
    └── admin.py
```

---

## Section 1 — Setup & First View

### Django vs FastAPI

|  | Django | FastAPI |
|----|----|----|
| Philosophy | **Batteries included** — ORM, admin, auth, templates built in | Minimal core, compose what you need |
| Data validation | Forms / DRF Serializers | Pydantic models |
| Auto docs | None (DRF provides browsable API) | Swagger UI + ReDoc |
| Async support | Partial (Django 4.1+) | Native async/await |
| Best for | Full-stack web apps, content sites | High-throughput APIs, microservices |

### Creating a Project

```bash
django-admin startproject blogplatform
cd blogplatform
python manage.py startapp blog
```

`startproject` generates the config package. `startapp` generates one **app** — a self-contained module with its own models, views, and URLs. A Django project is composed of one or more apps.

### Registering the App

Open `blogplatform/settings.py` and add the new app to `INSTALLED_APPS`:


```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',          # ← Django REST Framework
    'rest_framework.authtoken', # ← Token authentication
    'blog',                    # ← our app
]
```

### Running the Development Server

```bash
python manage.py migrate      # apply built-in migrations (creates db.sqlite3)
python manage.py runserver    # starts dev server at http://127.0.0.1:8000
```

### Your First View

A **view** is a Python function (or class) that receives an `HttpRequest` and returns an `HttpResponse`.


```python
# blog/views.py
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok", "version": "1.0.0"})
```

Wire it to a URL:


```python
# blog/urls.py  (create this file)
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health),
]
```


```python
# blogplatform/urls.py  (include the app URLs)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('blog.urls')),
]
```

Visit `http://127.0.0.1:8000/api/health/` — Django returns `{"status": "ok", "version": "1.0.0"}`.

**🏋️ Mini Challenge:** Add a `GET /api/ping/` view that returns `{"message": "pong", "timestamp": <current UTC time as string>}`. Import `datetime` from Python's standard library.


```python
# blog/views.py  (Section 1 checkpoint)

from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok", "version": "1.0.0"})
```


```python
# blog/urls.py  (Section 1 checkpoint)

from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health),
]
```

---

## Section 2 — Models & Migrations

### What Is a Django Model?

A **model** is a Python class that maps to a database table. Each class attribute is a column. Django's ORM translates Python operations into SQL.


```python
from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=200)
    body  = models.TextField()
```

Django creates the table `blog_post` (app name + model name, lowercase).

### Common Field Types

| Field | Python type | SQL type |
|----|----|----|
| `CharField(max_length=N)` | `str` | VARCHAR(N) |
| `TextField()` | `str` | TEXT |
| `IntegerField()` | `int` | INTEGER |
| `FloatField()` | `float` | REAL |
| `BooleanField()` | `bool` | BOOLEAN |
| `DateTimeField(auto_now_add=True)` | `datetime` | DATETIME (set on create) |
| `DateTimeField(auto_now=True)` | `datetime` | DATETIME (set on every save) |
| `ForeignKey(Model, on_delete=...)` | FK | INTEGER + constraint |

### Relationships


```python
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    # CASCADE: deleting a Post also deletes all its Comments
    # related_name: lets you do post.comments.all()
```

### The Migration Workflow

```
Edit models.py
      ↓
python manage.py makemigrations   ← generates SQL instructions in blog/migrations/
      ↓
python manage.py migrate          ← executes the SQL against the database
```

Always run both commands together. Never edit migration files by hand.

### Inspecting the Schema

```bash
python manage.py sqlmigrate blog 0001
# prints the SQL that Django will execute — useful for learning
```

**🏋️ Mini Challenge:** Add a `slug` field to `Post` (`SlugField(unique=True)`) and a `published` boolean field (default `False`). Run `makemigrations` and `migrate`. Confirm the columns appear with `sqlmigrate`.


```python
# blog/models.py  (Section 2 checkpoint)

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

---

## Section 3 — Django ORM

### The QuerySet

Every ORM operation returns a **QuerySet** — a lazy, chainable list of model instances. The SQL is only executed when you iterate, slice, or call `list()` on it.


```python
# Nothing hits the DB yet:
qs = Post.objects.filter(published=True)

# DB query fires here:
for post in qs:
    print(post.title)
```

### CRUD Operations


```python
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

# READ — all
Post.objects.all()

# READ — filter
Post.objects.filter(published=True)
Post.objects.filter(author__username='alice')   # ← double-underscore traverses FK

# READ — single record (raises DoesNotExist if missing)
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
| `icontains` | `filter(title__icontains='django')` | case-insensitive LIKE |
| `gt / gte / lt / lte` | `filter(id__gt=5)` | comparison operators |
| `in` | `filter(id__in=[1, 2, 3])` | `id IN (1,2,3)` |
| `isnull` | `filter(slug__isnull=True)` | `IS NULL` |
| Related field | `filter(author__username='alice')` | JOIN on FK |

### `select_related` and `prefetch_related`


```python
# BAD — N+1 query problem: one query per post to fetch the author
for post in Post.objects.all():
    print(post.author.username)

# GOOD — single JOIN query
for post in Post.objects.select_related('author').all():
    print(post.author.username)

# For many-to-many or reverse FK (e.g., all comments per post)
posts = Post.objects.prefetch_related('comments').all()
```

**🏋️ Mini Challenge:** Write a QuerySet that returns the 5 most recently created published posts whose title contains the word `"python"` (case-insensitive). Use method chaining on a single line.


```python
# Run these in the Django shell:  python manage.py shell
#
# Section 3 — ORM examples

# ── Setup ──────────────────────────────────────────────────────────────────
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

# Mini challenge answer ↓
recent_python = (
    Post.objects
    .filter(published=True, title__icontains='python')
    .order_by('-created_at')[:5]
)
```

---

## Section 4 — Views & URL Patterns

### Function-Based Views (FBVs)

A function-based view handles one or more HTTP methods in a single function. Use `request.method` to branch.


```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@require_http_methods(['GET', 'POST'])
def post_list(request):
    if request.method == 'GET':
        posts = list(Post.objects.values('id', 'title', 'slug', 'published'))
        return JsonResponse(posts, safe=False)

    elif request.method == 'POST':
        data = json.loads(request.body)
        post = Post.objects.create(**data)
        return JsonResponse({'id': post.id}, status=201)
```

### URL Patterns


```python
# blog/urls.py
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
| `<int:pk>`    | `0-9+`                    | `/posts/42/` → `pk=42` |
| `<str:slug>`  | non-`/` chars             | `/posts/hello-world/`  |
| `<slug:slug>` | letters, digits, `-`, `_` | `/posts/hello-world/`  |
| `<uuid:id>`   | UUID format               | `/items/550e8400-.../` |

### get_object_or_404


```python
from django.shortcuts import get_object_or_404

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)  # returns 404 if not found
    return JsonResponse({'id': post.id, 'title': post.title, 'body': post.body})
```

### Class-Based Views (CBVs)

Django ships with generic CBVs that handle common patterns without boilerplate:


```python
from django.views import View
from django.http import JsonResponse

class PostDetailView(View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        return JsonResponse({'id': post.id, 'title': post.title})

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.delete()
        return JsonResponse({}, status=204)
```


```python
# blog/urls.py
path('posts/<int:pk>/', PostDetailView.as_view()),
```

**🏋️ Mini Challenge:** Write a `post_detail` FBV that handles `GET` (return the post as JSON), `PUT` (update `title` and `body` from request body), and `DELETE` (delete the post). Use `get_object_or_404`.


```python
# blog/views.py  (Section 4 checkpoint — plain Django views)

import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import Post


def post_list(request):
    if request.method == 'GET':
        posts = list(
            Post.objects.filter(published=True)
                        .select_related('author')
                        .values('id', 'title', 'slug', 'author__username', 'created_at')
        )
        return JsonResponse(posts, safe=False)

    elif request.method == 'POST':
        data = json.loads(request.body)
        post = Post.objects.create(
            title=data['title'],
            slug=data['slug'],
            body=data['body'],
            author=request.user,
        )
        return JsonResponse({'id': post.id, 'title': post.title}, status=201)


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
        return JsonResponse({}, status=204)
```

---

## Section 5 — Django REST Framework: Serializers

### Why DRF?

Raw Django views work but require manual JSON parsing, validation, and serialisation. **Django REST Framework (DRF)** provides:

- **Serializers** — declare fields once; get validation and serialisation for free
- **Generic views / ViewSets** — CRUD with minimal code
- **Browsable API** — interactive HTML interface at every endpoint
- **Authentication & permissions** — pluggable classes

### ModelSerializer

A `ModelSerializer` auto-generates fields from a model. Compare with FastAPI's `response_model`:


```python
# blog/serializers.py
from rest_framework import serializers
from .models import Post, Comment

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'body', 'published', 'author', 'created_at']
        read_only_fields = ['id', 'created_at', 'author']
```

The `Meta` inner class maps the serializer to a model. `fields` lists which columns to include; `read_only_fields` cannot be set by the client.

### Validation


```python
class PostSerializer(serializers.ModelSerializer):
    title = serializers.CharField(min_length=5, max_length=200)

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

### Nested Serializers


```python
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

**🏋️ Mini Challenge:** Add a `comment_count` field to `PostSerializer` that returns the number of comments on each post. Use `serializers.SerializerMethodField` and implement the `get_comment_count` method.


```python
# blog/serializers.py  (Section 5 checkpoint)

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

---

## Section 6 — DRF Views & Routers

### APIView

`APIView` is DRF's equivalent of Django's `View` — each HTTP method is a separate method on the class. DRF handles content negotiation and authentication automatically.


```python
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

### ModelViewSet — Maximum Reuse

A **ViewSet** groups all CRUD operations into one class. A **ModelViewSet** auto-implements `list`, `create`, `retrieve`, `update`, `partial_update`, and `destroy`.


```python
from rest_framework import viewsets

class PostViewSet(viewsets.ModelViewSet):
    queryset            = Post.objects.select_related('author').all()
    serializer_class    = PostSerializer
```

### DRF Router

Pair a ViewSet with a `DefaultRouter` to auto-generate all URL patterns:


```python
# blog/urls.py
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet, basename='post')

urlpatterns = router.urls
```

This single `register` call generates:

| URL                | Method | Action           |
|--------------------|--------|------------------|
| `/api/posts/`      | GET    | `list`           |
| `/api/posts/`      | POST   | `create`         |
| `/api/posts/{pk}/` | GET    | `retrieve`       |
| `/api/posts/{pk}/` | PUT    | `update`         |
| `/api/posts/{pk}/` | PATCH  | `partial_update` |
| `/api/posts/{pk}/` | DELETE | `destroy`        |

### Custom Actions with `@action`


```python
from rest_framework.decorators import action

class PostViewSet(viewsets.ModelViewSet):
    queryset         = Post.objects.all()
    serializer_class = PostSerializer

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """POST /api/posts/{pk}/publish/ — marks a post as published."""
        post = self.get_object()
        post.published = True
        post.save()
        return Response({'status': 'published'})
```

**🏋️ Mini Challenge:** Add an `@action` called `unpublish` (detail=True, methods=['post']) that sets `post.published = False`. Register both `/publish/` and `/unpublish/` on the same ViewSet.


```python
# blog/views.py  (Section 6 checkpoint — DRF ViewSets)

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Post, Comment
from .serializers import PostSerializer, PostDetailSerializer, CommentSerializer


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
        ).select_related('author')

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)
```


```python
# blog/urls.py  (Section 6 checkpoint — nested router)

from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers  # pip install drf-nested-routers
from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet, basename='post')

# Nested: /api/posts/{post_pk}/comments/
posts_router = nested_routers.NestedDefaultRouter(router, 'posts', lookup='post')
posts_router.register('comments', views.CommentViewSet, basename='post-comments')

urlpatterns = router.urls + posts_router.urls
```

---

## Section 7 — Authentication & Permissions

### DRF Authentication Classes

| Class | How the client authenticates |
|----|----|
| `SessionAuthentication` | Django session cookie (browser) |
| `BasicAuthentication` | HTTP Basic — **only for testing** |
| `TokenAuthentication` | `Authorization: Token <token>` header |
| `JWTAuthentication` (via `djangorestframework-simplejwt`) | `Authorization: Bearer <jwt>` header |

### Setting Up Token Authentication

Add to `settings.py`:


```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}
```

Run `python manage.py migrate` to create the `authtoken_token` table.

Expose the token endpoint in `blogplatform/urls.py`:


```python
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
| `AllowAny`                  | Everyone — authenticated or not        |
| `IsAuthenticated`           | Must have a valid token/session        |
| `IsAuthenticatedOrReadOnly` | Unauthenticated users may only GET     |
| `IsAdminUser`               | `request.user.is_staff` must be `True` |

### Custom Object-Level Permission

Only the post's author should be able to edit or delete it:


```python
# blog/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """Allow read to everyone; write only to the object's owner."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:   # GET, HEAD, OPTIONS
            return True
        return obj.author == request.user
```

Apply it to the ViewSet:


```python
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsOwnerOrReadOnly

class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    ...
```

### User Registration View


```python
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

**🏋️ Mini Challenge:** Add a `DELETE /api/auth/token/` endpoint that deletes (revokes) the current user's token, forcing them to re-authenticate. The endpoint must require `IsAuthenticated`.


```python
# blog/permissions.py  (Section 7 checkpoint)

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Write access only to the object's owner; read access for everyone."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
```


```python
# blog/views.py  (Section 7 — auth views added)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth.models import User


class RegisterView(APIView):
    permission_classes = []  # public

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


```python
# blog/views.py  (Section 7 checkpoint — full file)

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
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names  = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return Comment.objects.filter(
            post_id=self.kwargs['post_pk']
        ).select_related('author')

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)


class RegisterView(APIView):
    permission_classes = []

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

---

## Section 8 — Django Admin

### What Is the Admin?

Django ships with a fully functional web-based admin interface at `/admin/`. It requires zero custom frontend code — just register your models.

```bash
python manage.py createsuperuser   # creates an admin user
python manage.py runserver
# open http://127.0.0.1:8000/admin/
```

### Basic Registration


```python
# blog/admin.py
from django.contrib import admin
from .models import Post, Comment

admin.site.register(Post)
admin.site.register(Comment)
```

This gives you list/add/edit/delete views for both models immediately.

### Customising the Admin

Use `ModelAdmin` to control columns, filters, search, and inline editing:


```python
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

    def make_published(self, request, queryset):
        queryset.update(published=True)
    make_published.short_description = 'Mark selected posts as published'
```

### Key `ModelAdmin` Options

| Option                | Effect                                     |
|-----------------------|--------------------------------------------|
| `list_display`        | Columns shown in the object list           |
| `list_filter`         | Sidebar filter panel                       |
| `search_fields`       | Enables a search box (uses `LIKE` queries) |
| `ordering`            | Default sort order                         |
| `prepopulated_fields` | Auto-fills one field from another          |
| `inlines`             | Embed related objects on the same page     |
| `actions`             | Bulk actions available from the list view  |
| `readonly_fields`     | Fields shown but not editable              |

**🏋️ Mini Challenge:** Register `Comment` with a `CommentAdmin` that shows `post`, `author`, and `created_at` in `list_display`, and allows filtering by `created_at`. Add a `search_fields` on `body` and `author__username`.


```python
# blog/admin.py  (Section 8 checkpoint)

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

---

## Section 9 — Final `settings.py` & `urls.py`

Bring all pieces together in the project config files.

### `blogplatform/settings.py` (relevant additions)


```python
INSTALLED_APPS = [
    # ... django defaults ...
    'rest_framework',
    'rest_framework.authtoken',
    'blog',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # browsable API login
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
```

### `blogplatform/urls.py` (final)


```python
from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views as drf_auth_views
from blog.views import RegisterView, RevokeTokenView

urlpatterns = [
    path('admin/',               admin.site.urls),
    path('api/',                 include('blog.urls')),
    path('api/auth/register/',   RegisterView.as_view()),
    path('api/auth/token/',      drf_auth_views.obtain_auth_token),
    path('api/auth/token/revoke/', RevokeTokenView.as_view()),
    path('api-auth/',            include('rest_framework.urls')),  # browsable API login
]
```

### Testing with curl

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "secret123"}'
# → {"token": "abc123..."}

# Create a post (authenticated)
curl -X POST http://127.0.0.1:8000/api/posts/ \
  -H 'Authorization: Token abc123...' \
  -H 'Content-Type: application/json' \
  -d '{"title": "Hello Django", "slug": "hello-django", "body": "My first post!"}'

# List posts (unauthenticated)
curl http://127.0.0.1:8000/api/posts/

# Publish a post
curl -X POST http://127.0.0.1:8000/api/posts/1/publish/ \
  -H 'Authorization: Token abc123...'
```


```python
# blogplatform/settings.py  (Section 9 checkpoint — additions only)

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


```python
# blogplatform/urls.py  (Section 9 checkpoint — final)

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

---

## Summary

| Concept | Key Takeaway |
|----|----|
| **Project vs App** | A project is configuration; apps are reusable modules. One project, many apps. |
| **Models** | Classes that map to DB tables. Fields are columns. Django handles DDL via migrations. |
| **Migrations** | `makemigrations` → generate SQL; `migrate` → execute SQL. Always run both. |
| **ORM** | Chainable QuerySets. Use `select_related` / `prefetch_related` to avoid N+1 queries. |
| **Views** | Functions or classes that receive `HttpRequest` and return `HttpResponse`. |
| **DRF Serializers** | Declare once — get validation, serialisation, and deserialization for free. |
| **ModelViewSet** | One class = full CRUD. Pair with `DefaultRouter` to auto-generate URL patterns. |
| **`@action`** | Attach extra endpoints to a ViewSet (`/publish/`, `/unpublish/`). |
| **Permissions** | `IsAuthenticatedOrReadOnly` + custom `IsOwnerOrReadOnly` protects write operations. |
| **Admin** | Register models, customise with `ModelAdmin` — full CRUD UI for free. |

---

### Further Reading

- [Django documentation](https://docs.djangoproject.com/)
- [Django REST Framework documentation](https://www.django-rest-framework.org/)
- [Django ORM cheatsheet](https://docs.djangoproject.com/en/stable/ref/models/querysets/)
- [drf-nested-routers](https://github.com/alanjds/drf-nested-routers) — nested URL routing for related resources
- [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/) — JWT authentication for DRF
