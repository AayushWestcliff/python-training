# Deep Dive: `asyncio` in Python

> *"Concurrency is not parallelism. Concurrency is about dealing with lots of things at once. Parallelism is about doing lots of things at once."*\
> — Rob Pike

---

This notebook is a **comprehensive, hands-on guide** to Python's `asyncio` library. We'll go from the fundamentals all the way to production patterns.

### What We'll Cover

| Section | Topic                                                       |
|---------|-------------------------------------------------------------|
| 1       | Why Async? — The I/O Problem                                |
| 2       | Coroutines & `await` — The Basics                           |
| 3       | Running Concurrently — `gather`, `create_task`, `TaskGroup` |
| 4       | Controlling Execution — Timeouts, Cancellation, Shielding   |
| 5       | Coordination — Queues, Locks, Semaphores, Events            |
| 6       | Async Iteration — `async for`, `async with`                 |
| 7       | Bridging Sync & Async — Running in Threads/Processes        |
| 8       | Real-World Project — Async Web Crawler                      |

### Prerequisites

- Functions, classes, exception handling
- Generators (`yield`) — helpful but not required
- Event-driven programming concepts (see the Event-Driven Programming notebook)

---

## Warm-Up Quiz: Concurrency Intuition

### Q1: You need to download 100 images from the internet. What's the bottleneck?

- A) Your CPU can't process the pixels fast enough
- B) Your program is **waiting** for each download to finish before starting the next
- C) Python is too slow

<details>
<summary>Click to reveal!</summary>

**B!** The CPU is mostly idle during downloads — it's just **waiting** for network data. This is an **I/O-bound** problem. `asyncio` is specifically designed for this.

</details>

### Q2: What's the difference between concurrency and parallelism?

<details>
<summary>Click to reveal!</summary>

**Concurrency**: One cook switching between multiple dishes (interleaving tasks)  
**Parallelism**: Multiple cooks each working on their own dish (simultaneous execution)

`asyncio` gives you **concurrency** on a single thread. For true parallelism, you need `multiprocessing`.

| | Concurrency | Parallelism |
|---|---|---|
| Threads | 1 (in asyncio) | Multiple |
| Best for | I/O-bound (network, disk) | CPU-bound (math, processing) |
| Python tool | `asyncio` | `multiprocessing` |

</details>

### Q3: How long does this take?


```python
import time
time.sleep(1)  # Wait 1 second
time.sleep(1)  # Wait 1 second
time.sleep(1)  # Wait 1 second
```

<details>
<summary>Click to reveal!</summary>

**3 seconds.** `time.sleep` is **blocking** — the entire program halts at each call.

With `asyncio`, we can do this in **1 second**:

```python
await asyncio.gather(
    asyncio.sleep(1),
    asyncio.sleep(1),
    asyncio.sleep(1),
)
```

All three sleeps run concurrently!

</details>

---

## 1. Why Async? — The I/O Problem

---

Let's see the problem with synchronous I/O firsthand.


```python
import time

def fetch_data_sync(source, delay):
    """Simulates a synchronous network call."""
    print(f"  [{source}] Requesting...")
    time.sleep(delay)  # BLOCKS the entire program!
    print(f"  [{source}] Done ({delay}s)")
    return f"{source}_data"


print("=== Synchronous (blocking) ===")
start = time.time()

r1 = fetch_data_sync("Database", 1.0)
r2 = fetch_data_sync("API", 1.5)
r3 = fetch_data_sync("Cache", 0.5)

elapsed = time.time() - start
print(f"\nResults: {[r1, r2, r3]}")
print(f"Total time: {elapsed:.1f}s (1.0 + 1.5 + 0.5 = 3.0s expected)")
```

    === Synchronous (blocking) ===
      [Database] Requesting...
      [Database] Done (1.0s)
      [API] Requesting...
      [API] Done (1.5s)
      [Cache] Requesting...
      [Cache] Done (0.5s)
    
    Results: ['Database_data', 'API_data', 'Cache_data']
    Total time: 3.0s (1.0 + 1.5 + 0.5 = 3.0s expected)



```python
import asyncio

async def fetch_data_async(source, delay):
    """Simulates an async network call."""
    print(f"  [{source}] Requesting...")
    await asyncio.sleep(delay)  # Non-blocking! Other tasks can run.
    print(f"  [{source}] Done ({delay}s)")
    return f"{source}_data"


print("=== Asynchronous (non-blocking) ===")
start = time.time()

r1, r2, r3 = await asyncio.gather(
    fetch_data_async("Database", 1.0),
    fetch_data_async("API", 1.5),
    fetch_data_async("Cache", 0.5),
)

elapsed = time.time() - start
print(f"\nResults: {[r1, r2, r3]}")
print(f"Total time: {elapsed:.1f}s (max of 1.0, 1.5, 0.5 = 1.5s expected)")
```

    === Asynchronous (non-blocking) ===
      [Database] Requesting...
      [API] Requesting...
      [Cache] Requesting...
      [Cache] Done (0.5s)
      [Database] Done (1.0s)
      [API] Done (1.5s)
    
    Results: ['Database_data', 'API_data', 'Cache_data']
    Total time: 1.5s (max of 1.0, 1.5, 0.5 = 1.5s expected)


**3.0s vs 1.5s** — async cut the time in half because all three operations ran concurrently!

### How It Works Under the Hood

```
Synchronous:             Asynchronous:

t=0  [DB starts]         t=0  [DB starts] [API starts] [Cache starts]
t=1  [DB done]           t=0.5            [Cache done]
     [API starts]        t=1  [DB done]
t=2.5 [API done]         t=1.5 [API done]
      [Cache starts]     
t=3   [Cache done]       Total: 1.5s

Total: 3.0s
```

The event loop **interleaves** the waiting — while one coroutine is waiting for I/O, the others get to run.

---

## 2. Coroutines & `await` — The Basics

---

### 2.1 Anatomy of a Coroutine


