# Creating Distributable Python Packages

So far you've shared code by copying `.py` files around. In this notebook we turn a small text-utility module into a real package that anyone can install with `pip install`, run from the terminal, and upgrade cleanly.

### Learning Objectives

By the end of this notebook you will be able to:

1. Explain the difference between a script, a module and a distributable package
2. Lay out a package using the modern `src/` layout
3. Write a complete `pyproject.toml` with metadata, dependencies and build settings
4. Install your package locally in editable mode with `pip install -e .`
5. Create CLI entry points so users can run your package from the terminal
6. Build a wheel (`.whl`) and a source distribution (`.tar.gz`)
7. Publish a package to TestPyPI
8. Pick the right version number using semantic versioning

### Prerequisites

- Python 3.9 or newer
- Comfortable with functions, modules and `import`
- Basic terminal use (running commands, changing directories)
- `pip` available (the notebook installs `build`, `pytest` and `twine` for you when needed)

### How to Use This Notebook

- Run the cells **from top to bottom**. We build one package, `texttools`, step by step, and later cells depend on files written by earlier ones.
- The package is created in a folder called `texttools_project/` next to this notebook. You can open it in your editor at any point to see the real files.
- Try the practice tasks and the challenge yourself first, then open *Show solution* to compare.
- Each section ends with a **Quick recap**. Read only the recaps when revising.

---

## 1. Why Not Just Share a `.py` File?

Say you've written a handy Python utility and a teammate wants to use it. The first thing most people do is email them the file. Here's what tends to go wrong:

| Problem | What happens |
|----|----|
| They save the file in the wrong folder | `ImportError`: Python can't find it |
| Your code needs `requests` | Nobody told them to install it |
| You fix a bug | They're still running the old copy |
| They want to run it as a command | They have to work out how to call the script |
| You release v2 | Nobody knows which version they have |

A **distributable package** fixes all of these. It's a bundle that:

- installs with one command: `pip install texttools`
- declares its own dependencies, so pip installs them too
- carries a version number
- can add commands to the terminal
- can be upgraded cleanly with `pip install --upgrade`

### The Packaging Pipeline at a Glance

```
You write code
     |
     v
[ pyproject.toml ]        <- describes your package (name, version, dependencies...)
     |
     v
[ python -m build ]       <- bundles your code into distributable files
     |
     v
[ .whl + .tar.gz files ]  <- the "wheel" is what pip actually installs
     |
     v
[ twine upload ]          <- publishes the files to PyPI
     |
     v
[ pip install texttools ] <- your users install it
```

We'll go through every step of this pipeline in this notebook.

**Quick recap**

- Copying `.py` files breaks as soon as there are dependencies, bug fixes or new versions.
- A package has a name, a version, its dependencies and (optionally) terminal commands.
- The pipeline is: `pyproject.toml` -> `python -m build` -> `twine upload` -> `pip install`.

---

## 2. Anatomy of a Modern Python Package

### The `src/` Layout

There are two common ways to lay out a package. We'll use the **`src/` layout**, which is what the Python Packaging Guide recommends:

```
texttools_project/           <- project root (usually your git repo)
|
+-- src/
|   +-- texttools/           <- the actual Python package
|       +-- __init__.py      <- marks it as a package, defines the public API
|       +-- core.py          <- the utility functions
|       +-- cli.py           <- the command-line interface
|
+-- tests/
|   +-- test_core.py         <- unit tests
|
+-- pyproject.toml           <- package metadata and build settings
+-- README.md
```

Why put the package inside `src/`? If the package folder sits right next to your tests, Python can import the *local folder* instead of the *installed package*. Your tests then pass on your machine even when the installed version is broken. With `src/`, the only way to import `texttools` is to install it, so your tests check what users actually get.

| Layout | What can go wrong |
|------------------|-----------------------------------------------------|
| Flat (no `src/`) | The local folder shadows the installed package during tests |
| `src/` layout | Tests always run against the installed package |

### What `__init__.py` Does

`__init__.py` has two jobs:

1. It tells Python that this folder is a **package**, not just a folder.
2. It defines the **public API**: what users get when they write `import texttools`.

Here's the `__init__.py` we're going to write. Don't run anything yet; we create the real file in Step 1 below.

```python
# src/texttools/__init__.py

__version__ = "0.1.0"

from texttools.core import word_count, reverse_words, title_case_smart

__all__ = ["word_count", "reverse_words", "title_case_smart"]
```

- `__version__` is the usual way to expose your package's version in code.
- `__all__` controls what `from texttools import *` brings in. Listing names here makes your public API explicit.

### Step 1: Create the Folder Structure

Now let's build `texttools` for real. Run the cells below in order. Each one writes a file into `texttools_project/`.


```python
import os
import pathlib

# Everything goes inside texttools_project/, next to this notebook.

BASE = pathlib.Path("texttools_project")

dirs = [
    BASE / "src" / "texttools",
    BASE / "tests",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

print("Directories created:")
for d in dirs:
    print(f"  {d}")
```

    Directories created:
      texttools_project/src/texttools
      texttools_project/tests


### Step 2: Write the Package Code

