# OOP Foundations in Python


### **Learning Objectives**

By the end of this notebook, you will be able to:

1. **Explain** object identity, mutability, and references in Python

2. **Create** classes with proper initialization, attributes, and methods

3. **Implement** encapsulation using properties with validation

4. **Apply** inheritance and polymorphism following the Liskov Substitution Principle

5. **Choose** between composition and inheritance for object relationships

6. **Use** dataclasses for cleaner data-focused classes

7. **Implement** common dunder methods (`__len__`, `__iter__`, `__eq__`, etc.)

8. **Build** a real-world mini-project demonstrating OOP concepts

---

### **Prerequisites**

- Python 3.8+ installed

- Understanding of basic Python syntax (variables, functions, loops)

- Familiarity with lists, dictionaries, and basic data structures

- Experience writing simple Python functions

---

## Why Object-Oriented Programming? Real-World Examples

Before we write any code, let's understand OOP through everyday examples. OOP models the real world by representing things as **objects** with **attributes** (data) and **behaviors** (actions).

---

### Example 1: A University System

Think about how a university works:

| Real-World Entity | Class | Attributes (Data) | Behaviors (Methods) |
|-------------------|-------|-------------------|---------------------|
| A student | `Student` | name, student_id, gpa, enrolled_courses | enroll(), drop_course(), calculate_gpa() |
| A professor | `Professor` | name, employee_id, department, courses_teaching | assign_grade(), publish_research() |
| A course | `Course` | code, title, credits, students_enrolled | add_student(), remove_student(), get_roster() |

**Key insight**: Each "thing" in the system becomes a **class**, and each specific instance (like "Alice" or "CS101") becomes an **object**.

---

### Example 2: Food Delivery App (Foodmandu, Pathao Food)

| Real-World Entity | Class | Attributes | Behaviors |
|-------------------|-------|------------|-----------|
| A customer | `Customer` | name, phone, address, payment_method | place_order(), track_order(), rate_restaurant() |
| A restaurant | `Restaurant` | name, location, menu_items, rating | accept_order(), update_menu(), close_for_day() |
| An order | `Order` | items, total_price, status, delivery_time | calculate_total(), apply_discount(), update_status() |
| A delivery rider | `Rider` | name, vehicle, current_location, orders_delivered | accept_delivery(), mark_delivered(), navigate_to() |

**Key insight**: Objects can **contain other objects** (an Order contains MenuItems) — this is **composition**.

---

### Example 3: Banking System (Your Bank App)

| Real-World Entity | Class | Attributes | Behaviors |
|-------------------|-------|------------|-----------|
| Account | `BankAccount` | account_number, balance, owner, type | deposit(), withdraw(), transfer(), get_statement() |
| Savings Account | `SavingsAccount` | (inherits from BankAccount) + interest_rate | calculate_interest(), apply_interest() |
| Customer | `Customer` | name, accounts[], contact_info | open_account(), close_account() |
| Transaction | `Transaction` | amount, date, type, from_account, to_account | execute(), reverse() |

**Key insight**: `SavingsAccount` **inherits** from `BankAccount` — it has all the same features plus some extra ones. This is **inheritance**.

---

### Example 4: Ride-Sharing App (Pathao, inDrive)

| Concept | Real-World Example | OOP Principle |
|---------|-------------------|---------------|
| **Class** | The concept of "a rider" | Blueprint/template |
| **Object** | You, specifically, as a rider | Instance of the class |
| **Attribute** | Your name, phone number, rating | Data stored in object |
| **Method** | Request a ride, cancel ride, rate driver | Actions the object can do |
| **Inheritance** | BikeRide and CarRide are both types of Ride | Child classes from parent |
| **Encapsulation** | Your payment details are hidden, you just tap "Pay" | Hiding internal details |
| **Polymorphism** | "Calculate fare" works differently for Bike vs Car | Same method, different behavior |

---

### The Four Pillars of OOP (Preview)

| Pillar | What It Means | Real-World Analogy |
|--------|---------------|-------------------|
| **Encapsulation** | Bundle data + methods together; hide internal details | A TV remote: you press buttons without knowing the electronics inside |
| **Abstraction** | Show only essential features, hide complexity | A car dashboard: you see speed, not engine internals |
| **Inheritance** | Create new classes based on existing ones | A "Mountain Bike" is a type of "Bicycle" which is a type of "Vehicle" |
| **Polymorphism** | Same interface, different implementations | "Make sound" → Dog barks, Cat meows, Bird chirps |

---

### Quick Mental Exercise

Before we code, think about these:

1. **Your phone**: What are its attributes? What methods does it have?
2. **A playlist on Spotify**: What data does it store? What can you do with it?
3. **An airline booking**: What objects are involved? How do they relate?

> **Think pair share**: Turn to your neighbor and describe one real-world system as classes with attributes and methods.

---

Now let's see how to implement these concepts in Python!

1️⃣ What objects exist? → Classes

2️⃣ What do they store? → Attributes

3️⃣ What can they do? → Methods

4️⃣ How do they relate? → Composition / Inheritance

---

## 1. Quick Warm-Up: Object Identity, Mutability & References

Before diving into classes, let's solidify our understanding of how Python handles objects under the hood.


```python
# Object Identity: Every object has a unique ID
a = [1, 2, 3]
b = a           # b references the SAME object as a
c = [1, 2, 3]   # c is a NEW object with same content

print(f"a = {a}")
print(f"b = {b}")
print(f"c = {c}")
print()
print(f"id(a) = {id(a)}")
print(f"id(b) = {id(b)}")
print(f"id(c) = {id(c)}")
print()
print(f"a is b: {a is b}")   # True - same object
print(f"a is c: {a is c}")   # False - different objects
print(f"a == c: {a == c}")   # True - equal values
```

    a = [1, 2, 3]
    b = [1, 2, 3]
    c = [1, 2, 3]
    
    id(a) = 4572384320
    id(b) = 4572384320
    id(c) = 4572575168
    
    a is b: True
    a is c: False
    a == c: True



