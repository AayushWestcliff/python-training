# Event-Driven Programming in Python

> *"Don't call us, we'll call you."* (the Hollywood Principle, also known as Inversion of Control)

In most programs you've written so far, **you** decide the order things happen. In an event-driven program, **events** decide: a button click, a message arriving, a timer going off. This notebook builds the idea up one step at a time, from plain callbacks to an event emitter, a home-made event loop, and finally Python's own `asyncio`.

You already live in an event-driven world:

- You don't keep checking whether someone texted you. Your phone **notifies** you.
- A waiter doesn't ask "ready to order?" every second. You **signal** them.
- A fire alarm doesn't walk from room to room. The **smoke triggers** it.

The idea is the same every time: **react when something happens** instead of constantly checking.

### Learning Objectives

By the end of this notebook you will be able to:

1. Pass functions around as callbacks, including separate success and error callbacks
2. Explain why deeply nested callbacks ("callback hell") are hard to work with
3. Build an event emitter (the Observer pattern) and register listeners with a decorator
4. Describe what an event loop does by building a small one yourself
5. Write coroutines with `async def` / `await` and run them concurrently with `asyncio.gather` and `asyncio.create_task`
6. Handle errors and timeouts in async code
7. Use three common async patterns: an async event emitter, producer/consumer queues, and retry with backoff

### Prerequisites

- Python 3.10 or newer
- Functions, including `*args`, `**kwargs` and `lambda`
- Classes and OOP basics (see the OOP notebook)
- Decorators help, but aren't required

### How to Use This Notebook

- Run the cells **from top to bottom**. Later cells reuse things defined earlier, such as `EventEmitter`.
- The `asyncio` cells use `await` directly at the top level of a cell. That works in Jupyter. In a normal `.py` script you'd put the code in an `async def main()` and call `asyncio.run(main())`.
- Some examples use random numbers or timings, so your output can differ a little from the saved output. That's expected.
- **Try It** cells are for you. Write your answer first, then open *Show solution* to compare.
- Each section ends with a **Quick recap**. Read only the recaps when revising before an exam.

### What We'll Cover

| Section | Topic | Main idea |
|---|---|---|
| 1 | Callbacks | Functions that respond to events |
| 2 | Building an Event System | The Observer pattern in action |
| 3 | The Event Loop | The engine behind event-driven code |
| 4 | `asyncio` and `async`/`await` | Python's built-in async framework |
| 5 | Real-World Patterns | Putting it all together |

---

## Warm-Up: Synchronous vs Event-Driven Thinking

Two quick questions before any code. Think about your answer, then open it.

### Question 1: What's wrong with this restaurant?

```
Synchronous Restaurant:
1. Waiter takes Order A
2. Waiter walks to kitchen, WAITS until food is cooked
3. Waiter delivers Order A
4. Waiter takes Order B
5. Waiter walks to kitchen, WAITS until food is cooked
6. Waiter delivers Order B
```

<details markdown="1">
<summary>Show answer</summary>

The waiter is **blocked**. While waiting for one order, they can't serve anyone else.

A real restaurant is event-driven:

1. Waiter takes Order A, sends it to the kitchen
2. Waiter takes Order B, sends it to the kitchen
3. Waiter takes Order C, sends it to the kitchen
4. Kitchen signals "Order A ready!", waiter delivers it
5. Kitchen signals "Order C ready!", waiter delivers it
6. Kitchen signals "Order B ready!", waiter delivers it

The waiter **reacts to events** (food being ready) instead of standing still until each order is done.

</details>

### Question 2: Which of these are event-driven?

- A) A `for` loop that processes every item in a list
- B) A button click handler on a web page
- C) Reading a file line by line
- D) A chat app that shows messages when they arrive
- E) A security camera that records when motion is detected

<details markdown="1">
<summary>Show answer</summary>

**B, D and E** are event-driven.

- **B**: the code waits for a click, then reacts.
- **D**: messages arrive as events, and the UI reacts by showing them.
- **E**: motion triggers an event, and recording is the reaction.

A and C are **sequential**: they process things in a fixed order that the program decides.

</details>

**Quick recap**

- Synchronous code does one thing at a time and waits (blocks) until each step is finished.
- Event-driven code reacts when something happens instead of waiting or constantly checking.

---

## 1. Callback Functions: The Building Block

A **callback** is a function you hand to another function, so that it can be **called back** later, when something happens.

```
You:     "When the food is ready, call me back."
Kitchen: "Sure. I'll call your function when it's done."
```

This works because in Python **functions are first-class objects**: you can store them in variables and pass them around like any other value.


```python
# Functions are objects! You can assign them to variables, pass them around...

def greet(name):
    return f"Hello, {name}!"

# Assign a function to a variable (NO parentheses = the function itself)
say_hello = greet
print(say_hello("Alice"))  # "Hello, Alice!"

# Functions have attributes just like any object
print(f"Function name: {greet.__name__}")
print(f"Type: {type(greet)}")
print(f"Same object? {say_hello is greet}")
```

    Hello, Alice!
    Function name: greet
    Type: <class 'function'>
    Same object? True


Notice that `say_hello = greet` has **no parentheses**. We're not calling `greet`, we're giving the same function a second name. The `()` is what actually runs a function.

### 1.1 Your First Callback


```python
# A simple callback example: a function that "calls back" when it's done

def download_file(url, on_complete):
    """Simulates downloading a file, then calls the callback."""
    print(f"Downloading from {url}...")

    # Simulate the download result
    data = f"<contents of {url}>"

    # Call the callback with the result!
    on_complete(data)


# Define what should happen when the download finishes
def handle_download(data):
    print(f"Download complete! Got: {data}")

def save_to_disk(data):
    print(f"Saving to disk: {data}")


# Pass DIFFERENT callbacks to get DIFFERENT behaviors!
download_file("https://example.com/file.txt", handle_download)
print()
download_file("https://example.com/file.txt", save_to_disk)
```

    Downloading from https://example.com/file.txt...
    Download complete! Got: <contents of https://example.com/file.txt>
    
    Downloading from https://example.com/file.txt...
    Saving to disk: <contents of https://example.com/file.txt>


`download_file` doesn't know or care what `on_complete` does. It does its job and then calls whatever function it was given. Pass a different function and you get different behaviour, without changing `download_file` at all.

That's **separation of concerns**: the downloader handles downloading, and the callback decides what to do with the result.

### 1.2 Callbacks with Lambda Functions

For short, one-line callbacks you can use a **lambda** (a small function without a name) instead of a full `def`:


```python
def process_numbers(numbers, transform):
    """Apply a transformation callback to each number."""
    return [transform(n) for n in numbers]

nums = [1, 2, 3, 4, 5]

# Lambda callbacks for different transformations
doubled = process_numbers(nums, lambda x: x * 2)
squared = process_numbers(nums, lambda x: x ** 2)
as_text = process_numbers(nums, lambda x: f"#{x}")

print(f"Doubled: {doubled}")
print(f"Squared: {squared}")
print(f"As text: {as_text}")
```

    Doubled: [2, 4, 6, 8, 10]
    Squared: [1, 4, 9, 16, 25]
    As text: ['#1', '#2', '#3', '#4', '#5']


### 1.3 Callbacks for Success and Failure

Real operations can **succeed or fail**. A common pattern is to pass two callbacks: one for each outcome.


```python
import random

def fetch_user(user_id, on_success, on_error):
    """Simulates fetching a user from a database."""
    print(f"Fetching user {user_id}...")

    # Simulate random success/failure
    if random.random() > 0.3:  # 70% chance of success
        user = {"id": user_id, "name": "Alice", "role": "admin"}
        on_success(user)
    else:
        on_error(f"User {user_id} not found in database")


# Define our callbacks
def handle_user(user):
    print(f"Got user: {user['name']} (role: {user['role']})")

def handle_error(error):
    print(f"ERROR: {error}")


# Run it a few times to see both outcomes!
for i in range(5):
    fetch_user(42, handle_user, handle_error)
    print()
```

    Fetching user 42...
    Got user: Alice (role: admin)
    
    Fetching user 42...
    Got user: Alice (role: admin)
    
    Fetching user 42...
    ERROR: User 42 not found in database
    
    Fetching user 42...
    Got user: Alice (role: admin)
    
    Fetching user 42...
    Got user: Alice (role: admin)
    


Your output will differ each time you run this, because of `random`. The point is the split of jobs: `fetch_user` decides **which** callback to call, and the caller decides **what** each callback does.

### Try It: Callback Calculator

Complete the `calculate` function below. It should:

1. Run `operation(a, b)`
2. Pass the answer to `on_result`
3. Pass the error to `on_error` if something goes wrong (for example, dividing by zero)


```python
def calculate(a, b, operation, on_result, on_error):
    """Perform a calculation and call the appropriate callback."""
    try:
        # YOUR CODE HERE: call the operation and pass result to on_result
        pass
    except Exception as e:
        # YOUR CODE HERE: pass the error to on_error
        pass


# Test it!
calculate(10, 3, lambda a, b: a + b,
          on_result=lambda r: print(f"Result: {r}"),
          on_error=lambda e: print(f"Error: {e}"))

calculate(10, 0, lambda a, b: a / b,
          on_result=lambda r: print(f"Result: {r}"),
          on_error=lambda e: print(f"Error: {e}"))


# Tests (uncomment after finishing):
# got = []
# calculate(6, 7, lambda a, b: a * b, on_result=got.append, on_error=got.append)
# assert got == [42]
# calculate(1, 0, lambda a, b: a / b, on_result=got.append, on_error=got.append)
# assert isinstance(got[-1], ZeroDivisionError)
# print("✓ Callback calculator works!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
def calculate(a, b, operation, on_result, on_error):
    try:
        result = operation(a, b)
        on_result(result)
    except Exception as e:
        on_error(e)
```

</details>

### 1.4 Callback Hell (The Problem)

Callbacks are fine for one step. They get ugly when each step needs the result of the previous one, because every step has to be nested **inside** the one before:


```python
# Callback Hell: nested callbacks become hard to read and maintain

def step1(callback):
    print("Step 1: Authenticating...")
    callback("auth_token_123")

def step2(token, callback):
    print(f"Step 2: Fetching data with {token}...")
    callback({"users": ["Alice", "Bob"]})

def step3(data, callback):
    print(f"Step 3: Processing {len(data['users'])} users...")
    callback("done")


# The "pyramid of doom" - each step nests inside the previous one
step1(lambda token:
    step2(token, lambda data:
        step3(data, lambda result:
            print(f"Final result: {result}")
        )
    )
)

# Imagine 10 steps deep... This is called "Callback Hell"
# async/await (Section 4) fixes this: the same steps read top to bottom.
```

    Step 1: Authenticating...
    Step 2: Fetching data with auth_token_123...
    Step 3: Processing 2 users...
    Final result: done


Only three steps, and it's already hard to see what runs when. Each step lives inside the previous step's lambda, so the code drifts to the right like a pyramid. Add error handling at every level and it gets much worse. Keep this picture in mind: in Section 4 we'll write the same flow with `async`/`await`.

**Quick recap**

- A callback is a function passed to another function, to be called later.
- Functions are objects: `greet` is the function itself, `greet()` calls it.
- Success/error callback pairs let the caller decide how to handle each outcome.
- Nesting many callbacks inside each other leads to "callback hell".

---

## 2. Building an Event System (Observer Pattern)

One callback is useful, but real applications have **many events**, and each event can have **many listeners**. Let's build an **event emitter**: an object that

1. lets you **register** callbacks for named events (`on`), and
2. **emits** an event, calling every callback registered for it (`emit`).

This is the **Observer pattern**. The emitter doesn't know who's listening; it just tells everyone who signed up.


```python
class EventEmitter:
    """A simple event system: register callbacks and emit events."""

    def __init__(self):
        self._listeners = {}  # {event_name: [list of callbacks]}

    def on(self, event, callback):
        """Register a callback for an event."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        return self  # allows chaining: emitter.on('a', f).on('b', g)

    def emit(self, event, *args, **kwargs):
        """Trigger an event, calling all registered callbacks."""
        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(*args, **kwargs)

    def off(self, event, callback):
        """Remove a specific callback from an event."""
        if event in self._listeners:
            self._listeners[event].remove(callback)


# Let's use it!
emitter = EventEmitter()

# Register multiple listeners for the same event
emitter.on("user_login", lambda user: print(f"Welcome back, {user}!"))
emitter.on("user_login", lambda user: print(f"[LOG] {user} logged in"))
emitter.on("user_login", lambda user: print(f"[ANALYTICS] Login event for {user}"))

# One event triggers ALL registered callbacks!
print("--- User logs in ---")
emitter.emit("user_login", "Alice")
```

    --- User logs in ---
    Welcome back, Alice!
    [LOG] Alice logged in
    [ANALYTICS] Login event for Alice


Three listeners, one `emit`, three reactions. The code that emits `"user_login"` doesn't need to know anything about logging or analytics. Those parts of the program simply subscribe.

### 2.1 Real-World Example: Online Store Events