`core.py` holds the three functions our package offers. We store the file's contents in a string and write it to disk, so you can read the whole file right here in the notebook.


```python
# src/texttools/core.py - the actual utility functions

core_code = '''"""Core text utility functions for texttools."""


def word_count(text: str) -> dict:
    """Count the frequency of each word in a string.

    Args:
        text: The input string to analyse.

    Returns:
        A dictionary mapping each word (lowercased) to its count.

    Example:
        >>> word_count("the cat sat on the mat")
        {'the': 2, 'cat': 1, 'sat': 1, 'on': 1, 'mat': 1}
    """
    words = text.lower().split()
    counts: dict = {}
    for word in words:
        # Strip basic punctuation
        word = word.strip(".,!?;:'")
        if word:
            counts[word] = counts.get(word, 0) + 1
    return counts


def reverse_words(text: str) -> str:
    """Reverse the order of words in a string.

    Args:
        text: The input string.

    Returns:
        A new string with word order reversed.

    Example:
        >>> reverse_words("Hello World")
        'World Hello'
    """
    return " ".join(reversed(text.split()))


def title_case_smart(text: str) -> str:
    """Convert a string to title case, skipping common short words.

    Short connector words (a, an, the, and, but, or, for, nor, on,
    at, to, by, in, of, up) remain lowercase unless they are the
    first or last word.

    Args:
        text: The input string.

    Returns:
        A title-cased string respecting common style guidelines.

    Example:
        >>> title_case_smart("the lord of the rings")
        'The Lord of the Rings'
    """
    SKIP = {"a", "an", "the", "and", "but", "or", "for", "nor",
            "on", "at", "to", "by", "in", "of", "up"}
    words = text.lower().split()
    result = []
    for i, word in enumerate(words):
        if i == 0 or i == len(words) - 1 or word not in SKIP:
            result.append(word.capitalize())
        else:
            result.append(word)
    return " ".join(result)
'''

(BASE / "src" / "texttools" / "core.py").write_text(core_code)
print("core.py written.")
```

    core.py written.



```python
# src/texttools/__init__.py - the public API

init_code = '''"""texttools - a small text utility library."""

__version__ = "0.1.0"

from texttools.core import word_count, reverse_words, title_case_smart

__all__ = ["word_count", "reverse_words", "title_case_smart"]
'''

(BASE / "src" / "texttools" / "__init__.py").write_text(init_code)
print("__init__.py written.")
```

    __init__.py written.


**What just happened?** We now have `src/texttools/core.py` and `src/texttools/__init__.py` on disk. You can't `import texttools` yet, because Python doesn't know about the `src/` folder. Installing the package (Section 4) is what fixes that.

**Quick recap**

- Use the `src/` layout: `src/<package>/` for code, `tests/` beside it, `pyproject.toml` at the root.
- `src/` stops your tests from accidentally importing the local folder instead of the installed package.
- `__init__.py` marks a package and defines its public API (`__version__`, `__all__`).

---

## 3. `pyproject.toml` Deep Dive

`pyproject.toml` is the one file that describes your package. It replaced the older `setup.py` and `setup.cfg` files, which you'll still see in older projects.

It has a few tables (sections). Let's go through them one at a time.

### `[build-system]`: *how* to build the package

This tells pip which build tool to use. We use `setuptools`:

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"
```

We ask for setuptools 77 or newer because that's the version that understands the modern `license = "MIT"` field below.

### `[project]`: *what* the package is

```toml
[project]
name = "texttools"
version = "0.1.0"
description = "A small text utility library"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.9"
license = "MIT"
dependencies = []

classifiers = [
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent",
]
```

A few notes:

- `dependencies` lists other packages yours needs, e.g. `["requests>=2.31"]`. Ours needs none.
- `license` is a short SPDX code like `"MIT"` or `"Apache-2.0"`. Older tutorials write `license = {text = "MIT"}` and add a `License :: ...` classifier; current setuptools warns about both, so don't copy that style.
- `classifiers` are tags that help people find your package on PyPI.

### `[project.scripts]`: terminal commands

This creates CLI commands (more on this in Section 5):

```toml
[project.scripts]
texttools = "texttools.cli:main"
#  ^command    ^module  ^function
```

### `[tool.setuptools.packages.find]`: where the code lives

This tells setuptools to look inside `src/` for packages. You need it for the `src/` layout:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

### Step 3: Write `pyproject.toml` and `README.md`

Now we put all of those tables together into one file.


```python
# Write the pyproject.toml for texttools

pyproject = """[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "texttools"
version = "0.1.0"
description = "A small text utility library for word analysis and formatting"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.9"
license = "MIT"
dependencies = []

classifiers = [
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent",
]

[project.scripts]
texttools = "texttools.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
"""

(BASE / "pyproject.toml").write_text(pyproject)
print("pyproject.toml written.")
```

    pyproject.toml written.


`pyproject.toml` says `readme = "README.md"`, so that file has to exist too. PyPI shows it as your package's front page.


```python
# Write a minimal README.md (referenced by pyproject.toml)

