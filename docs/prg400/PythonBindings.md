# Python Bindings: Connecting Python to C/C++

Python is quick to write but slow to run. C and C++ are the opposite. In this notebook you'll learn the main ways to call C and C++ code from Python, so you can get the best of both: write most of your program in Python and hand the heavy lifting to compiled code.

### Learning Objectives

By the end of this notebook you will be able to:

1. Explain what Python bindings are and why libraries like NumPy use them
2. Call C functions from Python with `ctypes`
3. Use `cffi` in ABI mode (load a library) and API mode (compile C code)
4. Write a small C extension module with the Python C API
5. Expose C++ functions and classes to Python with `pybind11`
6. Speed up Python code with Cython type declarations
7. Pass structs and callbacks between Python and C
8. Pick the right binding approach for a given job

### Prerequisites

- Python 3.10 or newer, and comfort with functions and classes
- Basic C: types, pointers, arrays and how to compile a file
- A **C/C++ compiler**:
    - **macOS:** run `xcode-select --install`. This gives you `clang`; the `gcc` and `c++` commands used below are aliases for it.
    - **Linux:** install `gcc`, `g++` and the Python headers, e.g. `sudo apt install build-essential python3-dev`.
    - **Windows:** the easiest path is WSL (then follow the Linux steps). For native Windows you need MinGW-w64 `gcc` for the `ctypes`/`cffi` examples and the "Microsoft C++ Build Tools" for extension modules. The `!gcc` / `!c++` commands here are written for macOS and Linux.
- Python packages: `cffi`, `pybind11`, `cython` and `setuptools` (the install cells below take care of them)

### How to Use This Notebook

- Run the cells **from top to bottom**. Later cells reuse libraries and variables built earlier (`lib_name`, `ctypes_lib`, ...).
- Cells starting with `%%writefile` save C/C++ source to disk; the cell after usually compiles it. All generated files land in the notebook's folder, and the **Cleanup** section at the end removes them.
- **Try it** and **Exercise** cells are for you. Write your answer first, then open *Show solution* to compare.
- Each section ends with a **Quick recap**. Read only the recaps when revising before an exam.

---

## Why Python Bindings?

Python is easy to write, but a pure Python loop is often 10 to 100 times slower than the same loop in C. A **binding** is the glue that lets Python call code written in another language. With bindings you can:

- **Speed up** the slow parts of a program (number crunching, image processing)
- **Reuse** existing C/C++ libraries instead of rewriting them (OpenSSL, SQLite, system APIs)
- **Reach** hardware and operating-system features that pure Python can't
- **Wrap** an old C codebase in a friendly Python interface

### Real-World Examples

You've probably already used bindings without noticing:

| Python Library | Underlying C/C++ Code            |
|----------------|----------------------------------|
| NumPy          | C and Fortran numerical routines |
| TensorFlow     | C++ computation engine           |
| Pillow (PIL)   | C image decoding libraries       |
| sqlite3        | SQLite C library                 |
| OpenCV (cv2)   | C++ computer vision library      |

### How Python Talks to C/C++

```
 Your Python Code
       |
       v
 [Binding Layer]   <-- ctypes, cffi, C API, pybind11, Cython
       |
       v
 Compiled C/C++ Code (.so / .dll / .dylib)
       |
       v
 Hardware (CPU, GPU, etc.)
```

The binding layer's job is translation: it turns Python objects into C values on the way in, and C values back into Python objects on the way out.

### Overview of Binding Approaches

| Approach | Language | Difficulty | Use Case |
|----|----|----|----|
| `ctypes` | C | Easy | Call existing shared libraries |
| `cffi` | C | Easy-Medium | Modern alternative to ctypes |
| Python C API | C | Hard | Maximum control, build extension modules |
| `pybind11` | C++ | Medium | Modern C++ bindings with clean syntax |
| Cython | C/C++ | Medium | Write C extensions using Python-like syntax |
| SWIG | C/C++ | Medium | Auto-generate bindings for multiple languages |

We'll go through them roughly in this order, from "no compiling Python-side at all" to "build a real extension module".

**Quick recap**

- A binding lets Python call compiled C/C++ code.
- We use bindings for speed, to reuse existing libraries, and to reach OS/hardware features.
- Many popular libraries (NumPy, Pillow, sqlite3) are thin Python layers over C or C++.

---

## 1. `ctypes`: Calling C from Python

`ctypes` ships with Python, so there's nothing to install. It loads a **shared library** (`.so` on Linux, `.dylib` on macOS, `.dll` on Windows) and lets you call its functions directly.

Things to know before we start:

- The C code must already be compiled. `ctypes` doesn't compile anything for you.
- You have to tell `ctypes` the argument types and return type of each function. It can't read C header files.
- If you get the types wrong, you get wrong answers or a crash, not a friendly error.

### 1.1 Creating a Simple C Library

First we need a C library to call. The next cell saves a small C file with five functions; the one after compiles it into a shared library.


```python
%%writefile mylib.c
#include <stdio.h>
#include <math.h>

// A simple function: add two integers
int add(int a, int b) {
    return a + b;
}

// Multiply two doubles
double multiply(double a, double b) {
    return a * b;
}

// Compute factorial iteratively
long long factorial(int n) {
    long long result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

// Modify an array in-place: square each element
void square_array(double* arr, int size) {
    for (int i = 0; i < size; i++) {
        arr[i] = arr[i] * arr[i];
    }
}

// Return a greeting string
const char* greet(const char* name) {
    static char buffer[256];
    snprintf(buffer, sizeof(buffer), "Hello, %s! Welcome from C.", name);
    return buffer;
}

```

    Writing mylib.c


Now compile it. The command is slightly different on each operating system, so we pick it with `platform.system()` and remember the file name in `lib_name` for later cells.

On macOS and Linux this is the same as typing `gcc -shared -fPIC -o mylib.so mylib.c` in a terminal. `-shared` asks for a library instead of a program, and `-fPIC` makes the code work no matter where in memory it gets loaded.


```python
import subprocess
import sys
import platform

# Step 2: Compile the C code into a shared library
if platform.system() == "Darwin":  # macOS
    print("Compiling for macOS...")
    cmd = ["gcc", "-shared", "-o", "mylib.dylib", "-fPIC", "mylib.c"]
    lib_name = "mylib.dylib"
elif platform.system() == "Linux":
    print("Compiling for Linux...")
    cmd = ["gcc", "-shared", "-o", "mylib.so", "-fPIC", "mylib.c"]
    lib_name = "mylib.so"
else:  # Windows
    print("Compiling for Windows...")
    cmd = ["gcc", "-shared", "-o", "mylib.dll", "mylib.c"]
    lib_name = "mylib.dll"

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    print(f"Compiled successfully: {lib_name}")
else:
    print(f"Compilation failed:\n{result.stderr}")
```

    Compiling for macOS...
    Compiled successfully: mylib.dylib


### 1.2 Loading and Calling C Functions with `ctypes`

`ctypes.CDLL` loads the library. After that, every C function is available as an attribute of `lib`.


```python
import ctypes
import os

# Load the shared library
lib = ctypes.CDLL(os.path.abspath(lib_name))

# --- Calling add(int, int) -> int ---
# By default, ctypes assumes every argument and the return value are C ints
result = lib.add(10, 25)
print(f"add(10, 25) = {result}")

# factorial really returns a long long, but ctypes doesn't know that yet.
# For small results the int guess happens to work...
print(f"factorial(5) = {lib.factorial(5)}")
```

    add(10, 25) = 35
    factorial(5) = 120


`add` worked with no setup because "everything is an `int`" is exactly what `ctypes` assumes. As soon as a function uses other types, you must spell them out with `argtypes` (a list of argument types) and `restype` (the return type).


```python
# --- Calling multiply(double, double) -> double ---
# For non-int types, we MUST specify argtypes and restype
lib.multiply.argtypes = [ctypes.c_double, ctypes.c_double]
lib.multiply.restype = ctypes.c_double

result = lib.multiply(3.14, 2.0)
print(f"multiply(3.14, 2.0) = {result}")
```

    multiply(3.14, 2.0) = 6.28



```python
# --- Calling factorial(int) -> long long ---
lib.factorial.argtypes = [ctypes.c_int]
lib.factorial.restype = ctypes.c_longlong

for n in [5, 10, 20]:
    print(f"factorial({n}) = {lib.factorial(n)}")
```

    factorial(5) = 120
    factorial(10) = 3628800
    factorial(20) = 2432902008176640000


