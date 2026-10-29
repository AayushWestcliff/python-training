# Deep Dive: `asyncio` in Python

> *"Concurrency is about dealing with lots of things at once. Parallelism is about doing lots of things at once."* (Rob Pike)

The Event-Driven Programming notebook gave you a first look at `async` and `await`. This notebook goes deeper into Python's `asyncio` library: running tasks together, timeouts and cancellation, sharing resources safely, mixing blocking code with async code, and finally a small web crawler that uses all of it.

### Learning Objectives

By the end of this notebook you will be able to:

1. Explain why async code helps with I/O-bound work (and why it doesn't speed up CPU-bound work)
2. Write coroutines and explain what can be `await`ed
3. Run work concurrently with `gather`, `create_task`, `TaskGroup` and `as_completed`
4. Control running tasks with timeouts, cancellation, `shield` and `wait`
5. Coordinate coroutines with queues, locks, semaphores and events
6. Use async generators, async comprehensions and async context managers
7. Call blocking code from async code with `asyncio.to_thread` and executors
8. Combine all of this in a rate-limited async web crawler

### Prerequisites

- Python 3.11 or newer recommended (`TaskGroup` needs 3.11; the notebook falls back to `gather` on 3.10)
- Functions, classes and exception handling
- Generators (`yield`) help, but aren't required
- The **Event-Driven Programming** notebook (callbacks, event loops, first steps with `async`/`await`)

### How to Use This Notebook

- Run the cells **from top to bottom**. Later cells reuse imports (`asyncio`, `random`, `time`) and helpers from earlier cells.
- The cells use `await` directly at the top level. That works in Jupyter. In a normal `.py` script you'd put the code in `async def main()` and call `asyncio.run(main())` (see Section 2.4).
- Many examples use random delays, so the order of lines and the timings in your output will differ a little from the saved output. That's expected.
- **Try It** cells are for you. Write your answer first, then open *Show solution* to compare.
- Each section ends with a **Quick recap**. Read only the recaps when revising before an exam.

### What We'll Cover

| Section | Topic |
|---|---|
| 1 | Why Async? The I/O Problem |
| 2 | Coroutines and `await`: The Basics |
| 3 | Running Concurrently: `gather`, `create_task`, `TaskGroup` |
| 4 | Controlling Execution: Timeouts, Cancellation, Shielding |
| 5 | Coordination: Queues, Locks, Semaphores, Events |
| 6 | Async Iteration: `async for`, `async with` |
| 7 | Bridging Sync and Async: Threads and Processes |
| 8 | Real-World Project: Async Web Crawler |

---

## Warm-Up Quiz: Concurrency Intuition

Think about each question before opening the answer.

### Q1: You need to download 100 images from the internet. What's the bottleneck?

- A) Your CPU can't process the pixels fast enough
- B) Your program is **waiting** for each download to finish before starting the next
- C) Python is too slow

<details markdown="1">
<summary>Show answer</summary>

**B.** During a download the CPU is mostly idle; it's just waiting for data to arrive over the network. That's called an **I/O-bound** problem, and it's exactly what `asyncio` is designed for.

</details>

### Q2: What's the difference between concurrency and parallelism?

<details markdown="1">
<summary>Show answer</summary>

- **Concurrency**: one cook switching between several dishes (tasks take turns).
- **Parallelism**: several cooks, each working on their own dish at the same moment.

`asyncio` gives you **concurrency** on a single thread. For true parallelism you need several processes (`multiprocessing`).

| | Concurrency | Parallelism |
|---|---|---|
| Threads | 1 (in asyncio) | Multiple (or multiple processes) |
| Best for | I/O-bound work (network, disk) | CPU-bound work (maths, image processing) |
| Python tool | `asyncio` | `multiprocessing` |

</details>

### Q3: How long does this cell take to run?

Write down your guess **before** you run it. The last line prints the actual time.


```python
import time

start = time.time()
time.sleep(1)  # wait 1 second
time.sleep(1)  # wait 1 second
time.sleep(1)  # wait 1 second
print(f"Took {time.time() - start:.1f}s")
```

    Took 3.0s


<details markdown="1">
<summary>Show answer</summary>

**About 3 seconds.** `time.sleep` is **blocking**: the whole program stops at each call, so the three waits add up.

With `asyncio`, the same three waits can overlap and take about **1 second**:

```python
await asyncio.gather(
    asyncio.sleep(1),
    asyncio.sleep(1),
    asyncio.sleep(1),
)
```

</details>

**Quick recap**