```python
# A coroutine function is defined with 'async def'
async def my_coroutine():
    print("Coroutine started")
    await asyncio.sleep(0.5)    # Yield control to the event loop
    print("Coroutine resumed")
    return 42


# Calling it returns a coroutine OBJECT — it does NOT execute yet!
coro = my_coroutine()
print(f"Type: {type(coro)}")
print(f"It hasn't printed anything yet!")

# 'await' actually executes it
result = await coro
print(f"Result: {result}")
```

    Type: <class 'coroutine'>
    It hasn't printed anything yet!
    Coroutine started
    Coroutine resumed
    Result: 42


### 2.2 What Can You `await`?

You can only `await` **awaitable** objects. There are three kinds:


```python
# 1. Coroutines (from 'async def')
async def get_value():
    return "from coroutine"

result1 = await get_value()
print(f"1. Coroutine: {result1}")


# 2. Tasks (scheduled coroutines)
async def delayed_value():
    await asyncio.sleep(0.1)
    return "from task"

task = asyncio.create_task(delayed_value())
result2 = await task
print(f"2. Task: {result2}")


# 3. Futures (low-level, rarely used directly)
loop = asyncio.get_event_loop()
future = loop.create_future()
future.set_result("from future")
result3 = await future
print(f"3. Future: {result3}")


# NOT awaitable (this would raise TypeError):
# await 42
# await "hello"
# await [1, 2, 3]
```

    1. Coroutine: from coroutine
    2. Task: from task
    3. Future: from future


### 2.3 The Golden Rule of `await`

Every `await` is a **checkpoint** where the event loop can switch to another task.

**No `await` = no switching = no concurrency.**


```python
async def cooperative():
    """Good: yields control regularly."""
    for i in range(3):
        print(f"  Cooperative: step {i}")
        await asyncio.sleep(0)  # Yield control, even with 0 delay!


async def greedy():
    """Bad: hogs the event loop with CPU-bound work."""
    total = 0
    for i in range(3):
        print(f"  Greedy: step {i}")
        # No await here! Other tasks are BLOCKED until this finishes.
        for _ in range(1_000_000):  # CPU-bound work
            total += 1
    return total


async def other_task():
    print("  Other: I want to run!")
    await asyncio.sleep(0)
    print("  Other: I finally ran!")


# With the cooperative coroutine, other_task gets interleaved
print("=== Cooperative ===")
await asyncio.gather(cooperative(), other_task())

print("\n=== Greedy ===")
await asyncio.gather(greedy(), other_task())
# Notice: other_task only runs AFTER greedy finishes!
```

    === Cooperative ===
      Cooperative: step 0
      Other: I want to run!
      Cooperative: step 1
      Other: I finally ran!
      Cooperative: step 2
    
    === Greedy ===
      Greedy: step 0
      Greedy: step 1
      Greedy: step 2
      Other: I want to run!
      Other: I finally ran!
    
    
    
    
    
    [3000000, None]


### Key Takeaway

`asyncio` uses **cooperative multitasking** — tasks must voluntarily yield control via `await`. A single long-running block of synchronous code will freeze everything. For CPU-heavy work inside async code, use `asyncio.to_thread()` (covered in Section 7).

### 2.4 `asyncio.run()` — The Entry Point

In Jupyter, we can `await` at the top level. In a normal `.py` script, you need `asyncio.run()`:


```python
# This is how you'd write it in a .py file:

script_code = '''
import asyncio

async def main():
    print("Hello from async!")
    await asyncio.sleep(1)
    print("Done!")

# This creates the event loop, runs main(), and cleans up
asyncio.run(main())
'''

print("In a .py script, you use asyncio.run():")
print(script_code)

# In Jupyter, asyncio.run() won't work because a loop is already running.
# Instead, just use 'await' directly:
async def main():
    print("Hello from async!")
    await asyncio.sleep(0.5)
    print("Done!")

await main()
```

    In a .py script, you use asyncio.run():
    
    import asyncio
    
    async def main():
        print("Hello from async!")
        await asyncio.sleep(1)
        print("Done!")
    
    # This creates the event loop, runs main(), and cleans up
    asyncio.run(main())
    
    Hello from async!
    Done!


### Try It Yourself: Async Timer

Write a coroutine `countdown(name, seconds)` that counts down from `seconds` to 0, printing each second. Then run **two countdowns concurrently**.


```python
async def countdown(name, seconds):
    """Count down from 'seconds' to 0, printing each second."""
    # YOUR CODE HERE
    pass


# Run two countdowns concurrently
# YOUR CODE: use asyncio.gather to run countdown("A", 5) and countdown("B", 3)
```

<details>
<summary>Solution</summary>

```python
async def countdown(name, seconds):
    for i in range(seconds, 0, -1):
        print(f"  [{name}] {i}...")
        await asyncio.sleep(1)
    print(f"  [{name}] DONE!")

await asyncio.gather(countdown("A", 5), countdown("B", 3))
```


Notice how both countdowns print interleaved — they truly run concurrently!

</details>

---

## 3. Running Concurrently — `gather`, `create_task`, `TaskGroup`

---

### 3.1 `asyncio.gather` — Run Multiple and Collect Results


```python
async def fetch(name, delay):
    await asyncio.sleep(delay)
    return f"{name} (took {delay}s)"


# gather returns results in the SAME ORDER as the arguments
results = await asyncio.gather(
    fetch("Alpha", 2),
    fetch("Beta", 0.5),
    fetch("Gamma", 1),
)

# Even though Beta finishes first, results are ordered Alpha, Beta, Gamma
for i, r in enumerate(results):
    print(f"  Result {i}: {r}")
```

      Result 0: Alpha (took 2s)
      Result 1: Beta (took 0.5s)
      Result 2: Gamma (took 1s)


### 3.2 Error Handling with `gather`