**What just happened?** `factorial(20)` is about 2.4 × 10¹⁸, far too big for a 32-bit `int`. Because we set `restype = ctypes.c_longlong`, `ctypes` reads all 64 bits of the answer. Without that line, `factorial(20)` would silently come back as a wrong, truncated number. That's why the rule is: **always set `argtypes` and `restype`**, even when the default seems to work.

### 1.3 Working with Pointers and Arrays

A C function that takes `double*` wants the address of a block of doubles. In `ctypes`, `ctypes.c_double * 5` is a *type* meaning "array of 5 doubles", and calling it creates one.


```python
# --- Calling square_array(double*, int) -> void ---
# We need to create a C-compatible array from Python

lib.square_array.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
lib.square_array.restype = None  # void return

# Create a C array of 5 doubles
ArrayType = ctypes.c_double * 5
data = ArrayType(1.0, 2.0, 3.0, 4.0, 5.0)

print(f"Before: {list(data)}")

lib.square_array(data, 5)

print(f"After:  {list(data)}")
# The C function modified our array in-place!
```

    Before: [1.0, 2.0, 3.0, 4.0, 5.0]
    After:  [1.0, 4.0, 9.0, 16.0, 25.0]


The C function changed our array **in place**: C received a pointer to the same memory that `data` uses, so no copy came back. This is how most C functions return large results.

### 1.4 Working with Strings

C strings are just bytes ending in a zero byte, so on the Python side we pass `bytes` (`b"..."` or `.encode()`) and decode what comes back.


```python
# --- Calling greet(const char*) -> const char* ---
lib.greet.argtypes = [ctypes.c_char_p]
lib.greet.restype = ctypes.c_char_p

# C strings are bytes in Python, so we encode
name = "Aayush".encode("utf-8")
greeting = lib.greet(name)
print(greeting.decode("utf-8"))
```

    Hello, Aayush! Welcome from C.


### 1.5 `ctypes` Type Mapping Reference

| C Type      | `ctypes` Type    | Python Type       |
|-------------|------------------|-------------------|
| `int`       | `c_int`          | `int`             |
| `long`      | `c_long`         | `int`             |
| `long long` | `c_longlong`     | `int`             |
| `size_t`    | `c_size_t`       | `int`             |
| `float`     | `c_float`        | `float`           |
| `double`    | `c_double`       | `float`           |
| `char`      | `c_char`         | `bytes` (1 char)  |
| `char*`     | `c_char_p`       | `bytes` or `None` |
| `void*`     | `c_void_p`       | `int` or `None`   |
| `int*`      | `POINTER(c_int)` | `ctypes` array    |
| `bool`      | `c_bool`         | `bool`            |

### 1.6 Calling System Libraries with `ctypes`

You don't have to write your own C code to use `ctypes`. The C libraries that come with your operating system work too. Here we call `sqrt` and `pow` from the C math library.


```python
import ctypes
import ctypes.util

# Find and load the C math library
libm_path = ctypes.util.find_library("m")
print(f"Math library path: {libm_path}")

if libm_path:
    libm = ctypes.CDLL(libm_path)
else:
    # On some systems, math functions are in libc
    libm = ctypes.CDLL(None)

# Call the C sqrt function
libm.sqrt.argtypes = [ctypes.c_double]
libm.sqrt.restype = ctypes.c_double

print(f"C sqrt(144.0) = {libm.sqrt(144.0)}")

# Call the C pow function
libm.pow.argtypes = [ctypes.c_double, ctypes.c_double]
libm.pow.restype = ctypes.c_double

print(f"C pow(2, 10) = {libm.pow(2.0, 10.0)}")
```

    Math library path: /usr/lib/libm.dylib
    C sqrt(144.0) = 12.0
    C pow(2, 10) = 1024.0


`ctypes.util.find_library("m")` searches the system for the math library (`libm`). On some systems the math functions live inside the main C library instead, so we fall back to `ctypes.CDLL(None)`, which means "the C library this Python process is already using".

### Try It: Call `strlen` with `ctypes`

Load the C standard library and call `strlen` to get the length of `b"Hello, World!"`.

Hint: `strlen` takes a `const char*` and returns a `size_t`. On macOS and Linux, `ctypes.CDLL(None)` gives you the C library; on Windows use `ctypes.cdll.msvcrt`.


```python
# Your code here:
# libc = ctypes.CDLL(None)  # loads the default C library

# libc.strlen.argtypes = [???]
# libc.strlen.restype = ???
# result = libc.strlen(b"Hello, World!")
# print(f"strlen = {result}")
```

<details markdown="1">
<summary>Show solution</summary>

```python
libc = ctypes.CDLL(None)  # Windows: ctypes.cdll.msvcrt

libc.strlen.argtypes = [ctypes.c_char_p]
libc.strlen.restype = ctypes.c_size_t
result = libc.strlen(b"Hello, World!")
print(f"strlen = {result}")  # strlen = 13
```

</details>

**Quick recap**

- `ctypes` is in the standard library and calls functions in an already-compiled shared library.
- Always set `argtypes` and `restype`; the default assumes `int` everywhere and can silently give wrong results.
- Arrays are made with `ctypes.c_double * n`; C can modify them in place.
- C strings are `bytes` in Python: encode before calling, decode the result.

---

## 2. `cffi`: C Foreign Function Interface

`cffi` does the same job as `ctypes`, but you describe the C functions using **real C declarations** instead of `ctypes` objects. It has two modes:

- **ABI mode:** load an existing shared library at runtime, just like `ctypes`.
- **API mode:** give `cffi` some C source code; it compiles it into a Python module for you.

Why people often prefer `cffi` over `ctypes`:

- You can copy declarations straight from a C header file.
- Error messages are clearer.
- API mode lets the C compiler check your types, which catches many mistakes before they turn into crashes.
- It's the recommended way to call C from PyPy.


```python
# Install cffi if needed
%pip install cffi -q
```

We use `%pip` rather than `!pip` so the package is installed into the same Python environment the notebook kernel is running in.

### 2.1 ABI Mode: Loading Existing Libraries

Here we load the same `mylib` we compiled for `ctypes`. Notice there is no `argtypes`/`restype` setup: the `cdef` declarations already contain all the type information.


```python
from cffi import FFI

ffi = FFI()

# Declare the C functions we want to call
# This looks like actual C header declarations!
ffi.cdef("""
    int add(int a, int b);
    double multiply(double a, double b);
    long long factorial(int n);
    void square_array(double* arr, int size);
    const char* greet(const char* name);
""")

# Load our compiled library
lib = ffi.dlopen(os.path.abspath(lib_name))

# Call functions -- much cleaner than ctypes!
print(f"add(15, 27) = {lib.add(15, 27)}")
print(f"multiply(2.5, 4.0) = {lib.multiply(2.5, 4.0)}")
print(f"factorial(12) = {lib.factorial(12)}")
```

    add(15, 27) = 42
    multiply(2.5, 4.0) = 10.0
    factorial(12) = 479001600



```python
# Working with arrays in cffi
arr = ffi.new("double[5]", [1.0, 2.0, 3.0, 4.0, 5.0])

print(f"Before: {[arr[i] for i in range(5)]}")

lib.square_array(arr, 5)

print(f"After:  {[arr[i] for i in range(5)]}")
```

    Before: [1.0, 2.0, 3.0, 4.0, 5.0]
    After:  [1.0, 4.0, 9.0, 16.0, 25.0]


`ffi.new("double[5]", [...])` allocates a C array and fills it. `cffi` frees it automatically when `arr` is no longer used.

When a C function returns `char*`, `cffi` gives you a pointer object. `ffi.string()` copies the characters into a Python `bytes` object:


```python
# Working with strings in cffi
result = lib.greet(b"Student")
print(ffi.string(result).decode("utf-8"))
```

    Hello, Student! Welcome from C.


### 2.2 API Mode: Compile C Code Inline

In API mode, `cffi` writes a small C wrapper around your code, runs the compiler and produces a real extension module (here called `_math_helpers`). The `cdef` part says what Python can see; `set_source` holds the actual C code. The compiler output below is long, and that's normal.


```python
from cffi import FFI

ffi_builder = FFI()

# Define the interface (what Python sees)
ffi_builder.cdef("""
    int fibonacci(int n);
    double distance(double x1, double y1, double x2, double y2);
""")

# Provide the actual C implementation
ffi_builder.set_source("_math_helpers", """
    #include <math.h>

    int fibonacci(int n) {
        if (n <= 1) return n;
        int a = 0, b = 1;
        for (int i = 2; i <= n; i++) {
            int temp = a + b;
            a = b;
            b = temp;
        }
        return b;
    }

    double distance(double x1, double y1, double x2, double y2) {
        return sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1));
    }
""",
    libraries=["m"]  # link against libm for sqrt
)

# Compile the extension module
ffi_builder.compile(verbose=True)
```

    generating ./_math_helpers.c
    the current directory is '/path/to/prg400'





    '/path/to/prg400/_math_helpers.cpython-312-darwin.so'