```python
class OnlineStore:
    """An online store powered by events."""

    def __init__(self):
        self.events = EventEmitter()
        self.inventory = {"laptop": 5, "phone": 10, "tablet": 3}
        self.revenue = 0

    def purchase(self, item, price):
        if item not in self.inventory or self.inventory[item] <= 0:
            self.events.emit("purchase_failed", item, "Out of stock")
            return

        self.inventory[item] -= 1
        self.revenue += price
        self.events.emit("purchase_complete", item, price)

        # Emit low stock warning if needed
        if self.inventory[item] <= 2:
            self.events.emit("low_stock", item, self.inventory[item])


# Create store and wire up event handlers
store = OnlineStore()

# Different parts of the system listen to different events
store.events.on("purchase_complete",
    lambda item, price: print(f"  Receipt: {item} purchased for ${price}"))

store.events.on("purchase_complete",
    lambda item, price: print(f"  [ANALYTICS] Sale: {item} @ ${price}"))

store.events.on("purchase_failed",
    lambda item, reason: print(f"  FAILED: {item} - {reason}"))

store.events.on("low_stock",
    lambda item, qty: print(f"  WARNING: {item} is low! Only {qty} left!"))


# Simulate purchases
print("Customer 1 buys a tablet:")
store.purchase("tablet", 499)
print("\nCustomer 2 buys a tablet:")
store.purchase("tablet", 499)
print("\nCustomer 3 buys a tablet:")
store.purchase("tablet", 499)
print("\nCustomer 4 tries to buy a tablet:")
store.purchase("tablet", 499)
```

    Customer 1 buys a tablet:
      Receipt: tablet purchased for $499
      [ANALYTICS] Sale: tablet @ $499
      WARNING: tablet is low! Only 2 left!
    
    Customer 2 buys a tablet:
      Receipt: tablet purchased for $499
      [ANALYTICS] Sale: tablet @ $499
      WARNING: tablet is low! Only 1 left!
    
    Customer 3 buys a tablet:
      Receipt: tablet purchased for $499
      [ANALYTICS] Sale: tablet @ $499
      WARNING: tablet is low! Only 0 left!
    
    Customer 4 tries to buy a tablet:
      FAILED: tablet - Out of stock


`OnlineStore` only announces **what happened** (`purchase_complete`, `low_stock`, `purchase_failed`). Receipts, analytics and warnings are wired up outside the class. To add, say, an email when stock runs low, you'd add one more `store.events.on(...)` line and leave `OnlineStore` untouched.

### Try It: Chat Room Events

Build a `ChatRoom` class that uses `EventEmitter` and emits these events:

- `"user_joined"` when someone joins (pass the username)
- `"message"` when someone sends a message (pass the username and the text)
- `"user_left"` when someone leaves (pass the username)


```python
class ChatRoom:
    def __init__(self, name):
        self.name = name
        self.events = EventEmitter()
        self.users = []

    def join(self, username):
        # YOUR CODE: add user to self.users and emit "user_joined"
        pass

    def send_message(self, username, text):
        # YOUR CODE: emit "message" with username and text
        pass

    def leave(self, username):
        # YOUR CODE: remove user from self.users and emit "user_left"
        pass


# Test your implementation!
room = ChatRoom("Python Learners")

# Wire up event handlers
room.events.on("user_joined", lambda u: print(f">> {u} entered the room"))
room.events.on("message", lambda u, t: print(f"   [{u}]: {t}"))
room.events.on("user_left", lambda u: print(f"<< {u} left the room"))

# Simulate a conversation
room.join("Alice")
room.join("Bob")
room.send_message("Alice", "Hey everyone!")
room.send_message("Bob", "Hi Alice!")
room.leave("Alice")


# Tests (uncomment after finishing):
# test_room = ChatRoom("Test")
# seen = []
# test_room.events.on("user_joined", lambda u: seen.append(("joined", u)))
# test_room.events.on("message", lambda u, t: seen.append(("message", u, t)))
# test_room.events.on("user_left", lambda u: seen.append(("left", u)))
# test_room.join("Ann")
# test_room.send_message("Ann", "hi")
# test_room.leave("Ann")
# assert seen == [("joined", "Ann"), ("message", "Ann", "hi"), ("left", "Ann")]
# assert test_room.users == []
# print("✓ ChatRoom works!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
class ChatRoom:
    def __init__(self, name):
        self.name = name
        self.events = EventEmitter()
        self.users = []

    def join(self, username):
        self.users.append(username)
        self.events.emit("user_joined", username)

    def send_message(self, username, text):
        self.events.emit("message", username, text)

    def leave(self, username):
        self.users.remove(username)
        self.events.emit("user_left", username)
```

</details>

### 2.2 Decorator Syntax for Event Registration

Writing `emitter.on("event", func)` after every function gets repetitive. A decorator lets you register a function right where you define it:


```python
class DecoratorEventEmitter(EventEmitter):
    """EventEmitter with decorator support."""

    def listener(self, event):
        """Decorator to register a function as an event listener."""
        def decorator(func):
            self.on(event, func)
            return func
        return decorator


# Now we can use @ syntax!
server = DecoratorEventEmitter()

@server.listener("request")
def log_request(method, path):
    print(f"[LOG] {method} {path}")

@server.listener("request")
def check_auth(method, path):
    if path.startswith("/admin"):
        print(f"[AUTH] Checking credentials for {path}")

@server.listener("error")
def handle_server_error(code, message):
    print(f"[ERROR {code}] {message}")


# Simulate server events
print("--- Normal request ---")
server.emit("request", "GET", "/home")
print("\n--- Admin request ---")
server.emit("request", "POST", "/admin/users")
print("\n--- Error ---")
server.emit("error", 404, "Page not found")
```

    --- Normal request ---
    [LOG] GET /home
    
    --- Admin request ---
    [LOG] POST /admin/users
    [AUTH] Checking credentials for /admin/users
    
    --- Error ---
    [ERROR 404] Page not found


`@server.listener("request")` calls `server.on("request", log_request)` for you and then returns the function unchanged, so `log_request` is still a normal function you can call yourself. Web frameworks such as Flask and FastAPI use exactly this trick to register routes (`@app.get("/")`).

**Quick recap**

- An event emitter keeps a dictionary of `event name -> list of callbacks`.
- `on()` subscribes a callback, `emit()` calls every subscriber, `off()` unsubscribes.
- The code that emits an event doesn't need to know who is listening (loose coupling).
- A decorator can register a listener at the point where the function is defined.

---

## 3. The Event Loop: The Engine Behind It All

An **event loop** is a loop that:

1. waits for events to occur,
2. sends each event to the right handler, and
3. goes back to waiting.

```
while running:
    event = wait_for_next_event()
    handler = find_handler(event)
    handler(event)
```

Every GUI app, web server and game engine has one. Let's build a simple one.