```python
# Mutability: Lists are mutable, strings/tuples are not
my_list = [1, 2, 3]
original_id = id(my_list)

my_list.append(4)  # Modifies in place
print(f"After append: {my_list}")
print(f"Same object? {id(my_list) == original_id}")  # True!

# Contrast with strings (immutable)
my_string = "hello"
string_id = id(my_string)
my_string = my_string + " world"  # Creates NEW object
print(f"\nAfter concatenation: {my_string}")
print(f"Same object? {id(my_string) == string_id}")  # False!
```

    After append: [1, 2, 3, 4]
    Same object? True
    
    After concatenation: hello world
    Same object? False



```python
# Reference traps: Mutable default arguments
def add_item_bad(item, items=[]):
    """BAD: Default list is shared across calls!"""
    items.append(item)
    return items

def add_item_good(item, items=None):
    """GOOD: Create new list if not provided."""
    if items is None:
        items = []
    items.append(item)
    return items

# Watch the difference
print("Bad function:")
print(add_item_bad("a"))  # ['a']
print(add_item_bad("b"))  # ['a', 'b'] - Oops!

print("\nGood function:")
print(add_item_good("a"))  # ['a']
print(add_item_good("b"))  # ['b'] - Correct!
```

    Bad function:
    ['a']
    ['a', 'b']
    
    Good function:
    ['a']
    ['b']


### 🎯 Try It: Predict the Output

Before running the cell below, predict what will be printed. Then run it to verify.


```python
# Try to predict before running!
x = [1, 2, 3]
y = x
x.append(4)
y = y + [5]

print(f"x = {x}")
print(f"y = {y}")
print(f"x is y: {x is y}")

# Why are they different?
# Hint: x.append() modifies in place, y + [5] creates a new list
```

    x = [1, 2, 3, 4]
    y = [1, 2, 3, 4, 5]
    x is y: False


---

## 2. Classes & Objects

A **class** is a blueprint for creating objects. An **object** is an instance of a class.

### 2.1 The `__init__` Method and Instance Attributes

The `__init__` method is called automatically when you create a new instance. It initializes the object's attributes.


```python
class Student:
    """Represents a student enrolled in a course."""
    
    def __init__(self, name: str, student_id: str, gpa: float = 0.0):
        """
        Initialize a new Student instance.
        
        Args:
            name: Student's full name
            student_id: Unique identifier
            gpa: Grade point average (default 0.0)
        """
        self.name = name              # Instance attribute
        self.student_id = student_id  # Instance attribute
        self.gpa = gpa               # Instance attribute with default
    
    def is_honor_roll(self) -> bool:
        """Check if student qualifies for honor roll."""
        return self.gpa >= 3.5

# Creating instances
alice = Student("Alice Johnson", "STU001", 3.8)
bob = Student("Bob Smith", "STU002", 2.9)

print(f"{alice.name} (GPA: {alice.gpa})")
print(f"Honor roll? {alice.is_honor_roll()}")
print()
print(f"{bob.name} (GPA: {bob.gpa})")
print(f"Honor roll? {bob.is_honor_roll()}")
```

    Alice Johnson (GPA: 3.8)
    Honor roll? True
    
    Bob Smith (GPA: 2.9)
    Honor roll? False


### 2.2 Class Attributes vs Instance Attributes

**Class attributes** are shared across all instances. **Instance attributes** are unique to each instance.


```python
class BankAccount:
    """A simple bank account with class-level tracking."""
    
    # Class attributes: shared by ALL instances
    bank_name = "Python National Bank"
    total_accounts = 0
    
    def __init__(self, owner: str, balance: float = 0.0):
        # Instance attributes: unique to each instance
        self.owner = owner
        self.balance = balance
        self.account_number = BankAccount.total_accounts + 1
        
        # Increment class attribute
        BankAccount.total_accounts += 1
    
    def deposit(self, amount: float) -> None:
        """Add money to the account."""
        if amount > 0:
            self.balance += amount

# Create accounts
acc1 = BankAccount("Alice", 1000)
acc2 = BankAccount("Bob", 500)

print(f"Bank: {BankAccount.bank_name}")  # Access via class
print(f"Total accounts: {BankAccount.total_accounts}")
print()
print(f"Account {acc1.account_number}: {acc1.owner} - ${acc1.balance}")
print(f"Account {acc2.account_number}: {acc2.owner} - ${acc2.balance}")

# Both instances share the same class attribute
assert acc1.bank_name == acc2.bank_name == BankAccount.bank_name
print("\n✓ Class attribute shared correctly")
```

    Bank: Python National Bank
    Total accounts: 2
    
    Account 1: Alice - $1000
    Account 2: Bob - $500
    
    ✓ Class attribute shared correctly


### 2.3 Methods: Instance, Class, and Static

Python supports three types of methods:
- **Instance methods**: Take `self` as first argument, operate on instance data
- **Class methods**: Take `cls` as first argument, operate on class data
- **Static methods**: No implicit first argument, utility functions


```python
import datetime

class Employee:
    """Demonstrates different method types."""
    
    company = "Tech Corp"
    employee_count = 0
    
    def __init__(self, name: str, hire_year: int):
        self.name = name
        self.hire_year = hire_year
        Employee.employee_count += 1
    
    # Instance method: operates on self
    def years_employed(self) -> int:
        """Calculate years with company."""
        return datetime.date.today().year - self.hire_year
    
    # Class method: operates on class, not instance
    @classmethod
    def get_company_info(cls) -> str:
        """Return company information."""
        return f"{cls.company} - {cls.employee_count} employees"
    
    # Alternative constructor using classmethod
    @classmethod
    def from_string(cls, data: str) -> "Employee":
        """Create employee from 'name,year' string."""
        name, year = data.split(",")
        return cls(name.strip(), int(year.strip()))
    
    # Static method: utility function, no self or cls
    @staticmethod
    def is_valid_year(year: int) -> bool:
        """Check if hire year is reasonable."""
        current_year = datetime.date.today().year
        return 1990 <= year <= current_year

# Using instance method
emp1 = Employee("Alice", 2020)
print(f"{emp1.name} - {emp1.years_employed()} years employed")

# Using class method
print(Employee.get_company_info())

# Using classmethod as alternative constructor
emp2 = Employee.from_string("Bob, 2022")
print(f"Created from string: {emp2.name} ({emp2.hire_year})")

# Using static method
print(f"Is 2020 valid? {Employee.is_valid_year(2020)}")
print(f"Is 1800 valid? {Employee.is_valid_year(1800)}")
```

    Alice - 6 years employed
    Tech Corp - 1 employees
    Created from string: Bob (2022)
    Is 2020 valid? True
    Is 1800 valid? False


