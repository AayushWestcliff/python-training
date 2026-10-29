# Event-Driven Programming in Python

> *"Don't call us, we'll call you."*\
> — The Hollywood Principle (a.k.a. Inversion of Control)

---

In traditional programming, **you** decide the order things happen. In event-driven programming, **events** decide.

Think about it: - You don't keep checking if someone texted you — your phone **notifies** you - A waiter doesn't keep asking "ready to order?" every second — you **signal** them - A fire alarm doesn't check every room — the **smoke triggers** it

This is the core idea: **react to things when they happen**, rather than constantly checking.

---

### What We'll Cover

| Section | Topic                     | Key Concept                         |
|---------|---------------------------|-------------------------------------|
| 1       | Callbacks                 | Functions that respond to events    |
| 2       | Building an Event System  | The Observer pattern in action      |
| 3       | The Event Loop            | The engine behind event-driven code |
| 4       | `asyncio` & `async/await` | Python's built-in async framework   |
| 5       | Real-World Patterns       | Putting it all together             |

---

### Prerequisites

- Functions (including `*args`, `**kwargs`)
- Classes and OOP basics
- Decorators (helpful, not required)

---

## Warm-Up: Synchronous vs Event-Driven Thinking

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

<details>
<summary>Click to reveal the problem!</summary>

**The waiter is BLOCKED!** While waiting for one order, they can't serve anyone else.

A real restaurant works event-driven:
1. Waiter takes Order A, sends to kitchen
2. Waiter takes Order B, sends to kitchen
3. Waiter takes Order C, sends to kitchen
4. **Kitchen signals**: "Order A ready!" -> Waiter delivers it
5. **Kitchen signals**: "Order C ready!" -> Waiter delivers it
6. **Kitchen signals**: "Order B ready!" -> Waiter delivers it

The waiter **reacts to events** (food being ready) instead of **blocking** on each order!

</details>

### Question 2: Which of these are event-driven?

- A) A `for` loop that processes every item in a list
- B) A button click handler on a web page
- C) Reading a file line by line
- D) A chat app that shows messages when they arrive
- E) A security camera that records when motion is detected

<details>
<summary>Click to reveal!</summary>

**B, D, and E** are event-driven!

- **B**: The code *waits* for a click event, then *reacts*
- **D**: Messages *arrive* as events, the UI *reacts* by displaying them
- **E**: Motion *triggers* an event, recording *reacts* to it

A and C are **sequential/synchronous** — they process things in a fixed order.

</details>

---

## 1. Callback Functions: The Building Block

---

A **callback** is a function you pass to another function, to be **called back** later when something happens.

```
You:     "Hey, when you're done cooking, CALL me BACK."
Kitchen: "Sure, I'll call your function when the event occurs."
```

This works because in Python, **functions are first-class objects** — you can pass them around like any other value.


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


### Key Insight

`download_file` doesn't know or care what `on_complete` does. It just **calls it back** when the work is done. This is **separation of concerns** — the downloader handles downloading, the callback handles what to do with the result.

### 1.2 Callbacks with Lambda Functions

For short callbacks, you can use **lambda** (anonymous functions):


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


### 1.3 Callbacks for Success AND Failure

Real-world operations can **succeed or fail**. A common pattern is to provide two callbacks:


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
    ERROR: User 42 not found in database
    
    Fetching user 42...
    Got user: Alice (role: admin)
    
    Fetching user 42...
    Got user: Alice (role: admin)
    
    Fetching user 42...
    Got user: Alice (role: admin)


### Try It Yourself: Callback Calculator

Complete the `calculate` function below. It should: 1. Perform the operation 2. Call `on_result` with the answer 3. Call `on_error` if something goes wrong (like division by zero)


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
```

<details>
<summary>Solution</summary>

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

Callbacks are great for simple cases, but they can get **ugly** when you chain many together:


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
# async/await (Section 4) solves this elegantly!
```

    Step 1: Authenticating...
    Step 2: Fetching data with auth_token_123...
    Step 3: Processing 2 users...
    Final result: done


---

## 2. Building an Event System (Observer Pattern)

---

A single callback is useful, but real applications have **many events** with **many listeners**. Let's build an **Event Emitter** — an object that:

1.  Lets you **register** callbacks for named events
2.  **Emits** events, calling all registered callbacks

This is the **Observer Pattern** in action.


```python
class EventEmitter:
    """A simple event system — register callbacks and emit events."""

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


### Try It Yourself: Chat Room Events

Build a `ChatRoom` class using `EventEmitter` that emits these events: - `"user_joined"` — when someone joins (pass the username) - `"message"` — when someone sends a message (pass username and text) - `"user_left"` — when someone leaves (pass the username)


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
```

