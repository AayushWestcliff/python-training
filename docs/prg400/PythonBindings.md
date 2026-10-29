# Python Bindings: Connecting Python to C/C++

> *"Python is great for prototyping and glue code, but when you need raw speed, you call C."*

---

### Learning Objectives

By the end of this notebook, you will be able to:

1.  **Explain** what Python bindings are and why they matter
2.  **Use** `ctypes` to call C functions from Python
3.  **Use** `cffi` as a modern alternative to `ctypes`
4.  **Write** C extension modules using the Python C API
5.  **Use** `pybind11` to create Python bindings for C++ code
6.  **Use** Cython to write high-performance Python extensions
7.  **Compare** different binding approaches and choose the right one for a given scenario

---

## Why Python Bindings?

---

Python is powerful and easy to write, but it's **slow** compared to compiled languages like C and C++. Python bindings let you:

- **Speed up** performance-critical code (numerical computation, image processing)
- **Reuse** existing C/C++ libraries (OpenSSL, SQLite, system APIs)
- **Access** hardware and OS features not available in pure Python
- **Wrap** legacy codebases with a Pythonic interface

### Real-World Examples

| Python Library | Underlying C/C++ Code            |
|----------------|----------------------------------|
| NumPy          | C and Fortran numerical routines |
| TensorFlow     | C++ computation engine           |
| Pillow (PIL)   | C image decoding libraries       |
| sqlite3        | SQLite C library                 |
| OpenCV (cv2)   | C++ computer vision library      |

---

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

The **binding layer** translates between Python objects and C/C++ data types.

---

## Overview of Binding Approaches

---

| Approach | Language | Difficulty | Use Case |
|----|----|----|----|
| `ctypes` | C | Easy | Call existing shared libraries |
| `cffi` | C | Easy-Medium | Modern alternative to ctypes |
| Python C API | C | Hard | Maximum control, build extension modules |
| `pybind11` | C++ | Medium | Modern C++ bindings with clean syntax |
| Cython | C/C++ | Medium | Write C extensions using Python-like syntax |
| SWIG | C/C++ | Medium | Auto-generate bindings for multiple languages |

---

## 1. `ctypes` -- Calling C from Python (No Compilation Needed)

---

`ctypes` is a **built-in** Python module. It lets you load shared libraries (`.so` on Linux, `.dll` on Windows, `.dylib` on macOS) and call their functions directly.

### Key Concepts

- No need to write any C code yourself -- just load existing libraries
- You must manually specify argument types and return types
- Part of Python's standard library (no `pip install` needed)

### 1.1 Creating a Simple C Library

Let's start by writing a small C file and compiling it into a shared library.


```python
# Step 1: Write a C source file
c_code = r"""
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
"""

with open("mylib.c", "w") as f:
    f.write(c_code)

print("C source file written: mylib.c")
```

    C source file written: mylib.c



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


```python
import ctypes
import os

# Load the shared library
lib = ctypes.CDLL(os.path.abspath(lib_name))

# --- Calling add(int, int) -> int ---
# By default, ctypes assumes int arguments and int return
result = lib.add(10, 25)
print(f"add(10, 25) = {result}")

factorial = lib.factorial(5)
print(f"factorial(5) = {factorial}")
```

    add(10, 25) = 35
    factorial(5) = 120



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


### 1.3 Working with Pointers and Arrays


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


### 1.4 Working with Strings


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
| `float`     | `c_float`        | `float`           |
| `double`    | `c_double`       | `float`           |
| `char`      | `c_char`         | `bytes` (1 char)  |
| `char*`     | `c_char_p`       | `bytes` or `None` |
| `void*`     | `c_void_p`       | `int` or `None`   |
| `int*`      | `POINTER(c_int)` | `ctypes` array    |
| `bool`      | `c_bool`         | `bool`            |

### 1.6 Calling System Libraries with `ctypes`

You don't always need to write your own C code. You can call **system libraries** directly.


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


### Try It: Use ctypes to call `strlen`

Load the C standard library and call the `strlen` function to find the length of a string.

```bash
# Your code here:
# Hint: strlen takes a const char* and returns a size_t (use c_size_t)
# libc = ctypes.CDLL(None)  # loads the default C library

# libc.strlen.argtypes = [???]
# libc.strlen.restype = ???
# result = libc.strlen(b"Hello, World!")
# print(f"strlen = {result}")
```