```python
import time
from collections import deque


class SimpleEventLoop:
    """A minimal event loop to understand the concept."""

    def __init__(self):
        self._queue = deque()      # Events waiting to be processed
        self._handlers = {}        # {event_type: handler_function}
        self._running = False
        self._timers = []          # Scheduled events

    def register(self, event_type, handler):
        """Register a handler for an event type."""
        self._handlers[event_type] = handler

    def post(self, event_type, data=None):
        """Add an event to the queue."""
        self._queue.append((event_type, data))

    def schedule(self, delay, event_type, data=None):
        """Schedule an event for the future."""
        fire_at = time.time() + delay
        self._timers.append((fire_at, event_type, data))
        self._timers.sort(key=lambda t: t[0])  # Keep sorted by time

    def run(self):
        """Run the event loop until no events remain."""
        self._running = True
        print("Event loop started!")

        while self._running:
            # Check if any timers have fired
            now = time.time()
            while self._timers and self._timers[0][0] <= now:
                _, event_type, data = self._timers.pop(0)
                self._queue.append((event_type, data))

            # Process one event from the queue
            if self._queue:
                event_type, data = self._queue.popleft()

                if event_type == "__STOP__":
                    self._running = False
                    print("Event loop stopped!")
                    break

                handler = self._handlers.get(event_type)
                if handler:
                    handler(data)
                else:
                    print(f"No handler for event: {event_type}")

            # If nothing to do right now but timers pending, wait a bit
            elif self._timers:
                time.sleep(0.01)
            else:
                # No events, no timers: we're done
                break

        print("Event loop finished.")


# Create and configure our event loop
loop = SimpleEventLoop()

loop.register("greet", lambda data: print(f"  Hello, {data}!"))
loop.register("alarm", lambda data: print(f"  ALARM: {data}"))
loop.register("tick",  lambda data: print(f"  Tick #{data}"))

# Queue up some events
loop.post("greet", "Alice")
loop.post("greet", "Bob")
loop.post("tick", 1)

# Schedule a delayed event (0.5 seconds from now)
loop.schedule(0.5, "alarm", "Wake up!")
loop.schedule(0.3, "tick", 2)

# Run it!
loop.run()
```

    Event loop started!
      Hello, Alice!
      Hello, Bob!
      Tick #1


      Tick #2
      ALARM: Wake up!
    Event loop finished.


Look at the order. The three posted events run first, in the order they were queued. The scheduled events wait until their time comes, so `Tick #2` (0.3 s) fires before the alarm (0.5 s), even though the alarm was scheduled first. When the queue is empty and no timers are left, the loop ends. (You could also stop it early by posting a `"__STOP__"` event.)

### How This Connects to `asyncio`

Our `SimpleEventLoop` is a toy version of what Python's `asyncio` does for real:

| Our `SimpleEventLoop` | `asyncio` |
|---|---|
| `loop.post(event)` puts work in the queue | `asyncio.create_task(coro)` schedules a coroutine |
| Handlers run when their event comes up | Coroutines resume when what they're waiting for is ready |
| `loop.schedule(delay, ...)` | `asyncio.sleep(delay)` and other timers |
| `loop.run()` | `asyncio.run(main())` |
| The event queue | The loop's internal queue of ready work |

One big difference: our handlers always run from start to finish. An `asyncio` coroutine can **pause in the middle** at an `await` and let other code run. That's what we'll look at next.

**Quick recap**

- An event loop repeatedly takes the next event and runs its handler.
- Events can be queued straight away or scheduled for later with a timer.
- `asyncio` is a production-quality event loop; coroutines are what it runs.

---

## 4. `asyncio`: Python's Async Framework

`asyncio` is Python's built-in library for writing **concurrent** code with the `async`/`await` syntax. "Concurrent" here means many tasks make progress during the same period of time, by taking turns while the others are waiting.

### Key Vocabulary

| Term | What it means | Analogy |
|---|---|---|
| **Coroutine** | A function that can pause and resume | A bookmark in a book |
| **`async def`** | Defines a coroutine function | "This function can pause" |
| **`await`** | Pause here until the result is ready | "I'll wait here, others can go ahead" |
| **Event loop** | Schedules and runs coroutines | The restaurant manager |
| **Task** | A coroutine scheduled to run concurrently | An order ticket |

### 4.1 Your First Coroutine


```python
import asyncio

# A coroutine is defined with 'async def'
async def say_hello(name, delay):
    print(f"Hello, {name}! (waiting {delay}s...)")
    await asyncio.sleep(delay)  # Non-blocking pause!
    print(f"Goodbye, {name}! (after {delay}s)")
    return f"{name} done"


# In Jupyter, we can use 'await' directly at the top level
result = await say_hello("Alice", 1)
print(f"Result: {result}")
```

    Hello, Alice! (waiting 1s...)


    Goodbye, Alice! (after 1s)
    Result: Alice done


### 4.2 `await` vs No `await`

The most common beginner mistake: forgetting `await`. What happens then?


```python
async def greet():
    return "Hello!"

# WITHOUT await: you get a coroutine OBJECT, not the result!
result_wrong = greet()
print(f"Without await: {result_wrong}")
print(f"Type: {type(result_wrong)}")

# WITH await: you get the actual return value
result_right = await greet()
print(f"\nWith await: {result_right}")
print(f"Type: {type(result_right)}")

# Clean up the unawaited coroutine
result_wrong.close()
```

    Without await: <coroutine object greet at 0x10bd8ac80>
    Type: <class 'coroutine'>
    
    With await: Hello!
    Type: <class 'str'>


Calling an `async def` function does **not** run it. It only builds a coroutine object, like a recipe that hasn't been cooked yet. `await` is what actually runs it and hands you the return value. The `.close()` at the end tidies up the coroutine we never ran, so Python doesn't warn about it.

Now remember the pyramid from Section 1.4? Here are the same three steps written with `async`/`await`:


```python
# The callback-hell example from Section 1.4, rewritten with async/await

async def authenticate():
    print("Step 1: Authenticating...")
    return "auth_token_123"

async def fetch_data(token):
    print(f"Step 2: Fetching data with {token}...")
    return {"users": ["Alice", "Bob"]}

async def process(data):
    print(f"Step 3: Processing {len(data['users'])} users...")
    return "done"


token = await authenticate()
data = await fetch_data(token)
result = await process(data)
print(f"Final result: {result}")
```

    Step 1: Authenticating...
    Step 2: Fetching data with auth_token_123...
    Step 3: Processing 2 users...
    Final result: done


Same steps, same output, but each step is one line and the code reads top to bottom. You could also wrap all three lines in a single `try/except` to handle errors, which is very awkward with nested callbacks.

### 4.3 Running Tasks Concurrently with `asyncio.gather`