<details>
<summary>Solution</summary>

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

We can make our event system even cleaner with decorators:


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
def handle_error(code, message):
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


---

## 3. The Event Loop: The Engine Behind It All

---

An **event loop** is a loop that: 1. Waits for events to occur 2. Dispatches them to the right handlers 3. Goes back to waiting

```
while running:
    event = wait_for_next_event()
    handler = find_handler(event)
    handler(event)
```

Every GUI app, web server, and game engine has one. Let's build a simple one!


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
                # No events, no timers — we're done
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


### How This Connects to `asyncio`

Our `SimpleEventLoop` above is a toy version of what Python's `asyncio` does under the hood:

| Our Event Loop                 | `asyncio`                  |
|--------------------------------|----------------------------|
| `loop.post(event)`             | Scheduling a coroutine     |
| `loop.register(type, handler)` | `async def` functions      |
| `loop.schedule(delay, ...)`    | `asyncio.sleep()` / timers |
| `loop.run()`                   | `asyncio.run()`            |
| Event queue                    | The asyncio task queue     |

Now let's see the real thing!

---

## 4. `asyncio` — Python's Async Framework

---

`asyncio` is Python's built-in library for writing **concurrent** code using `async/await` syntax.

### Key Vocabulary

| Term | What It Means | Analogy |
|----|----|----|
| **Coroutine** | A function that can pause and resume | A bookmark in a book |
| **`async def`** | Declares a coroutine function | "This function can pause" |
| **`await`** | Pauses until a result is ready | "I'll wait here, but others can go" |
| **Event Loop** | Manages and schedules coroutines | The restaurant manager |
| **Task** | A coroutine wrapped for concurrent execution | An order ticket |

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


### Important: `await` vs no `await`

A common mistake — what happens if you forget `await`?


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

    Without await: <coroutine object greet at 0x10a92cc10>
    Type: <class 'coroutine'>
    
    With await: Hello!
    Type: <class 'str'>


### 4.2 Running Tasks Concurrently with `asyncio.gather`

This is where async gets **powerful** — doing multiple things at once!


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


Notice the difference! - **Sequential**: ~6 seconds (2 + 2 + 2) - **Concurrent**: ~2 seconds (all 3 run at the same time!)

`asyncio.gather` starts all coroutines, and while one is "sleeping" (waiting for I/O), the others can run.

### 4.3 `asyncio.create_task` — Fire and Forget


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


### 4.4 Error Handling in Async Code


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


### 4.5 Timeouts — Don't Wait Forever


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


### Try It Yourself: Async Web Scraper Simulation

Complete the `fetch_page` coroutine and use `asyncio.gather` to fetch all pages concurrently.


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
```

<details>
<summary>Solution</summary>

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

### 4.6 Async Generators and `async for`

Just like regular generators yield values one at a time, **async generators** yield values with `await` in between:


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
      [TempSensor-A] Reading #1: 23.8C (OK)
      [TempSensor-A] Reading #2: 23.1C (OK)
      [TempSensor-A] Reading #3: 25.4C (OK)
      [TempSensor-A] Reading #4: 26.8C (OK)
      [TempSensor-A] Reading #5: 28.9C (HIGH)
    Done!


### 4.7 Async Context Managers

Just like `with open(...)` manages file resources, `async with` manages **async resources**:


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
        """Called when exiting 'async with' — even if there's an error!"""
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


# Use it with 'async with' — connection is automatically cleaned up!
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


---

## 5. Real-World Patterns: Putting It All Together

---

### 5.1 Pattern: Async Event Emitter

Combining our EventEmitter with asyncio for async handlers:


```python
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
            if asyncio.iscoroutinefunction(callback):
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


### 5.2 Pattern: Producer-Consumer with `asyncio.Queue`

A classic pattern where one coroutine produces data and another consumes it:


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
      [NEW ORDER] Pasta
      [Chef Alice] Burger READY! (took 1.1s)
      [Chef Alice] Cooking Pasta...
      [NEW ORDER] Salad
      [NEW ORDER] Soup
      [Chef Bob] Pizza READY! (took 1.4s)
      [Chef Bob] Cooking Salad...
      [Chef Alice] Pasta READY! (took 0.8s)
      [Chef Alice] Cooking Soup...
      [NEW ORDER] Steak
      [Chef Alice] Soup READY! (took 0.8s)
      [Chef Alice] Cooking Steak...
      [Chef Bob] Salad READY! (took 1.0s)
      [Chef Bob] No more orders, going home!
      [Chef Alice] Steak READY! (took 0.7s)
      [Chef Alice] No more orders, going home!
    
    Kitchen closed!