### 2.4 `__repr__` vs `__str__`

- **`__repr__`**: Unambiguous representation for developers (debugging)
- **`__str__`**: Readable representation for users (display)

Rule of thumb: `__repr__` should return something you can use to recreate the object.


```python
class Point:
    """A 2D point with proper string representations."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __repr__(self) -> str:
        """Developer representation - can recreate object."""
        return f"Point({self.x}, {self.y})"
    
    def __str__(self) -> str:
        """User-friendly representation."""
        return f"({self.x}, {self.y})"

p = Point(3.5, 4.2)

print(f"repr: {repr(p)}")  # Point(3.5, 4.2)
print(f"str:  {str(p)}")   # (3.5, 4.2)
print(f"print: {p}")       # Uses __str__

# In a list, __repr__ is used
points = [Point(1, 2), Point(3, 4)]
print(f"List: {points}")
```

    repr: Point(3.5, 4.2)
    str:  (3.5, 4.2)
    print: (3.5, 4.2)
    List: [Point(1, 2), Point(3, 4)]


### 🎯 Try It: Create a Book Class

Create a `Book` class with:
- `title`, `author`, `pages` as instance attributes
- `total_books` as a class attribute (tracks count)
- `__repr__` that shows `Book('Title', 'Author', pages)`
- `is_long()` method that returns True if pages > 300


```python
# Your code here:
class Book:
    total_books = 0
    
    def __init__(self, title: str, author: str, pages: int):
        # TODO: Initialize attributes
        pass
    
    def __repr__(self) -> str:
        # TODO: Return representation
        pass
    
    def is_long(self) -> bool:
        # TODO: Check if pages > 300
        pass

# Test your implementation:
# book1 = Book("Python Crash Course", "Eric Matthes", 544)
# book2 = Book("Clean Code", "Robert Martin", 464)
# print(book1)
# print(f"Is long? {book1.is_long()}")
# print(f"Total books: {Book.total_books}")
```

---

## 3. Encapsulation & Properties

**Encapsulation** means bundling data with methods that operate on it, while controlling access.

Python uses naming conventions:
- `public_attr`: Public, accessible from anywhere
- `_protected_attr`: Protected, "internal use" (convention only)
- `__private_attr`: Private, name-mangled to `_ClassName__private_attr`

### 3.1 The `@property` Decorator

Properties let you define attributes with custom getter, setter, and deleter behavior.


```python
class Temperature:
    """Temperature with validation using properties."""
    
    def __init__(self, celsius: float = 0.0):
        self._celsius = celsius  # Protected attribute
    
    @property
    def celsius(self) -> float:
        """Get temperature in Celsius."""
        return self._celsius
    
    @celsius.setter
    def celsius(self, value: float) -> None:
        """Set temperature with validation."""
        if value < -273.15:
            raise ValueError("Temperature below absolute zero is not possible")
        self._celsius = value
    
    @property
    def fahrenheit(self) -> float:
        """Get temperature in Fahrenheit (computed property)."""
        return self._celsius * 9/5 + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        """Set temperature via Fahrenheit."""
        self.celsius = (value - 32) * 5/9  # Uses celsius setter validation

# Usage looks like simple attributes
temp = Temperature(25)
print(f"Celsius: {temp.celsius}°C")
print(f"Fahrenheit: {temp.fahrenheit}°F")

temp.fahrenheit = 98.6
print(f"\nAfter setting to 98.6°F:")
print(f"Celsius: {temp.celsius:.1f}°C")

# Validation works
try:
    temp.celsius = -300
except ValueError as e:
    print(f"\n✓ Validation error: {e}")
```

    Celsius: 25°C
    Fahrenheit: 77.0°F
    
    After setting to 98.6°F:
    Celsius: 37.0°C
    
    ✓ Validation error: Temperature below absolute zero is not possible


### 3.2 Validation Rules with Properties

Properties are perfect for enforcing business rules.


```python
class User:
    """User with validated email and age."""
    
    def __init__(self, username: str, email: str, age: int):
        self.username = username
        self.email = email  # Uses setter
        self.age = age      # Uses setter
    
    @property
    def email(self) -> str:
        return self._email
    
    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError(f"Invalid email format: {value}")
        self._email = value.lower().strip()
    
    @property
    def age(self) -> int:
        return self._age
    
    @age.setter
    def age(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Age must be an integer")
        if not 0 <= value <= 150:
            raise ValueError("Age must be between 0 and 150")
        self._age = value
    
    @property
    def is_adult(self) -> bool:
        """Read-only computed property."""
        return self._age >= 18

# Valid user
user = User("alice", "Alice@Example.COM", 25)
print(f"Username: {user.username}")
print(f"Email: {user.email}")  # Normalized to lowercase
print(f"Age: {user.age}")
print(f"Is adult: {user.is_adult}")

# Test validations
test_cases = [
    ("invalid_email", "bademail", 20),
    ("invalid_age_type", "valid@email.com", "twenty"),
    ("invalid_age_range", "valid@email.com", -5),
]

print("\nValidation tests:")
for name, email, age in test_cases:
    try:
        User(name, email, age)
    except (ValueError, TypeError) as e:
        print(f"  ✓ {name}: {e}")
```

    Username: alice
    Email: alice@example.com
    Age: 25
    Is adult: True
    
    Validation tests:
      ✓ invalid_email: Invalid email format: bademail
      ✓ invalid_age_type: Age must be an integer
      ✓ invalid_age_range: Age must be between 0 and 150


---

## 4. Inheritance & Polymorphism

**Inheritance** allows a class to inherit attributes and methods from a parent class.

**Polymorphism** means objects of different types can be treated uniformly through a common interface.

### 4.1 Base Class and Child Class