```python
# Your code here:
# Hint: strlen takes a const char* and returns a size_t (use c_size_t)
libc = ctypes.CDLL(None)  # loads the default C library

libc.strlen.argtypes = [ctypes.c_char_p]
libc.strlen.restype = ctypes.c_size_t
result = libc.strlen(b"Hello, World!")
print(f"strlen = {result}")
```

    strlen = 13


---

## 2. `cffi` -- C Foreign Function Interface

---

`cffi` is a more modern and Pythonic alternative to `ctypes`. It has two modes:

- **ABI mode** (like ctypes): Load and call shared libraries at runtime
- **API mode**: Compile C code at build time for better performance and safety

### Why `cffi` over `ctypes`?

- You write C declarations in actual C syntax (not ctypes wrappers)
- Better error messages
- Supports both ABI and API (compiled) mode
- Used by PyPy for its C extension support


```python
# Install cffi if needed
!pip install cffi -q
```

### 2.1 ABI Mode -- Loading Existing Libraries


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



```python
# Working with strings in cffi
result = lib.greet(b"Student")
print(ffi.string(result).decode("utf-8"))
```

    Hello, Student! Welcome from C.


### 2.2 API Mode -- Compile C Code Inline

API mode compiles C code at build time, giving you better performance and type safety.


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
    the current directory is '/Users/aayush/Documents/Kings/python-training/prg400'
    
    
    ld: warning: duplicate -rpath '/Users/aayush/micromamba/envs/stats/lib' ignored
    
    
    
    
    
    '/Users/aayush/Documents/Kings/python-training/prg400/_math_helpers.cpython-310-darwin.so'



```python
import sys

sys.path.append(os.path.abspath("../lib"))
# Now import and use the compiled module
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

---

## 3. Python C API -- Writing Extension Modules

---

The **Python C API** lets you write C code that directly creates Python objects. This is how CPython itself is built and how many high-performance libraries (like NumPy) work internally.

### When to Use the C API

- You need **maximum performance** and control
- You're building a library that will be distributed to many users
- You want tight integration with Python's internals

### Trade-offs

- Most complex approach -- lots of boilerplate
- Manual reference counting (`Py_INCREF` / `Py_DECREF`)
- Easy to introduce memory leaks or segfaults
- Only works with CPython (not PyPy, Jython, etc.)

### 3.1 Anatomy of a C Extension Module

A C extension module has three parts:

1.  **Function implementations** -- the actual C functions that do work
2.  **Method table** -- maps Python function names to C function pointers
3.  **Module definition** -- describes the module to Python


```python
# Let's write a complete C extension module
c_extension_code = r"""
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
"""

with open("mymodule.c", "w") as f:
    f.write(c_extension_code)

print("C extension source written: mymodule.c")
```

    C extension source written: mymodule.c



```python
# Write a setup.py to build the extension
setup_code = """
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
"""

with open("setup.py", "w") as f:
    f.write(setup_code)

print("setup.py written")
```

    setup.py written



```python
# Build the extension module
!python setup.py build_ext --inplace 2>&1 | tail -5
```

    building 'mymodule' extension
    clang -Wno-unused-result -Wsign-compare -Wunreachable-code -DNDEBUG -fwrapv -O2 -Wall -fPIC -O2 -isystem /Users/aayush/micromamba/envs/stats/include -arch arm64 -fPIC -O2 -isystem /Users/aayush/micromamba/envs/stats/include -arch arm64 -I/Users/aayush/micromamba/envs/stats/include/python3.10 -c mymodule.c -o build/temp.macosx-11.0-arm64-cpython-310/mymodule.o
    clang -bundle -undefined dynamic_lookup -Wl,-rpath,/Users/aayush/micromamba/envs/stats/lib -L/Users/aayush/micromamba/envs/stats/lib -Wl,-rpath,/Users/aayush/micromamba/envs/stats/lib -L/Users/aayush/micromamba/envs/stats/lib build/temp.macosx-11.0-arm64-cpython-310/mymodule.o -o build/lib.macosx-11.0-arm64-cpython-310/mymodule.cpython-310-darwin.so
    ld: warning: duplicate -rpath '/Users/aayush/micromamba/envs/stats/lib' ignored
    copying build/lib.macosx-11.0-arm64-cpython-310/mymodule.cpython-310-darwin.so ->



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


### 3.2 PyArg_ParseTuple Format Codes

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
| `|`  | --                            | marks start of optional args |

### 3.3 Reference Counting: The Critical Concept

In the C API, **you** manage memory. Every Python object has a reference count.

```bash
// You got a NEW reference (you own it) -- must DECREF when done
PyObject* result = PyLong_FromLong(42);
// ... use result ...
Py_DECREF(result);  // Release your reference