readme = '''# texttools

A small text utility library for word analysis and formatting.

## Installation

~~~bash
pip install texttools
~~~

## Usage

~~~python
from texttools import word_count, reverse_words, title_case_smart

print(word_count("the cat sat on the mat"))
# {'the': 2, 'cat': 1, 'sat': 1, 'on': 1, 'mat': 1}

print(reverse_words("Hello World"))
# 'World Hello'

print(title_case_smart("the lord of the rings"))
# 'The Lord of the Rings'
~~~

## CLI

~~~bash
texttools count "the cat sat on the mat"
texttools reverse "Hello World"
texttools titlecase "the lord of the rings"
~~~
'''

(BASE / "README.md").write_text(readme)
print("README.md written.")
```

    README.md written.


**Quick recap**

- `[build-system]` says *how* to build (setuptools); `[project]` says *what* the package is.
- Use `license = "MIT"` (an SPDX string), not the old `{text = ...}` table or license classifiers.
- `[project.scripts]` maps a terminal command to a Python function.
- With the `src/` layout you need `[tool.setuptools.packages.find] where = ["src"]`.

---

## 4. Installing Locally with `pip install -e .`

Before publishing anything, you want to use and test the package on your own machine. The `-e` flag means **editable install**.

### Editable Install vs Regular Install

| Mode | Command | How it works |
|----|----|----|
| Regular | `pip install .` | Copies your files into `site-packages`. Every change needs a reinstall. |
| Editable | `pip install -e .` | Points Python at your source folder. Changes show up straight away. |

During development you'll almost always use editable mode.

### What Happens Under the Hood

```
pip install -e texttools_project/
     |
     v
reads pyproject.toml
     |
     v
writes a small .pth file into site-packages that points to src/
     |
     v
Python can now find 'import texttools'
```

### Step 4: Install the Package

In a terminal you'd run `pip install -e texttools_project/`. Here we run the same command from Python so it installs into this notebook's environment.


```python
import subprocess, sys

result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-e", str(BASE), "--quiet"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("Package installed successfully.")
else:
    print("Error:")
    print(result.stderr)

# Make the package importable in the current kernel session
# (pip editable installs use .pth files, loaded at startup, not dynamically)
src_path = str(BASE / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Added {src_path} to sys.path")
```

    Package installed successfully.
    Added texttools_project/src to sys.path


**What just happened?** pip installed `texttools` in editable mode. The `.pth` file it wrote is only read when Python starts, so this already-running notebook wouldn't see it. That's why the cell also adds `src/` to `sys.path` by hand. In a fresh terminal or a restarted kernel you wouldn't need that line.

Let's check that the import works.


```python
# Verify the install

# Force a fresh import in case texttools was already loaded
for key in list(sys.modules.keys()):
    if key.startswith("texttools"):
        del sys.modules[key]

import texttools

print(f"texttools version: {texttools.__version__}")
print()

sample = "the quick brown fox jumps over the lazy dog"

print("word_count():")
print(texttools.word_count(sample))

print()
print("reverse_words():")
print(texttools.reverse_words(sample))

print()
print("title_case_smart():")
print(texttools.title_case_smart("the lord of the rings: the return of the king"))
```

    texttools version: 0.1.0
    
    word_count():
    {'the': 2, 'quick': 1, 'brown': 1, 'fox': 1, 'jumps': 1, 'over': 1, 'lazy': 1, 'dog': 1}
    
    reverse_words():
    dog lazy the over jumps fox brown quick the
    
    title_case_smart():
    The Lord of the Rings: the Return of the King


**Checkpoint:** you should see `texttools version: 0.1.0` followed by the results of the three functions. If you get `ModuleNotFoundError`, re-run the install cell above.

Notice the title-case result: `the` stays lowercase after `Rings:` because our function only looks at word position, not punctuation. Good enough for a teaching example.

**Quick recap**

- `pip install -e .` installs your package in editable mode: edit the code, re-run, no reinstall.
- A regular `pip install .` copies the files, so you'd need to reinstall after every change.
- Editable installs work through a `.pth` file that Python reads at start-up.

---

## 5. Entry Points: Creating CLI Commands

Entry points let users run your package as a normal terminal command:

```bash
$ texttools count "the cat sat on the mat"
cat: 1
mat: 1
on: 1
sat: 1
the: 2
```

### How It Works

When pip installs your package, it reads `[project.scripts]` from `pyproject.toml`:

```toml
[project.scripts]
texttools = "texttools.cli:main"
#  ^command    ^module  ^function
```

pip then creates a tiny launcher program called `texttools` in your environment's `bin/` folder (`Scripts\` on Windows). Running it simply calls `texttools.cli.main()`.

### Step 5: Write the CLI Module

`cli.py` uses `argparse` from the standard library to read the command-line arguments. It has three sub-commands: `count`, `reverse` and `titlecase`.


```python
# src/texttools/cli.py - command-line interface

cli_code = '''"""Command-line interface for texttools."""

import argparse
import sys
from texttools.core import word_count, reverse_words, title_case_smart


def main() -> None:
    """Entry point for the texttools CLI."""
    parser = argparse.ArgumentParser(
        prog="texttools",
        description="Text utility commands",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # count command
    count_parser = subparsers.add_parser("count", help="Count word frequencies")
    count_parser.add_argument("text", help="Text to analyse")

    # reverse command
    reverse_parser = subparsers.add_parser("reverse", help="Reverse word order")
    reverse_parser.add_argument("text", help="Text to reverse")

    # titlecase command
    title_parser = subparsers.add_parser("titlecase", help="Smart title case")
    title_parser.add_argument("text", help="Text to convert")

    args = parser.parse_args()

    if args.command == "count":
        counts = word_count(args.text)
        for word, n in sorted(counts.items()):
            print(f"{word}: {n}")

    elif args.command == "reverse":
        print(reverse_words(args.text))

    elif args.command == "titlecase":
        print(title_case_smart(args.text))


if __name__ == "__main__":
    main()
'''

(BASE / "src" / "texttools" / "cli.py").write_text(cli_code)
print("cli.py written.")

# Reinstall so pip registers the new entry point
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-e", str(BASE), "--quiet"],
    capture_output=True,
    text=True
)
print("Package reinstalled." if result.returncode == 0 else result.stderr)

