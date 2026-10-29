# Creating Distributable Python Packages

> *"Namespaces are one honking great idea — let's do more of those!"*
>
> — The Zen of Python

---

### Learning Objectives

By the end of this notebook, you will be able to:

1.  **Explain** the difference between a Python script, a module, and a distributable package
2.  **Structure** a package using the modern `src/` layout
3.  **Write** a complete `pyproject.toml` with metadata, dependencies, and build config
4.  **Install** your package locally in editable mode with `pip install -e .`
5.  **Create** CLI entry points so users can run your package from the terminal
6.  **Build** a distributable wheel (`.whl`) and source distribution (`.tar.gz`)
7.  **Publish** a package to TestPyPI
8.  **Apply** semantic versioning correctly

---

### Prerequisites

- Python 3.8+ installed
- Comfortable with functions, modules, and `import`
- Basic terminal usage (running commands)
- `pip` and `build` installed (`pip install build`)

---

## Section 1 — Why Not Just Share a `.py` File?

Imagine you wrote a brilliant Python utility. You want your teammate — or the world — to use it.

Your first instinct might be:

> *"I'll just email them the file."*

Here's what happens next:

| Problem | Consequence |
|----|----|
| They put the file in the wrong directory | `ImportError` — it can't be found |
| Your code depends on `requests` | They don't know they need to install it |
| You fix a bug | They're still using the old file |
| They want a CLI command | They have to figure out how to run the script |
| You release v2 | Nobody knows which version they have |

**A distributable package solves all of this.** It is a bundle that:

- Can be installed with a single command: `pip install texttools`
- Declares its own dependencies automatically
- Has a version number
- Can expose CLI commands
- Can be updated cleanly

---

### The Packaging Ecosystem at a Glance

```
You write code
     |
     v
[ pyproject.toml ]  <- describes your package (name, version, deps...)
     |
     v
[ python -m build ]  <- packages your code into a distributable format
     |
     v
[ .whl file ]  <- the "wheel" - what pip installs
     |
     v
[ pip upload to PyPI ]  <- published for anyone to install
     |
     v
[ pip install texttools ]  <- your users install it
```

We will build every step of this chain today.

---

## Section 2 — Anatomy of a Modern Python Package

### The `src/` Layout

There are two common ways to lay out a Python package. We will use the **`src/` layout** — the modern, recommended approach:

```
texttools/                   <- project root (repo root)
|
+-- src/
|   +-- texttools/           <- the actual Python package
|       +-- __init__.py      <- makes it a package, exposes public API
|       +-- core.py          <- core utility functions
|       +-- cli.py           <- command-line interface
|
+-- tests/
|   +-- test_core.py         <- unit tests
|
+-- pyproject.toml           <- package metadata and build config
+-- README.md
```

**Why `src/`?** Without it, Python can accidentally import your local folder instead of the installed package. The `src/` directory forces Python to only use the installed version during testing.

| Layout           | Risk                                                |
|------------------|-----------------------------------------------------|
| Flat (no `src/`) | Local folder shadows installed package during tests |
| `src/` layout    | Tests always run against the installed package      |

---

### What `__init__.py` Does

The `__init__.py` file serves two purposes:

1.  **Signals to Python** that this directory is a package (not just a folder)
2.  **Defines the public API** — what users see when they `import texttools`


```python
# src/texttools/__init__.py

__version__ = "0.1.0"

from texttools.core import word_count, reverse_words, title_case_smart

__all__ = ["word_count", "reverse_words", "title_case_smart"]
```

> **`__version__`** is the conventional way to expose your package version in code.
>
> **`__all__`** controls what `from texttools import *` exports. Defining it makes your public API explicit.

---

### Building `texttools` — Step 1: Create the File Structure

Let's build our package from scratch. Run the cells below in sequence.


```python
import os
import pathlib

# Build the package inside a temporary working directory
# so it does not interfere with this notebook environment.

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



```python
# src/texttools/core.py - the actual utility functions