The build produced a file like `_math_helpers.cpython-312-darwin.so` in the current folder, so we can import it like any other module. It gives us its own `ffi` and `lib` objects.

> **Heads up:** this replaces the `ffi` and `lib` names from the ABI-mode example above. That's why later cells reload `mylib` under a new name.


```python
# Import and use the compiled module (it was built in the current folder)
from _math_helpers import ffi, lib

print(f"fibonacci(10) = {lib.fibonacci(10)}")
print(f"fibonacci(30) = {lib.fibonacci(30)}")

print(f"distance(0,0 -> 3,4) = {lib.distance(0, 0, 3, 4)}")
print(f"distance(1,2 -> 4,6) = {lib.distance(1, 2, 4, 6):.4f}")
```

    fibonacci(10) = 55
    fibonacci(30) = 832040
    distance(0,0 -> 3,4) = 5.0
    distance(1,2 -> 4,6) = 5.0000


### `ctypes` vs `cffi` Comparison

| Feature | `ctypes` | `cffi` |
|----|----|----|
| Part of stdlib | Yes | No (pip install) |
| Type declarations | Python objects (`c_int`, `c_double`) | C syntax (`int`, `double`) |
| Compilation support | No (ABI only) | Yes (API mode) |
| Error messages | Cryptic (segfaults) | Better error reporting |
| PyPy support | Limited | Excellent |
| Learning curve | Lower | Slightly higher |

**Quick recap**

- `cffi` describes C functions with ordinary C declarations in `ffi.cdef()`.
- ABI mode (`ffi.dlopen`) loads an existing library, like `ctypes`.
- API mode (`set_source` + `compile`) builds a real extension module from C source.
- Use `ffi.new()` to allocate C data and `ffi.string()` to read C strings.

---

## 3. Python C API: Writing Extension Modules

The **Python C API** is the C interface CPython itself is built on. With it you write C functions that take and return real Python objects. NumPy's core and many of the standard library modules (like `math`) are written this way.

Use it when:

- you need full control and the best possible performance
- you're building a library that needs tight integration with Python's internals

The downsides:

- It's the most work: lots of boilerplate for every function.
- You manage memory yourself with reference counts (`Py_INCREF` / `Py_DECREF`).
- Mistakes cause memory leaks or segfaults.
- It only works with CPython (not PyPy and friends).

In practice you'll usually reach for `pybind11` or Cython instead. We still look at the C API because every other tool generates this kind of code for you behind the scenes.

### 3.1 Anatomy of a C Extension Module

A C extension module has three parts:

1. **Function implementations:** the C functions that do the work
2. **Method table:** maps Python function names to those C functions
3. **Module definition:** describes the module to Python, plus an init function named `PyInit_<modulename>`

Read through the comments in the next cell; they walk through each part.


```python
%%writefile mymodule.c
#include <Python.h>

// ========================================
// Part 1: Function Implementations
// ========================================

// Every C function that will be callable from Python has the signature:
//   static PyObject* func_name(PyObject* self, PyObject* args)

static PyObject* mymodule_add(PyObject* self, PyObject* args) {
    int a, b;

    // Parse Python arguments: "ii" means two integers
    if (!PyArg_ParseTuple(args, "ii", &a, &b)) {
        return NULL;  // Raise TypeError on parse failure
    }

    // Return a Python int object
    return PyLong_FromLong(a + b);
}

static PyObject* mymodule_fibonacci(PyObject* self, PyObject* args) {
    int n;

    if (!PyArg_ParseTuple(args, "i", &n)) {
        return NULL;
    }

    if (n < 0) {
        PyErr_SetString(PyExc_ValueError, "n must be non-negative");
        return NULL;
    }

    long long a = 0, b = 1;
    for (int i = 0; i < n; i++) {
        long long temp = a + b;
        a = b;
        b = temp;
    }

    return PyLong_FromLongLong(a);
}

static PyObject* mymodule_sum_list(PyObject* self, PyObject* args) {
    PyObject* list_obj;

    // "O" means a single Python object
    if (!PyArg_ParseTuple(args, "O", &list_obj)) {
        return NULL;
    }

    // Verify it's actually a list
    if (!PyList_Check(list_obj)) {
        PyErr_SetString(PyExc_TypeError, "Expected a list");
        return NULL;
    }

    double total = 0.0;
    Py_ssize_t size = PyList_Size(list_obj);

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyList_GetItem(list_obj, i);  // Borrowed reference

        if (PyLong_Check(item)) {
            total += PyLong_AsDouble(item);
        } else if (PyFloat_Check(item)) {
            total += PyFloat_AsDouble(item);
        } else {
            PyErr_SetString(PyExc_TypeError, "List must contain only numbers");
            return NULL;
        }
    }

    return PyFloat_FromDouble(total);
}

// ========================================
// Part 2: Method Table
// ========================================

static PyMethodDef MyModuleMethods[] = {
    {"add",       mymodule_add,       METH_VARARGS, "Add two integers."},
    {"fibonacci", mymodule_fibonacci, METH_VARARGS, "Compute nth Fibonacci number."},
    {"sum_list",  mymodule_sum_list,  METH_VARARGS, "Sum a list of numbers."},
    {NULL, NULL, 0, NULL}  // Sentinel: marks end of table
};

// ========================================
// Part 3: Module Definition
// ========================================

static struct PyModuleDef mymodule = {
    PyModuleDef_HEAD_INIT,
    "mymodule",           // Module name
    "A sample C extension module for demonstration.",  // Docstring
    -1,                    // -1 means module keeps state in global variables
    MyModuleMethods        // Method table
};

// Module initialization function
// MUST be named PyInit_<modulename>
PyMODINIT_FUNC PyInit_mymodule(void) {
    return PyModule_Create(&mymodule);
}

```

    Writing mymodule.c


To compile an extension module we need the right compiler flags and the Python header files. `setuptools` knows all of this, so we write a tiny `setup.py` and let it do the work.


```python
%%writefile setup.py
from setuptools import setup, Extension

module = Extension(
    'mymodule',
    sources=['mymodule.c'],
)

setup(
    name='mymodule',
    version='1.0',
    description='A sample C extension module',
    ext_modules=[module],
)

```

    Writing setup.py



```python
import sys

# Build the extension module in the current folder.
# {sys.executable} makes sure we use the same Python as this notebook.
!{sys.executable} setup.py build_ext --inplace 2>&1 | tail -5
```

    running build_ext
    building 'mymodule' extension
    clang -fno-strict-overflow -Wsign-compare -Wunreachable-code -fno-common -dynamic -DNDEBUG -g -O3 -Wall -I/path/to/prg400/venv/include -I/opt/homebrew/opt/python@3.12/Frameworks/Python.framework/Versions/3.12/include/python3.12 -c mymodule.c -o build/temp.macosx-26.0-arm64-cpython-312/mymodule.o
    clang -bundle -undefined dynamic_lookup build/temp.macosx-26.0-arm64-cpython-312/mymodule.o -o build/lib.macosx-26.0-arm64-cpython-312/mymodule.cpython-312-darwin.so
    copying build/lib.macosx-26.0-arm64-cpython-312/mymodule.cpython-312-darwin.so -> 


`build_ext --inplace` puts the compiled module (e.g. `mymodule.cpython-312-darwin.so`) right next to the notebook, so a normal `import` finds it.


```python
# Use our C extension module!
import mymodule

print(f"mymodule.add(100, 200) = {mymodule.add(100, 200)}")
print(f"mymodule.fibonacci(10) = {mymodule.fibonacci(10)}")
print(f"mymodule.fibonacci(50) = {mymodule.fibonacci(50)}")
print(f"mymodule.sum_list([1, 2.5, 3, 4.5]) = {mymodule.sum_list([1, 2.5, 3, 4.5])}")
```

    mymodule.add(100, 200) = 300
    mymodule.fibonacci(10) = 55
    mymodule.fibonacci(50) = 12586269025
    mymodule.sum_list([1, 2.5, 3, 4.5]) = 11.0


Note that `fibonacci(50)` is 12,586,269,025, bigger than a 32-bit `int` can hold. It works because the C code uses `long long` and returns it with `PyLong_FromLongLong`.

Errors raised in C with `PyErr_SetString` arrive in Python as normal exceptions:


```python
# Error handling works too!
try:
    mymodule.fibonacci(-1)
except ValueError as e:
    print(f"Caught error: {e}")

try:
    mymodule.sum_list("not a list")
except TypeError as e:
    print(f"Caught error: {e}")

try:
    mymodule.sum_list([1, 2, "three"])
except TypeError as e:
    print(f"Caught error: {e}")
```

    Caught error: n must be non-negative
    Caught error: Expected a list
    Caught error: List must contain only numbers


### 3.2 `PyArg_ParseTuple` Format Codes

`PyArg_ParseTuple(args, "ii", &a, &b)` reads the Python arguments into C variables. The string says what types to expect:

| Code | C Type                        | Python Type                  |
|------|-------------------------------|------------------------------|
| `i`  | `int`                         | `int`                        |
| `l`  | `long`                        | `int`                        |
| `L`  | `long long`                   | `int`                        |
| `f`  | `float`                       | `float`                      |
| `d`  | `double`                      | `float`                      |
| `s`  | `const char*`                 | `str`                        |
| `O`  | `PyObject*`                   | any object                   |
| `O!` | `PyObject*` (with type check) | specific type                |
| <code>&#124;</code> | (none)             | marks the start of optional arguments |

### 3.3 Reference Counting: The Critical Concept

Every Python object keeps a count of how many places refer to it. When the count drops to zero, the object is freed. In Python this happens for you; in the C API **you** keep the count correct.

```c
// You got a NEW reference (you own it) -- must DECREF when done
PyObject* result = PyLong_FromLong(42);
// ... use result ...
Py_DECREF(result);  // Release your reference

// You got a BORROWED reference (someone else owns it) -- do NOT DECREF
PyObject* item = PyList_GetItem(list, 0);  // Borrowed!
// ... use item but do NOT Py_DECREF(item) ...
```

The rules:

- Functions that **create** objects give you a **new** reference. You must `Py_DECREF` it when you're done (or return it).
- Functions that **get** items from containers usually give you a **borrowed** reference. Don't `Py_DECREF` it.
- When your function returns an object, ownership passes to the caller.
- If you want to keep a borrowed reference for later, call `Py_INCREF` on it first.

Get this wrong in one direction and you leak memory; get it wrong in the other and Python frees an object you're still using.

**Quick recap**

- A C extension module has three parts: functions, a method table and a module definition with `PyInit_<name>`.
- `PyArg_ParseTuple` converts Python arguments to C; `PyLong_From...` / `PyFloat_From...` convert results back.
- Return `NULL` after `PyErr_SetString` to raise a Python exception.
- New references must be released with `Py_DECREF`; borrowed references must not.
- Build with `setuptools` (`setup.py build_ext --inplace`).

---

## 4. `pybind11`: Modern C++ Bindings

`pybind11` is a **header-only** C++ library for exposing C++ code to Python. "Header-only" means there's nothing to link: you `#include` it and compile. Compared with the raw C API, it removes almost all the boilerplate.

What you get:

- Short, readable binding code
- Automatic conversions between STL containers and Python types (`std::vector` ↔ `list`, `std::string` ↔ `str`, ...)
- Support for classes, inheritance, overloading and lambdas
- C++ exceptions turned into Python exceptions

It's currently the most popular way to bind C++ code (its successor `nanobind` works the same way).


```python
# Install pybind11
%pip install pybind11 -q
```

### 4.1 A Simple pybind11 Module

All the binding code lives in the `PYBIND11_MODULE` block at the bottom. Everything above it is ordinary C++ that knows nothing about Python.


```python
%%writefile mathtools.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>  // For automatic STL <-> Python conversions
#include <string>
#include <vector>
#include <numeric>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

// ---- Simple Functions ----

int add(int a, int b) {
    return a + b;
}

double hypotenuse(double a, double b) {
    return std::sqrt(a * a + b * b);
}

std::string repeat_string(const std::string& s, int n) {
    std::string result;
    for (int i = 0; i < n; i++) {
        result += s;
    }
    return result;
}

// ---- Working with STL Containers ----

// pybind11 automatically converts std::vector <-> Python list!
std::vector<int> range_vec(int start, int end) {
    std::vector<int> result;
    for (int i = start; i < end; i++) {
        result.push_back(i);
    }
    return result;
}

double dot_product(const std::vector<double>& a, const std::vector<double>& b) {
    if (a.size() != b.size()) {
        throw std::runtime_error("Vectors must have the same length");
    }
    return std::inner_product(a.begin(), a.end(), b.begin(), 0.0);
}

// ---- A C++ Class Exposed to Python ----

class Vector2D {
public:
    double x, y;

    Vector2D(double x = 0, double y = 0) : x(x), y(y) {}

    double magnitude() const {
        return std::sqrt(x * x + y * y);
    }

    Vector2D normalized() const {
        double mag = magnitude();
        if (mag == 0) throw std::runtime_error("Cannot normalize zero vector");
        return Vector2D(x / mag, y / mag);
    }

    Vector2D operator+(const Vector2D& other) const {
        return Vector2D(x + other.x, y + other.y);
    }

    double dot(const Vector2D& other) const {
        return x * other.x + y * other.y;
    }

    std::string repr() const {
        return "Vector2D(" + std::to_string(x) + ", " + std::to_string(y) + ")";
    }
};

// ---- Module Definition ----

PYBIND11_MODULE(mathtools, m) {
    m.doc() = "A C++ math utilities module built with pybind11";

    // Bind simple functions
    m.def("add", &add, "Add two integers",
          py::arg("a"), py::arg("b"));  // Named arguments!

    m.def("hypotenuse", &hypotenuse, "Compute hypotenuse",
          py::arg("a"), py::arg("b"));

    m.def("repeat_string", &repeat_string, "Repeat a string n times",
          py::arg("s"), py::arg("n") = 2);  // Default argument!

    m.def("range_vec", &range_vec, "Create a vector of integers",
          py::arg("start"), py::arg("end"));

    m.def("dot_product", &dot_product, "Compute dot product of two vectors",
          py::arg("a"), py::arg("b"));

    // Bind a C++ class
    py::class_<Vector2D>(m, "Vector2D")
        .def(py::init<double, double>(),   // Constructor
             py::arg("x") = 0, py::arg("y") = 0)
        .def_readwrite("x", &Vector2D::x)  // Public attributes
        .def_readwrite("y", &Vector2D::y)
        .def("magnitude", &Vector2D::magnitude)
        .def("normalized", &Vector2D::normalized)
        .def("dot", &Vector2D::dot, py::arg("other"))
        .def("__add__", &Vector2D::operator+)  // Python operator overloading!
        .def("__repr__", &Vector2D::repr);
}

```

    Writing mathtools.cpp


### 4.2 Compiling the Module

We compile with the C++ compiler directly. It needs two include folders (Python's headers and pybind11's headers), and the output file must end with Python's extension suffix (e.g. `.cpython-312-darwin.so`) so `import` can find it.

On macOS we also pass `-undefined dynamic_lookup`, which says "the Python functions you can't find yet will be provided by the Python process that loads this module". Linux doesn't need it.


```python
import platform
import sys
import sysconfig

import pybind11

include_flags = f"-I{sysconfig.get_paths()['include']} -I{pybind11.get_include()}"
ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
mac_flags = "-undefined dynamic_lookup" if platform.system() == "Darwin" else ""

print(f"Include flags: {include_flags}")
print(f"Extension suffix: {ext_suffix}")

# Compile
!c++ -O2 -shared -std=c++17 -fPIC {mac_flags} {include_flags} mathtools.cpp -o mathtools{ext_suffix}
```

    Include flags: -I/opt/homebrew/opt/python@3.12/Frameworks/Python.framework/Versions/3.12/include/python3.12 -I/path/to/prg400/venv/lib/python3.12/site-packages/pybind11/include
    Extension suffix: .cpython-312-darwin.so


No output after the two `print`s means the compile succeeded. For a real project you'd let `setuptools` or `scikit-build` run this command for you, but it's worth seeing it once by hand.

Now the module behaves like any Python module, including keyword and default arguments:


```python
import mathtools

# Simple functions
print(f"add(a=5, b=3) = {mathtools.add(a=5, b=3)}")
print(f"hypotenuse(3, 4) = {mathtools.hypotenuse(3, 4)}")
print(f"repeat_string('Ha', 3) = {mathtools.repeat_string('Ha', 3)}")
print(f"repeat_string('Hi') = {mathtools.repeat_string('Hi')}  (default n=2)")
```

    add(a=5, b=3) = 8
    hypotenuse(3, 4) = 5.0
    repeat_string('Ha', 3) = HaHaHa
    repeat_string('Hi') = HiHi  (default n=2)