- I/O-bound work spends most of its time waiting; that waiting is what async code overlaps.
- Concurrency = taking turns on one thread. Parallelism = running at the same moment on several cores.
- `time.sleep` blocks everything; `await asyncio.sleep` lets other tasks run meanwhile.

---

## 1. Why Async? The I/O Problem

Let's see the problem with synchronous I/O for ourselves. First, three "network calls" made the normal way:


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


Each call has to finish before the next one starts, so the waits add up. Now the same three calls written with `asyncio`:


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


**3.0 s vs 1.5 s.** The async version takes only as long as the slowest call, because all three waits happen at the same time.

### How It Works Under the Hood

```
Synchronous:             Asynchronous:

t=0   [DB starts]        t=0   [DB starts] [API starts] [Cache starts]
t=1   [DB done]          t=0.5             [Cache done]
      [API starts]       t=1   [DB done]
t=2.5 [API done]         t=1.5 [API done]
      [Cache starts]
t=3   [Cache done]       Total: 1.5s

Total: 3.0s
```

The event loop **interleaves** the waiting: while one coroutine is waiting for I/O, the others get to run.

**Quick recap**

- Blocking calls run one after another, so total time = sum of all waits.
- With `asyncio.gather`, waits overlap, so total time = the longest single wait.

---

## 2. Coroutines and `await`: The Basics

### 2.1 Anatomy of a Coroutine


```python
# A coroutine function is defined with 'async def'
async def my_coroutine():
    print("Coroutine started")
    await asyncio.sleep(0.5)    # Yield control to the event loop
    print("Coroutine resumed")
    return 42


# Calling it returns a coroutine OBJECT: it does NOT execute yet!
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


Calling `my_coroutine()` only **creates** a coroutine object; none of the code inside runs yet. That's why "Coroutine started" appears after our two `print` lines. The code runs when we `await` it.

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
loop = asyncio.get_running_loop()
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


In everyday code you'll await coroutines and tasks. **Futures** are the low-level building block that tasks are built on; libraries use them, but application code rarely creates one directly.

Inside async code, get the current loop with `asyncio.get_running_loop()`. The older `asyncio.get_event_loop()` is deprecated in many situations.

### 2.3 The Golden Rule of `await`

Every `await` is a **checkpoint** where the event loop may switch to another task.

**No `await` means no switching, which means no concurrency.**


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
results = await asyncio.gather(greedy(), other_task())
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


In the cooperative run, `other_task` gets a turn between the steps. In the greedy run, `greedy` never reaches an `await`, so `other_task` has to wait until it's completely finished.

`asyncio` uses **cooperative multitasking**: a task only gives up control when it reaches an `await`. One long block of synchronous code freezes everything else. For heavy blocking work inside async code, use `asyncio.to_thread()` (Section 7).

### 2.4 `asyncio.run()`: The Entry Point

In Jupyter we can `await` at the top level. In a normal `.py` script you need `asyncio.run()`:


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


If you call `asyncio.run()` inside Jupyter you get `RuntimeError: asyncio.run() cannot be called from a running event loop`. Jupyter already runs an event loop for you, which is why this notebook uses top-level `await` instead.

### Try It: Async Timer

Write a coroutine `countdown(name, seconds)` that counts down from `seconds`, printing one number per second, and prints `DONE!` at the end. Then run **two countdowns concurrently**.


```python
async def countdown(name, seconds):
    """Count down from 'seconds' to 0, printing each second."""
    # YOUR CODE HERE
    pass


# Run two countdowns concurrently
# YOUR CODE: use asyncio.gather to run countdown("A", 5) and countdown("B", 3)


# Tests (uncomment after finishing):
# start = time.time()
# await asyncio.gather(countdown("A", 2), countdown("B", 1))
# elapsed = time.time() - start
# assert 1.8 < elapsed < 2.5, "The two countdowns should run at the same time"
# print("✓ Countdown works!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
async def countdown(name, seconds):
    for i in range(seconds, 0, -1):
        print(f"  [{name}] {i}...")
        await asyncio.sleep(1)
    print(f"  [{name}] DONE!")