### 5.3 Pattern: Async Retry with Exponential Backoff

A practical pattern for handling flaky network calls:


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


---

## Quiz Time: Test Your Understanding

### Q1: What does this print?


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

<details>
<summary>Click to reveal!</summary>

```
1
3
4
2
5
```


**Why?**
- `a()` and `b()` start together, both print their first line (`1`, `3`)
- Both hit `await asyncio.sleep()` — they *pause* and yield control
- `b()` has a shorter sleep (0.5s), so it resumes first and prints `4`
- `a()` resumes after 1s and prints `2`
- `gather` finishes, so `5` prints last

</details>

### Q2: What's wrong with this code?


```python
async def get_data():
    await asyncio.sleep(1)
    return {"key": "value"}

data = get_data()
print(data["key"])
```

<details>
<summary>Click to reveal!</summary>

**Missing `await`!** `data = get_data()` returns a coroutine object, not the dict.

Fix: `data = await get_data()`

This is the #1 most common asyncio mistake.

</details>

### Q3: Which runs faster and why?


```python
# Option A
r1 = await fetch(url1)
r2 = await fetch(url2)
r3 = await fetch(url3)

# Option B
r1, r2, r3 = await asyncio.gather(fetch(url1), fetch(url2), fetch(url3))
```

<details>
<summary>Click to reveal!</summary>

**Option B is faster!**

- **Option A**: Sequential. Waits for each fetch to complete before starting the next. Total time = sum of all fetch times.
- **Option B**: Concurrent. All three fetches run at the same time. Total time = max of all fetch times.

If each fetch takes 1 second: A = 3s, B = 1s.

</details>

---

## Final Challenge: Async Task Pipeline

Build an async pipeline that processes "orders" through multiple stages. Each stage is a coroutine that transforms the order.

**Requirements:** 1. Create an `AsyncPipeline` class with `add_stage(name, handler)` and `process(item)` methods 2. Each stage's handler is an async function that takes an item and returns a transformed item 3. `process()` should run the item through all stages **sequentially** (output of one is input to next) 4. Add logging that shows each stage starting/finishing 5. Process multiple orders **concurrently** using `asyncio.gather`


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
```

<details>
<summary>Solution</summary>

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
        print(f"  [Order #{item['id']}] Pipeline complete!")
        return result


pipeline = AsyncPipeline()
pipeline.add_stage("Validate", validate_order)
pipeline.add_stage("Calculate Total", calculate_total)
pipeline.add_stage("Apply Discount", apply_discount)

results = await asyncio.gather(*[pipeline.process(order) for order in orders])

print("\n" + "="*50)
print("PROCESSED ORDERS")
print("="*50)
for order in results:
    print(f"  Order #{order['id']}: {order['item']} -> ${order['total']:.2f} (discount: ${order['discount']:.2f})")
```

</details>

---

## Summary & Cheat Sheet

### Callbacks


```python
# Pass a function to be called later
def do_work(on_done):
    result = heavy_computation()
    on_done(result)  # Call back!

do_work(lambda r: print(f"Got: {r}"))
```

### Event Emitter (Observer Pattern)


```python
emitter = EventEmitter()
emitter.on("event_name", handler_func)   # Subscribe
emitter.emit("event_name", data)          # Publish
emitter.off("event_name", handler_func)   # Unsubscribe
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

# Fire-and-forget task
task = asyncio.create_task(my_task())

# Timeout
result = await asyncio.wait_for(slow_task(), timeout=5.0)

# Producer-consumer
queue = asyncio.Queue()
await queue.put(item)
item = await queue.get()
```

### When to Use What

| Situation                       | Use                                  |
|---------------------------------|--------------------------------------|
| Simple "do X when Y happens"    | Callback function                    |
| Many listeners for named events | Event Emitter                        |
| I/O-bound concurrent operations | `asyncio` + `async/await`            |
| CPU-bound parallel processing   | `multiprocessing` (not covered here) |

### Key Takeaways

1.  **Callbacks** are functions passed to other functions to be called later
2.  **Event emitters** let you decouple *what happens* from *who cares about it*
3.  **`async/await`** makes async code read like synchronous code (no callback hell!)
4.  **`asyncio.gather`** is your go-to for running things concurrently
5.  Always **`await`** your coroutines — forgetting it is the #1 async bug

---

## Further Reading

- [Official asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)
- [Python Concurrency with asyncio (book)](https://www.manning.com/books/python-concurrency-with-asyncio)

---

*Next up: We'll see how these patterns are used in web frameworks (FastAPI, Django Channels) and real-time applications!*