```python
# STL containers converted automatically!
nums = mathtools.range_vec(1, 6)
print(f"range_vec(1, 6) = {nums}")
print(f"Type: {type(nums)}")

# Pass Python lists to C++ std::vector
dp = mathtools.dot_product([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
print(f"dot_product([1,2,3], [4,5,6]) = {dp}")
```

    range_vec(1, 6) = [1, 2, 3, 4, 5]
    Type: <class 'list'>
    dot_product([1,2,3], [4,5,6]) = 32.0


`range_vec` returned a C++ `std::vector<int>`, and `pybind11` turned it into a normal Python `list`. Going the other way, our Python lists became `std::vector<double>` for `dot_product`.

C++ classes work too. Because we bound `operator+` as `__add__` and `repr()` as `__repr__`, `Vector2D` objects support `+` and print nicely:


```python
# Using the C++ class from Python
v1 = mathtools.Vector2D(3, 4)
v2 = mathtools.Vector2D(1, 2)

print(f"v1 = {v1}")
print(f"v2 = {v2}")
print(f"v1.magnitude() = {v1.magnitude()}")
print(f"v1.normalized() = {v1.normalized()}")
print(f"v1 + v2 = {v1 + v2}")
print(f"v1.dot(v2) = {v1.dot(v2)}")

# Access attributes
print(f"v1.x = {v1.x}, v1.y = {v1.y}")
v1.x = 10
print(f"After v1.x = 10: {v1}")
```

    v1 = Vector2D(3.000000, 4.000000)
    v2 = Vector2D(1.000000, 2.000000)
    v1.magnitude() = 5.0
    v1.normalized() = Vector2D(0.600000, 0.800000)
    v1 + v2 = Vector2D(4.000000, 6.000000)
    v1.dot(v2) = 11.0
    v1.x = 3.0, v1.y = 4.0
    After v1.x = 10: Vector2D(10.000000, 4.000000)



```python
# C++ exceptions become Python exceptions!
try:
    mathtools.dot_product([1, 2], [1, 2, 3])
except RuntimeError as e:
    print(f"Caught: {e}")

try:
    zero = mathtools.Vector2D(0, 0)
    zero.normalized()
except RuntimeError as e:
    print(f"Caught: {e}")
```

    Caught: Vectors must have the same length
    Caught: Cannot normalize zero vector


A `std::runtime_error` thrown in C++ arrives in Python as a `RuntimeError`, with the same message.

**Quick recap**

- `pybind11` is a header-only C++ library; all binding code lives in `PYBIND11_MODULE`.
- `m.def(...)` binds functions; `py::arg` gives keyword and default arguments.
- `py::class_<T>` binds classes, including attributes, methods and operators.
- STL containers and C++ exceptions are converted to Python types automatically.

---

## 5. Cython: Python-like Syntax, C-like Speed

Cython is a language that is almost Python, plus optional C type declarations (`cdef int i`). Cython translates your code into C and compiles it into an extension module.

Why use it:

- It's the easiest way to speed up existing Python code: start with plain Python, then add types to the slow parts.
- It can also call C and C++ libraries directly.
- Big projects such as scikit-learn, pandas and lxml use it.

In Jupyter, the `%%cython` cell magic compiles a cell for you, so you don't need a `setup.py`.


```python
%pip install cython -q
```


```python
# Enable the %%cython magic
%load_ext Cython
```

### 5.1 Basic Cython: Adding Type Declarations

Let's start with a pure Python function that finds primes, and time it.


```python
# Pure Python version -- for comparison
def python_primes(n):
    """Find all primes up to n using trial division."""
    primes = []
    for candidate in range(2, n + 1):
        is_prime = True
        for divisor in range(2, int(candidate ** 0.5) + 1):
            if candidate % divisor == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
    return primes

%timeit python_primes(10000)
```

    2.33 ms ± 18.3 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)


Now the Cython version. The algorithm is identical; we only declare the C types of the variables.

We take the square root with C's `sqrt` and cast it to an `int` with `<int>`. Watch out: writing `candidate ** 0.5` with a C `int` here does *not* behave like Python, and in an earlier version of this notebook it quietly reported 25 and 49 as primes.


```cython
%%cython
# Cython version: almost the same code, but with type declarations!
from libc.math cimport sqrt

def cython_primes(int n):
    """Find all primes up to n using trial division (Cython)."""
    cdef list primes = []
    cdef int candidate, divisor
    cdef bint is_prime

    for candidate in range(2, n + 1):
        is_prime = True
        for divisor in range(2, <int>sqrt(candidate) + 1):
            if candidate % divisor == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
    return primes
```


```python
# Compare performance!
print("Pure Python:")
%timeit python_primes(10000)

print("\nCython:")
%timeit cython_primes(10000)

# Always check that the fast version gives the same answer
assert python_primes(10000) == cython_primes(10000)
print(cython_primes(100))
print(f"\nResults match! Found {len(cython_primes(100))} primes up to 100")
```

    Pure Python:


    2.34 ms ± 16.8 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)
    
    Cython:


    76 μs ± 683 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    
    Results match! Found 25 primes up to 100


**What just happened?** The typed loop variables let Cython turn the inner loop into plain C arithmetic with no Python objects involved, which is where the speedup comes from. The `assert` matters just as much as the timing: a fast function that gives wrong answers is useless. Your exact timings will differ from your neighbour's.

### 5.2 Cython with C Functions

`cimport` (note the **c**) imports C-level declarations. Here we use C's `sqrt`, `sin`, `cos` and `M_PI` straight from `libc.math`.


```cython
%%cython
# Cython can call C standard library functions directly!
from libc.math cimport sqrt, sin, cos, M_PI

def fast_distance(double x1, double y1, double x2, double y2):
    """Compute Euclidean distance using C's sqrt."""
    cdef double dx = x2 - x1
    cdef double dy = y2 - y1
    return sqrt(dx * dx + dy * dy)

def circle_points(int n):
    """Generate n points on a unit circle."""
    cdef list points = []
    cdef double angle
    cdef int i

    for i in range(n):
        angle = 2.0 * M_PI * i / n
        points.append((cos(angle), sin(angle)))
    return points
```


```python
print(f"distance(0,0 -> 3,4) = {fast_distance(0, 0, 3, 4)}")

points = circle_points(8)
print(f"\n8 points on unit circle:")
for i, (x, y) in enumerate(points):
    print(f"  Point {i}: ({x:7.4f}, {y:7.4f})")
```

    distance(0,0 -> 3,4) = 5.0
    
    8 points on unit circle:
      Point 0: ( 1.0000,  0.0000)
      Point 1: ( 0.7071,  0.7071)
      Point 2: ( 0.0000,  1.0000)
      Point 3: (-0.7071,  0.7071)
      Point 4: (-1.0000,  0.0000)
      Point 5: (-0.7071, -0.7071)
      Point 6: (-0.0000, -1.0000)
      Point 7: ( 0.7071, -0.7071)


### 5.3 Wrapping Existing C Code with Cython

To call a C function Cython doesn't know about yet, you declare it in a `cdef extern from` block. It works like a header file: you tell Cython the function names and their types.


```cython
%%cython
# Cython can wrap external C functions
# First, declare the C interface (like a header file)

cdef extern from "string.h":
    size_t strlen(const char* s)
    int strcmp(const char* s1, const char* s2)

def c_string_length(bytes s):
    """Get string length using C's strlen."""
    return strlen(s)

def c_string_compare(bytes s1, bytes s2):
    """Compare strings using C's strcmp.
    Returns: negative if s1 < s2, 0 if equal, positive if s1 > s2"""
    cdef int result = strcmp(s1, s2)
    if result < 0:
        return f"{s1} < {s2}"
    elif result == 0:
        return f"{s1} == {s2}"
    else:
        return f"{s1} > {s2}"
```


```python
print(f"strlen('Hello') = {c_string_length(b'Hello')}")
print(f"strlen('Python Bindings') = {c_string_length(b'Python Bindings')}")

print(f"\nstrcmp: {c_string_compare(b'apple', b'banana')}")
print(f"strcmp: {c_string_compare(b'hello', b'hello')}")
print(f"strcmp: {c_string_compare(b'zebra', b'aardvark')}")
```

    strlen('Hello') = 5
    strlen('Python Bindings') = 15
    
    strcmp: b'apple' < b'banana'
    strcmp: b'hello' == b'hello'
    strcmp: b'zebra' > b'aardvark'


`strcmp` only tells us the order of two strings: negative, zero or positive. The Python wrapper turns that number into a readable message.

**Quick recap**