await asyncio.gather(countdown("A", 5), countdown("B", 3))
```

</details>

**Quick recap**

- Calling an `async def` function creates a coroutine object; nothing runs until it is awaited.
- You can await coroutines, tasks and futures.
- The event loop can only switch tasks at an `await`; long synchronous code blocks everything.
- In scripts, start async code with `asyncio.run(main())`. In Jupyter, use top-level `await`.

---

## 3. Running Concurrently: `gather`, `create_task`, `TaskGroup`

### 3.1 `asyncio.gather`: Run Several and Collect the Results


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


Beta finishes first, but the results come back in the order of the arguments. The whole cell takes about 2 seconds (the slowest call), not 3.5.

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


Be careful with the default behaviour. "All results lost!" means **you** don't get the results back from `gather`. A and C are **not** cancelled: they keep running in the background. With `return_exceptions=True`, exceptions are returned in the results list like normal values, so you can check each one.

### 3.3 `asyncio.create_task`: Schedule and Continue


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


Notice that "Doing other work..." is printed **before** "Uploading photo.jpg...". `create_task` schedules the upload, but it only starts at the next `await`, when `main` hands control back to the event loop. `task.done()` lets you check on a task without waiting for it.

### 3.4 `asyncio.TaskGroup`: Structured Concurrency (Python 3.11+)

`TaskGroup` is the modern way to manage a group of tasks. When the `async with` block ends, **every task in it has finished**. If one task fails, the group cancels the others.


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

      A: processed
      B: processed
      C: processed


If a task inside a `TaskGroup` raises an exception, the other tasks are cancelled and the errors are raised together as an `ExceptionGroup`, which you can catch with `except*`.

### `gather` vs `create_task` vs `TaskGroup`

| Feature | `gather` | `create_task` | `TaskGroup` (3.11+) |
|---|---|---|---|
| Returns results | Yes, in argument order | Await each task yourself | Via `task.result()` |
| Error handling | `return_exceptions=True` | Your own `try/except` | Cancels the other tasks on error |
| Cancellation | Manual | Manual | Automatic |
| Use when | You want all results together | You want to start now and await later | You need cleanup guarantees |

### 3.5 `asyncio.as_completed`: Process Results As They Arrive


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


      #1 finished: /orders (1.41s)


      #2 finished: /products (1.61s)


      #3 finished: /users (2.03s)
      #4 finished: /stats (2.19s)


      #5 finished: /reviews (2.38s)


Unlike `gather`, `as_completed` hands you results in **finishing order**, so the fastest endpoint comes first. Use it when you want to show progress or act on each result as soon as it's ready.

### Try It: Parallel Data Fetcher

Write `fetch_all(server_ids)`, which queries all servers concurrently and returns two lists: the successful results and the error messages. Use `gather` with `return_exceptions=True`.


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


# Tests (uncomment after finishing):
# successes, failures = await fetch_all(range(1, 11))
# print(f"Successes: {len(successes)}")
# for s in successes:
#     print(f"  Server {s['server']}: {s['data']} ({s['latency']}s)")
# print(f"\nFailures: {len(failures)}")
# for f in failures:
#     print(f"  {f}")
# assert len(successes) + len(failures) == 10
# assert all(isinstance(s, dict) for s in successes)
# assert all("is down" in f for f in failures)
# print("✓ fetch_all works!")
```

<details markdown="1">
<summary>Show solution</summary>

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

**Quick recap**

- `gather` runs coroutines concurrently and returns results in argument order.
- By default the first exception propagates out of `gather`; `return_exceptions=True` collects them instead.
- `create_task` starts a coroutine in the background. Keep a reference and await it later.
- `TaskGroup` (3.11+) waits for all its tasks and cancels the rest if one fails.
- `as_completed` gives you results in the order they finish.

---

## 4. Controlling Execution: Timeouts, Cancellation, Shielding

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


When the timeout runs out, `wait_for` cancels `slow_query` and raises a timeout error, so the cell takes about 2 seconds instead of 5. (Since Python 3.11, `asyncio.TimeoutError` is just another name for the built-in `TimeoutError`.)

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


`task.cancel()` doesn't stop the task instantly. It raises `CancelledError` **inside** the task at its next `await`. The task can catch it to clean up (close files, release connections), but it should then **re-raise** it so the cancellation actually completes.

### 4.3 Shielding Tasks from Cancellation

Sometimes a piece of work **must not be cancelled**, for example saving data to a database:


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


Cancelling `task` cancels `process_with_save`, which was waiting on the shield. The inner `critical_save` is protected, so it keeps running in the background and "Save complete!" still appears. The final `asyncio.sleep(1.5)` is only there to give it time to finish before the cell ends.

### 4.4 `asyncio.wait`: Fine-Grained Control

`wait` gives you more control than `gather`: you can wait for the **first** task to complete, the **first** one to raise an exception, or **all** of them.


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


`wait` returns two **sets** of tasks, `done` and `pending`, rather than results; call `.result()` on each finished task. Sets have no order, so the remaining results may print in either order.

**Quick recap**

- `asyncio.wait_for(coro, timeout)` cancels the coroutine if it takes too long.
- `task.cancel()` raises `CancelledError` inside the task; clean up, then re-raise.
- `asyncio.shield()` protects inner work from being cancelled along with its caller.
- `asyncio.wait()` returns `(done, pending)` sets and can stop at the first finished task.