```python
async def might_fail(name, fail=False):
    await asyncio.sleep(0.3)
    if fail:
        raise ValueError(f"{name} failed!")
    return f"{name} ok"


# Default: one failure crashes ALL tasks
print("=== Default (crash on first error) ===")
try:
    results = await asyncio.gather(
        might_fail("A"),
        might_fail("B", fail=True),
        might_fail("C"),
    )
except ValueError as e:
    print(f"  Caught: {e}")
    print("  All results lost!")


# With return_exceptions=True: failures become return values
print("\n=== return_exceptions=True (resilient) ===")
results = await asyncio.gather(
    might_fail("A"),
    might_fail("B", fail=True),
    might_fail("C"),
    return_exceptions=True,
)

for r in results:
    if isinstance(r, Exception):
        print(f"  FAILED: {r}")
    else:
        print(f"  OK: {r}")
```

    === Default (crash on first error) ===
      Caught: B failed!
      All results lost!
    
    === return_exceptions=True (resilient) ===
      OK: A ok
      FAILED: B failed!
      OK: C ok


### 3.3 `asyncio.create_task` — Schedule and Continue


```python
async def slow_upload(filename):
    print(f"  Uploading {filename}...")
    await asyncio.sleep(2)
    print(f"  Upload complete: {filename}")
    return f"{filename} uploaded"


async def main():
    # create_task schedules the coroutine to run in the BACKGROUND
    task = asyncio.create_task(slow_upload("photo.jpg"))

    # We can do other work while it runs!
    print("  Doing other work...")
    await asyncio.sleep(1)
    print("  Still doing work...")

    # When we need the result, we await the task
    result = await task
    print(f"  Result: {result}")

    # We can also check state without awaiting
    task2 = asyncio.create_task(slow_upload("video.mp4"))
    await asyncio.sleep(0.5)
    print(f"  Is task2 done? {task2.done()}")
    await task2
    print(f"  Is task2 done? {task2.done()}")


await main()
```

      Doing other work...
      Uploading photo.jpg...
      Still doing work...
      Upload complete: photo.jpg
      Result: photo.jpg uploaded
      Uploading video.mp4...
      Is task2 done? False
      Upload complete: video.mp4
      Is task2 done? True


### 3.4 `asyncio.TaskGroup` — Structured Concurrency (Python 3.11+)

`TaskGroup` is the modern way to manage groups of tasks. It ensures **all tasks complete or all are cancelled on error**.


```python
import sys

async def process_item(item, delay):
    await asyncio.sleep(delay)
    return f"{item}: processed"


if sys.version_info >= (3, 11):
    # TaskGroup is available in Python 3.11+
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(process_item("A", 1))
        task2 = tg.create_task(process_item("B", 0.5))
        task3 = tg.create_task(process_item("C", 1.5))

    # All tasks guaranteed to be done here
    print(f"  {task1.result()}")
    print(f"  {task2.result()}")
    print(f"  {task3.result()}")
else:
    # Fallback for Python 3.10 and below
    print(f"  Python {sys.version_info.major}.{sys.version_info.minor} detected.")
    print("  TaskGroup requires Python 3.11+. Using gather instead:")
    results = await asyncio.gather(
        process_item("A", 1),
        process_item("B", 0.5),
        process_item("C", 1.5),
    )
    for r in results:
        print(f"  {r}")
```

      Python 3.10 detected.
      TaskGroup requires Python 3.11+. Using gather instead:
      A: processed
      B: processed
      C: processed


### `gather` vs `create_task` vs `TaskGroup`

| Feature | `gather` | `create_task` | `TaskGroup` (3.11+) |
|----|----|----|----|
| Returns results | Yes, in order | Must `await` individually | Via `.result()` |
| Error handling | `return_exceptions` | Manual try/except | Auto-cancels all on error |
| Cancellation | Manual | Manual | Automatic |
| Use when | You want all results together | Fire-and-forget or check later | You need cleanup guarantees |

### 3.5 `asyncio.as_completed` — Process Results As They Arrive


```python
import random

async def api_call(endpoint):
    delay = random.uniform(0.5, 2.5)
    await asyncio.sleep(delay)
    return {"endpoint": endpoint, "latency": round(delay, 2)}


endpoints = ["/users", "/products", "/orders", "/reviews", "/stats"]

# gather waits for ALL to complete, then gives you results
# as_completed gives you results ONE AT A TIME as they finish!

print("Results arriving as they complete:")
coros = [api_call(ep) for ep in endpoints]

for i, coro in enumerate(asyncio.as_completed(coros)):
    result = await coro
    print(f"  #{i+1} finished: {result['endpoint']} ({result['latency']}s)")
```

    Results arriving as they complete:
      #1 finished: /stats (0.61s)
      #2 finished: /reviews (0.79s)
      #3 finished: /users (1.17s)
      #4 finished: /orders (1.6s)
      #5 finished: /products (2.14s)


### Try It Yourself: Parallel Data Fetcher

Write an async function that fetches data from multiple "servers" concurrently and returns only the **successful** results. Use `gather` with `return_exceptions=True`.


```python
async def query_server(server_id):
    """Simulates querying a server. Some servers will fail."""
    delay = random.uniform(0.2, 1.0)
    await asyncio.sleep(delay)
    if random.random() < 0.3:  # 30% failure rate
        raise ConnectionError(f"Server {server_id} is down")
    return {"server": server_id, "data": f"response_{server_id}", "latency": round(delay, 2)}


async def fetch_all(server_ids):
    """
    Query all servers concurrently.
    Return a tuple: (successes, failures)
    - successes: list of result dicts
    - failures: list of error strings
    """
    # YOUR CODE HERE
    pass


# Test it
# successes, failures = await fetch_all(range(1, 11))
# print(f"Successes: {len(successes)}")
# for s in successes:
#     print(f"  Server {s['server']}: {s['data']} ({s['latency']}s)")
# print(f"\nFailures: {len(failures)}")
# for f in failures:
#     print(f"  {f}")
```

<details>
<summary>Solution</summary>

```python
async def fetch_all(server_ids):
    results = await asyncio.gather(
        *[query_server(sid) for sid in server_ids],
        return_exceptions=True,
    )
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [str(r) for r in results if isinstance(r, Exception)]
    return successes, failures


successes, failures = await fetch_all(range(1, 11))
print(f"Successes: {len(successes)}")
for s in successes:
    print(f"  Server {s['server']}: {s['data']} ({s['latency']}s)")
print(f"\nFailures: {len(failures)}")
for f in failures:
    print(f"  {f}")
```