core_code = "\"\"\"Core text utility functions for texttools.\"\"\"\n\n\ndef word_count(text: str) -> dict:\n    \"\"\"Count the frequency of each word in a string.\n\n    Args:\n        text: The input string to analyse.\n\n    Returns:\n        A dictionary mapping each word (lowercased) to its count.\n\n    Example:\n        >>> word_count(\"the cat sat on the mat\")\n        {'the': 2, 'cat': 1, 'sat': 1, 'on': 1, 'mat': 1}\n    \"\"\"\n    words = text.lower().split()\n    counts: dict = {}\n    for word in words:\n        # Strip basic punctuation\n        word = word.strip(\".,!?;:'\")\n        if word:\n            counts[word] = counts.get(word, 0) + 1\n    return counts\n\n\ndef reverse_words(text: str) -> str:\n    \"\"\"Reverse the order of words in a string.\n\n    Args:\n        text: The input string.\n\n    Returns:\n        A new string with word order reversed.\n\n    Example:\n        >>> reverse_words(\"Hello World\")\n        'World Hello'\n    \"\"\"\n    return \" \".join(reversed(text.split()))\n\n\ndef title_case_smart(text: str) -> str:\n    \"\"\"Convert a string to title case, skipping common short words.\n\n    Short connector words (a, an, the, and, but, or, for, nor, on,\n    at, to, by, in, of, up) remain lowercase unless they are the\n    first or last word.\n\n    Args:\n        text: The input string.\n\n    Returns:\n        A title-cased string respecting common style guidelines.\n\n    Example:\n        >>> title_case_smart(\"the lord of the rings\")\n        'The Lord of the Rings'\n    \"\"\"\n    SKIP = {\"a\", \"an\", \"the\", \"and\", \"but\", \"or\", \"for\", \"nor\",\n            \"on\", \"at\", \"to\", \"by\", \"in\", \"of\", \"up\"}\n    words = text.lower().split()\n    result = []\n    for i, word in enumerate(words):\n        if i == 0 or i == len(words) - 1 or word not in SKIP:\n            result.append(word.capitalize())\n        else:\n            result.append(word)\n    return \" \".join(result)\n"

(BASE / "src" / "texttools" / "core.py").write_text(core_code)
print("core.py written.")
```

    core.py written.



```python
# src/texttools/__init__.py - the public API

init_code = "\"\"\"texttools - a small text utility library.\"\"\"\n\n__version__ = \"0.1.0\"\n\nfrom texttools.core import word_count, reverse_words, title_case_smart\n\n__all__ = [\"word_count\", \"reverse_words\", \"title_case_smart\"]\n"

(BASE / "src" / "texttools" / "__init__.py").write_text(init_code)
print("__init__.py written.")
```

    __init__.py written.


---

## Section 3 — `pyproject.toml` Deep Dive

`pyproject.toml` is the single source of truth for your package. It replaced the older `setup.py` and `setup.cfg` approach.

It has three main sections:

### `[build-system]`

Tells pip **how** to build your package. We use `setuptools`:

```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"
```

### `[project]`

Describes **what** your package is:

```toml
[project]
name = "texttools"
version = "0.1.0"
description = "A small text utility library"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
dependencies = []

classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
```

### `[project.scripts]`

Defines CLI commands (covered in Section 5):


```python
[project.scripts]
texttools = "texttools.cli:main"
#  command     module   function
```

### `[tool.setuptools.packages.find]`

Tells setuptools where to find your package — critical for the `src/` layout:


```python
[tool.setuptools.packages.find]
where = ["src"]
```


```python
# Write the pyproject.toml for texttools

pyproject = "[build-system]\nrequires = [\"setuptools>=42\", \"wheel\"]\nbuild-backend = \"setuptools.build_meta\"\n\n[project]\nname = \"texttools\"\nversion = \"0.1.0\"\ndescription = \"A small text utility library for word analysis and formatting\"\nauthors = [{name = \"Your Name\", email = \"you@example.com\"}]\nreadme = \"README.md\"\nrequires-python = \">=3.8\"\nlicense = {text = \"MIT\"}\ndependencies = []\n\nclassifiers = [\n    \"Programming Language :: Python :: 3\",\n    \"License :: OSI Approved :: MIT License\",\n    \"Operating System :: OS Independent\",\n]\n\n[project.scripts]\ntexttools = \"texttools.cli:main\"\n\n[tool.setuptools.packages.find]\nwhere = [\"src\"]\n"

(BASE / "pyproject.toml").write_text(pyproject)
print("pyproject.toml written.")
```

    pyproject.toml written.



```python
# Write a minimal README.md (referenced by pyproject.toml)