# Make sure src/ is still on the path
if src_path not in sys.path:
    sys.path.insert(0, src_path)
```

    cli.py written.


    Package reinstalled.


We reinstalled because entry points are created at install time. Adding `cli.py` alone doesn't create the `texttools` command.

Now let's try the CLI. In a terminal you would type `texttools count "..."`. Here we call the same code with `python -m texttools.cli`, which works no matter where the launcher was installed.


```python
# Test the CLI programmatically

result = subprocess.run(
    [sys.executable, "-m", "texttools.cli", "count", "the cat sat on the mat"],
    capture_output=True,
    text=True
)
print("texttools count 'the cat sat on the mat':")
print(result.stdout)

result2 = subprocess.run(
    [sys.executable, "-m", "texttools.cli", "titlecase", "the lord of the rings"],
    capture_output=True,
    text=True
)
print("texttools titlecase 'the lord of the rings':")
print(result2.stdout)
```

    texttools count 'the cat sat on the mat':
    cat: 1
    mat: 1
    on: 1
    sat: 1
    the: 2
    
    texttools titlecase 'the lord of the rings':
    The Lord of the Rings
    


**Checkpoint:** the word counts should be sorted alphabetically, and the title should read `The Lord of the Rings`.

**Why `if __name__ == "__main__":`?** That guard at the bottom of `cli.py` is what makes `python -m texttools.cli` work. The installed `texttools` command doesn't need it, because it calls `main()` directly. The guard is just handy while you're developing.

**Quick recap**

- `[project.scripts]` turns `command = "module:function"` into a real terminal command.
- The command is created when the package is installed, so reinstall after adding an entry point.
- `argparse` sub-parsers give you `git`-style sub-commands like `texttools count`.

---

## 6. Testing the Installed Package

Tests should run against the **installed** package, not loose source files. The `src/` layout guarantees that: the tests can only `import texttools` because it's installed.

### Test Structure

```
tests/
+-- test_core.py
```

Note there's **no `__init__.py` in `tests/`**. pytest doesn't need one, and leaving it out avoids confusing import problems.

### Step 6: Write and Run the Tests


```python
# Write the test file

test_code = '''"""Tests for texttools.core"""

import pytest
from texttools import word_count, reverse_words, title_case_smart


class TestWordCount:
    def test_basic_count(self):
        result = word_count("the cat sat on the mat")
        assert result["the"] == 2
        assert result["cat"] == 1

    def test_case_insensitive(self):
        result = word_count("Python python PYTHON")
        assert result["python"] == 3

    def test_strips_punctuation(self):
        result = word_count("hello, world!")
        assert "hello" in result
        assert "world" in result

    def test_empty_string(self):
        assert word_count("") == {}


class TestReverseWords:
    def test_basic_reverse(self):
        assert reverse_words("Hello World") == "World Hello"

    def test_single_word(self):
        assert reverse_words("Python") == "Python"

    def test_multiple_words(self):
        assert reverse_words("one two three") == "three two one"


class TestTitleCaseSmart:
    def test_short_words_lowercase(self):
        result = title_case_smart("the lord of the rings")
        assert result == "The Lord of the Rings"

    def test_first_word_always_capitalised(self):
        result = title_case_smart("of mice and men")
        assert result.startswith("Of")

    def test_last_word_always_capitalised(self):
        result = title_case_smart("the cat in the hat")
        assert result.endswith("Hat")

    def test_single_word(self):
        assert title_case_smart("python") == "Python"
'''

(BASE / "tests" / "test_core.py").write_text(test_code)
print("test_core.py written.")
```

    test_core.py written.



```python
# Install pytest if needed
subprocess.run(
    [sys.executable, "-m", "pip", "install", "pytest", "--quiet"],
    capture_output=True
)

# Run the tests