```python
from abc import ABC, abstractmethod

class Shape(ABC):
    """Abstract base class for shapes."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def area(self) -> float:
        """Calculate and return the area."""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """Calculate and return the perimeter."""
        pass
    
    def describe(self) -> str:
        """Common method for all shapes."""
        return f"{self.name}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"


class Rectangle(Shape):
    """Rectangle implementation."""
    
    def __init__(self, width: float, height: float):
        super().__init__("Rectangle")  # Call parent __init__
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height
    
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


class Circle(Shape):
    """Circle implementation."""
    
    import math
    
    def __init__(self, radius: float):
        super().__init__("Circle")
        self.radius = radius
    
    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2
    
    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius


# Polymorphism in action: same interface, different implementations
shapes = [Rectangle(5, 3), Circle(4), Rectangle(2, 2)]

for shape in shapes:
    print(shape.describe())

# Verify inheritance
rect = Rectangle(10, 5)
print(f"\nIs Rectangle a Shape? {isinstance(rect, Shape)}")
print(f"Is Rectangle a Rectangle? {isinstance(rect, Rectangle)}")
```

    Rectangle: area=15.00, perimeter=16.00
    Circle: area=50.27, perimeter=25.13
    Rectangle: area=4.00, perimeter=8.00
    
    Is Rectangle a Shape? True
    Is Rectangle a Rectangle? True


### 4.2 Method Overriding and `super()`

Child classes can override parent methods. Use `super()` to call parent implementation.


```python
class Vehicle:
    """Base class for vehicles."""
    
    def __init__(self, brand: str, model: str, year: int):
        self.brand = brand
        self.model = model
        self.year = year
    
    def start(self) -> str:
        return f"Starting {self.brand} {self.model}"
    
    def info(self) -> str:
        return f"{self.year} {self.brand} {self.model}"


class ElectricCar(Vehicle):
    """Electric car with battery."""
    
    def __init__(self, brand: str, model: str, year: int, battery_kwh: float):
        super().__init__(brand, model, year)  # Call parent __init__
        self.battery_kwh = battery_kwh
    
    def start(self) -> str:
        # Override parent method
        return f"🔋 Silently starting {self.brand} {self.model}"
    
    def info(self) -> str:
        # Extend parent method
        base_info = super().info()  # Get parent's info
        return f"{base_info} (Electric, {self.battery_kwh} kWh)"
    
    def charge(self, kwh: float) -> str:
        """New method specific to ElectricCar."""
        return f"Charging {kwh} kWh"


# Regular vehicle
car = Vehicle("Honda", "Civic", 2022)
print(car.start())
print(car.info())

print()

# Electric car
tesla = ElectricCar("Tesla", "Model 3", 2023, 75)
print(tesla.start())    # Overridden
print(tesla.info())     # Extended with super()
print(tesla.charge(50)) # New method
```

    Starting Honda Civic
    2022 Honda Civic
    
    🔋 Silently starting Tesla Model 3
    2023 Tesla Model 3 (Electric, 75 kWh)
    Charging 50 kWh


### 4.3 Liskov Substitution Principle (LSP)

> "Objects of a superclass should be replaceable with objects of a subclass without breaking the program."

**Bad Example**: Square inheriting from Rectangle breaks LSP because setting width should not affect height for a Rectangle, but must for a Square.


```python
# BAD: Violates LSP
class RectangleBad:
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height
    
    @property
    def width(self) -> float:
        return self._width
    
    @width.setter
    def width(self, value: float) -> None:
        self._width = value
    
    @property
    def height(self) -> float:
        return self._height
    
    @height.setter
    def height(self, value: float) -> None:
        self._height = value
    
    def area(self) -> float:
        return self._width * self._height


class SquareBad(RectangleBad):
    """Violates LSP: changing width also changes height."""
    
    def __init__(self, side: float):
        super().__init__(side, side)
    
    @RectangleBad.width.setter
    def width(self, value: float) -> None:
        self._width = value
        self._height = value  # Forces square constraint
    
    @RectangleBad.height.setter
    def height(self, value: float) -> None:
        self._height = value
        self._width = value  # Forces square constraint


def calculate_expected_area(shape: RectangleBad) -> float:
    """Function that expects normal Rectangle behavior."""
    shape.width = 5
    shape.height = 4
    # Expect area to be 5 * 4 = 20
    return shape.area()


rect = RectangleBad(3, 3)
square = SquareBad(3)

print(f"Rectangle area: {calculate_expected_area(rect)}")  # 20 ✓
print(f"Square area: {calculate_expected_area(square)}")    # 16 ✗ (LSP violated!)
print("\n⚠️ Square violates LSP: behavior changed unexpectedly")
```

    Rectangle area: 20
    Square area: 16
    
    ⚠️ Square violates LSP: behavior changed unexpectedly



```python
# GOOD: LSP-compliant design using shared base
from abc import ABC, abstractmethod

class ShapeLSP(ABC):
    """Abstract base for shapes - LSP compliant."""
    
    @abstractmethod
    def area(self) -> float:
        pass


class RectangleGood(ShapeLSP):
    """Rectangle that doesn't promise width/height independence."""
    
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height


class SquareGood(ShapeLSP):
    """Square as its own type, not a Rectangle subclass."""
    
    def __init__(self, side: float):
        self.side = side
    
    def area(self) -> float:
        return self.side ** 2


# Both work correctly with the interface
shapes_lsp = [RectangleGood(5, 4), SquareGood(4)]
for s in shapes_lsp:
    print(f"{s.__class__.__name__}: area = {s.area()}")

print("\n✓ LSP compliant: each shape behaves consistently")
```

    RectangleGood: area = 20
    SquareGood: area = 16
    
    ✓ LSP compliant: each shape behaves consistently


---

## 5. Composition vs Inheritance

**Inheritance**: "is-a" relationship (Dog is an Animal)
**Composition**: "has-a" relationship (Car has an Engine)

> **Prefer composition over inheritance** - it's more flexible and avoids tight coupling.

### 5.1 Composition Example: Computer System