readme = "# texttools\n\nA small text utility library for word analysis and formatting.\n\n## Installation\n\n```bash\npip install texttools\n```\n\n## Usage\n\n```python\nfrom texttools import word_count, reverse_words, title_case_smart\n\nprint(word_count(\"the cat sat on the mat\"))\n# {'the': 2, 'cat': 1, 'sat': 1, 'on': 1, 'mat': 1}\n\nprint(reverse_words(\"Hello World\"))\n# 'World Hello'\n\nprint(title_case_smart(\"the lord of the rings\"))\n# 'The Lord of the Rings'\n```\n\n## CLI\n\n```bash\ntexttools count \"the cat sat on the mat\"\ntexttools reverse \"Hello World\"\ntexttools titlecase \"the lord of the rings\"\n```\n"

(BASE / "README.md").write_text(readme)
print("README.md written.")
```

    README.md written.


---

## Section 4 — Installing Locally with `pip install -e .`

Before publishing to PyPI, you want to use and test your package locally. The `-e` flag stands for **editable install**.

### Editable Install vs Regular Install

| Mode | Command | How it works |
|----|----|----|
| Regular | `pip install .` | Copies files into `site-packages` — changes require reinstall |
| Editable | `pip install -e .` | Links to your source — changes are reflected immediately |

**Editable mode is the standard workflow during development.**

### How It Works Under the Hood

```
pip install -e texttools_project/
     |
     v
reads pyproject.toml
     |
     v
creates a .pth file in site-packages pointing to src/
     |
     v
Python can now find 'import texttools'
```


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


---

## Section 5 — Entry Points: Creating CLI Commands

Entry points let users run your package as a command from the terminal:

```bash
$ texttools count "the cat sat on the mat"
cat: 1
mat: 1
on:  1
sat: 1
the: 2
```

### How It Works

When pip installs your package, it reads `[project.scripts]` in `pyproject.toml`:


```python
[project.scripts]
texttools = "texttools.cli:main"
#  command     module   function
```

pip creates a small wrapper executable (`texttools`) in the system `bin/` directory that calls `texttools.cli.main()`.

### Writing the CLI Module

The `cli.py` module uses `argparse` to parse command-line arguments.


```python
# src/texttools/cli.py - command-line interface

cli_code = "\"\"\"Command-line interface for texttools.\"\"\"\n\nimport argparse\nimport sys\nfrom texttools.core import word_count, reverse_words, title_case_smart\n\n\ndef main() -> None:\n    \"\"\"Entry point for the texttools CLI.\"\"\"\n    parser = argparse.ArgumentParser(\n        prog=\"texttools\",\n        description=\"Text utility commands\",\n    )\n\n    subparsers = parser.add_subparsers(dest=\"command\", required=True)\n\n    # count command\n    count_parser = subparsers.add_parser(\"count\", help=\"Count word frequencies\")\n    count_parser.add_argument(\"text\", help=\"Text to analyse\")\n\n    # reverse command\n    reverse_parser = subparsers.add_parser(\"reverse\", help=\"Reverse word order\")\n    reverse_parser.add_argument(\"text\", help=\"Text to reverse\")\n\n    # titlecase command\n    title_parser = subparsers.add_parser(\"titlecase\", help=\"Smart title case\")\n    title_parser.add_argument(\"text\", help=\"Text to convert\")\n\n    args = parser.parse_args()\n\n    if args.command == \"count\":\n        counts = word_count(args.text)\n        for word, n in sorted(counts.items()):\n            print(f\"{word}: {n}\")\n\n    elif args.command == \"reverse\":\n        print(reverse_words(args.text))\n\n    elif args.command == \"titlecase\":\n        print(title_case_smart(args.text))\n\n\nif __name__ == \"__main__\":\n    main()\n"

(BASE / "src" / "texttools" / "cli.py").write_text(cli_code)
print("cli.py written.")

# Reinstall to register the entry point
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-e", str(BASE), "--quiet"],
    capture_output=True,
    text=True
)
print("Package reinstalled." if result.returncode == 0 else result.stderr)

# Ensure src/ stays on path
if src_path not in sys.path:
    sys.path.insert(0, src_path)
```

    cli.py written.
    Package reinstalled.



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


> **Note on `if __name__ == "__main__"`:**
>
> This guard lets you run the module directly with `python -m texttools.cli`. Entry points call `main()` directly — the guard is for manual invocation during development.

---

## Section 6 — Testing the Installed Package

A critical point: **tests should run against the installed package, not the local source files.** This is exactly what the `src/` layout guarantees.

### Test Structure

```
tests/
+-- test_core.py
```

Note: **no `__init__.py` in `tests/`**. pytest does not need it, and omitting it avoids import conflicts.


```python
# Write the test file