- Cython is Python plus optional C type declarations (`cdef int x`), compiled to C.
- In Jupyter, `%load_ext Cython` and then `%%cython` compiles a cell.
- Typed loops run as plain C and can be many times faster than Python.
- `cimport` and `cdef extern from` give direct access to C functions.
- Always check that the optimised version gives the same results as the original.

---

## 6. Performance Comparison

Let's benchmark several approaches on the same task: the sum of squares of 100,000 numbers.

First, the Cython version:


```cython
%%cython
def cython_sum_squares(list data):
    cdef double total = 0.0
    cdef double x
    cdef int i
    cdef int n = len(data)
    for i in range(n):
        x = data[i]
        total += x * x
    return total
```


```python
import time

# Prepare test data
test_data = list(range(1, 100001))  # 100,000 numbers

# --- Pure Python ---
def python_sum_squares(data):
    total = 0.0
    for x in data:
        total += x * x
    return total

# --- ctypes version ---
# Reload mylib under a new name (`lib` now points at the cffi module from section 2)
ctypes_lib = ctypes.CDLL(os.path.abspath(lib_name))
ctypes_lib.square_array.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
ctypes_lib.square_array.restype = None

def ctypes_sum_squares(data):
    n = len(data)
    ArrType = ctypes.c_double * n
    arr = ArrType(*data)
    ctypes_lib.square_array(arr, n)
    return sum(arr)

# --- Benchmark ---
approaches = [
    ("Pure Python", python_sum_squares),
    ("Python built-in sum", lambda d: sum(x*x for x in d)),
    ("ctypes (C)", ctypes_sum_squares),
    ("Cython", cython_sum_squares),
]

print(f"{'Approach':<25} {'Time (ms)':>12} {'Speedup':>10}")
print("-" * 50)

baseline = None
for name, func in approaches:
    # Warm up
    func(test_data)

    # Time it
    start = time.perf_counter()
    for _ in range(100):
        result = func(test_data)
    elapsed = (time.perf_counter() - start) / 100 * 1000  # ms

    if baseline is None:
        baseline = elapsed

    speedup = baseline / elapsed
    print(f"{name:<25} {elapsed:>10.3f}ms {speedup:>9.1f}x")
```

    Approach                     Time (ms)    Speedup
    --------------------------------------------------


    Pure Python                    2.096ms       1.0x


    Python built-in sum            2.112ms       1.0x

    


    ctypes (C)                     7.709ms       0.3x
    Cython                         0.527ms       4.0x


**What just happened?** Two results usually surprise students:

- **`ctypes` is the slowest**, even though the squaring happens in C. Converting 100,000 Python numbers into a C array (and summing them back in Python) costs far more than the C work itself. Crossing the Python/C boundary has a price, so bindings pay off when C does a lot of work per call, not when you shuttle data back and forth.
- **Cython wins** because the whole loop, including reading the list, runs as compiled code.

Your numbers will be different on your machine, but the ranking is usually the same.

**Quick recap**

- Calling C is not automatically faster: converting data between Python and C costs time.
- Bindings pay off when each call does a lot of work in C.
- Measure before and after optimising, and on realistic data.

---

## 7. Structures and Complex Data Types

Real C code often groups data in structs. Here we use `ctypes` to pass structs to C.

### 7.1 Structs with `ctypes`

First, a C library that works with two structs: a 3D point and a student record.


```python
%%writefile structs.c
#include <stdio.h>
#include <math.h>
#include <string.h>

typedef struct {
    double x;
    double y;
    double z;
} Point3D;

double point_distance(Point3D* a, Point3D* b) {
    double dx = b->x - a->x;
    double dy = b->y - a->y;
    double dz = b->z - a->z;
    return sqrt(dx*dx + dy*dy + dz*dz);
}

void point_midpoint(Point3D* a, Point3D* b, Point3D* result) {
    result->x = (a->x + b->x) / 2.0;
    result->y = (a->y + b->y) / 2.0;
    result->z = (a->z + b->z) / 2.0;
}

typedef struct {
    char name[64];
    int age;
    double gpa;
} Student;

void print_student(Student* s) {
    printf("Student: %s, Age: %d, GPA: %.2f\n", s->name, s->age, s->gpa);
}

```

    Writing structs.c



```python
import platform

# Compile (Linux needs -lm to link sqrt from the math library)
if platform.system() == "Darwin":
    !gcc -shared -o structs.dylib -fPIC structs.c
    struct_lib_name = "structs.dylib"
elif platform.system() == "Linux":
    !gcc -shared -o structs.so -fPIC structs.c -lm
    struct_lib_name = "structs.so"
else:
    !gcc -shared -o structs.dll structs.c
    struct_lib_name = "structs.dll"

print(f"Compiled: {struct_lib_name}")
```

    Compiled: structs.dylib


On the Python side, a struct is a class that inherits from `ctypes.Structure` and lists its fields in `_fields_`. The fields must be in the **same order with the same types** as the C struct, because `ctypes` uses them to lay out the bytes in memory.

`ctypes.byref(p1)` passes the address of `p1`, which is what a `Point3D*` parameter expects.


```python
import ctypes
import os

# Define the C struct as a Python class
class Point3D(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]

    def __repr__(self):
        return f"Point3D({self.x}, {self.y}, {self.z})"

class Student(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 64),
        ("age", ctypes.c_int),
        ("gpa", ctypes.c_double),
    ]

# Load the library
slib = ctypes.CDLL(os.path.abspath(struct_lib_name))

# Set up function signatures
slib.point_distance.argtypes = [ctypes.POINTER(Point3D), ctypes.POINTER(Point3D)]
slib.point_distance.restype = ctypes.c_double

slib.point_midpoint.argtypes = [
    ctypes.POINTER(Point3D), ctypes.POINTER(Point3D), ctypes.POINTER(Point3D)
]
slib.point_midpoint.restype = None

# Create struct instances and use them
p1 = Point3D(1.0, 2.0, 3.0)
p2 = Point3D(4.0, 6.0, 3.0)

dist = slib.point_distance(ctypes.byref(p1), ctypes.byref(p2))
print(f"Distance between {p1} and {p2} = {dist:.4f}")

mid = Point3D()
slib.point_midpoint(ctypes.byref(p1), ctypes.byref(p2), ctypes.byref(mid))
print(f"Midpoint = {mid}")
```

    Distance between Point3D(1.0, 2.0, 3.0) and Point3D(4.0, 6.0, 3.0) = 5.0000
    Midpoint = Point3D(2.5, 4.0, 3.0)


`point_midpoint` doesn't return anything. It writes its answer into the `mid` struct we passed by reference, the same "output parameter" pattern as `square_array`.

A fixed-size `char name[64]` becomes `ctypes.c_char * 64`, and we fill it with `bytes`:


```python
# Using a struct with strings
slib.print_student.argtypes = [ctypes.POINTER(Student)]
slib.print_student.restype = None

student = Student()
student.name = b"Alice Johnson"  # C strings are bytes
student.age = 21
student.gpa = 3.85

slib.print_student(ctypes.byref(student))

# The printf above writes to the C-level stdout; print from Python as well
print(f"From Python: {student.name.decode()}, {student.age}, {student.gpa}")
```

    From Python: Alice Johnson, 21, 3.85


> The `printf` output comes from C, not from Python's `print`. Jupyter only captures Python's output, so the C line often appears in the terminal that started Jupyter instead of under the cell. That's why the cell also prints the fields from Python.

**Quick recap**

- Mirror a C struct with a `ctypes.Structure` subclass and a `_fields_` list in the same order as C.
- Use `ctypes.byref(obj)` to pass a pointer to a struct.
- Fixed-size C strings (`char name[64]`) become `ctypes.c_char * 64` and take `bytes`.

---

## 8. Callbacks: Passing Python Functions to C

Sometimes C needs to call *back* into Python: think of a sort that takes a comparison function, an event handler, or a numerical routine that needs "the function to integrate". In C this is done with a **function pointer**.


```python
%%writefile callbacks.c
#include <stdio.h>

// Type for a callback function: takes a double, returns a double
typedef double (*MathFunc)(double);

// Apply a function to each element of an array
void apply_func(double* arr, int size, MathFunc func) {
    for (int i = 0; i < size; i++) {
        arr[i] = func(arr[i]);
    }
}

// Numerical integration using the trapezoidal rule
double integrate(MathFunc f, double a, double b, int n) {
    double h = (b - a) / n;
    double sum = 0.5 * (f(a) + f(b));
    for (int i = 1; i < n; i++) {
        sum += f(a + i * h);
    }
    return sum * h;
}

```

    Writing callbacks.c