```python
class CPU:
    """Central Processing Unit component."""
    
    def __init__(self, brand: str, cores: int, speed_ghz: float):
        self.brand = brand
        self.cores = cores
        self.speed_ghz = speed_ghz
    
    def process(self, task: str) -> str:
        return f"CPU processing '{task}' on {self.cores} cores at {self.speed_ghz}GHz"


class RAM:
    """Memory component."""
    
    def __init__(self, size_gb: int, type_: str = "DDR4"):
        self.size_gb = size_gb
        self.type_ = type_
    
    def load(self, data: str) -> str:
        return f"Loading '{data}' into {self.size_gb}GB {self.type_} RAM"


class Storage:
    """Storage component."""
    
    def __init__(self, size_gb: int, type_: str = "SSD"):
        self.size_gb = size_gb
        self.type_ = type_
    
    def save(self, file: str) -> str:
        return f"Saving '{file}' to {self.size_gb}GB {self.type_}"


class Computer:
    """Computer composed of components (has-a relationship)."""
    
    def __init__(self, name: str, cpu: CPU, ram: RAM, storage: Storage):
        self.name = name
        self.cpu = cpu        # Has-a CPU
        self.ram = ram        # Has-a RAM
        self.storage = storage  # Has-a Storage
    
    def run_program(self, program: str) -> None:
        """Run a program using all components."""
        print(f"--- {self.name} running '{program}' ---")
        print(self.storage.save(program))
        print(self.ram.load(program))
        print(self.cpu.process(program))
    
    def specs(self) -> str:
        """Return computer specifications."""
        return (f"{self.name}: {self.cpu.brand} {self.cpu.cores}-core, "
                f"{self.ram.size_gb}GB RAM, {self.storage.size_gb}GB {self.storage.type_}")


# Build a computer using composition
gaming_pc = Computer(
    name="Gaming Rig",
    cpu=CPU("AMD Ryzen 9", 12, 4.8),
    ram=RAM(32, "DDR5"),
    storage=Storage(2000, "NVMe SSD")
)

print(gaming_pc.specs())
print()
gaming_pc.run_program("Cyberpunk 2077")
```

    Gaming Rig: AMD Ryzen 9 12-core, 32GB RAM, 2000GB NVMe SSD
    
    --- Gaming Rig running 'Cyberpunk 2077' ---
    Saving 'Cyberpunk 2077' to 2000GB NVMe SSD
    Loading 'Cyberpunk 2077' into 32GB DDR5 RAM
    CPU processing 'Cyberpunk 2077' on 12 cores at 4.8GHz


---

## 6. Dataclasses

Dataclasses (Python 3.7+) reduce boilerplate for classes that mainly store data.

### 6.1 Basic Dataclass


```python
from dataclasses import dataclass, field
from typing import List

# Regular class (lots of boilerplate)
class ProductOld:
    def __init__(self, name: str, price: float, quantity: int = 0):
        self.name = name
        self.price = price
        self.quantity = quantity
    
    def __repr__(self):
        return f"ProductOld(name={self.name!r}, price={self.price}, quantity={self.quantity})"
    
    def __eq__(self, other):
        if not isinstance(other, ProductOld):
            return NotImplemented
        return (self.name, self.price, self.quantity) == (other.name, other.price, other.quantity)


# Dataclass (same functionality, less code!)
@dataclass
class Product:
    """Product with auto-generated __init__, __repr__, __eq__."""
    name: str
    price: float
    quantity: int = 0  # Default value
    
    def total_value(self) -> float:
        """You can still add custom methods."""
        return self.price * self.quantity


# Usage
laptop = Product("MacBook Pro", 2499.99, 5)
mouse = Product("Magic Mouse", 99.99)

print(laptop)  # Auto __repr__
print(f"Total value: ${laptop.total_value():.2f}")

# Auto __eq__
mouse2 = Product("Magic Mouse", 99.99)
print(f"\nmouse == mouse2: {mouse == mouse2}")  # True
```

    Product(name='MacBook Pro', price=2499.99, quantity=5)
    Total value: $12499.95
    
    mouse == mouse2: True


### 6.2 Frozen Dataclass (Immutable)

Use `frozen=True` to create immutable instances (like tuples).


```python
@dataclass(frozen=True)
class Coordinate:
    """Immutable coordinate - cannot be modified after creation."""
    latitude: float
    longitude: float
    
    def distance_to(self, other: "Coordinate") -> float:
        """Simplified distance calculation (not real geo distance)."""
        import math
        return math.sqrt(
            (self.latitude - other.latitude) ** 2 +
            (self.longitude - other.longitude) ** 2
        )

# Create immutable coordinates
home = Coordinate(27.7172, 85.3240)  # Kathmandu
office = Coordinate(27.6915, 85.3420)

print(f"Home: {home}")
print(f"Distance: {home.distance_to(office):.4f}")

# Cannot modify frozen dataclass
try:
    home.latitude = 28.0  # Will raise FrozenInstanceError
except Exception as e:
    print(f"\n✓ Cannot modify frozen: {type(e).__name__}")

# Frozen dataclasses can be used as dict keys or set elements
locations = {home: "Home", office: "Office"}
print(f"\nLocations dict: {locations}")
```

    Home: Coordinate(latitude=27.7172, longitude=85.324)
    Distance: 0.0314
    
    ✓ Cannot modify frozen: FrozenInstanceError
    
    Locations dict: {Coordinate(latitude=27.7172, longitude=85.324): 'Home', Coordinate(latitude=27.6915, longitude=85.342): 'Office'}


### 6.3 Default Factory for Mutable Defaults

Use `field(default_factory=...)` for mutable default values (lists, dicts).


```python
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ShoppingCart:
    """Shopping cart with mutable defaults done right."""
    customer_name: str
    # WRONG: items: List[str] = []  # Would share list across instances!
    # RIGHT: Use field with default_factory
    items: List[str] = field(default_factory=list)
    prices: Dict[str, float] = field(default_factory=dict)
    
    def add_item(self, item: str, price: float) -> None:
        self.items.append(item)
        self.prices[item] = price
    
    def total(self) -> float:
        return sum(self.prices.values())


# Each instance gets its own list/dict
cart1 = ShoppingCart("Alice")
cart1.add_item("Laptop", 999.99)
cart1.add_item("Mouse", 49.99)

cart2 = ShoppingCart("Bob")
cart2.add_item("Keyboard", 129.99)

print(f"Cart 1 ({cart1.customer_name}): {cart1.items} = ${cart1.total():.2f}")
print(f"Cart 2 ({cart2.customer_name}): {cart2.items} = ${cart2.total():.2f}")

# Verify they're independent
assert cart1.items is not cart2.items
print("\n✓ Each cart has independent items list")
```

    Cart 1 (Alice): ['Laptop', 'Mouse'] = $1049.98
    Cart 2 (Bob): ['Keyboard'] = $129.99
    
    ✓ Each cart has independent items list