result = subprocess.run(
    [sys.executable, "-m", "pytest", str(BASE / "tests"), "-v", "--color=no"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print(result.stderr)
```

    ============================= test session starts ==============================
    platform darwin -- Python 3.12.14, pytest-9.2.0, pluggy-1.7.0 -- .venv/bin/python
    cachedir: .pytest_cache
    rootdir: texttools_project
    configfile: pyproject.toml
    plugins: platformdirs-4.14.0, anyio-4.15.1
    collecting ... collected 11 items
    
    texttools_project/tests/test_core.py::TestWordCount::test_basic_count PASSED [  9%]
    texttools_project/tests/test_core.py::TestWordCount::test_case_insensitive PASSED [ 18%]
    texttools_project/tests/test_core.py::TestWordCount::test_strips_punctuation PASSED [ 27%]
    texttools_project/tests/test_core.py::TestWordCount::test_empty_string PASSED [ 36%]
    texttools_project/tests/test_core.py::TestReverseWords::test_basic_reverse PASSED [ 45%]
    texttools_project/tests/test_core.py::TestReverseWords::test_single_word PASSED [ 54%]
    texttools_project/tests/test_core.py::TestReverseWords::test_multiple_words PASSED [ 63%]
    texttools_project/tests/test_core.py::TestTitleCaseSmart::test_short_words_lowercase PASSED [ 72%]
    texttools_project/tests/test_core.py::TestTitleCaseSmart::test_first_word_always_capitalised PASSED [ 81%]
    texttools_project/tests/test_core.py::TestTitleCaseSmart::test_last_word_always_capitalised PASSED [ 90%]
    texttools_project/tests/test_core.py::TestTitleCaseSmart::test_single_word PASSED [100%]
    
    ============================== 11 passed in 0.01s ==============================
    


**Checkpoint:** you should see `11 passed`. If a test fails, read the assertion message, fix `core.py`, and run the test cell again. Thanks to the editable install there's no need to reinstall.

**Quick recap**

- Put tests in `tests/` next to `src/`, with no `__init__.py`.
- Run them with `python -m pytest tests/`.
- Because of the `src/` layout, a passing test means the *installed* package works.

---

## 7. Building a Distribution

When you're ready to share the package, you build it into files that pip can install:

| Format | Extension | Description |
|----|----|----|
| Wheel | `.whl` | Ready-to-install archive. Fast to install and the most common format. |
| Source distribution (sdist) | `.tar.gz` | Archive of your source code. pip builds it on the user's machine. |

Always publish **both**. pip prefers the wheel and falls back to the sdist.

### The `build` Tool

`python -m build` reads `pyproject.toml` and creates both files in a `dist/` folder:

```text
dist/
+-- texttools-0.1.0-py3-none-any.whl
+-- texttools-0.1.0.tar.gz
```

### Reading a Wheel's Filename

```text
texttools - 0.1.0 - py3 - none - any .whl
^           ^       ^     ^      ^
package     version python abi   platform

py3   = works with Python 3
none  = no compiled code, so no ABI requirement (pure Python)
any   = works on any operating system
```

### Step 7: Build the Package

This is the same as running `python -m build texttools_project/` in a terminal. It can take a little while the first time because it sets up a clean build environment.


```python
# Install the build tool if not already present
subprocess.run(
    [sys.executable, "-m", "pip", "install", "build", "--quiet"],
    capture_output=True
)

# Build the package
result = subprocess.run(
    [sys.executable, "-m", "build", str(BASE)],
    capture_output=True,
    text=True,
    env={**os.environ, "NO_COLOR": "1"},  # plain text output, no colour codes
)

# The full log is long; the last line tells us whether it worked
print(result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "(no output)")
if result.returncode != 0:
    print("STDERR:", result.stderr[-1000:])
```

    Successfully built texttools-0.1.0.tar.gz and texttools-0.1.0-py3-none-any.whl


A wheel is just a zip file, so we can look inside it with the `zipfile` module:


```python
import zipfile

dist_dir = BASE / "dist"
print("Contents of dist/:")
for f in sorted(dist_dir.iterdir()):
    size_kb = f.stat().st_size / 1024
    print(f"  {f.name:45s}  {size_kb:.1f} KB")

print()

# Peek inside the wheel (it is just a zip file)
whl = next(dist_dir.glob("*.whl"))
print(f"Contents of {whl.name}:")
with zipfile.ZipFile(whl) as z:
    for name in sorted(z.namelist()):
        print(f"  {name}")
```

    Contents of dist/:
      texttools-0.1.0-py3-none-any.whl               3.4 KB
      texttools-0.1.0.tar.gz                         3.1 KB
    
    Contents of texttools-0.1.0-py3-none-any.whl:
      texttools-0.1.0.dist-info/METADATA
      texttools-0.1.0.dist-info/RECORD
      texttools-0.1.0.dist-info/WHEEL
      texttools-0.1.0.dist-info/entry_points.txt
      texttools-0.1.0.dist-info/top_level.txt
      texttools/__init__.py
      texttools/cli.py
      texttools/core.py


**Checkpoint:** `dist/` should contain one `.whl` and one `.tar.gz`. Inside the wheel you should see your three `.py` files plus a `dist-info/` folder. `METADATA` holds what you wrote in `pyproject.toml`, and `entry_points.txt` holds the `texttools` command.

**Quick recap**

- `python -m build` creates a wheel (`.whl`) and an sdist (`.tar.gz`) in `dist/`.
- A wheel name reads `name-version-python-abi-platform.whl`; `py3-none-any` means pure Python.
- A wheel is a zip file of your package plus a `dist-info/` metadata folder.

---

## 8. Publishing to TestPyPI

**PyPI** (the Python Package Index, [pypi.org](https://pypi.org)) is the official registry. `pip install` downloads from there.

**TestPyPI** ([test.pypi.org](https://test.pypi.org)) is a separate practice server. Always try an upload there before using the real PyPI.

### Before You Publish

1. Create an account at [test.pypi.org](https://test.pypi.org).
2. Create an API token: *Account settings -> API tokens*.
3. Install `twine`: `pip install twine`.
4. Pick a **unique name**. Package names on PyPI and TestPyPI are first come, first served, and `texttools` is almost certainly taken. Change `name` in `pyproject.toml` to something like `texttools-yourname`, then rebuild. Users still write `import texttools`, because the import name comes from the `src/texttools/` folder, not from `name`.

### The Workflow

```text
Build              ->   Check              ->   Upload
python -m build         twine check dist/*      twine upload dist/*
```

### Step 8: Check the Files Before Uploading

`twine check` makes sure your metadata is valid and that your README will display properly on PyPI.


```python
# Install twine
subprocess.run(
    [sys.executable, "-m", "pip", "install", "twine", "--quiet"],
    capture_output=True
)

import glob as glob_module
dist_files = glob_module.glob(str(BASE / "dist" / "*"))

result = subprocess.run(
    [sys.executable, "-m", "twine", "--no-color", "check"] + dist_files,
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr)
```

    Checking texttools_project/dist/texttools-0.1.0-py3-none-any.whl: PASSED
    Checking texttools_project/dist/texttools-0.1.0.tar.gz: PASSED
    


**Checkpoint:** both files should say `PASSED`.

### Step 9: Upload to TestPyPI (in your terminal)

This step isn't run in the notebook because it needs your own TestPyPI account and token. In a terminal, from the `texttools_project/` folder:

```bash
twine upload --repository testpypi dist/*
```

When twine asks for credentials:

- **Username:** `__token__` (type exactly that)
- **Password:** your API token, which starts with `pypi-`

To avoid typing the token every time, save it in a `~/.pypirc` file in your home folder:

```ini
# ~/.pypirc
[testpypi]
username = __token__
password = pypi-your-token-here
```

Keep this file private and never commit it to git.

### Step 10: Install From TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ texttools-yourname
```

If your package has dependencies, add `--extra-index-url https://pypi.org/simple/` so pip can find them on the real PyPI (TestPyPI doesn't host most packages).

### Step 11: Publish to the Real PyPI

Once everything works on TestPyPI, create an account and token on [pypi.org](https://pypi.org) and run:

```bash
twine upload dist/*
pip install texttools-yourname
```

**Quick recap**

- Practise on TestPyPI first; real PyPI uploads can't be undone.
- `twine check dist/*` validates the files; `twine upload` publishes them.
- Log in with username `__token__` and an API token as the password.
- The distribution name (`name` in `pyproject.toml`) must be unique; the import name can stay the same.

---

## 9. Versioning Best Practices

### Semantic Versioning (SemVer)

Most Python packages use **semantic versioning**: `MAJOR.MINOR.PATCH`.

```text
  1  .  4  .  2
  ^     ^     ^
MAJOR MINOR PATCH
```

| Part | Bump it when... | Example |
|-----------|----------------------------------------------|---------------------|
| **MAJOR** | you break backwards compatibility | `1.4.2` -> `2.0.0` |
| **MINOR** | you add a feature that doesn't break existing code | `1.4.2` -> `1.5.0` |
| **PATCH** | you fix a bug without changing the API | `1.4.2` -> `1.4.3` |

When you bump one part, reset the parts to its right to zero. Versions starting with `0.` (like `0.1.0`) tell users the API isn't stable yet.

### Keeping the Version in One Place

Right now the version lives in two places:

1. `pyproject.toml` -> `version = "0.1.0"`
2. `src/texttools/__init__.py` -> `__version__ = "0.1.0"`

Update one, forget the other, and they drift apart. There are two clean fixes.

**Option A: read the version from the installed metadata.** `pyproject.toml` becomes the only place you write the version, and your code asks for it at run time:


```python
# Option A: importlib.metadata reads version from the installed package metadata.
# pyproject.toml is the ONLY place you define the version.

from importlib.metadata import version, PackageNotFoundError

try:
    pkg_version = version("texttools")
except PackageNotFoundError:
    pkg_version = "unknown"

print(f"Version from metadata: {pkg_version}")
```

    Version from metadata: 0.1.0


**Option B: keep `__version__` in `__init__.py` and let `pyproject.toml` read it.** Remove the `version = ...` line from `[project]` and add:

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "texttools.__version__"}
```

Now `__init__.py` is the one place to change the version. (You must delete the fixed `version` line; setuptools refuses a version that's both fixed and `dynamic`.)

### Releasing a New Version

```text
1. Update the version (pyproject.toml, or __init__.py with Option B)
2. git commit -m "Bump version to 0.2.0"
3. git tag v0.2.0
4. Delete the old dist/ folder, then: python -m build
5. twine upload dist/*
```

PyPI never lets you upload the same version twice, even if you delete it. If you made a mistake, release a new patch version.

**Quick recap**

- SemVer: MAJOR for breaking changes, MINOR for new features, PATCH for bug fixes.
- Keep the version in one place: read it with `importlib.metadata.version()` or use `dynamic = ["version"]`.
- Every upload needs a new version number; PyPI won't accept the same one twice.

---

## 10. Full Package Checklist

Use this list before every release:

```text
Structure
  [ ] src/<package>/ layout with __init__.py
  [ ] __version__ defined (or using importlib.metadata)
  [ ] tests/ folder with no __init__.py
  [ ] README.md with installation and usage examples

pyproject.toml
  [ ] name is unique (search PyPI first)
  [ ] version follows SemVer
  [ ] description is one informative sentence
  [ ] requires-python set correctly
  [ ] dependencies listed (even if empty)
  [ ] license set as an SPDX string, e.g. "MIT"
  [ ] classifiers added
  [ ] [tool.setuptools.packages.find] where = ["src"]

Quality
  [ ] All public functions have docstrings
  [ ] Tests cover the normal cases and the edge cases
  [ ] twine check passes with no warnings

Publishing
  [ ] Tested on TestPyPI first
  [ ] Git tag created for this version
  [ ] No secrets or passwords in the code
```

---

## 11. Practice

A few quick tasks to check your understanding before the bigger challenge. Answer each one before opening the solution.

### Task 1: Which number do you bump?

`texttools` is at version `1.4.2`. What is the next version for each change?

1. You fix a bug where `word_count("")` crashed.
2. You add a new function `char_count()`.
3. You rename `reverse_words()` to `reverse()` and delete the old name.

<details markdown="1">
<summary>Show solution</summary>

1. **`1.4.3`**: a bug fix is a PATCH.
2. **`1.5.0`**: a new feature that doesn't break anything is a MINOR bump (PATCH resets to 0).
3. **`2.0.0`**: removing a name breaks existing code, so it's a MAJOR bump.

</details>

### Task 2: Add a second command

Add a terminal command called `tt-count` that runs a function `count_main()` in `texttools/cli.py`. What do you add to `pyproject.toml`, and what must you do afterwards?

<details markdown="1">
<summary>Show solution</summary>

```toml
[project.scripts]
texttools = "texttools.cli:main"
tt-count = "texttools.cli:count_main"
```

Then write `count_main()` in `cli.py` and **reinstall** (`pip install -e .`), because commands are only created at install time.

</details>

### Task 3: Read a wheel filename

What does `requests-2.32.3-py3-none-any.whl` tell you? And what would you guess `numpy-2.1.0-cp312-cp312-macosx_14_0_arm64.whl` means?

<details markdown="1">
<summary>Show solution</summary>

- `requests` version `2.32.3`, for any Python 3 (`py3`), with no compiled code (`none`), on any operating system (`any`).
- `numpy` version `2.1.0`, compiled for CPython 3.12 (`cp312`), using the CPython 3.12 ABI, and only for macOS 14 on Apple Silicon (`arm64`). numpy contains C code, so it needs a separate wheel per platform.

</details>

---

## Challenge: Build Your Own Package

Build a distributable package called **`numtools`** (or pick your own name) from scratch.

### Requirements

1. Use the `src/` layout.
2. Write a proper `pyproject.toml` with all the fields we used.
3. Expose at least **3 functions** in the public API through `__init__.py`.
4. Add a **CLI entry point** with at least 2 sub-commands.
5. Include **tests** that cover each function.
6. Pass `twine check` after building.

### Ideas for Functions

| Theme | Possible functions |
|----|----|
| Numbers | `is_prime(n)`, `fibonacci(n)`, `factorial(n)` |
| Dates | `days_until(date)`, `is_weekend(date)`, `format_date(date, style)` |
| Files | `count_lines(path)`, `find_duplicates(dir)`, `largest_files(dir, n)` |
| Colours | `hex_to_rgb(hex)`, `rgb_to_hex(r, g, b)`, `contrast_ratio(c1, c2)` |

### Starter Structure

```text
numtools/
+-- src/
|   +-- numtools/
|       +-- __init__.py
|       +-- core.py
|       +-- cli.py
+-- tests/
|   +-- test_core.py
+-- pyproject.toml
+-- README.md
```

Work in the cell below. You can copy the patterns from the `texttools` cells above, or create the files in your editor and run the commands in a terminal.


```python
# Your workspace - build numtools here

challenge_base = pathlib.Path("numtools")

# TODO: Create the src/numtools/ and tests/ directories
# TODO: Write core.py with at least 3 functions
# TODO: Write __init__.py exposing the public API
# TODO: Write cli.py with a main() entry point
# TODO: Write pyproject.toml
# TODO: Write test_core.py
# TODO: pip install -e numtools/
# TODO: pytest numtools/tests/
# TODO: python -m build numtools/
# TODO: twine check numtools/dist/*

print("Good luck!")
```

    Good luck!


Stuck? Open a hint before you look at the full solution.

<details markdown="1">
<summary>Hint 1: pyproject.toml skeleton</summary>

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "numtools"
version = "0.1.0"
description = "YOUR DESCRIPTION HERE"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.9"
license = "MIT"
dependencies = []

[project.scripts]
numtools = "numtools.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

</details>

<details markdown="1">
<summary>Hint 2: is_prime() implementation</summary>

```python
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
```

</details>

<details markdown="1">
<summary>Show solution</summary>

```python
import pathlib, subprocess, sys

root = pathlib.Path("numtools")
pkg = root / "src" / "numtools"
pkg.mkdir(parents=True, exist_ok=True)
(root / "tests").mkdir(exist_ok=True)

(pkg / "core.py").write_text('''"""Small number utilities."""


def is_prime(n: int) -> bool:
    """Return True if n is a prime number."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def fibonacci(n: int) -> list:
    """Return the first n Fibonacci numbers."""
    seq = []
    a, b = 0, 1
    for _ in range(n):
        seq.append(a)
        a, b = b, a + b
    return seq


def factorial(n: int) -> int:
    """Return n! for n >= 0."""
    if n < 0:
        raise ValueError("n must be >= 0")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
''')

(pkg / "__init__.py").write_text('''"""numtools - small number utilities."""

__version__ = "0.1.0"

from numtools.core import is_prime, fibonacci, factorial

__all__ = ["is_prime", "fibonacci", "factorial"]
''')

(pkg / "cli.py").write_text('''"""Command-line interface for numtools."""

import argparse
from numtools.core import is_prime, fibonacci, factorial


def main() -> None:
    parser = argparse.ArgumentParser(prog="numtools")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prime", "fib", "fact"):
        sub.add_parser(name).add_argument("n", type=int)
    args = parser.parse_args()

    if args.command == "prime":
        print(is_prime(args.n))
    elif args.command == "fib":
        print(fibonacci(args.n))
    elif args.command == "fact":
        print(factorial(args.n))


if __name__ == "__main__":
    main()
''')

(root / "tests" / "test_core.py").write_text('''import pytest
from numtools import is_prime, fibonacci, factorial


def test_is_prime():
    assert is_prime(7)
    assert not is_prime(1)
    assert not is_prime(9)


def test_fibonacci():
    assert fibonacci(6) == [0, 1, 1, 2, 3, 5]
    assert fibonacci(0) == []


def test_factorial():
    assert factorial(0) == 1
    assert factorial(5) == 120
    with pytest.raises(ValueError):
        factorial(-1)
''')

(root / "README.md").write_text("# numtools\n\nSmall number utilities: is_prime, fibonacci, factorial.\n")

(root / "pyproject.toml").write_text('''[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "numtools"
version = "0.1.0"
description = "Small number utilities"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.9"
license = "MIT"
dependencies = []

[project.scripts]
numtools = "numtools.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
''')


def run(*args):
    out = subprocess.run([sys.executable, "-m", *args], capture_output=True, text=True)
    print(" ".join(args[:2]), "->", "OK" if out.returncode == 0 else out.stdout + out.stderr)


run("pip", "install", "-e", str(root), "--quiet")
run("pytest", str(root / "tests"), "-q")
run("build", str(root))
run("twine", "check", *map(str, (root / "dist").glob("*")))
```

</details>

In a terminal, the last four lines are simply:

```bash
pip install -e numtools/
pytest numtools/tests/
python -m build numtools/
twine check numtools/dist/*
```

---

## Summary & Cheat Sheet

| Concept | Remember this |
|----|----|
| `src/` layout | Keeps local source from shadowing the installed package during tests |
| `__init__.py` | Marks the package, defines the public API, holds `__version__` |
| `pyproject.toml` | One file for metadata, dependencies and build settings |
| Editable install | `pip install -e .`: changes show up without reinstalling |
| Entry points | `[project.scripts]` maps a terminal command to a Python function |
| `python -m build` | Creates `.whl` and `.tar.gz` in `dist/` |
| `twine` | `twine check` validates, `twine upload` publishes to PyPI/TestPyPI |
| SemVer | `MAJOR.MINOR.PATCH`: think about which number your change deserves |

### Commands You'll Use Most

```bash
pip install -e .                               # editable install while developing
python -m pytest tests/                        # run the tests
python -m build                                # create dist/*.whl and dist/*.tar.gz
twine check dist/*                             # validate before uploading
twine upload --repository testpypi dist/*      # practice upload
twine upload dist/*                            # real upload to PyPI
```

### Further Reading

- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
- [Writing your pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [TestPyPI](https://test.pypi.org)
- [setuptools documentation](https://setuptools.pypa.io/en/latest/)

### What's Next

The next notebook, **FastAPI**, moves from libraries to web services. The same ideas carry over: a `pyproject.toml` or `requirements.txt` to pin dependencies, a clear project layout, and tests that run against what you actually ship.