</details>

---

## 4. Controlling Execution — Timeouts, Cancellation, Shielding

---

### 4.1 Timeouts with `asyncio.wait_for`


```python
async def slow_query():
    print("  Query started...")
    await asyncio.sleep(5)  # Takes 5 seconds
    return "query result"


# Set a 2-second timeout
print("=== wait_for timeout ===")
try:
    result = await asyncio.wait_for(slow_query(), timeout=2.0)
    print(f"  Result: {result}")
except asyncio.TimeoutError:
    print("  Timed out! Query took too long.")
    print("  The coroutine was automatically CANCELLED.")
```

    === wait_for timeout ===
      Query started...
      Timed out! Query took too long.
      The coroutine was automatically CANCELLED.


### 4.2 Task Cancellation


```python
async def long_running_job():
    try:
        print("  Job: Starting...")
        for i in range(10):
            print(f"  Job: Step {i+1}/10")
            await asyncio.sleep(0.5)
        print("  Job: Completed!")  # This won't print
    except asyncio.CancelledError:
        # This is where you do cleanup!
        print("  Job: CANCELLED! Cleaning up resources...")
        raise  # Re-raise to properly cancel


async def supervisor():
    task = asyncio.create_task(long_running_job())

    # Let it run for 1.5 seconds, then cancel
    await asyncio.sleep(1.5)
    print("  Supervisor: Cancelling the job!")
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print("  Supervisor: Job was successfully cancelled.")


await supervisor()
```

      Job: Starting...
      Job: Step 1/10
      Job: Step 2/10
      Job: Step 3/10
      Supervisor: Cancelling the job!
      Job: CANCELLED! Cleaning up resources...
      Supervisor: Job was successfully cancelled.


### 4.3 Shielding Tasks from Cancellation

Sometimes a task **must not be cancelled** (e.g., saving data to a database):


```python
async def critical_save(data):
    """This MUST complete even if the parent is cancelled."""
    print(f"  Saving '{data}' to database...")
    await asyncio.sleep(1)
    print(f"  Save complete!")
    return True


async def process_with_save():
    print("  Processing...")
    await asyncio.sleep(0.5)

    # Shield protects the inner coroutine from cancellation
    try:
        result = await asyncio.shield(critical_save("important_data"))
        print(f"  Save result: {result}")
    except asyncio.CancelledError:
        print("  Process was cancelled, but save continues in background!")
        raise


task = asyncio.create_task(process_with_save())
await asyncio.sleep(0.8)  # Let it start the save
task.cancel()

try:
    await task
except asyncio.CancelledError:
    pass

# Give the shielded save time to complete
await asyncio.sleep(1.5)
print("  All done.")
```

      Processing...
      Saving 'important_data' to database...
      Process was cancelled, but save continues in background!
      Save complete!
      All done.


### 4.4 `asyncio.wait` — Fine-Grained Control

`wait` gives you more control than `gather`: you can wait for the **first** task to complete, **first** to fail, or **all**.


```python
async def racer(name, speed):
    await asyncio.sleep(speed)
    return f"{name} finished in {speed}s!"


tasks = [
    asyncio.create_task(racer("Alice", 2.0)),
    asyncio.create_task(racer("Bob", 1.0)),
    asyncio.create_task(racer("Charlie", 1.5)),
]

# FIRST_COMPLETED: returns as soon as ONE task finishes
done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

print("First to finish:")
for task in done:
    print(f"  {task.result()}")

print(f"\nStill running: {len(pending)} tasks")

# Clean up: wait for the rest
remaining_done, _ = await asyncio.wait(pending)
print("\nRemaining results:")
for task in remaining_done:
    print(f"  {task.result()}")
```

    First to finish:
      Bob finished in 1.0s!
    
    Still running: 2 tasks
    
    Remaining results:
      Alice finished in 2.0s!
      Charlie finished in 1.5s!


---

## 5. Coordination — Queues, Locks, Semaphores, Events

---

When coroutines share data or resources, you need coordination primitives.

### 5.1 `asyncio.Queue` — Producer/Consumer


```python
async def producer(queue, n_items):
    for i in range(n_items):
        item = f"item-{i}"
        await asyncio.sleep(random.uniform(0.1, 0.5))
        await queue.put(item)
        print(f"  [Producer] Put: {item} (queue size: {queue.qsize()})")


async def consumer(queue, name):
    while True:
        item = await queue.get()  # Blocks until an item is available
        if item is None:  # Poison pill = stop signal
            print(f"  [{name}] Received stop signal. Shutting down.")
            break

        # Process the item
        process_time = random.uniform(0.2, 0.8)
        print(f"  [{name}] Processing: {item}...")
        await asyncio.sleep(process_time)
        print(f"  [{name}] Done: {item} ({process_time:.1f}s)")
        queue.task_done()


# Bounded queue: maxsize prevents producer from getting too far ahead
queue = asyncio.Queue(maxsize=3)

# Start 1 producer and 2 consumers
prod = asyncio.create_task(producer(queue, 6))
cons1 = asyncio.create_task(consumer(queue, "Worker-A"))
cons2 = asyncio.create_task(consumer(queue, "Worker-B"))

# Wait for producer to finish
await prod

# Wait for all items to be processed
await queue.join()

# Send stop signals
await queue.put(None)
await queue.put(None)
await asyncio.gather(cons1, cons2)

print("\nAll work complete!")
```

      [Producer] Put: item-0 (queue size: 1)
      [Worker-A] Processing: item-0...
      [Worker-A] Done: item-0 (0.2s)
      [Producer] Put: item-1 (queue size: 1)
      [Worker-B] Processing: item-1...
      [Worker-B] Done: item-1 (0.4s)
      [Producer] Put: item-2 (queue size: 1)
      [Worker-A] Processing: item-2...
      [Producer] Put: item-3 (queue size: 1)
      [Worker-B] Processing: item-3...
      [Worker-A] Done: item-2 (0.7s)
      [Producer] Put: item-4 (queue size: 1)
      [Worker-A] Processing: item-4...
      [Producer] Put: item-5 (queue size: 1)
      [Worker-B] Done: item-3 (0.8s)
      [Worker-B] Processing: item-5...
      [Worker-A] Done: item-4 (0.4s)
      [Worker-B] Done: item-5 (0.5s)
      [Worker-A] Received stop signal. Shutting down.
      [Worker-B] Received stop signal. Shutting down.
    
    All work complete!