---

## 7. Dunder Methods You Actually Use

"Dunder" = double underscore methods (`__name__`). They enable Python's syntactic sugar.

### 7.1 Container Methods: `__len__`, `__iter__`, `__contains__`


```python
class Playlist:
    """A playlist that behaves like a container."""
    
    def __init__(self, name: str):
        self.name = name
        self._songs: List[str] = []
    
    def add(self, song: str) -> None:
        self._songs.append(song)
    
    def __len__(self) -> int:
        """Enable len(playlist)."""
        return len(self._songs)
    
    def __iter__(self):
        """Enable for song in playlist."""
        return iter(self._songs)
    
    def __contains__(self, song: str) -> bool:
        """Enable 'song in playlist'."""
        return song in self._songs
    
    def __getitem__(self, index: int) -> str:
        """Enable playlist[0]."""
        return self._songs[index]
    
    def __repr__(self) -> str:
        return f"Playlist('{self.name}', {len(self)} songs)"


# Create and populate playlist
playlist = Playlist("Road Trip Mix")
playlist.add("Hotel California")
playlist.add("Bohemian Rhapsody")
playlist.add("Stairway to Heaven")

# Now use Python's built-in operations
print(f"Playlist: {playlist}")
print(f"Length: {len(playlist)}")                    # __len__
print(f"First song: {playlist[0]}")                  # __getitem__
print(f"Contains 'Yesterday': {'Yesterday' in playlist}")  # __contains__
print(f"Contains 'Hotel California': {'Hotel California' in playlist}")

print("\nAll songs:")
for song in playlist:  # __iter__
    print(f"  ♪ {song}")
```

    Playlist: Playlist('Road Trip Mix', 3 songs)
    Length: 3
    First song: Hotel California
    Contains 'Yesterday': False
    Contains 'Hotel California': True
    
    All songs:
      ♪ Hotel California
      ♪ Bohemian Rhapsody
      ♪ Stairway to Heaven


### 7.2 Equality and Ordering: `__eq__`, `__lt__`, etc.


```python
from functools import total_ordering

@total_ordering  # Generates other comparisons from __eq__ and __lt__
class Version:
    """Software version with comparison support."""
    
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch
    
    def __repr__(self) -> str:
        return f"Version({self.major}, {self.minor}, {self.patch})"
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __eq__(self, other: object) -> bool:
        """Enable == comparison."""
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __lt__(self, other: "Version") -> bool:
        """Enable < comparison. @total_ordering provides <=, >, >=."""
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __hash__(self) -> int:
        """Make hashable for use in sets/dicts."""
        return hash((self.major, self.minor, self.patch))


# Create versions
v1 = Version(1, 0, 0)
v2 = Version(1, 2, 3)
v3 = Version(2, 0, 0)
v4 = Version(1, 2, 3)

print(f"v1 = {v1}, v2 = {v2}, v3 = {v3}")
print(f"v2 == v4: {v2 == v4}")
print(f"v1 < v2: {v1 < v2}")
print(f"v3 > v2: {v3 > v2}")

# Sorting works automatically
versions = [v3, v1, v2]
print(f"\nSorted: {sorted(versions)}")
```

    v1 = 1.0.0, v2 = 1.2.3, v3 = 2.0.0
    v2 == v4: True
    v1 < v2: True
    v3 > v2: True
    
    Sorted: [Version(1, 0, 0), Version(1, 2, 3), Version(2, 0, 0)]


---

## 8. Real-Life Mini-Project: Food Delivery Order System

Let's build a complete system demonstrating OOP concepts:
- **Classes**: `Customer`, `MenuItem`, `Order`
- **Composition**: Order has MenuItems
- **Encapsulation**: Validated properties
- **Polymorphism**: Different discount strategies

### 8.1 Core Classes


```python
from dataclasses import dataclass, field
from typing import List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class Category(Enum):
    """Menu item categories."""
    APPETIZER = "appetizer"
    MAIN = "main"
    DESSERT = "dessert"
    BEVERAGE = "beverage"


@dataclass
class MenuItem:
    """A single menu item with pricing."""
    name: str
    price: float
    category: Category
    is_vegetarian: bool = False
    
    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")
    
    def __str__(self) -> str:
        veg = " (V)" if self.is_vegetarian else ""
        return f"{self.name}{veg} - ${self.price:.2f}"


@dataclass
class Customer:
    """A customer with loyalty status."""
    name: str
    email: str
    phone: str
    is_premium: bool = False
    orders_count: int = 0
    
    def __str__(self) -> str:
        status = "Premium" if self.is_premium else "Regular"
        return f"{self.name} ({status} - {self.orders_count} orders)"


# Abstract base for discount strategies (Strategy Pattern preview)
class DiscountStrategy(ABC):
    """Abstract discount strategy."""
    
    @abstractmethod
    def calculate_discount(self, subtotal: float, customer: Customer) -> float:
        """Return discount amount."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class NoDiscount(DiscountStrategy):
    """No discount applied."""
    
    def calculate_discount(self, subtotal: float, customer: Customer) -> float:
        return 0.0
    
    @property
    def name(self) -> str:
        return "No discount"


class PremiumDiscount(DiscountStrategy):
    """10% off for premium customers."""
    
    def calculate_discount(self, subtotal: float, customer: Customer) -> float:
        if customer.is_premium:
            return subtotal * 0.10
        return 0.0
    
    @property
    def name(self) -> str:
        return "Premium 10% off"


class BulkDiscount(DiscountStrategy):
    """15% off for orders over $50."""
    
    def calculate_discount(self, subtotal: float, customer: Customer) -> float:
        if subtotal >= 50:
            return subtotal * 0.15
        return 0.0
    
    @property
    def name(self) -> str:
        return "Bulk 15% off (orders $50+)"


print("✓ Core classes defined")
```

    ✓ Core classes defined