---

## 5. Coordination: Queues, Locks, Semaphores, Events

When coroutines share data or resources, they need ways to coordinate. `asyncio` provides the same tools you'd find in threading, in async form.

### 5.1 `asyncio.Queue`: Producer/Consumer


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


      [Producer] Put: item-1 (queue size: 1)
      [Worker-B] Processing: item-1...


      [Worker-A] Done: item-0 (0.5s)
      [Producer] Put: item-2 (queue size: 1)
      [Worker-A] Processing: item-2...


      [Producer] Put: item-3 (queue size: 1)
      [Worker-B] Done: item-1 (0.8s)
      [Worker-B] Processing: item-3...


      [Worker-A] Done: item-2 (0.6s)


      [Producer] Put: item-4 (queue size: 1)
      [Worker-A] Processing: item-4...


      [Producer] Put: item-5 (queue size: 1)
      [Worker-B] Done: item-3 (0.8s)
      [Worker-B] Processing: item-5...


      [Worker-A] Done: item-4 (0.5s)


      [Worker-B] Done: item-5 (0.4s)
      [Worker-A] Received stop signal. Shutting down.
      [Worker-B] Received stop signal. Shutting down.
    
    All work complete!


`maxsize=3` means `put` waits when the queue is full, so a fast producer can't run far ahead of the consumers. `queue.join()` waits until every item has been marked done with `task_done()`. Only then do we send one `None` (the stop signal, or *poison pill*) per worker.

### 5.2 `asyncio.Lock`: Mutual Exclusion


```python
# Shared counter WITHOUT a lock: race condition!
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


# Shared counter WITH a lock: safe!
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


Without the lock, both coroutines read the same value, pause at `await asyncio.sleep(0)`, and then both write `temp + 1`, so half of the increments are lost. Inside `async with lock`, only one coroutine at a time can run the read-pause-write steps.

So yes, single-threaded async code can still have race conditions, but only at `await` points.

### 5.3 `asyncio.Semaphore`: Rate Limiting

A semaphore limits **how many** coroutines can use a resource at the same time. It's ideal for rate limiting API calls.


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


      Done: /api/item/0
      Calling /api/item/3...


      Done: /api/item/2
      Calling /api/item/4...
      Done: /api/item/1
      Calling /api/item/5...


      Done: /api/item/4
      Calling /api/item/6...


      Done: /api/item/3
      Calling /api/item/7...


      Done: /api/item/5
      Done: /api/item/6


      Done: /api/item/7
    
    All done in 3.1s
    Results: ['/api/item/0: ok', '/api/item/1: ok', '/api/item/2: ok', '/api/item/3: ok', '/api/item/4: ok', '/api/item/5: ok', '/api/item/6: ok', '/api/item/7: ok']


There are never more than three calls in progress; a new call starts only when one finishes. Eight calls of about 1 second each, three at a time, take about 3 seconds in total.

### 5.4 `asyncio.Event`: Signal Between Coroutines


```python
async def waiter(event, name):
    print(f"  [{name}] Waiting for the signal...")
    await event.wait()  # Blocks until the event is set
    print(f"  [{name}] Got the signal! Proceeding.")


async def trigger(event):
    print("  [Trigger] Preparing... (1 second)")
    await asyncio.sleep(1)
    print("  [Trigger] Setting the event!")
    event.set()  # All waiters are released simultaneously!


event = asyncio.Event()

# Three coroutines wait, one triggers
results = await asyncio.gather(
    waiter(event, "Worker-A"),
    waiter(event, "Worker-B"),
    waiter(event, "Worker-C"),
    trigger(event),
)
```

      [Worker-A] Waiting for the signal...
      [Worker-B] Waiting for the signal...
      [Worker-C] Waiting for the signal...
      [Trigger] Preparing... (1 second)


      [Trigger] Setting the event!
      [Worker-A] Got the signal! Proceeding.
      [Worker-B] Got the signal! Proceeding.
      [Worker-C] Got the signal! Proceeding.


All three workers block on `event.wait()`. A single `event.set()` releases every one of them at once. Use an `Event` when several tasks need to wait for one thing to happen (for example "configuration loaded" or "shutdown requested").

### Try It: Rate-Limited Downloader

Write `download_file(file_id, semaphore)` and use it to download 20 "files" concurrently, but never more than **5 at a time**. Track the total time and compare it with how long the downloads would take one after another.


```python
async def download_file(file_id, semaphore):
    """Simulate downloading a file. Takes 0.5 - 1.5 seconds."""
    # YOUR CODE HERE:
    # 1. Acquire the semaphore
    # 2. Print that you're starting the download
    # 3. Sleep for a random time
    # 4. Return a dict: {"file": file_id, "time": <seconds it took>}
    pass