### 5.2 `asyncio.Lock` — Mutual Exclusion


```python
# Shared counter WITHOUT a lock — race condition!
counter_no_lock = 0

async def increment_unsafe(n):
    global counter_no_lock
    for _ in range(n):
        temp = counter_no_lock
        await asyncio.sleep(0)  # Context switch point!
        counter_no_lock = temp + 1


counter_no_lock = 0
await asyncio.gather(
    increment_unsafe(100),
    increment_unsafe(100),
)
print(f"Without lock: counter = {counter_no_lock} (expected 200)")


# Shared counter WITH a lock — safe!
counter_with_lock = 0
lock = asyncio.Lock()

async def increment_safe(n):
    global counter_with_lock
    for _ in range(n):
        async with lock:  # Only one coroutine can enter at a time
            temp = counter_with_lock
            await asyncio.sleep(0)
            counter_with_lock = temp + 1


counter_with_lock = 0
await asyncio.gather(
    increment_safe(100),
    increment_safe(100),
)
print(f"With lock:    counter = {counter_with_lock} (expected 200)")
```

    Without lock: counter = 100 (expected 200)
    With lock:    counter = 200 (expected 200)


### 5.3 `asyncio.Semaphore` — Rate Limiting

A semaphore limits **how many** coroutines can access a resource simultaneously. Perfect for rate limiting API calls.


```python
async def call_api(endpoint, semaphore):
    async with semaphore:  # Blocks if too many concurrent calls
        print(f"  Calling {endpoint}...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        print(f"  Done: {endpoint}")
        return f"{endpoint}: ok"


# Allow at most 3 concurrent API calls
sem = asyncio.Semaphore(3)

endpoints = [f"/api/item/{i}" for i in range(8)]

print("Processing 8 endpoints with max 3 concurrent:\n")
start = time.time()
results = await asyncio.gather(*[call_api(ep, sem) for ep in endpoints])
print(f"\nAll done in {time.time() - start:.1f}s")
print(f"Results: {results}")
```

    Processing 8 endpoints with max 3 concurrent:
    
      Calling /api/item/0...
      Calling /api/item/1...
      Calling /api/item/2...
      Done: /api/item/1
      Calling /api/item/3...
      Done: /api/item/2
      Calling /api/item/4...
      Done: /api/item/3
      Calling /api/item/5...
      Done: /api/item/0
      Calling /api/item/6...
      Done: /api/item/6
      Calling /api/item/7...
      Done: /api/item/4
      Done: /api/item/5
      Done: /api/item/7
    
    All done in 2.8s
    Results: ['/api/item/0: ok', '/api/item/1: ok', '/api/item/2: ok', '/api/item/3: ok', '/api/item/4: ok', '/api/item/5: ok', '/api/item/6: ok', '/api/item/7: ok']


### 5.4 `asyncio.Event` — Signal Between Coroutines


```python
async def waiter(event, name):
    print(f"  [{name}] Waiting for the signal...")
    await event.wait()  # Blocks until the event is set
    print(f"  [{name}] Got the signal! Proceeding.")


async def trigger(event):
    print("  [Trigger] Preparing... (3 seconds)")
    await asyncio.sleep(1)
    print("  [Trigger] Setting the event!")
    event.set()  # All waiters are released simultaneously!


event = asyncio.Event()

# Three coroutines wait, one triggers
await asyncio.gather(
    waiter(event, "Worker-A"),
    waiter(event, "Worker-B"),
    waiter(event, "Worker-C"),
    trigger(event),
)
```

      [Worker-A] Waiting for the signal...
      [Worker-B] Waiting for the signal...
      [Worker-C] Waiting for the signal...
      [Trigger] Preparing... (3 seconds)
      [Trigger] Setting the event!
      [Worker-A] Got the signal! Proceeding.
      [Worker-B] Got the signal! Proceeding.
      [Worker-C] Got the signal! Proceeding.
    
    
    
    
    
    [None, None, None, None]


### Try It Yourself: Rate-Limited Downloader

Build a function that downloads 20 "files" concurrently, but never more than **5 at a time**. Track the total download time and compare it to what it would be sequentially.


```python
async def download_file(file_id, semaphore):
    """Simulate downloading a file. Takes 0.5 - 1.5 seconds."""
    # YOUR CODE HERE:
    # 1. Acquire the semaphore
    # 2. Print that you're starting the download
    # 3. Sleep for a random time
    # 4. Return the file_id and download time
    pass


# YOUR CODE: create a semaphore, download 20 files, print stats
# Hint: Track total time, count successes, calculate average latency
```

<details>
<summary>Solution</summary>

```python
async def download_file(file_id, semaphore):
    async with semaphore:
        delay = random.uniform(0.5, 1.5)
        print(f"  Downloading file {file_id}...")
        await asyncio.sleep(delay)
        return {"file": file_id, "time": round(delay, 2)}


sem = asyncio.Semaphore(5)
start = time.time()

results = await asyncio.gather(
    *[download_file(i, sem) for i in range(20)]
)

total = time.time() - start
seq_estimate = sum(r["time"] for r in results)

print(f"\n{'='*40}")
print(f"Downloaded {len(results)} files")
print(f"Concurrent time: {total:.1f}s")
print(f"Sequential would be: ~{seq_estimate:.1f}s")
print(f"Speedup: {seq_estimate/total:.1f}x")
```

</details>

---

## 6. Async Iteration — `async for` and `async with`

---

### 6.1 Async Generators