// You got a BORROWED reference (someone else owns it) -- do NOT DECREF
PyObject* item = PyList_GetItem(list, 0);  // Borrowed!
// ... use item but do NOT Py_DECREF(item) ...
```

**Rules:** - Functions that **create** objects give you a **new** reference (you must DECREF) - Functions that **get** items from containers give you a **borrowed** reference (don't DECREF) - When returning an object from your function, you transfer ownership to the caller - `Py_INCREF` if you want to keep a borrowed reference alive

---

## 4. `pybind11` -- Modern C++ Bindings

---

`pybind11` is a **header-only** C++ library that makes it easy to expose C++ code to Python. It's inspired by Boost.Python but is much lighter and uses modern C++11/14/17 features.

### Why `pybind11`?

- Clean, modern C++ syntax
- Automatic type conversions (STL containers \<-> Python types)
- Supports classes, inheritance, overloading, lambdas
- Header-only -- easy to integrate
- The **most popular** way to create C++ bindings today


```python
# Install pybind11
!pip install pybind11 -q
```

### 4.1 A Simple pybind11 Module


```python
cpp_code = r"""
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
"""

with open("mathtools.cpp", "w") as f:
    f.write(cpp_code)

print("C++ source written: mathtools.cpp")
```

    C++ source written: mathtools.cpp


```bash
# Build using pybind11's build helpers
import pybind11
import sysconfig

# Get compiler flags
include_flags = !python -m pybind11 --includes
include_flags = include_flags[0]

ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')

print(f"Include flags: {include_flags}")
print(f"Extension suffix: {ext_suffix}")

# Compile
!c++ -O2 -shared -std=c++17 -fPIC -undefined dynamic_lookup {include_flags} mathtools.cpp -o mathtools{ext_suffix}
```

```
Include flags: -I/Users/aayush/micromamba/envs/stats/include/python3.10 -I/Users/aayush/micromamba/envs/stats/lib/python3.10/site-packages/pybind11/include
Extension suffix: .cpython-310-darwin.so
```


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


---

## 5. Cython -- Python-like Syntax, C-like Speed

---

Cython is a **superset of Python** that adds optional C type declarations. You write `.pyx` files that look almost like Python but compile to C.

### Why Cython?

- Easiest migration path from pure Python to C speed
- Write Python-like code with type annotations for speed
- Can also wrap existing C/C++ libraries
- Used by major projects: scikit-learn, pandas, lxml


```python
!pip install cython -q
```


```python
# Cython can be used directly in Jupyter with the %%cython magic
%load_ext Cython
```

    The Cython extension is already loaded. To reload it, use:
      %reload_ext Cython


### 5.1 Basic Cython: Adding Type Declarations


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

    3.09 ms ± 77.7 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)


```bash
%%cython
# Cython version -- almost the same code, but with type declarations!

def cython_primes(int n):
    """Find all primes up to n using trial division (Cython)."""
    cdef list primes = []
    cdef int candidate, divisor
    cdef bint is_prime

    for candidate in range(2, n + 1):
        is_prime = True
        for divisor in range(2, int(candidate ** 0.5) + 1):
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

# Verify correctness
# assert python_primes(100) == cython_primes(100)
print(python_primes(100))
print(cython_primes(100))
print(f"\nResults match! Found {len(cython_primes(100))} primes up to 100")
```

    Pure Python:
    3.03 ms ± 146 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)
    
    Cython:
    438 μs ± 11.7 μs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 25, 29, 31, 37, 41, 43, 47, 49, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    
    Results match! Found 27 primes up to 100


### 5.2 Cython with C Functions

```bash
%%cython
# Cython can call C standard library functions directly!
from libc.math cimport sqrt, sin, cos, M_PI
from libc.stdlib cimport malloc, free

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

```bash
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


---

## 6. Performance Comparison

---

Let's benchmark all approaches on the same task: computing the sum of squares of a large list.

```bash
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
# Reload the ctypes library (lib was overwritten by the cffi API mode import above)
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
    Pure Python                    2.690ms       1.0x
    Python built-in sum            2.276ms       1.2x
    ctypes (C)                     8.426ms       0.3x
    Cython                         0.608ms       4.4x


---

## 7. Structures and Complex Data Types

---

Real-world C/C++ code often uses structs. Let's see how each approach handles them.

### 7.1 Structs with `ctypes`


```python
# Write a C library with structs
struct_c_code = r"""
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
"""

with open("structs.c", "w") as f:
    f.write(struct_c_code)

# Compile
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



```python
# Using a struct with strings
slib.print_student.argtypes = [ctypes.POINTER(Student)]
slib.print_student.restype = None