# YOUR CODE: create a semaphore, download 20 files, print stats
# Hint: Track total time, count successes, calculate average latency


# Tests (uncomment after finishing):
# sem = asyncio.Semaphore(5)
# start = time.time()
# results = await asyncio.gather(*[download_file(i, sem) for i in range(20)])
# elapsed = time.time() - start
# assert len(results) == 20
# assert elapsed < sum(r["time"] for r in results), "Downloads should overlap"
# assert elapsed > 1.9, "At most 5 at a time: 20 files need at least 4 rounds of 0.5s"
# print(f"✓ Downloaded 20 files in {elapsed:.1f}s")
```

<details markdown="1">
<summary>Show solution</summary>

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

print(f"\n{'=' * 40}")
print(f"Downloaded {len(results)} files")
print(f"Concurrent time: {total:.1f}s")
print(f"Sequential would be: ~{seq_estimate:.1f}s")
print(f"Speedup: {seq_estimate / total:.1f}x")
```

</details>

**Quick recap**

- `asyncio.Queue` hands work from producers to consumers; `task_done()` + `join()` track completion.
- `asyncio.Lock` lets only one coroutine at a time into a critical section.
- `asyncio.Semaphore(n)` lets at most `n` coroutines in at once, which is handy for rate limiting.
- `asyncio.Event` lets many coroutines wait until one of them signals with `set()`.

---

## 6. Async Iteration: `async for` and `async with`

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


      Event #0: value=85


      Event #1: value=40


      Event #2: value=56


      Event #3: value=52


      Event #4: value=15


An `async def` that contains `yield` is an **async generator**. `async for` awaits each item, so while the loop waits for the next event, other tasks can run.

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


Careful: `[await get_price(item) for item in items]` awaits the calls **one after another**, so it's sequential (4 × 0.1 s). To fetch all the prices at the same time, you'd write `await asyncio.gather(*(get_price(item) for item in items))`.

### 6.3 Async Context Managers (`async with`)

Use `async with` when setting up or tearing down a resource involves async operations.


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


Two ways to write the same idea:

- **Class-based**: write `__aenter__` (setup) and `__aexit__` (teardown).
- **`@asynccontextmanager`**: write one async generator. The code before `yield` is the setup, the code after it is the teardown. Putting the teardown in `finally` makes sure it runs even if the block raises an error.

**Quick recap**

- An `async def` with `yield` is an async generator; consume it with `async for`.
- `await` inside a list comprehension runs the calls sequentially; use `gather` to run them concurrently.
- Async context managers handle async setup/teardown; `@asynccontextmanager` is the short way to write one.

---

## 7. Bridging Sync and Async: Threads and Processes

Sometimes you need to call **blocking** code from async code (for example a library that has no async version), or start async code from normal synchronous code.

### 7.1 `asyncio.to_thread`: Run Blocking Code Without Freezing the Loop


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


The event loop stays free while the two threads work, so the sleep, the blocking I/O and the hashing all overlap.

One caveat: because of Python's **GIL** (Global Interpreter Lock), only one thread runs Python code at a time. Moving `cpu_heavy_work` to a thread stops it from freezing the loop, but it does **not** make CPU-heavy Python code faster. For real CPU speed-ups you need separate processes.

### 7.2 `loop.run_in_executor`: Thread Pools and Process Pools

`run_in_executor` lets you choose the pool the work runs in. Here's a thread pool:


```python
from concurrent.futures import ThreadPoolExecutor


def compute(n):
    """A CPU-bound function."""
    return sum(i * i for i in range(n))


# Using a custom thread pool
loop = asyncio.get_running_loop()

with ThreadPoolExecutor(max_workers=4) as pool:
    results = await asyncio.gather(
        loop.run_in_executor(pool, compute, 1_000_000),
        loop.run_in_executor(pool, compute, 2_000_000),
        loop.run_in_executor(pool, compute, 3_000_000),
    )

for i, r in enumerate(results):
    print(f"  Result {i}: {r:,}")
```

      Result 0: 333,332,833,333,500,000
      Result 1: 2,666,664,666,667,000,000
      Result 2: 8,999,995,500,000,500,000


We print the results with `{r:,}`. Formatting with `{r:,.0f}` would first turn these big integers into floats and print slightly wrong digits at the end.