```python
import platform

if platform.system() == "Darwin":
    !gcc -shared -o callbacks.dylib -fPIC callbacks.c
    cb_lib_name = "callbacks.dylib"
elif platform.system() == "Linux":
    !gcc -shared -o callbacks.so -fPIC callbacks.c
    cb_lib_name = "callbacks.so"
else:
    !gcc -shared -o callbacks.dll callbacks.c
    cb_lib_name = "callbacks.dll"

print(f"Compiled: {cb_lib_name}")
```

    Compiled: callbacks.dylib


`ctypes.CFUNCTYPE(return_type, arg_types...)` creates a function-pointer type. Using it as a decorator wraps a Python function so C can call it like a normal C function.


```python
import ctypes
import math

# Define the callback type: double (*)(double)
MATHFUNC = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_double)

# Load the library
cblib = ctypes.CDLL(os.path.abspath(cb_lib_name))

# Set up apply_func
cblib.apply_func.argtypes = [
    ctypes.POINTER(ctypes.c_double), ctypes.c_int, MATHFUNC
]
cblib.apply_func.restype = None

# Create a Python callback and wrap it
@MATHFUNC
def square(x):
    return x * x

@MATHFUNC
def cube(x):
    return x * x * x

# Apply the callback
data = (ctypes.c_double * 5)(1, 2, 3, 4, 5)
print(f"Original: {list(data)}")

cblib.apply_func(data, 5, square)
print(f"Squared:  {list(data)}")

# Reset and try cube
data = (ctypes.c_double * 5)(1, 2, 3, 4, 5)
cblib.apply_func(data, 5, cube)
print(f"Cubed:    {list(data)}")
```

    Original: [1.0, 2.0, 3.0, 4.0, 5.0]
    Squared:  [1.0, 4.0, 9.0, 16.0, 25.0]
    Cubed:    [1.0, 8.0, 27.0, 64.0, 125.0]



```python
# Numerical integration with callbacks
cblib.integrate.argtypes = [MATHFUNC, ctypes.c_double, ctypes.c_double, ctypes.c_int]
cblib.integrate.restype = ctypes.c_double

# Integrate sin(x) from 0 to pi => should be 2.0
@MATHFUNC
def sin_func(x):
    return math.sin(x)

result = cblib.integrate(sin_func, 0, math.pi, 10000)
print(f"Integral of sin(x) from 0 to pi = {result:.6f} (expected: 2.0)")

# Integrate x^2 from 0 to 1 => should be 1/3 = 0.333...
result = cblib.integrate(square, 0, 1, 10000)
print(f"Integral of x^2 from 0 to 1 = {result:.6f} (expected: 0.333333)")
```

    Integral of sin(x) from 0 to pi = 2.000000 (expected: 2.0)
    Integral of x^2 from 0 to 1 = 0.333333 (expected: 0.333333)


**What just happened?** `integrate` called our Python `sin_func` 10,001 times from inside C. Each call crosses from C back into Python, so callbacks are convenient but not fast.

One more trap: keep a Python reference to every callback object (here the names `square`, `cube`, `sin_func`) for as long as C might call it. If Python garbage-collects it while C still holds the pointer, the program crashes.

**Quick recap**

- C uses function pointers for callbacks; `ctypes.CFUNCTYPE` builds the matching type.
- Decorate a Python function with that type to pass it to C.
- Every callback call crosses back into Python, so it's slow in tight loops.
- Keep a reference to callback objects while C may still use them.

---

## 9. SWIG: Simplified Wrapper and Interface Generator

SWIG reads your C/C++ header files and **generates** binding code for many languages: Python, Java, Ruby and more. We won't run it here (it's a separate tool to install), but you should recognise it when you meet it in older projects.

### How SWIG Works

```
  mylib.h (C/C++ header)  +  mylib.i (SWIG interface file)
                    |
                    v
              swig -python
                    |
                    v
        mylib_wrap.c (auto-generated)  +  mylib.py (Python wrapper)
                    |
                    v
              gcc / compile
                    |
                    v
           _mylib.so (shared library)
```

### When to Use SWIG

- You have a large existing C/C++ codebase.
- You need bindings for several languages, not just Python.
- You want the wrappers generated with as little hand-written code as possible.

### SWIG Interface File Example

```c
// mylib.i -- SWIG interface file
%module mylib
%{
#include "mylib.h"    // Include our header
%}

// Tell SWIG which functions to wrap
int add(int a, int b);
double multiply(double a, double b);
```

Then build with:

```bash
swig -python mylib.i
gcc -shared -fPIC -I/usr/include/python3.x mylib.c mylib_wrap.c -o _mylib.so
```

SWIG works, but the generated code is large and hard to debug. For new Python-only projects, `pybind11` or Cython are usually a better choice.

**Quick recap**

- SWIG generates bindings from header files plus a small `.i` interface file.
- Its strength is targeting many languages from one codebase.
- For new Python-only projects, prefer `pybind11` or Cython.

---

## 10. Choosing the Right Approach

### Decision Flowchart

```
Do you already have a compiled C/C++ library (.so/.dll)?
  |
  +-- YES --> Is it a simple API (few functions)?
  |             |
  |             +-- YES --> Use ctypes or cffi (ABI mode)
  |             +-- NO  --> Use cffi (API mode) or pybind11
  |
  +-- NO --> Are you writing new performance-critical code?
               |
               +-- In C?   --> Python C API or cffi (API mode)
               +-- In C++? --> pybind11
               +-- Prefer Python-like syntax? --> Cython
```

### Summary Table

| Approach | Best For | Avoid When |
|----|----|----|
| `ctypes` | Quick prototyping, calling system libs | Complex APIs, C++ |
| `cffi` | Clean C bindings, PyPy support | C++ classes |
| Python C API | Maximum control, CPython internals | Rapid development |
| `pybind11` | C++ code, classes, templates | Pure C projects |
| Cython | Speeding up Python code incrementally | When you can't install Cython |
| SWIG | Multi-language bindings, large codebases | Small projects |

**Quick recap**

- Existing C library with a few functions: `ctypes` or `cffi` ABI mode.
- C++ code, especially classes: `pybind11`.
- Slow Python code you want to speed up gradually: Cython.
- The raw C API is for when you really need full control.

---

## 11. Best Practices and Common Pitfalls

### Do's