### 8.2 The Order Class (Composition)


```python
class Order:
    """
    An order that HAS-A customer and HAS MenuItems (composition).
    Demonstrates encapsulation and composition.
    """
    
    _order_counter = 0  # Class attribute for order numbering
    TAX_RATE = 0.13     # 13% tax
    
    def __init__(self, customer: Customer, discount_strategy: DiscountStrategy = None):
        Order._order_counter += 1
        self._order_id = Order._order_counter
        self._customer = customer              # Composition: Order HAS-A Customer
        self._items: List[tuple[MenuItem, int]] = []  # (item, quantity)
        self._discount_strategy = discount_strategy or NoDiscount()
        self._created_at = datetime.now()
        self._is_completed = False
    
    @property
    def order_id(self) -> int:
        return self._order_id
    
    @property
    def customer(self) -> Customer:
        return self._customer
    
    @property
    def is_completed(self) -> bool:
        return self._is_completed
    
    def add_item(self, item: MenuItem, quantity: int = 1) -> None:
        """Add item to order."""
        if self._is_completed:
            raise ValueError("Cannot modify completed order")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        self._items.append((item, quantity))
    
    @property
    def subtotal(self) -> float:
        """Calculate subtotal before tax and discount."""
        return sum(item.price * qty for item, qty in self._items)
    
    @property
    def discount_amount(self) -> float:
        """Calculate discount based on strategy."""
        return self._discount_strategy.calculate_discount(
            self.subtotal, self._customer
        )
    
    @property
    def tax_amount(self) -> float:
        """Calculate tax on discounted amount."""
        return (self.subtotal - self.discount_amount) * self.TAX_RATE
    
    @property
    def total(self) -> float:
        """Calculate final total."""
        return self.subtotal - self.discount_amount + self.tax_amount
    
    def complete(self) -> None:
        """Mark order as completed."""
        self._is_completed = True
        self._customer.orders_count += 1
    
    # Container methods
    def __len__(self) -> int:
        """Return number of line items."""
        return len(self._items)
    
    def __iter__(self):
        """Iterate over items."""
        return iter(self._items)
    
    def __str__(self) -> str:
        lines = [
            f"═══ Order #{self._order_id} ═══",
            f"Customer: {self._customer.name}",
            f"Date: {self._created_at.strftime('%Y-%m-%d %H:%M')}",
            "─" * 30,
        ]
        for item, qty in self._items:
            lines.append(f"  {qty}x {item.name:<20} ${item.price * qty:.2f}")
        lines.extend([
            "─" * 30,
            f"  {'Subtotal:':<22} ${self.subtotal:.2f}",
            f"  {self._discount_strategy.name:<22} -${self.discount_amount:.2f}",
            f"  {'Tax (13%):':<22} ${self.tax_amount:.2f}",
            "═" * 30,
            f"  {'TOTAL:':<22} ${self.total:.2f}",
        ])
        return "\n".join(lines)


print("✓ Order class defined")
```

    ✓ Order class defined


### 8.3 Demo: Creating Orders


```python
# Create menu items
menu = [
    MenuItem("Spring Rolls", 8.99, Category.APPETIZER, is_vegetarian=True),
    MenuItem("Chicken Wings", 12.99, Category.APPETIZER),
    MenuItem("Margherita Pizza", 16.99, Category.MAIN, is_vegetarian=True),
    MenuItem("Grilled Salmon", 24.99, Category.MAIN),
    MenuItem("Tiramisu", 9.99, Category.DESSERT),
    MenuItem("Iced Tea", 3.99, Category.BEVERAGE),
]

# Create customers
alice = Customer("Alice", "alice@example.com", "555-1234", is_premium=True)
bob = Customer("Bob", "bob@example.com", "555-5678")

print("=== Menu ===")
for item in menu:
    print(f"  {item}")
print()

# Create an order with premium discount
order1 = Order(alice, PremiumDiscount())
order1.add_item(menu[3], 2)  # 2x Grilled Salmon
order1.add_item(menu[0], 1)  # 1x Spring Rolls
order1.add_item(menu[5], 2)  # 2x Iced Tea

print(order1)
```

    === Menu ===
      Spring Rolls (V) - $8.99
      Chicken Wings - $12.99
      Margherita Pizza (V) - $16.99
      Grilled Salmon - $24.99
      Tiramisu - $9.99
      Iced Tea - $3.99
    
    ═══ Order #1 ═══
    Customer: Alice
    Date: 2026-03-09 21:35
    ──────────────────────────────
      2x Grilled Salmon       $49.98
      1x Spring Rolls         $8.99
      2x Iced Tea             $7.98
    ──────────────────────────────
      Subtotal:              $66.95
      Premium 10% off        -$6.70
      Tax (13%):             $7.83
    ══════════════════════════════
      TOTAL:                 $68.09


### 8.4 What-If Scenarios


```python
print("═══ WHAT-IF SCENARIOS ═══\n")

# Scenario 1: Regular customer, no discount vs bulk discount
order_no_disc = Order(bob, NoDiscount())
order_bulk = Order(bob, BulkDiscount())

# Add same items to both
for order in [order_no_disc, order_bulk]:
    order.add_item(menu[2], 2)  # 2x Pizza
    order.add_item(menu[4], 2)  # 2x Tiramisu

print("Scenario 1: Same order, different discount strategies")
print(f"  No discount total: ${order_no_disc.total:.2f}")
print(f"  Bulk discount total: ${order_bulk.total:.2f}")
print(f"  Savings: ${order_no_disc.total - order_bulk.total:.2f}")

print()

# Scenario 2: Premium customer with different order sizes
print("Scenario 2: Premium customer - small vs large order")
small_order = Order(alice, PremiumDiscount())
small_order.add_item(menu[5], 1)  # Just a drink

large_order = Order(alice, PremiumDiscount())
large_order.add_item(menu[3], 3)  # 3x Salmon
large_order.add_item(menu[4], 2)  # 2x Tiramisu

print(f"  Small order (1 drink): ${small_order.total:.2f}")
print(f"  Large order: ${large_order.total:.2f}")
print(f"  Premium discount on large: ${large_order.discount_amount:.2f}")

print()

# Scenario 3: Comparing strategies for the same large order
print("Scenario 3: Which discount is better for $70+ order?")
base_amount = 70.0

premium_disc = PremiumDiscount().calculate_discount(base_amount, alice)
bulk_disc = BulkDiscount().calculate_discount(base_amount, alice)

print(f"  On ${base_amount:.2f} order:")
print(f"    Premium (10%): saves ${premium_disc:.2f}")
print(f"    Bulk (15%): saves ${bulk_disc:.2f}")
print(f"  → Bulk discount is better by ${bulk_disc - premium_disc:.2f}")
```

    ═══ WHAT-IF SCENARIOS ═══
    
    Scenario 1: Same order, different discount strategies
      No discount total: $60.97
      Bulk discount total: $51.83
      Savings: $9.15
    
    Scenario 2: Premium customer - small vs large order
      Small order (1 drink): $4.06
      Large order: $96.56
      Premium discount on large: $9.50
    
    Scenario 3: Which discount is better for $70+ order?
      On $70.00 order:
        Premium (10%): saves $7.00
        Bulk (15%): saves $10.50
      → Bulk discount is better by $3.50