For CPU-bound work, swap in a `ProcessPoolExecutor` so each job runs in its own process, on its own core. Process pools need the worker function to be importable by the child processes, so they don't work reliably with functions defined in a notebook. Use them from a `.py` script like this:

```python
# cpu_jobs.py
import asyncio
from concurrent.futures import ProcessPoolExecutor


def compute(n):
    return sum(i * i for i in range(n))


async def main():
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        results = await asyncio.gather(
            *(loop.run_in_executor(pool, compute, n) for n in (1_000_000, 2_000_000, 3_000_000))
        )
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
```

### When to Use What

| Situation | Solution |
|---|---|
| Blocking I/O (file reads, a non-async database driver) | `asyncio.to_thread()` or a `ThreadPoolExecutor` |
| CPU-bound computation | `ProcessPoolExecutor` or `multiprocessing` |
| Async-native I/O (`aiohttp`, `asyncpg`) | Just `await` it directly |
| Calling async code from sync code | `asyncio.run()` |

**Quick recap**

- Never call blocking functions directly in async code; they freeze the event loop.
- `asyncio.to_thread(func, *args)` runs a blocking function in a thread and lets you await the result.
- Threads keep the loop responsive but don't speed up CPU-bound Python code (GIL). Use processes for that.
- `loop.run_in_executor(pool, func, *args)` lets you pick a thread pool or a process pool.

---

## 8. Real-World Project: Async Web Crawler

Let's put everything together. We'll build a simulated web crawler that:

1. starts from a list of seed URLs,
2. fetches pages concurrently, with a semaphore limiting how many fetches run at once,
3. reads the links on each page,
4. uses a queue to keep track of the pages still to visit (the *crawl frontier*),
5. stops following links beyond a maximum depth, and stops after a maximum number of pages,
6. retries a failed fetch a couple of times before giving up on that page.

Instead of a real network we use `FAKE_WEB`, a dictionary of pages and their links, so the crawler runs anywhere.


```python
import asyncio
import random
import time


# Simulated web: maps each URL to the links on that page
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


async def fetch_with_retry(url, semaphore, worker_id, attempts=3):
    """Try a fetch up to `attempts` times before giving up."""
    for attempt in range(1, attempts + 1):
        try:
            return await fetch_page(url, semaphore)
        except ConnectionError as e:
            print(f"  [W{worker_id}] ERROR (attempt {attempt}/{attempts}): {e}")
    return None  # every attempt failed


async def crawl(seeds, max_pages=15, max_depth=2, max_concurrent=3):
    """Crawl starting from the seed URLs."""
    visited = set()
    results = []
    queue = asyncio.Queue()  # holds (url, depth) pairs
    semaphore = asyncio.Semaphore(max_concurrent)

    for url in seeds:
        queue.put_nowait((url, 0))

    async def worker(worker_id):
        while True:
            url, depth = await queue.get()
            try:
                if url in visited or len(visited) >= max_pages:
                    continue  # skip it (the finally block still runs)
                visited.add(url)

                page = await fetch_with_retry(url, semaphore, worker_id)
                if page is None:
                    continue

                results.append(page)
                print(f"  [W{worker_id}] Crawled {url} (depth {depth}, "
                      f"{page['size']}B, {page['latency']}s, {len(page['links'])} links)")

                # Queue the links we found, unless we're already at max depth
                if depth < max_depth:
                    for link in page["links"]:
                        if link not in visited:
                            queue.put_nowait((link, depth + 1))
            finally:
                queue.task_done()  # mark this queue item as handled

    workers = [asyncio.create_task(worker(i)) for i in range(max_concurrent)]

    # join() returns once every queued URL has been handled
    # (including all the links discovered along the way)
    await queue.join()

    # The workers are now idle, waiting on an empty queue, so stop them
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    return results


# Run the crawler!
print("Starting web crawler...\n")
start = time.time()

pages = await crawl(["/"], max_pages=11, max_depth=2, max_concurrent=3)

elapsed = time.time() - start
total_bytes = sum(p["size"] for p in pages)
avg_latency = sum(p["latency"] for p in pages) / len(pages) if pages else 0

print(f"\n{'=' * 50}")
print("CRAWL REPORT")
print(f"{'=' * 50}")
print(f"  Pages crawled:    {len(pages)}")
print(f"  Total data:       {total_bytes:,} bytes")
print(f"  Avg latency:      {avg_latency:.3f}s")
print(f"  Wall clock time:  {elapsed:.1f}s")
print(f"  Sequential est:   ~{sum(p['latency'] for p in pages):.1f}s")
```

    Starting web crawler...
    


      [W0] Crawled / (depth 0, 1638B, 0.357s, 3 links)


      [W0] Crawled /about (depth 1, 1862B, 0.209s, 3 links)
      [W2] Crawled /blog (depth 1, 1888B, 0.346s, 3 links)


      [W1] ERROR (attempt 1/3): Failed to fetch /products
      [W2] Crawled /about/history (depth 2, 1348B, 0.145s, 2 links)


      [W0] Crawled /about/team (depth 2, 3923B, 0.474s, 1 links)
      [W1] Crawled /products (depth 1, 4847B, 0.278s, 3 links)
      [W2] Crawled /blog/post-1 (depth 2, 800B, 0.255s, 2 links)
      [W0] Crawled /blog/post-2 (depth 2, 3632B, 0.199s, 2 links)


      [W2] ERROR (attempt 1/3): Failed to fetch /products/2
      [W1] Crawled /products/1 (depth 2, 4731B, 0.487s, 2 links)
      [W0] Crawled /products/3 (depth 2, 4505B, 0.355s, 1 links)


      [W2] Crawled /products/2 (depth 2, 4574B, 0.227s, 2 links)
    
    ==================================================
    CRAWL REPORT
    ==================================================
      Pages crawled:    11
      Total data:       33,748 bytes
      Avg latency:      0.303s
      Wall clock time:  1.8s
      Sequential est:   ~3.3s