- Always set `argtypes` and `restype` in `ctypes`. Wrong types cause wrong results or crashes.
- Decide who allocates and who frees every piece of memory, and write it down.
- Test with small inputs before scaling up.
- Wrap calls in `try/except` where the binding raises Python exceptions. (A real crash inside C can't be caught; it kills the kernel.)
- Document the C types each function expects.

### Don'ts

- Don't forget that C strings are `bytes` (`b"hello"`), not `str`.
- Don't pass Python objects to C functions that expect C types.
- Don't ignore return values that signal errors.
- Don't assume a compiled library works on another OS or CPU architecture. Recompile it there.
- Don't call C through `ctypes` inside a tight Python loop; the per-call overhead adds up.

### Memory Safety

`ctypes` arrays check their index on the **Python** side. C does no such check, so the real danger is giving C the wrong size.


```python
arr = (ctypes.c_int * 5)()

# Python-side indexing is bounds-checked by ctypes:
try:
    arr[10] = 42
except IndexError as e:
    print(f"ctypes caught it: {e}")

# C has no such check. This would make square_array write past the
# end of a 5-element buffer: undefined behaviour, maybe a crash.
# DON'T run it:
# ctypes_lib.square_array((ctypes.c_double * 5)(), 1000)

# SAFE: always pass the real length
small = (ctypes.c_double * 5)(1, 2, 3, 4, 5)
ctypes_lib.square_array(small, len(small))
print(list(small))
```

    ctypes caught it: invalid index
    [1.0, 4.0, 9.0, 16.0, 25.0]


Using `len(small)` instead of a hand-typed number means the size you pass to C can never drift away from the real size of the array.

**Quick recap**

- Set types explicitly and agree on who owns each piece of memory.
- C does no bounds checking: always pass the true length of a buffer.
- A crash in C kills the whole Python process; `try/except` can't save you.
- Recompile native libraries for each OS and CPU architecture.

---

## Exercises

Each exercise has an empty code cell for your answer. Try it yourself before opening the solution.

### Exercise 1: Matrix Multiplication with `ctypes`

Write a C function that multiplies two 3x3 matrices, compile it, and call it from Python using `ctypes`.

1. Write a C function `void mat_mult(double* A, double* B, double* C, int n)` that stores `A × B` in `C`. Store each matrix as a flat array of `n*n` doubles in row order, so element `(i, j)` is at index `i*n + j`.
2. Compile it into a shared library.
3. Load it with `ctypes` and call it.
4. Check the result against a matrix product computed in plain Python.


```python
# Your code here:

```

<details markdown="1">
<summary>Show solution</summary>

```python
import ctypes, os, platform, subprocess

c_src = r"""
void mat_mult(double* A, double* B, double* C, int n) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double s = 0.0;
            for (int k = 0; k < n; k++)
                s += A[i*n + k] * B[k*n + j];
            C[i*n + j] = s;
        }
}
"""
with open("matmul.c", "w") as f:
    f.write(c_src)

ext = {"Darwin": "dylib", "Linux": "so"}.get(platform.system(), "dll")
subprocess.run(["gcc", "-shared", "-fPIC", "-o", f"matmul.{ext}", "matmul.c"], check=True)

mm = ctypes.CDLL(os.path.abspath(f"matmul.{ext}"))
Arr = ctypes.POINTER(ctypes.c_double)
mm.mat_mult.argtypes = [Arr, Arr, Arr, ctypes.c_int]
mm.mat_mult.restype = None

n = 3
A = [1, 2, 3, 4, 5, 6, 7, 8, 9]
B = [9, 8, 7, 6, 5, 4, 3, 2, 1]
a = (ctypes.c_double * 9)(*A)
b = (ctypes.c_double * 9)(*B)
c = (ctypes.c_double * 9)()
mm.mat_mult(a, b, c, n)

expected = [sum(A[i*n + k] * B[k*n + j] for k in range(n))
            for i in range(n) for j in range(n)]
print(list(c))                  # [30.0, 24.0, 18.0, 84.0, 69.0, 54.0, 138.0, 114.0, 90.0]
assert list(c) == expected
```

</details>

### Exercise 2: String Processing with `cffi`

Use `cffi` in API mode to write a C function that:

- takes a string and a character
- returns how many times that character appears in the string

Use `ffi.cdef()` and `ffi.set_source()` to define and compile it, then call it from Python.


```python
# Your code here:

```

<details markdown="1">
<summary>Show solution</summary>

```python
from cffi import FFI

builder = FFI()
builder.cdef("int count_char(const char* s, char c);")
builder.set_source("_strtools", """
    int count_char(const char* s, char c) {
        int count = 0;
        for (; *s; s++)
            if (*s == c) count++;
        return count;
    }
""")
builder.compile(verbose=False)

from _strtools import lib as strlib

print(strlib.count_char(b"mississippi", b"s"))  # 4
print(strlib.count_char(b"banana", b"a"))       # 3
```

</details>

### Exercise 3: Cython Optimization

Take the pure Python function below and make it faster with Cython type declarations. Then measure the speedup with `%timeit` and compare the two results.


```python
# Optimize this with Cython:
def mandelbrot_python(width, height, max_iter=100):
    """Generate a Mandelbrot set."""
    result = []
    for row in range(height):
        for col in range(width):
            c_real = (col - width / 2) * 4.0 / width
            c_imag = (row - height / 2) * 4.0 / height
            z_real, z_imag = 0.0, 0.0
            iteration = 0
            while z_real * z_real + z_imag * z_imag < 4.0 and iteration < max_iter:
                z_real, z_imag = z_real * z_real - z_imag * z_imag + c_real, 2 * z_real * z_imag + c_imag
                iteration += 1
            result.append(iteration)
    return result

# Hint: Add cdef declarations for all numeric variables
# Use %%cython magic in the next cell
```


```python
# Write your Cython version here, starting the cell with %%cython

```

<details markdown="1">
<summary>Show solution</summary>

```python
%%cython
def mandelbrot_cython(int width, int height, int max_iter=100):
    """Generate a Mandelbrot set (Cython)."""
    cdef list result = []
    cdef int row, col, iteration
    cdef double c_real, c_imag, z_real, z_imag, tmp

    for row in range(height):
        for col in range(width):
            c_real = (col - width / 2.0) * 4.0 / width
            c_imag = (row - height / 2.0) * 4.0 / height
            z_real = 0.0
            z_imag = 0.0
            iteration = 0
            while z_real * z_real + z_imag * z_imag < 4.0 and iteration < max_iter:
                tmp = z_real * z_real - z_imag * z_imag + c_real
                z_imag = 2 * z_real * z_imag + c_imag
                z_real = tmp
                iteration += 1
            result.append(iteration)
    return result

# In the next cell:
# py = mandelbrot_python(200, 100)
# cy = mandelbrot_cython(200, 100)
# print(sum(p != c for p, c in zip(py, cy)), "of", len(py), "pixels differ")
# %timeit mandelbrot_python(200, 100)
# %timeit mandelbrot_cython(200, 100)
```

</details>

Two things to notice in the solution:

- `width / 2.0` instead of `width / 2`: with C `int`s, `/` can mean integer division, so the float literal keeps the maths the same as the Python version.
- When you compare the results, a handful of pixels (4 out of 20,000 on an Apple M-series Mac) may differ by one iteration. Those points sit exactly on the `|z|² = 4` boundary, and the C compiler is allowed to fuse a multiply and an add into one instruction with slightly different rounding. That's floating-point arithmetic, not a bug in your code.

**Quick recap**

- Exercise 1 is the full `ctypes` workflow: write C, compile, set types, call, verify.
- Exercise 2 shows how little code `cffi` API mode needs for a new C function.
- Exercise 3 is the usual Cython recipe: same algorithm, add `cdef` types, then measure and compare.

---

## Cleanup

This notebook created quite a few source files and compiled libraries in the current folder. Run the next cell to remove them.


```python
# Clean up generated files
import glob

patterns = [
    "mylib.c", "mylib.so", "mylib.dylib", "mylib.dll",
    "structs.c", "structs.so", "structs.dylib", "structs.dll",
    "callbacks.c", "callbacks.so", "callbacks.dylib", "callbacks.dll",
    "mathtools.cpp", "mathtools*.so",
    "mymodule.c", "mymodule*.so", "mymodule*.cpython*",
    "setup.py", "_math_helpers*",
    "matmul.*", "_strtools*",  # from the exercise solutions
]

for pattern in patterns:
    for f in glob.glob(pattern):
        os.remove(f)
        print(f"Removed: {f}")

# Remove build directory
import shutil
if os.path.exists("build"):
    shutil.rmtree("build")
    print("Removed: build/")

print("\nCleanup complete!")
```

    Removed: mylib.c
    Removed: mylib.dylib
    Removed: structs.c
    Removed: structs.dylib
    Removed: callbacks.c
    Removed: callbacks.dylib
    Removed: mathtools.cpp
    Removed: mathtools.cpython-312-darwin.so
    Removed: mymodule.c
    Removed: mymodule.cpython-312-darwin.so
    Removed: setup.py
    Removed: _math_helpers.o
    Removed: _math_helpers.c
    Removed: _math_helpers.cpython-312-darwin.so
    Removed: build/
    
    Cleanup complete!


---

## Summary & Cheat Sheet

| What We Covered  | Key Takeaway                                             |
|------------------|----------------------------------------------------------|
| `ctypes`         | Built-in, load any shared library, manual type mapping   |
| `cffi`           | C-syntax declarations; ABI mode loads, API mode compiles |
| Python C API     | Full control, lots of boilerplate, manual refcounting    |
| `pybind11`       | Best for C++, automatic conversions, clean syntax        |
| Cython           | Python-like syntax compiles to C, easy optimization path |
| SWIG             | Auto-generates bindings, good for multi-language support |
| Structs          | Mirror C structs in Python with `ctypes.Structure`       |
| Callbacks        | Pass Python functions to C using `CFUNCTYPE`             |

### Commands to Remember

```python
# ctypes
lib = ctypes.CDLL("./mylib.so")
lib.f.argtypes = [ctypes.c_double]; lib.f.restype = ctypes.c_double

# cffi
ffi = FFI(); ffi.cdef("double f(double);"); lib = ffi.dlopen("./mylib.so")

# C extension / pybind11 build
!{sys.executable} setup.py build_ext --inplace
# (add -undefined dynamic_lookup on macOS)
!c++ -O2 -shared -std=c++17 -fPIC $(python -m pybind11 --includes) m.cpp -o m$(python3-config --extension-suffix)

# Cython in Jupyter
%load_ext Cython
%%cython
```

### What's Next

- Explore NumPy's C API and the buffer protocol for passing whole arrays without copying.
- Try `maturin` and `PyO3` to write Python extensions in Rust.
- Pick a library you use (NumPy, Pillow, pandas) and look at how it organises its C, C++ or Cython code.