```python
async def event_stream(source, count=5):
    """Simulates a stream of events arriving over time."""
    for i in range(count):
        await asyncio.sleep(random.uniform(0.2, 0.8))
        event = {
            "source": source,
            "id": i,
            "value": random.randint(1, 100),
        }
        yield event  # 'yield' in an 'async def' = async generator


# Consume with 'async for'
print("Receiving events:")
async for event in event_stream("sensor-1", count=5):
    print(f"  Event #{event['id']}: value={event['value']}")
```

    Receiving events:
      Event #0: value=39
      Event #1: value=4
      Event #2: value=88
      Event #3: value=75
      Event #4: value=45


### 6.2 Async Comprehensions


```python
async def get_price(item):
    await asyncio.sleep(0.1)
    prices = {"apple": 1.50, "banana": 0.75, "cherry": 3.00, "date": 5.50}
    return prices.get(item, 0)


# Async list comprehension (awaits inside the comprehension!)
items = ["apple", "banana", "cherry", "date"]
prices = [await get_price(item) for item in items]
print(f"Prices: {dict(zip(items, prices))}")


# Async generator comprehension with 'async for'
async def number_stream(n):
    for i in range(n):
        await asyncio.sleep(0.05)
        yield i

# Filter even numbers from the async stream
evens = [x async for x in number_stream(10) if x % 2 == 0]
print(f"Even numbers: {evens}")
```

    Prices: {'apple': 1.5, 'banana': 0.75, 'cherry': 3.0, 'date': 5.5}
    Even numbers: [0, 2, 4, 6, 8]


### 6.3 Async Context Managers (`async with`)

Use `async with` when setup or teardown involves async operations.


```python
from contextlib import asynccontextmanager


# Method 1: Class-based (implement __aenter__ and __aexit__)
class AsyncTimer:
    """Times an async block."""
    def __init__(self, label):
        self.label = label

    async def __aenter__(self):
        self.start = time.time()
        print(f"  [{self.label}] Timer started")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start
        print(f"  [{self.label}] Timer stopped: {elapsed:.2f}s")


async with AsyncTimer("fetch") as timer:
    await asyncio.sleep(0.7)
    print("  Doing work...")


# Method 2: Decorator-based (simpler for most cases)
@asynccontextmanager
async def managed_connection(db_name):
    print(f"  Connecting to {db_name}...")
    await asyncio.sleep(0.3)
    conn = {"db": db_name, "status": "connected"}
    try:
        yield conn  # Hand the connection to the caller
    finally:
        print(f"  Disconnecting from {db_name}...")
        await asyncio.sleep(0.1)
        print(f"  Disconnected.")


print()
async with managed_connection("mydb") as conn:
    print(f"  Using connection: {conn}")
```

      [fetch] Timer started
      Doing work...
      [fetch] Timer stopped: 0.70s
    
      Connecting to mydb...
      Using connection: {'db': 'mydb', 'status': 'connected'}
      Disconnecting from mydb...
      Disconnected.


---

## 7. Bridging Sync & Async — Threads and Processes

---

Sometimes you need to call **blocking** code from async code, or **async** code from sync code.

### 7.1 `asyncio.to_thread` — Run Blocking Code Without Freezing the Loop


```python
import hashlib


def cpu_heavy_work(data):
    """Simulates CPU-bound work (blocking!)."""
    result = data
    for _ in range(100_000):
        result = hashlib.sha256(result.encode()).hexdigest()
    return result[:16]


def blocking_io():
    """Simulates blocking I/O (like a non-async database driver)."""
    time.sleep(1)
    return "data from blocking call"


# BAD: calling blocking functions directly freezes the event loop
# GOOD: run them in a thread with to_thread()

print("Running blocking + async work concurrently:")
start = time.time()

results = await asyncio.gather(
    asyncio.to_thread(cpu_heavy_work, "hello"),     # Runs in a thread
    asyncio.to_thread(blocking_io),                  # Runs in a thread
    asyncio.sleep(1),                                # Runs in the event loop
)

print(f"\nHash result: {results[0]}")
print(f"IO result: {results[1]}")
print(f"Total time: {time.time() - start:.1f}s (all ran concurrently!)")
```

    Running blocking + async work concurrently:
    
    Hash result: 3b2d9ab4b38fe0bc
    IO result: data from blocking call
    Total time: 1.0s (all ran concurrently!)


### 7.2 `loop.run_in_executor` — Thread Pool or Process Pool


```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


def compute(n):
    """A CPU-bound function."""
    return sum(i * i for i in range(n))


# Using a custom thread pool
loop = asyncio.get_event_loop()

with ThreadPoolExecutor(max_workers=4) as pool:
    results = await asyncio.gather(
        loop.run_in_executor(pool, compute, 1_000_000),
        loop.run_in_executor(pool, compute, 2_000_000),
        loop.run_in_executor(pool, compute, 3_000_000),
    )

for i, r in enumerate(results):
    print(f"  Result {i}: {r:,.0f}")
```

      Result 0: 333,332,833,333,500,032
      Result 1: 2,666,664,666,666,999,808
      Result 2: 8,999,995,500,000,499,712


### When to Use What

| Situation | Solution |
|----|----|
| Blocking I/O (file read, non-async DB) | `asyncio.to_thread()` or `ThreadPoolExecutor` |
| CPU-bound computation | `ProcessPoolExecutor` or `multiprocessing` |
| Async-native I/O (aiohttp, asyncpg) | Just `await` directly |
| Calling async from sync code | `asyncio.run()` |

---

## 8. Real-World Project: Async Web Crawler

---

Let's put everything together! We'll build a simulated web crawler that: 1. Starts from a list of seed URLs 2. Fetches pages concurrently (rate limited) 3. Extracts links from each page 4. Uses a queue to manage the crawl frontier 5. Respects a max depth and max pages limit