test_code = "\"\"\"Tests for texttools.core\"\"\"\n\nimport pytest\nfrom texttools import word_count, reverse_words, title_case_smart\n\n\nclass TestWordCount:\n    def test_basic_count(self):\n        result = word_count(\"the cat sat on the mat\")\n        assert result[\"the\"] == 2\n        assert result[\"cat\"] == 1\n\n    def test_case_insensitive(self):\n        result = word_count(\"Python python PYTHON\")\n        assert result[\"python\"] == 3\n\n    def test_strips_punctuation(self):\n        result = word_count(\"hello, world!\")\n        assert \"hello\" in result\n        assert \"world\" in result\n\n    def test_empty_string(self):\n        assert word_count(\"\") == {}\n\n\nclass TestReverseWords:\n    def test_basic_reverse(self):\n        assert reverse_words(\"Hello World\") == \"World Hello\"\n\n    def test_single_word(self):\n        assert reverse_words(\"Python\") == \"Python\"\n\n    def test_multiple_words(self):\n        assert reverse_words(\"one two three\") == \"three two one\"\n\n\nclass TestTitleCaseSmart:\n    def test_short_words_lowercase(self):\n        result = title_case_smart(\"the lord of the rings\")\n        assert result == \"The Lord of the Rings\"\n\n    def test_first_word_always_capitalised(self):\n        result = title_case_smart(\"of mice and men\")\n        assert result.startswith(\"Of\")\n\n    def test_last_word_always_capitalised(self):\n        result = title_case_smart(\"the cat in the hat\")\n        assert result.endswith(\"Hat\")\n\n    def test_single_word(self):\n        assert title_case_smart(\"python\") == \"Python\"\n"

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
    [sys.executable, "-m", "pytest", str(BASE / "tests"), "-v"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print(result.stderr)
```

    [1m============================= test session starts ==============================[0m
    platform darwin -- Python 3.10.18, pytest-9.0.3, pluggy-1.6.0 -- /Users/aayush/micromamba/envs/stats/bin/python
    cachedir: .pytest_cache
    rootdir: /Users/aayush/Documents/Kings/python-training/prg400/texttools_project
    configfile: pyproject.toml
    [1mcollecting ... [0mcollected 11 items
    
    texttools_project/tests/test_core.py::TestWordCount::test_basic_count [32mPASSED[0m[32m [  9%][0m
    texttools_project/tests/test_core.py::TestWordCount::test_case_insensitive [32mPASSED[0m[32m [ 18%][0m
    texttools_project/tests/test_core.py::TestWordCount::test_strips_punctuation [32mPASSED[0m[32m [ 27%][0m
    texttools_project/tests/test_core.py::TestWordCount::test_empty_string [32mPASSED[0m[32m [ 36%][0m
    texttools_project/tests/test_core.py::TestReverseWords::test_basic_reverse [32mPASSED[0m[32m [ 45%][0m
    texttools_project/tests/test_core.py::TestReverseWords::test_single_word [32mPASSED[0m[32m [ 54%][0m
    texttools_project/tests/test_core.py::TestReverseWords::test_multiple_words [32mPASSED[0m[32m [ 63%][0m
    texttools_project/tests/test_core.py::TestTitleCaseSmart::test_short_words_lowercase [32mPASSED[0m[32m [ 72%][0m
    texttools_project/tests/test_core.py::TestTitleCaseSmart::test_first_word_always_capitalised [32mPASSED[0m[32m [ 81%][0m
    texttools_project/tests/test_core.py::TestTitleCaseSmart::test_last_word_always_capitalised [32mPASSED[0m[32m [ 90%][0m
    texttools_project/tests/test_core.py::TestTitleCaseSmart::test_single_word [32mPASSED[0m[32m [100%][0m
    
    [32m============================== [32m[1m11 passed[0m[32m in 0.01s[0m[32m ==============================[0m


---

## Section 7 — Building a Distribution

When you are ready to share your package, build it into a distributable format:

| Format | Extension | Description |
|----|----|----|
| Wheel | `.whl` | Binary distribution — fast to install, most common |
| Source distribution | `.tar.gz` | Source code archive — pip builds it on the user's machine |

Always publish **both**. pip prefers wheels; the source distribution is a fallback.

### The `build` Tool

`python -m build` reads your `pyproject.toml` and produces both formats in a `dist/` directory:

```bash
dist/
+-- texttools-0.1.0-py3-none-any.whl
+-- texttools-0.1.0.tar.gz
```

### Wheel Filename Anatomy

```
texttools - 0.1.0 - py3 - none - any .whl
^           ^       ^     ^      ^
package     version py   abi    platform

py3   = works with Python 3
none  = no ABI dependency (pure Python)
any   = works on any OS
```


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
    text=True
)

output = result.stdout
print(output[-1500:] if len(output) > 1500 else output)
if result.returncode != 0:
    print("STDERR:", result.stderr[-1000:])
```

    ttools.egg-info/top_level.txt
    reading manifest file 'src/texttools.egg-info/SOURCES.txt'
    writing manifest file 'src/texttools.egg-info/SOURCES.txt'
    installing to build/bdist.macosx-11.0-arm64/wheel
    running install
    running install_lib
    creating build/bdist.macosx-11.0-arm64/wheel
    creating build/bdist.macosx-11.0-arm64/wheel/texttools
    copying build/lib/texttools/__init__.py -> build/bdist.macosx-11.0-arm64/wheel/./texttools
    copying build/lib/texttools/core.py -> build/bdist.macosx-11.0-arm64/wheel/./texttools
    copying build/lib/texttools/cli.py -> build/bdist.macosx-11.0-arm64/wheel/./texttools
    running install_egg_info
    Copying src/texttools.egg-info to build/bdist.macosx-11.0-arm64/wheel/./texttools-0.1.0-py3.10.egg-info
    running install_scripts
    creating build/bdist.macosx-11.0-arm64/wheel/texttools-0.1.0.dist-info/WHEEL
    creating '/Users/aayush/Documents/Kings/python-training/prg400/texttools_project/dist/.tmp-ivcv_32v/texttools-0.1.0-py3-none-any.whl' and adding 'build/bdist.macosx-11.0-arm64/wheel' to it
    adding 'texttools/__init__.py'
    adding 'texttools/cli.py'
    adding 'texttools/core.py'
    adding 'texttools-0.1.0.dist-info/METADATA'
    adding 'texttools-0.1.0.dist-info/WHEEL'
    adding 'texttools-0.1.0.dist-info/entry_points.txt'
    adding 'texttools-0.1.0.dist-info/top_level.txt'
    adding 'texttools-0.1.0.dist-info/RECORD'
    removing build/bdist.macosx-11.0-arm64/wheel
    [1m[92mSuccessfully built [4mtexttools-0.1.0.tar.gz[0m[1m[92m and [4mtexttools-0.1.0-py3-none-any.whl[0m[1m[92m[0m



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


---

## Section 8 — Publishing to TestPyPI

**PyPI** (the Python Package Index) is the official registry — `pip install` downloads from here.

**TestPyPI** is a separate, safe sandbox for testing uploads. Always test there before publishing to real PyPI.

### Before You Publish

1.  Create an account at [test.pypi.org](https://test.pypi.org)
2.  Generate an API token: Account Settings → API Tokens
3.  Install `twine`: `pip install twine`

### The Workflow

```
Build          ->   Validate        ->   Upload
python -m build    twine check          twine upload
                   dist/*
```

### Step 1 — Validate Before Uploading

`twine check` verifies your metadata is well-formed and the README renders correctly on PyPI.


```python
# Install twine
subprocess.run(
    [sys.executable, "-m", "pip", "install", "twine", "--quiet"],
    capture_output=True
)

import glob as glob_module
dist_files = glob_module.glob(str(BASE / "dist" / "*"))

result = subprocess.run(
    [sys.executable, "-m", "twine", "check"] + dist_files,
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr)
```

    Checking texttools_project/dist/texttools-0.1.0-py3-none-any.whl: [32mPASSED[0m
    Checking texttools_project/dist/texttools-0.1.0.tar.gz: [32mPASSED[0m


### Step 2 — Upload to TestPyPI

**This is not auto-executed** — you need a real TestPyPI account and token.

```bash
# Run in your terminal
twine upload --repository testpypi dist/*
```

When prompted: - Username: `__token__` (literally) - Password: your API token (starts with `pypi-`)

Or use a `.pypirc` config file:


```python
# ~/.pypirc
[testpypi]
username = __token__
password = pypi-your-token-here
```

### Step 3 — Install From TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ texttools
```

### Step 4 — Publish to Real PyPI

```bash
twine upload dist/*
pip install texttools
```

---

## Section 9 — Versioning Best Practices

### Semantic Versioning (SemVer)

The standard for Python packages is **SemVer**: `MAJOR.MINOR.PATCH`

```
  1  .  4  .  2
  ^     ^     ^
MAJOR MINOR PATCH
```

| Part      | Increment when...                            | Example             |
|-----------|----------------------------------------------|---------------------|
| **MAJOR** | You break backwards compatibility            | `1.0.0` -> `2.0.0` |
| **MINOR** | You add functionality (backwards-compatible) | `1.0.0` -> `1.1.0` |
| **PATCH** | You fix a bug (backwards-compatible)         | `1.0.0` -> `1.0.1` |

**`0.x.y`** versions (like `0.1.0`) signal that the API is not yet stable.

---

### The Single Source of Truth Problem

Version numbers appear in two places:

1.  `pyproject.toml` -> `version = "0.1.0"`
2.  `src/texttools/__init__.py` -> `__version__ = "0.1.0"`

If you update one and forget the other, they diverge. Two clean solutions:

**Option A — Read from installed metadata at runtime (Python 3.8+):**


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


**Option B — Keep `__version__` in `__init__.py`, read it in `pyproject.toml`:**

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "texttools.__version__"}
```

With this, `pyproject.toml` reads the version from your `__init__.py` — one place to change it.

---

### Bumping Versions

```
1. Update version in pyproject.toml (and __init__.py if applicable)
2. git commit -m "bump version to 0.2.0"
3. git tag v0.2.0
4. python -m build
5. twine upload dist/*
```

> **Important:** PyPI does not allow re-uploading the same version.

---

## Section 10 — Full Package Checklist

```
Structure
  [ ] src/<package>/ layout with __init__.py
  [ ] __version__ defined (or using importlib.metadata)
  [ ] tests/ directory with no __init__.py
  [ ] README.md with installation and usage examples

pyproject.toml
  [ ] name is unique (check PyPI first)
  [ ] version follows SemVer
  [ ] description is a single informative sentence
  [ ] requires-python set correctly
  [ ] dependencies listed (even if empty)
  [ ] classifiers added
  [ ] [tool.setuptools.packages.find] where = ["src"] set

Quality
  [ ] All functions have docstrings
  [ ] Tests cover happy path and edge cases
  [ ] twine check passes with no warnings

Publishing
  [ ] Tested on TestPyPI first
  [ ] Git tag created for this version
  [ ] No secrets or credentials in the code
```

---

## Challenge — Build Your Own Package

Build a distributable package called **`numtools`** (or choose your own name) from scratch.

### Requirements

1.  Use the `src/` layout
2.  Have a proper `pyproject.toml` with all required fields
3.  Expose at least **3 functions** in its public API via `__init__.py`
4.  Have a **CLI entry point** with at least 2 subcommands
5.  Include **tests** covering each function
6.  Pass `twine check` after building

### Suggested Function Ideas

| Theme | Possible Functions |
|----|----|
| Numbers | `is_prime(n)`, `fibonacci(n)`, `factorial(n)` |
| Dates | `days_until(date)`, `is_weekend(date)`, `format_date(date, style)` |
| Files | `count_lines(path)`, `find_duplicates(dir)`, `largest_files(dir, n)` |
| Colours | `hex_to_rgb(hex)`, `rgb_to_hex(r,g,b)`, `contrast_ratio(c1, c2)` |

### Starter Structure

```
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


<details>
<summary>Hint - pyproject.toml skeleton</summary>

```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "numtools"
version = "0.1.0"
description = "YOUR DESCRIPTION HERE"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
dependencies = []

[project.scripts]
numtools = "numtools.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

</details>

<details>
<summary>Hint - is_prime() implementation</summary>

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

---

## Summary

| Concept | Key Takeaway |
|----|----|
| **`src/` layout** | Prevents local source from shadowing the installed package |
| **`__init__.py`** | Defines the public API; holds `__version__` |
| **`pyproject.toml`** | Single config for metadata, build system, and tooling |
| **Editable install** | `pip install -e .` — changes are live without reinstalling |
| **Entry points** | `[project.scripts]` maps a terminal command to a Python function |
| **`python -m build`** | Produces `.whl` and `.tar.gz` in `dist/` |
| **`twine`** | Validates and uploads distributions to PyPI/TestPyPI |
| **SemVer** | `MAJOR.MINOR.PATCH` — be intentional about which number you bump |

---

### Further Reading

- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
- [pyproject.toml specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [TestPyPI](https://test.pypi.org)
- [setuptools documentation](https://setuptools.pypa.io/en/latest/)