How the pieces fit together:

- The **queue** holds `(url, depth)` pairs waiting to be crawled. Three **workers** take URLs off it.
- The **`visited` set** makes sure no page is crawled twice, even though many pages link back to `/`.
- Every `queue.get()` is matched by a `queue.task_done()` in a `finally` block, even when a URL is skipped. That's what lets `await queue.join()` know when **all** the work, including newly discovered links, is finished.
- Once the queue is drained, the workers are just waiting forever on `queue.get()`, so we cancel them.
- The **semaphore** caps how many fetches run at once. Here it matches the number of workers; in a bigger crawler you might have many workers sharing a smaller limit.

Your report will differ between runs because of the random delays and failures. Try changing `max_depth` to `1` and see which pages drop out.

**Quick recap**

- A queue plus a fixed number of worker tasks is the standard shape for an async crawler or job runner.
- Pair every `queue.get()` with `queue.task_done()` (in `finally`) so `queue.join()` knows when the work is done.
- Cancel idle workers after `join()`, then gather them so their cancellation is cleaned up.

---

## Final Challenge: Async Job Scheduler

Build an async job scheduler that:

1. accepts jobs with **priorities** (higher priority runs first),
2. limits concurrency with a semaphore,
3. supports a **timeout** per job,
4. collects results and errors separately, and
5. prints some statistics at the end.

Store each success as `{"name": ..., "result": ...}` in `self.results` and each failure as `{"name": ..., "error": ...}` in `self.errors`, using the string `"timeout"` as the error for jobs that time out.


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


# Tests (uncomment after finishing):
# results, errors = await scheduler.run_all()
# assert len(results) + len(errors) == 6
# assert {"name": "Slow-1", "error": "timeout"} in errors
# assert [name for _, name, _, _ in scheduler.jobs][:2] == ["Flaky-1", "Flaky-2"]  # highest priority first
# print(f"✓ Successes: {len(results)}, Failures: {len(errors)}")
```

<details markdown="1">
<summary>Show solution</summary>

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

        print(f"\n{'=' * 40}")
        print(f"JOB REPORT ({elapsed:.1f}s total)")
        print(f"{'=' * 40}")
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

**Quick recap**

- Sorting the jobs before creating the tasks, plus a semaphore, makes higher-priority jobs start first.
- `wait_for` gives every job its own timeout; `try/except` around it keeps one bad job from stopping the rest.

---

## Quiz: Test Your Knowledge

For each question, **predict the answer first**, then run the cell (where there is one) and open the answer.

### Q1: What's the output order?


```python
async def f(label, delay):
    print(f"start {label}")
    await asyncio.sleep(delay)
    print(f"end {label}")

results = await asyncio.gather(f("X", 1), f("Y", 0.5), f("Z", 0.1))
```

    start X
    start Y
    start Z
    end Z


    end Y


    end X


<details markdown="1">
<summary>Show answer</summary>

```
start X
start Y
start Z
end Z     (0.1s)
end Y     (0.5s)
end X     (1.0s)
```

All three start immediately, because `gather` runs them concurrently. They finish in order of their sleep time.

</details>

### Q2: Will this code finish?

To be safe, the cell stops waiting after 2 seconds, so a hang can't freeze your notebook.


```python
lock = asyncio.Lock()

async def task_a():
    async with lock:
        await task_b()

async def task_b():
    async with lock:
        print("done")