```python
import asyncio
import random
import time


# Simulated web: maps URLs to their "content" and outgoing links
FAKE_WEB = {
    "/": ["/about", "/products", "/blog"],
    "/about": ["/about/team", "/about/history", "/"],
    "/products": ["/products/1", "/products/2", "/products/3"],
    "/blog": ["/blog/post-1", "/blog/post-2", "/"],
    "/about/team": ["/about"],
    "/about/history": ["/about", "/"],
    "/products/1": ["/products", "/"],
    "/products/2": ["/products", "/products/1"],
    "/products/3": ["/products"],
    "/blog/post-1": ["/blog", "/blog/post-2"],
    "/blog/post-2": ["/blog", "/"],
}


async def fetch_page(url, semaphore):
    """Simulate fetching a web page."""
    async with semaphore:
        delay = random.uniform(0.1, 0.5)
        await asyncio.sleep(delay)

        if random.random() < 0.1:  # 10% chance of failure
            raise ConnectionError(f"Failed to fetch {url}")

        links = FAKE_WEB.get(url, [])
        size = random.randint(500, 5000)
        return {"url": url, "links": links, "size": size, "latency": round(delay, 3)}


async def crawl(seeds, max_pages=15, max_concurrent=3):
    """Crawl starting from seed URLs."""
    visited = set()
    results = []
    queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(max_concurrent)

    # Seed the queue
    for url in seeds:
        await queue.put(url)

    async def worker(worker_id):
        while len(visited) < max_pages:
            try:
                url = queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
                continue

            if url in visited:
                continue

            visited.add(url)

            try:
                page = await fetch_page(url, semaphore)
                results.append(page)
                print(f"  [W{worker_id}] Crawled {url} "
                      f"({page['size']}B, {page['latency']}s, "
                      f"{len(page['links'])} links)")

                # Add discovered links to the queue
                for link in page["links"]:
                    if link not in visited:
                        await queue.put(link)
            except ConnectionError as e:
                print(f"  [W{worker_id}] ERROR: {e}")

    # Run workers concurrently
    workers = [asyncio.create_task(worker(i)) for i in range(max_concurrent)]

    # Wait until enough pages crawled or workers finish
    while len(visited) < max_pages and not queue.empty():
        await asyncio.sleep(0.1)

    # Give workers a moment to finish current pages
    await asyncio.sleep(1)

    # Cancel remaining workers
    for w in workers:
        w.cancel()

    return results


# Run the crawler!
print("Starting web crawler...\n")
start = time.time()

pages = await crawl(["/"], max_pages=11, max_concurrent=3)

elapsed = time.time() - start
total_bytes = sum(p["size"] for p in pages)
avg_latency = sum(p["latency"] for p in pages) / len(pages) if pages else 0

print(f"\n{'='*50}")
print(f"CRAWL REPORT")
print(f"{'='*50}")
print(f"  Pages crawled:    {len(pages)}")
print(f"  Total data:       {total_bytes:,} bytes")
print(f"  Avg latency:      {avg_latency:.3f}s")
print(f"  Wall clock time:  {elapsed:.1f}s")
print(f"  Sequential est:   ~{sum(p['latency'] for p in pages):.1f}s")
```

    Starting web crawler...
    
      [W0] ERROR: Failed to fetch /
    
    ==================================================
    CRAWL REPORT
    ==================================================
      Pages crawled:    0
      Total data:       0 bytes
      Avg latency:      0.000s
      Wall clock time:  1.1s
      Sequential est:   ~0.0s


---

## Final Challenge: Async Job Scheduler

Build a complete async job scheduler that:

1.  Accepts jobs with **priorities** (higher priority runs first)
2.  Limits concurrency with a semaphore
3.  Supports **timeouts** per job
4.  Collects results and errors separately
5.  Reports statistics at the end


```python
import asyncio
import random
import time


class AsyncJobScheduler:
    def __init__(self, max_concurrent=3, default_timeout=5.0):
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.jobs = []  # List of (priority, name, coro_func, timeout)
        self.results = []
        self.errors = []

    def add_job(self, name, coro_func, priority=0, timeout=None):
        """Add a job. Higher priority = runs first."""
        # YOUR CODE HERE
        pass

    async def run_all(self):
        """Run all jobs respecting priority, concurrency, and timeouts."""
        # YOUR CODE HERE:
        # 1. Sort jobs by priority (highest first)
        # 2. Create a semaphore
        # 3. For each job, create a task that:
        #    a. Acquires the semaphore
        #    b. Runs the coroutine with wait_for (timeout)
        #    c. Stores result or error
        # 4. Gather all tasks
        # 5. Return (results, errors)
        pass


# --- Test jobs ---

async def fast_job():
    await asyncio.sleep(0.3)
    return "fast result"

async def slow_job():
    await asyncio.sleep(3)
    return "slow result"

async def flaky_job():
    await asyncio.sleep(0.5)
    if random.random() < 0.5:
        raise RuntimeError("Random failure!")
    return "flaky result"


# --- Build and run ---
scheduler = AsyncJobScheduler(max_concurrent=2, default_timeout=2.0)

scheduler.add_job("Fast-1", fast_job, priority=1)
scheduler.add_job("Fast-2", fast_job, priority=1)
scheduler.add_job("Slow-1", slow_job, priority=0)  # Will timeout!
scheduler.add_job("Flaky-1", flaky_job, priority=2)  # Highest priority
scheduler.add_job("Flaky-2", flaky_job, priority=2)
scheduler.add_job("Fast-3", fast_job, priority=1)

# Run and print report
# results, errors = await scheduler.run_all()
# print(f"\nSuccesses: {len(results)}, Failures: {len(errors)}")
```

<details>
<summary>Solution</summary>