Here's where async really pays off: doing several things during the same wait.


```python
import asyncio
import time


async def make_coffee(order):
    print(f"  Starting coffee: {order}")
    await asyncio.sleep(2)  # Takes 2 seconds
    print(f"  Coffee ready: {order}")
    return f"{order} (hot)"


# SEQUENTIAL: One at a time (slow!)
print("=== Sequential (one at a time) ===")
start = time.time()

coffee1 = await make_coffee("Espresso")
coffee2 = await make_coffee("Latte")
coffee3 = await make_coffee("Cappuccino")

print(f"Total time: {time.time() - start:.1f}s")
print(f"Orders: {[coffee1, coffee2, coffee3]}")


print("\n=== Concurrent (all at once!) ===")
start = time.time()

# asyncio.gather runs all coroutines concurrently!
results = await asyncio.gather(
    make_coffee("Espresso"),
    make_coffee("Latte"),
    make_coffee("Cappuccino"),
)

print(f"Total time: {time.time() - start:.1f}s")
print(f"Orders: {results}")
```

    === Sequential (one at a time) ===
      Starting coffee: Espresso


      Coffee ready: Espresso
      Starting coffee: Latte


      Coffee ready: Latte
      Starting coffee: Cappuccino


      Coffee ready: Cappuccino
    Total time: 6.0s
    Orders: ['Espresso (hot)', 'Latte (hot)', 'Cappuccino (hot)']
    
    === Concurrent (all at once!) ===
      Starting coffee: Espresso
      Starting coffee: Latte
      Starting coffee: Cappuccino


      Coffee ready: Espresso
      Coffee ready: Latte
      Coffee ready: Cappuccino
    Total time: 2.0s
    Orders: ['Espresso (hot)', 'Latte (hot)', 'Cappuccino (hot)']


- **Sequential**: about 6 seconds (2 + 2 + 2)
- **Concurrent**: about 2 seconds, because all three coffees wait at the same time

While one coroutine is sleeping (in real code: waiting for the network or the disk), the event loop runs the others. `gather` returns the results in the same order you passed the coroutines in.

### 4.4 `asyncio.create_task`: Start Now, Collect Later

`gather` starts coroutines and waits for them in one go. `create_task` splits that into two steps: it schedules a coroutine to start **as soon as the event loop gets a chance**, and gives you back a `Task` object you can await later.


```python
async def background_job(name, duration):
    print(f"  [{name}] Started")
    await asyncio.sleep(duration)
    print(f"  [{name}] Finished after {duration}s")
    return name


async def main():
    print("Creating tasks...")

    # create_task schedules the coroutine to run WITHOUT waiting
    task1 = asyncio.create_task(background_job("Backup", 2))
    task2 = asyncio.create_task(background_job("Email", 1))
    task3 = asyncio.create_task(background_job("Report", 3))

    print("Tasks created! Doing other work...")
    await asyncio.sleep(0.5)
    print("Still working...")

    # Now wait for all tasks to finish
    results = await asyncio.gather(task1, task2, task3)
    print(f"\nAll done! Completed: {results}")


await main()
```

    Creating tasks...
    Tasks created! Doing other work...
      [Backup] Started
      [Email] Started
      [Report] Started


    Still working...


      [Email] Finished after 1s


      [Backup] Finished after 2s


      [Report] Finished after 3s
    
    All done! Completed: ['Backup', 'Email', 'Report']


Look at the output order. "Tasks created! Doing other work..." is printed **before** any task starts. Creating a task only schedules it; the tasks actually start at the next `await` (`asyncio.sleep(0.5)`), when `main` hands control back to the event loop.

Always keep a reference to the tasks you create (here `task1`, `task2`, `task3`) and await them at some point. The event loop only keeps a weak reference to a task, so a task nobody refers to can disappear before it finishes.

### 4.5 Error Handling in Async Code


```python
async def risky_operation(name, should_fail=False):
    await asyncio.sleep(0.5)
    if should_fail:
        raise ConnectionError(f"{name}: Connection refused!")
    return f"{name}: Success!"


# Method 1: try/except (just like sync code!)
print("=== try/except ===")
try:
    result = await risky_operation("API Call", should_fail=True)
except ConnectionError as e:
    print(f"Caught error: {e}")


# Method 2: gather with return_exceptions=True
print("\n=== gather with return_exceptions ===")
results = await asyncio.gather(
    risky_operation("Task A", should_fail=False),
    risky_operation("Task B", should_fail=True),
    risky_operation("Task C", should_fail=False),
    return_exceptions=True  # Don't let one failure crash everything
)

for r in results:
    if isinstance(r, Exception):
        print(f"  FAILED: {r}")
    else:
        print(f"  OK: {r}")
```

    === try/except ===


    Caught error: API Call: Connection refused!
    
    === gather with return_exceptions ===


      OK: Task A: Success!
      FAILED: Task B: Connection refused!
      OK: Task C: Success!


Without `return_exceptions=True`, the first exception would be raised straight out of `gather` and you wouldn't get the other results back. With it, each exception is returned in the results list in its normal position, so you can check every result one by one.

### 4.6 Timeouts: Don't Wait Forever


```python
async def slow_api_call():
    """Simulates a very slow API."""
    print("Calling slow API...")
    await asyncio.sleep(10)  # This takes 10 seconds!
    return "data"


# Use asyncio.wait_for to set a timeout
try:
    result = await asyncio.wait_for(slow_api_call(), timeout=2.0)
    print(f"Got: {result}")
except asyncio.TimeoutError:
    print("Timed out after 2 seconds! The API was too slow.")
```

    Calling slow API...


    Timed out after 2 seconds! The API was too slow.


`wait_for` cancels `slow_api_call` when the 2 seconds are up, so this cell takes about 2 seconds, not 10. (Since Python 3.11, `asyncio.TimeoutError` is just another name for the built-in `TimeoutError`.)

### Try It: Async Web Scraper Simulation

Complete the `fetch_page` coroutine, then use `asyncio.gather` to fetch all five pages concurrently. Each page takes at most 2 seconds, so the whole thing should take about 2 seconds, not 5 to 10.