---

## 9. Practice Section: In-Class Exercises

Complete these exercises during class. Each includes a hint and expected outcome.

### Exercise 1: Counter Class

Create a `Counter` class that:
- Starts at 0 (or a given value)
- Has `increment()`, `decrement()`, `reset()` methods
- Has a `value` property (read-only)

**Hint**: Use `__init__` with a default parameter and a property for read-only access.

**Expected**: `Counter().increment().increment().value` → `2`


```python
# Exercise 1: Your code here
class Counter:
    pass

# Test (uncomment when ready):
# c = Counter()
# c.increment()
# c.increment()
# assert c.value == 2
# c.decrement()
# assert c.value == 1
# c.reset()
# assert c.value == 0
# print("✓ Exercise 1 passed!")
```

### Exercise 2: Temperature Converter (Classmethod)

Add a `from_fahrenheit(cls, f)` classmethod to convert from Fahrenheit.

**Hint**: Formula is `(f - 32) * 5/9`

**Expected**: `Temperature.from_fahrenheit(212).celsius` → `100.0`


```python
# Exercise 2: Your code here
class TemperatureEx2:
    def __init__(self, celsius: float):
        self.celsius = celsius
    
    # TODO: Add from_fahrenheit classmethod

# Test:
# t = TemperatureEx2.from_fahrenheit(212)
# assert t.celsius == 100.0
# print("✓ Exercise 2 passed!")
```

### Exercise 3: Password Property with Validation

Create a `UserAccount` class where the `password` property must be at least 8 characters.

**Hint**: Raise `ValueError` in the setter if validation fails.

**Expected**: Setting password to "abc" should raise ValueError.


```python
# Exercise 3: Your code here
class UserAccount:
    pass

# Test:
# user = UserAccount("alice", "secure123")  # Should work
# try:
#     user.password = "short"  # Should raise ValueError
#     print("✗ Should have raised ValueError")
# except ValueError:
#     print("✓ Exercise 3 passed!")
```

### Exercise 4: Animal Inheritance

Create `Animal` base class and `Dog`, `Cat` subclasses with `speak()` method.

**Hint**: Each subclass returns different sound ("Woof!" vs "Meow!").

**Expected**: `Dog("Rex").speak()` → `"Rex says Woof!"`


```python
# Exercise 4: Your code here
class Animal:
    pass

class Dog(Animal):
    pass

class Cat(Animal):
    pass

# Test:
# assert Dog("Rex").speak() == "Rex says Woof!"
# assert Cat("Whiskers").speak() == "Whiskers says Meow!"
# print("✓ Exercise 4 passed!")
```

### Exercise 5: Dataclass with Validation

Create a `Product` dataclass with `name`, `price`, `stock`. Use `__post_init__` to validate price >= 0.

**Hint**: `__post_init__` runs after auto-generated `__init__`.

**Expected**: `Product("X", -5, 10)` should raise ValueError.


```python
# Exercise 5: Your code here
from dataclasses import dataclass

@dataclass
class ProductEx5:
    name: str
    price: float
    stock: int
    # TODO: Add __post_init__ for validation

# Test:
# p = ProductEx5("Widget", 9.99, 100)  # Should work
# try:
#     ProductEx5("Bad", -5, 10)  # Should raise
#     print("✗ Should have raised ValueError")
# except ValueError:
#     print("✓ Exercise 5 passed!")
```

### Exercise 6: Make it Iterable

Add `__len__` and `__iter__` to this `TaskList` class.

**Hint**: Delegate to the internal `_tasks` list.

**Expected**: `list(task_list)` should return the tasks.


```python
# Exercise 6: Your code here
class TaskList:
    def __init__(self):
        self._tasks = []
    
    def add(self, task: str):
        self._tasks.append(task)
    
    # TODO: Add __len__
    # TODO: Add __iter__

# Test:
# tl = TaskList()
# tl.add("Buy milk")
# tl.add("Call mom")
# assert len(tl) == 2
# assert list(tl) == ["Buy milk", "Call mom"]
# print("✓ Exercise 6 passed!")
```

### Exercise 7: Composition - Library System

Create `Library` that HAS `Book` objects. Implement `add_book()` and `find_by_author()`.

**Hint**: Store books in a list, filter by author name.

**Expected**: `library.find_by_author("Rowling")` returns matching books.


```python
# Exercise 7: Your code here
@dataclass
class BookEx7:
    title: str
    author: str

class Library:
    pass
    # TODO: Implement add_book and find_by_author

# Test:
# lib = Library()
# lib.add_book(BookEx7("Harry Potter", "J.K. Rowling"))
# lib.add_book(BookEx7("Clean Code", "Robert Martin"))
# rowling_books = lib.find_by_author("Rowling")
# assert len(rowling_books) == 1
# print("✓ Exercise 7 passed!")
```

### Exercise 8: Implement `__eq__` and `__hash__`

Make `Student` comparable by student_id and usable in sets.

**Hint**: Two students are equal if they have the same student_id.

**Expected**: `Student("Alice", 1) == Student("Alice Smith", 1)` → True