```python
class AsyncJobScheduler:
    def __init__(self, max_concurrent=3, default_timeout=5.0):
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.jobs = []
        self.results = []
        self.errors = []

    def add_job(self, name, coro_func, priority=0, timeout=None):
        timeout = timeout or self.default_timeout
        self.jobs.append((priority, name, coro_func, timeout))

    async def _run_job(self, name, coro_func, timeout, semaphore):
        async with semaphore:
            try:
                print(f"  [{name}] Starting...")
                result = await asyncio.wait_for(coro_func(), timeout=timeout)
                print(f"  [{name}] Success: {result}")
                self.results.append({"name": name, "result": result})
            except asyncio.TimeoutError:
                print(f"  [{name}] TIMEOUT after {timeout}s")
                self.errors.append({"name": name, "error": "timeout"})
            except Exception as e:
                print(f"  [{name}] FAILED: {e}")
                self.errors.append({"name": name, "error": str(e)})

    async def run_all(self):
        self.results.clear()
        self.errors.clear()

        # Sort by priority (highest first)
        self.jobs.sort(key=lambda j: j[0], reverse=True)

        sem = asyncio.Semaphore(self.max_concurrent)
        tasks = [
            self._run_job(name, coro_func, timeout, sem)
            for _, name, coro_func, timeout in self.jobs
        ]

        start = time.time()
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        print(f"\n{'='*40}")
        print(f"JOB REPORT ({elapsed:.1f}s total)")
        print(f"{'='*40}")
        print(f"  Successes: {len(self.results)}")
        print(f"  Failures:  {len(self.errors)}")
        for e in self.errors:
            print(f"    - {e['name']}: {e['error']}")

        return self.results, self.errors


scheduler = AsyncJobScheduler(max_concurrent=2, default_timeout=2.0)
scheduler.add_job("Fast-1", fast_job, priority=1)
scheduler.add_job("Fast-2", fast_job, priority=1)
scheduler.add_job("Slow-1", slow_job, priority=0)
scheduler.add_job("Flaky-1", flaky_job, priority=2)
scheduler.add_job("Flaky-2", flaky_job, priority=2)
scheduler.add_job("Fast-3", fast_job, priority=1)

results, errors = await scheduler.run_all()
```

</details>

---

## Quiz: Test Your Knowledge

### Q1: What's the output order?


```python
async def f(label, delay):
    print(f"start {label}")
    await asyncio.sleep(delay)
    print(f"end {label}")

await asyncio.gather(f("X", 1), f("Y", 0.5), f("Z", 0.1))
```

<details>
<summary>Click to reveal!</summary>

```
start X
start Y
start Z
end Z     (0.1s)
end Y     (0.5s)
end X     (1.0s)
```


All start immediately (gather runs them concurrently). They end in order of their sleep duration.

</details>

### Q2: Will this code deadlock?


```python
lock = asyncio.Lock()

async def task_a():
    async with lock:
        await task_b()

async def task_b():
    async with lock:
        print("done")

await task_a()
```

<details>
<summary>Click to reveal!</summary>

**Yes, it deadlocks!** `task_a` holds the lock and calls `task_b`, which tries to acquire the same lock. Since `asyncio.Lock` is NOT re-entrant, `task_b` waits forever.

Fix: restructure the code so the lock is not held across the call, or avoid nested lock acquisition.

</details>

### Q3: What's wrong with this code?


```python
async def fetch_all(urls):
    results = []
    for url in urls:
        result = await fetch(url)
        results.append(result)
    return results
```

<details>
<summary>Click to reveal!</summary>

**It's sequential!** The `for` loop `await`s each `fetch()` one at a time. To fetch concurrently:


```python
async def fetch_all(urls):
    return await asyncio.gather(*[fetch(url) for url in urls])
```


This is the most common asyncio performance mistake.

</details>

### Q4: When should you use `asyncio.to_thread()`?

<details>
<summary>Click to reveal!</summary>

When you need to call a **blocking** function from async code without freezing the event loop. Common cases:
- Non-async database drivers (sqlite3, psycopg2)
- File I/O (open/read/write)
- CPU-bound operations
- Third-party libraries that don't support async


```python
# Instead of:
data = open("big_file.csv").read()  # Blocks!

# Do:
data = await asyncio.to_thread(open("big_file.csv").read)
```

</details>

---

## Summary & Cheat Sheet

### Core Patterns


```python
import asyncio

# Define a coroutine
async def work():
    await asyncio.sleep(1)
    return "done"

# Run from a script
asyncio.run(work())

# Run concurrently
results = await asyncio.gather(a(), b(), c())

# Fire and forget
task = asyncio.create_task(work())

# Process as completed
for coro in asyncio.as_completed([a(), b(), c()]):
    result = await coro
```

### Control Flow


```python
# Timeout
await asyncio.wait_for(slow(), timeout=5.0)

# Cancellation
task.cancel()

# Shield from cancellation
await asyncio.shield(critical_operation())

# Wait for first/all
done, pending = await asyncio.wait(tasks, return_when=FIRST_COMPLETED)
```

### Coordination

```bash
# Queue (producer-consumer)
queue = asyncio.Queue(maxsize=10)
await queue.put(item)
item = await queue.get()

# Lock (mutual exclusion)
async with asyncio.Lock():
    # critical section

# Semaphore (rate limiting)
async with asyncio.Semaphore(5):
    # max 5 concurrent

# Event (signaling)
event = asyncio.Event()
await event.wait()   # block until set
event.set()          # release all waiters
```

### Bridging Sync/Async


```python
# Blocking -> async
result = await asyncio.to_thread(blocking_func, arg1, arg2)

# Async -> sync (script entry point)
asyncio.run(main())
```

### Common Mistakes

| Mistake                       | Fix                            |
|-------------------------------|--------------------------------|
| Forgetting `await`            | Always `await` coroutine calls |
| Sequential `await` in a loop  | Use `gather()` instead         |
| Calling `time.sleep()`        | Use `asyncio.sleep()`          |
| Blocking I/O in async code    | Use `asyncio.to_thread()`      |
| Not handling `CancelledError` | Add try/except for cleanup     |

---

## Further Reading

- [Official asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)
- [Python Concurrency with asyncio (book)](https://www.manning.com/books/python-concurrency-with-asyncio)
- Popular async libraries: `aiohttp` (HTTP), `asyncpg` (PostgreSQL), `aiofiles` (file I/O), `aiocache` (caching)

---

*This notebook pairs with the Event-Driven Programming notebook. Together they cover the full spectrum from callbacks to production async patterns.*