student = Student()
student.name = b"Alice Johnson"  # C strings are bytes
student.age = 21
student.gpa = 3.85

slib.print_student(ctypes.byref(student))
```

    Student: Alice Johnson, Age: 21, GPA: 3.85


---

## 8. Callbacks: Passing Python Functions to C

---

Sometimes C code needs to call back into Python. This is common in event-driven code, sorting algorithms, and numerical methods.


```python
# Write C code that accepts function pointers
callback_code = r"""
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
"""

with open("callbacks.c", "w") as f:
    f.write(callback_code)

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


---

## 9. SWIG -- Simplified Wrapper and Interface Generator

---

SWIG is a tool that **automatically generates** binding code for multiple languages (Python, Java, Ruby, etc.) from C/C++ header files.

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

- You have a large existing C/C++ codebase
- You need bindings for multiple languages (not just Python)
- You want auto-generated wrappers with minimal hand-written code

### SWIG Interface File Example

```bash
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

    swig -python mylib.i
    gcc -shared -fPIC -I/usr/include/python3.x mylib.c mylib_wrap.c -o _mylib.so

SWIG is powerful but has a steeper learning curve and generates verbose wrapper code. For new projects, **pybind11** or **Cython** are generally preferred.

---

## 10. Choosing the Right Approach

---

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

---

## 11. Best Practices and Common Pitfalls

---

### Do's

- Always set `argtypes` and `restype` in ctypes (prevents segfaults)
- Handle memory management carefully (who allocates? who frees?)
- Test with small inputs before scaling up
- Use `try/except` around C calls -- crashes in C can be hard to debug
- Document the expected C types for each function

### Don'ts

- Don't forget that C strings are bytes (`b"hello"`) not Python strings
- Don't pass Python objects to C functions that expect C types
- Don't ignore return values that indicate errors
- Don't assume the same binary works across OS/architecture
- Don't use `ctypes` for performance-critical tight loops (overhead per call)

### Memory Safety


```python
# DANGEROUS: buffer overflow!
arr = (ctypes.c_int * 5)()
arr[10] = 42  # Writing past the end -- undefined behavior!

# SAFE: check bounds yourself
size = 5
arr = (ctypes.c_int * size)()
index = 10
if 0 <= index < size:
    arr[index] = 42
```

---

## Exercises

---

### Exercise 1: Matrix Multiplication with ctypes

Write a C function that multiplies two 3x3 matrices, compile it, and call it from Python using `ctypes`.

```bash
# Your code here:
# 1. Write a C function: void mat_mult(double* A, double* B, double* C, int n)
# 2. Compile it into a shared library
# 3. Load it with ctypes and call it
# 4. Verify the result against Python's manual calculation
```

### Exercise 2: String Processing with cffi

Use cffi (API mode) to write a C function that: - Takes a string and a character - Returns the count of that character in the string

```bash
# Your code here:
# Use ffi.cdef() and ffi.set_source() to define and compile the function
```

### Exercise 3: Cython Optimization

Take this pure Python function and optimize it with Cython type declarations. Measure the speedup.


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

```bash
# Write your Cython version here using %%cython magic
```

---

## Cleanup


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
    Removed: mathtools.cpython-310-darwin.so
    Removed: mymodule.c
    Removed: mymodule.cpython-310-darwin.so
    Removed: setup.py
    Removed: _math_helpers.o
    Removed: _math_helpers.cpython-310-darwin.so
    Removed: _math_helpers.c
    Removed: build/
    
    Cleanup complete!


---

## Summary

| What We Covered  | Key Takeaway                                             |
|------------------|----------------------------------------------------------|
| **ctypes**       | Built-in, load any shared library, manual type mapping   |
| **cffi**         | Cleaner C declarations, supports compilation (API mode)  |
| **Python C API** | Full control, lots of boilerplate, manual refcounting    |
| **pybind11**     | Best for C++, automatic conversions, clean syntax        |
| **Cython**       | Python-like syntax compiles to C, easy optimization path |
| **SWIG**         | Auto-generates bindings, good for multi-language support |
| **Structs**      | Mirror C structs in Python with ctypes.Structure         |
| **Callbacks**    | Pass Python functions to C using CFUNCTYPE               |

### What's Next?

- Explore NumPy's C API for array-level bindings
- Look into `maturin` and `PyO3` for Rust-Python bindings
- Study how major libraries (NumPy, Pandas) use these techniques internally