```python
import asyncio
import random
import time


async def fetch_page(url):
    """Simulate fetching a web page.

    - Print that you're starting to fetch the URL
    - await asyncio.sleep for a random time between 0.5 and 2.0 seconds
    - Return a dict with 'url' and 'size' (random int between 1000-5000)
    """
    # YOUR CODE HERE
    pass


urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
    "https://example.com/page4",
    "https://example.com/page5",
]

# YOUR CODE: use asyncio.gather to fetch ALL pages concurrently
start = time.time()
# results = ???

# Print results
# for page in results:
#     print(f"  {page['url']} -> {page['size']} bytes")
# print(f"\nTotal time: {time.time() - start:.1f}s")


# Tests (uncomment after finishing):
# assert len(results) == 5
# assert time.time() - start < 2.5, "The pages should be fetched concurrently"
# page = await fetch_page("https://example.com/test")
# assert page["url"] == "https://example.com/test"
# assert 1000 <= page["size"] <= 5000
# print("✓ Scraper works!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
async def fetch_page(url):
    print(f"  Fetching {url}...")
    delay = random.uniform(0.5, 2.0)
    await asyncio.sleep(delay)
    size = random.randint(1000, 5000)
    print(f"  Got {url} ({size} bytes, {delay:.1f}s)")
    return {"url": url, "size": size}


start = time.time()
results = await asyncio.gather(*[fetch_page(url) for url in urls])

print("\n--- Results ---")
for page in results:
    print(f"  {page['url']} -> {page['size']} bytes")
print(f"\nTotal time: {time.time() - start:.1f}s")
```

</details>

### 4.7 Async Generators and `async for`

A normal generator `yield`s values one at a time. An **async generator** can also `await` between values, which makes it a good fit for data that arrives over time:


```python
async def live_sensor_data(sensor_name, readings=5):
    """Simulates a sensor that produces readings over time."""
    for i in range(readings):
        await asyncio.sleep(0.5)  # Sensor reads every 0.5s
        value = random.uniform(20.0, 30.0)  # Temperature in Celsius
        yield {"sensor": sensor_name, "reading": i + 1, "temp": round(value, 1)}


# Consume the async generator with 'async for'
print("Reading sensor data...")
async for data in live_sensor_data("TempSensor-A", readings=5):
    status = "HIGH" if data["temp"] > 27 else "OK"
    print(f"  [{data['sensor']}] Reading #{data['reading']}: {data['temp']}C ({status})")

print("Done!")
```

    Reading sensor data...


      [TempSensor-A] Reading #1: 23.7C (OK)


      [TempSensor-A] Reading #2: 23.0C (OK)


      [TempSensor-A] Reading #3: 23.6C (OK)


      [TempSensor-A] Reading #4: 26.1C (OK)


      [TempSensor-A] Reading #5: 21.6C (OK)
    Done!


`async for` asks the generator for the next value and waits (without blocking other tasks) until it's ready. Your temperatures will be different each run.

### 4.8 Async Context Managers

`with open(...)` makes sure a file gets closed. `async with` does the same job for resources whose setup or cleanup needs to `await`, like network or database connections:


```python
class AsyncDatabaseConnection:
    """Simulates an async database connection."""

    def __init__(self, db_name):
        self.db_name = db_name
        self.connected = False

    async def __aenter__(self):
        """Called when entering 'async with'."""
        print(f"Connecting to {self.db_name}...")
        await asyncio.sleep(0.5)  # Simulate connection time
        self.connected = True
        print(f"Connected to {self.db_name}!")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting 'async with': even if there's an error!"""
        print(f"Closing connection to {self.db_name}...")
        await asyncio.sleep(0.2)  # Simulate cleanup
        self.connected = False
        print("Connection closed.")

    async def query(self, sql):
        if not self.connected:
            raise RuntimeError("Not connected!")
        print(f"  Executing: {sql}")
        await asyncio.sleep(0.3)
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


# Use it with 'async with': connection is automatically cleaned up!
async with AsyncDatabaseConnection("mydb") as db:
    results = await db.query("SELECT * FROM users")
    print(f"  Results: {results}")

# Connection is guaranteed to be closed here, even if an error occurred
```

    Connecting to mydb...


    Connected to mydb!
      Executing: SELECT * FROM users


      Results: [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
    Closing connection to mydb...


    Connection closed.


`__aenter__` and `__aexit__` are the async versions of `__enter__` and `__exit__`. Because they're `async`, connecting and disconnecting can `await` without freezing other tasks. `__aexit__` runs even if the code inside the block raises an error, so the connection is always closed.

**Quick recap**

- `async def` defines a coroutine; calling it only creates a coroutine object. `await` runs it.
- `asyncio.gather` runs several coroutines concurrently and returns results in argument order.
- `asyncio.create_task` starts a coroutine in the background; keep the task and await it later.
- Use `try/except`, `return_exceptions=True` and `asyncio.wait_for` to handle errors and timeouts.
- `async for` consumes async generators; `async with` manages async resources.

---

## 5. Real-World Patterns: Putting It All Together

### 5.1 Pattern: Async Event Emitter

Let's combine the `EventEmitter` from Section 2 with `asyncio`, so that handlers can be coroutines:


```python
import inspect


class AsyncEventEmitter:
    """An event emitter that supports async handlers."""

    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    async def emit(self, event, *args, **kwargs):
        """Emit an event, running all handlers concurrently."""
        if event not in self._listeners:
            return

        tasks = []
        for callback in self._listeners[event]:
            if inspect.iscoroutinefunction(callback):
                tasks.append(callback(*args, **kwargs))
            else:
                callback(*args, **kwargs)  # Sync handlers run immediately

        if tasks:
            await asyncio.gather(*tasks)


# Example: Async notification system
notifications = AsyncEventEmitter()

async def send_email(user, message):
    print(f"  Sending email to {user}...")
    await asyncio.sleep(1)  # Simulate sending
    print(f"  Email sent to {user}!")

async def send_push(user, message):
    print(f"  Sending push notification to {user}...")
    await asyncio.sleep(0.5)
    print(f"  Push sent to {user}!")

def log_notification(user, message):
    print(f"  [LOG] Notification for {user}: {message}")


notifications.on("alert", send_email)
notifications.on("alert", send_push)
notifications.on("alert", log_notification)  # sync handler mixed in!

print("Triggering alert...")
start = time.time()
await notifications.emit("alert", "Alice", "Server is down!")
print(f"\nAll notifications sent in {time.time() - start:.1f}s")
print("(Email and push ran concurrently!)")
```

    Triggering alert...
      [LOG] Notification for Alice: Server is down!
      Sending email to Alice...
      Sending push notification to Alice...


      Push sent to Alice!


      Email sent to Alice!
    
    All notifications sent in 1.0s
    (Email and push ran concurrently!)


The two async handlers run together through `gather`, so sending everything takes about 1 second (the slower handler), not 1.5. The sync logger runs immediately inside `emit`, which is why its line appears first.

`inspect.iscoroutinefunction` tells us whether a handler was defined with `async def`. (Older code uses `asyncio.iscoroutinefunction`, which is deprecated since Python 3.14.)

### 5.2 Pattern: Producer/Consumer with `asyncio.Queue`

A classic pattern: one coroutine **produces** work and puts it on a queue, others **consume** it.


```python
async def order_producer(queue, orders):
    """Simulates customers placing orders."""
    for order in orders:
        await asyncio.sleep(random.uniform(0.2, 0.8))
        print(f"  [NEW ORDER] {order}")
        await queue.put(order)

    # Signal that no more orders are coming
    await queue.put(None)


async def order_consumer(queue, chef_name):
    """Simulates a chef processing orders."""
    while True:
        order = await queue.get()  # Wait for an order

        if order is None:
            await queue.put(None)  # Pass the signal to other consumers
            print(f"  [{chef_name}] No more orders, going home!")
            break

        cook_time = random.uniform(0.5, 1.5)
        print(f"  [{chef_name}] Cooking {order}...")
        await asyncio.sleep(cook_time)
        print(f"  [{chef_name}] {order} READY! (took {cook_time:.1f}s)")
        queue.task_done()


# Set up the kitchen
order_queue = asyncio.Queue()

orders = ["Burger", "Pizza", "Pasta", "Salad", "Soup", "Steak"]

print("Kitchen is open!\n")
await asyncio.gather(
    order_producer(order_queue, orders),
    order_consumer(order_queue, "Chef Alice"),
    order_consumer(order_queue, "Chef Bob"),
)
print("\nKitchen closed!")
```

    Kitchen is open!
    


      [NEW ORDER] Burger
      [Chef Alice] Cooking Burger...


      [NEW ORDER] Pizza
      [Chef Bob] Cooking Pizza...
      [Chef Alice] Burger READY! (took 0.7s)


      [NEW ORDER] Pasta
      [Chef Alice] Cooking Pasta...
      [Chef Bob] Pizza READY! (took 0.8s)


      [NEW ORDER] Salad
      [Chef Bob] Cooking Salad...


      [NEW ORDER] Soup


      [NEW ORDER] Steak
      [Chef Alice] Pasta READY! (took 1.5s)
      [Chef Alice] Cooking Soup...


      [Chef Bob] Salad READY! (took 1.4s)
      [Chef Bob] Cooking Steak...


      [Chef Bob] Steak READY! (took 0.7s)
      [Chef Bob] No more orders, going home!
      [Chef Alice] Soup READY! (took 1.4s)
      [Chef Alice] No more orders, going home!
    
    Kitchen closed!


The `None` at the end is a **sentinel** (also called a *poison pill*): it tells a chef there's no more work. Each chef that receives it puts it back on the queue, so the other chef gets the message too. The order of the lines will vary between runs because the timings are random.

### 5.3 Pattern: Async Retry with Exponential Backoff

A practical pattern for flaky network calls: if a call fails, wait a bit and try again, waiting longer each time.


```python
async def retry_with_backoff(coro_func, max_retries=3, base_delay=1.0):
    """Retry an async function with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            result = await coro_func()
            return result
        except Exception as e:
            if attempt == max_retries:
                print(f"  All {max_retries + 1} attempts failed. Giving up.")
                raise

            delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s...
            print(f"  Attempt {attempt + 1} failed: {e}")
            print(f"  Retrying in {delay}s...")
            await asyncio.sleep(delay)


# Simulate a flaky API
call_count = 0

async def flaky_api():
    global call_count
    call_count += 1
    if call_count < 3:  # Fails the first 2 times
        raise ConnectionError("Server unavailable")
    return {"status": "ok", "data": [1, 2, 3]}


call_count = 0
print("Calling flaky API with retry...")
result = await retry_with_backoff(flaky_api, max_retries=3, base_delay=0.5)
print(f"\nSuccess! Got: {result}")
```

    Calling flaky API with retry...
      Attempt 1 failed: Server unavailable
      Retrying in 0.5s...


      Attempt 2 failed: Server unavailable
      Retrying in 1.0s...


    
    Success! Got: {'status': 'ok', 'data': [1, 2, 3]}


Each failure doubles the wait (0.5 s, then 1 s, then 2 s, ...). Waiting longer each time gives a struggling server room to recover instead of hammering it with requests. If every attempt fails, the bare `raise` passes the last error on to the caller.

**Quick recap**

- An async event emitter can run all coroutine handlers for an event concurrently with `gather`.
- `asyncio.Queue` connects producers and consumers; a sentinel such as `None` signals "no more work".
- Retry with exponential backoff: try, wait, try again, doubling the wait each time.

---

## Quiz Time: Test Your Understanding

For each question, **predict the answer first**, then run the cell and open the answer.

### Q1: What does this print, and in what order?


```python
async def a():
    print("1")
    await asyncio.sleep(1)
    print("2")

async def b():
    print("3")
    await asyncio.sleep(0.5)
    print("4")

await asyncio.gather(a(), b())
print("5")
```

    1
    3


    4


    2
    5


<details markdown="1">
<summary>Show answer</summary>

```
1
3
4
2
5
```

**Why?**

- `a()` and `b()` start together, and both print their first line (`1`, `3`).
- Both reach `await asyncio.sleep()`, pause, and hand control back to the event loop.
- `b()` has the shorter sleep (0.5 s), so it resumes first and prints `4`.
- `a()` resumes after 1 s and prints `2`.
- `gather` finishes, so `5` is printed last.

</details>

### Q2: What's wrong with this code?

Run it and read the error message. Can you explain it?


```python
async def get_data():
    await asyncio.sleep(1)
    return {"key": "value"}

data = get_data()
try:
    print(data["key"])
except TypeError as e:
    print(f"TypeError: {e}")
finally:
    data.close()  # tidy up the coroutine object we never awaited
```

    TypeError: 'coroutine' object is not subscriptable


<details markdown="1">
<summary>Show answer</summary>

**The `await` is missing.** `data = get_data()` returns a coroutine object, not the dictionary, and you can't index a coroutine with `["key"]`.

Fix: `data = await get_data()`

This is the most common asyncio mistake of all.

</details>

### Q3: Which option runs faster, and why?

Both options fetch the same three (pretend) URLs. Each fetch takes 1 second. Guess the two times before you run it.


```python
async def fetch(url):
    await asyncio.sleep(1)  # pretend each request takes 1 second
    return f"<html from {url}>"

url1, url2, url3 = "/a", "/b", "/c"

# Option A
start = time.time()
r1 = await fetch(url1)
r2 = await fetch(url2)
r3 = await fetch(url3)
print(f"Option A: {time.time() - start:.1f}s")

# Option B
start = time.time()
r1, r2, r3 = await asyncio.gather(fetch(url1), fetch(url2), fetch(url3))
print(f"Option B: {time.time() - start:.1f}s")
```

    Option A: 3.0s


    Option B: 1.0s


<details markdown="1">
<summary>Show answer</summary>

**Option B is faster.**

- **Option A** is sequential. It waits for each fetch to finish before starting the next. Total time = the **sum** of all fetch times (3 s).
- **Option B** is concurrent. All three fetches wait at the same time. Total time = the **longest** single fetch (1 s).

</details>

**Quick recap**

- Coroutines started with `gather` interleave at every `await`; shorter waits finish first.
- A missing `await` gives you a coroutine object instead of a result.
- Awaiting one call after another is sequential; use `gather` to overlap the waiting.

---

## Final Challenge: Async Task Pipeline

Build an async pipeline that pushes "orders" through several stages. Each stage is a coroutine that takes an order and returns the updated order.

**Requirements:**

1. Create an `AsyncPipeline` class with `add_stage(name, handler)` and `process(item)` methods.
2. Each stage's handler is an async function that takes an item and returns a transformed item.
3. `process()` runs the item through all stages **one after another** (the output of one stage is the input to the next).
4. Print a log line as each stage starts and finishes.
5. Process several orders **concurrently** using `asyncio.gather`.


```python
class AsyncPipeline:
    def __init__(self):
        self.stages = []  # List of (name, handler) tuples

    def add_stage(self, name, handler):
        """Add a processing stage."""
        # YOUR CODE HERE
        pass

    async def process(self, item):
        """Run an item through all stages sequentially."""
        # YOUR CODE HERE:
        # - Loop through self.stages
        # - Print when each stage starts
        # - await the handler with the item
        # - Print when each stage finishes
        # - Return the final result
        pass


# --- Pipeline stages ---

async def validate_order(order):
    await asyncio.sleep(0.3)
    order["validated"] = True
    return order

async def calculate_total(order):
    await asyncio.sleep(0.2)
    order["total"] = order["quantity"] * order["price"]
    return order

async def apply_discount(order):
    await asyncio.sleep(0.1)
    if order["total"] > 100:
        order["discount"] = order["total"] * 0.1
        order["total"] -= order["discount"]
    else:
        order["discount"] = 0
    return order


# --- Build the pipeline ---
pipeline = AsyncPipeline()
pipeline.add_stage("Validate", validate_order)
pipeline.add_stage("Calculate Total", calculate_total)
pipeline.add_stage("Apply Discount", apply_discount)


# --- Process multiple orders concurrently ---
orders = [
    {"id": 1, "item": "Laptop", "quantity": 1, "price": 999},
    {"id": 2, "item": "Mouse", "quantity": 3, "price": 25},
    {"id": 3, "item": "Monitor", "quantity": 2, "price": 350},
]

# YOUR CODE: process all orders concurrently with asyncio.gather
# results = ???

# Print final results
# print("\n" + "="*50)
# print("PROCESSED ORDERS")
# print("="*50)
# for order in results:
#     print(f"  Order #{order['id']}: {order['item']} -> ${order['total']:.2f} (discount: ${order['discount']:.2f})")


# Tests (uncomment after finishing):
# assert [name for name, _ in pipeline.stages] == ["Validate", "Calculate Total", "Apply Discount"]
# by_id = {order["id"]: order for order in results}
# assert by_id[1]["validated"] and round(by_id[1]["total"], 2) == 899.10
# assert by_id[2]["total"] == 75 and by_id[2]["discount"] == 0
# assert round(by_id[3]["total"], 2) == 630.00
# print("✓ Pipeline works!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
class AsyncPipeline:
    def __init__(self):
        self.stages = []

    def add_stage(self, name, handler):
        self.stages.append((name, handler))

    async def process(self, item):
        result = item
        for name, handler in self.stages:
            print(f"  [Order #{item['id']}] Stage: {name}...")
            result = await handler(result)
            print(f"  [Order #{item['id']}] Finished: {name}")
        print(f"  [Order #{item['id']}] Pipeline complete!")
        return result


pipeline = AsyncPipeline()
pipeline.add_stage("Validate", validate_order)
pipeline.add_stage("Calculate Total", calculate_total)
pipeline.add_stage("Apply Discount", apply_discount)

results = await asyncio.gather(*[pipeline.process(order) for order in orders])

print("\n" + "=" * 50)
print("PROCESSED ORDERS")
print("=" * 50)
for order in results:
    print(f"  Order #{order['id']}: {order['item']} -> ${order['total']:.2f} (discount: ${order['discount']:.2f})")
```

</details>

**Quick recap**

- Inside one order, the stages run in sequence because each needs the previous result.
- Across orders, `gather` runs the pipelines concurrently, so the three orders overlap.

---

## Summary & Cheat Sheet

### Callbacks

```python
# Pass a function to be called later
def do_work(on_done):
    result = heavy_computation()
    on_done(result)  # call back!

do_work(lambda r: print(f"Got: {r}"))
```

### Event Emitter (Observer Pattern)

```python
emitter = EventEmitter()
emitter.on("event_name", handler_func)   # subscribe
emitter.emit("event_name", data)         # publish
emitter.off("event_name", handler_func)  # unsubscribe
```

### asyncio Essentials

```python
import asyncio

# Define a coroutine
async def my_task():
    await asyncio.sleep(1)
    return "done"

# Run coroutines concurrently
results = await asyncio.gather(task1(), task2(), task3())

# Start a task in the background, await it later
task = asyncio.create_task(my_task())
result = await task

# Timeout
result = await asyncio.wait_for(slow_task(), timeout=5.0)

# Producer/consumer
queue = asyncio.Queue()
await queue.put(item)
item = await queue.get()

# In a .py script (not in Jupyter)
asyncio.run(main())
```

### When to Use What

| Situation | Use |
|---|---|
| Simple "do X when Y happens" | A callback function |
| Many listeners for named events | An event emitter |
| Many I/O-bound operations at once (network, disk) | `asyncio` with `async`/`await` |
| CPU-heavy work in parallel | `multiprocessing` (not covered here) |

### Key Takeaways

1. **Callbacks** are functions passed to other functions to be called later.
2. **Event emitters** separate *what happened* from *who cares about it*.
3. **`async`/`await`** lets async code read like normal top-to-bottom code, with no callback hell.
4. **`asyncio.gather`** is your go-to for running things concurrently.
5. Always **`await`** your coroutines. Forgetting it is the number one async bug.

### Further Reading

- [Official asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)
- [Python Concurrency with asyncio (book)](https://www.manning.com/books/python-concurrency-with-asyncio)

### What's Next

The next notebook, **Async Programming**, goes much deeper into `asyncio`: `TaskGroup`, cancellation, locks, semaphores, mixing blocking code with async code, and a small async web crawler. Later, the **FastAPI** notebook shows these ideas in a real web framework.