try:
    await asyncio.wait_for(task_a(), timeout=2)
except asyncio.TimeoutError:
    print("Still waiting after 2 seconds...")
```

    Still waiting after 2 seconds...


<details markdown="1">
<summary>Show answer</summary>

**No, it deadlocks.** `task_a` holds the lock and then calls `task_b`, which tries to take the same lock. `asyncio.Lock` is **not re-entrant** (the task that holds it can't take it a second time), so `task_b` waits forever. Without the `wait_for` timeout, the cell would never finish.

Fix: restructure the code so the lock isn't held while calling `task_b`, or avoid taking the same lock twice.

</details>

### Q3: What's wrong with this code?

Assume `fetch(url)` is a coroutine that takes about 1 second.


```python
async def fetch_all(urls):
    results = []
    for url in urls:
        result = await fetch(url)
        results.append(result)
    return results
```

<details markdown="1">
<summary>Show answer</summary>

**It's sequential.** The `for` loop awaits each `fetch()` one at a time, so 10 URLs take about 10 seconds. To fetch them concurrently:

```python
async def fetch_all(urls):
    return await asyncio.gather(*[fetch(url) for url in urls])
```

This is the most common asyncio performance mistake.

</details>

### Q4: When should you use `asyncio.to_thread()`?

<details markdown="1">
<summary>Show answer</summary>

When you need to call a **blocking** function from async code without freezing the event loop. Common cases:

- Database drivers that aren't async (`sqlite3`, `psycopg2`)
- File I/O (`open`, `read`, `write`)
- Third-party libraries that don't support async
- CPU-heavy work, to keep the loop responsive (it won't run faster, because of the GIL)

```python
def read_file(path):
    with open(path) as f:
        return f.read()

# Instead of:
data = read_file("big_file.csv")                           # blocks the event loop

# Do:
data = await asyncio.to_thread(read_file, "big_file.csv")  # runs in a thread
```

</details>

**Quick recap**

- Coroutines in `gather` start together and finish in order of how long they wait.
- `asyncio.Lock` is not re-entrant: taking it twice in the same task deadlocks.
- Awaiting inside a `for` loop is sequential; use `gather` to overlap the waits.
- `asyncio.to_thread` is for blocking calls you can't make async.

---

## Summary & Cheat Sheet

### Core Patterns

```python
import asyncio

# Define a coroutine
async def work():
    await asyncio.sleep(1)
    return "done"

# Run from a .py script (not inside Jupyter)
asyncio.run(work())

# Run concurrently
results = await asyncio.gather(a(), b(), c())

# Start in the background, await later (keep the reference!)
task = asyncio.create_task(work())
result = await task

# Structured concurrency (3.11+)
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(a())
    t2 = tg.create_task(b())

# Process results as they complete
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

# Wait for the first one (or all)
done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
```

### Coordination

```python
# Queue (producer/consumer)
queue = asyncio.Queue(maxsize=10)
await queue.put(item)
item = await queue.get()
queue.task_done()

# Lock (one at a time): create it ONCE and share it
lock = asyncio.Lock()
async with lock:
    ...  # critical section

# Semaphore (at most 5 at a time): create it ONCE and share it
sem = asyncio.Semaphore(5)
async with sem:
    ...  # rate-limited work

# Event (signalling)
event = asyncio.Event()
await event.wait()   # block until set
event.set()          # release all waiters
```

### Bridging Sync and Async

```python
# Blocking function -> awaitable
result = await asyncio.to_thread(blocking_func, arg1, arg2)

# Async code -> from a sync script's entry point
asyncio.run(main())
```

### Common Mistakes

| Mistake | Fix |
|---|---|
| Forgetting `await` | Always `await` coroutine calls |
| `await` inside a loop, one call at a time | Use `gather()` instead |
| Calling `time.sleep()` | Use `await asyncio.sleep()` |
| Blocking I/O in async code | Use `asyncio.to_thread()` |
| Creating a new `Lock`/`Semaphore` on every use | Create it once and share it |
| Not handling `CancelledError` | Catch it to clean up, then re-raise |

### Further Reading

- [Official asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)
- [Python Concurrency with asyncio (book)](https://www.manning.com/books/python-concurrency-with-asyncio)
- Popular async libraries: `aiohttp` (HTTP), `asyncpg` (PostgreSQL), `aiofiles` (file I/O), `aiocache` (caching)

### What's Next

This notebook and the Event-Driven Programming notebook together take you from callbacks all the way to production-style async patterns. You'll use these ideas again in the **FastAPI** notebook, where endpoints can be `async def` functions running on exactly this kind of event loop.
