# SOLID Principles in Python

SOLID is a set of five design rules for object-oriented code. In this notebook we take each rule, look at a small piece of code that breaks it, fix it, and then use all five together in an order-processing example.

### Learning Objectives

By the end of this notebook you will be able to:

1. Explain each of the five SOLID principles in your own words
2. Spot code that breaks a principle (the "code smell")
3. Refactor that code using small classes, abstract base classes and dependency injection
4. Write fake (mock) objects to test a class without a real database or email server
5. Combine the principles in a small but realistic design

### Prerequisites

- The **OOP Foundations** notebook (classes, inheritance, composition, dataclasses)
- Python 3.10 or newer
- Basic idea of an abstract class (`from abc import ABC, abstractmethod`). We'll recap it as we go.

### How to Use This Notebook

- Run the cells **from top to bottom**. Some later cells reuse classes defined earlier.
- Every principle has a **bad example** and a **good example**. Run both and compare the output before reading the explanation.
- The **Practice Exercises** at the end are for you. Write your answer first, then open *Show solution* to compare.
- Each section ends with a **Quick recap**. Read only the recaps when revising before an exam.

### The Five Principles at a Glance

| Letter | Principle | In one line |
|---|---|---|
| **S** | Single Responsibility | A class should have only one reason to change. |
| **O** | Open/Closed | Add new behaviour by adding code, not by editing working code. |
| **L** | Liskov Substitution | A subclass must work anywhere its parent class works. |
| **I** | Interface Segregation | Many small interfaces beat one big one. |
| **D** | Dependency Inversion | Depend on abstractions, not on concrete classes. |

Don't try to memorise the table yet. It will make much more sense after you've seen the examples.

---

## 1. Single Responsibility Principle (SRP)

> *"A class should have only one reason to change."*

A good way to test this: ask **who** might ask you to change the class. If the answer is "HR, the database team *and* the managers", the class is doing too many jobs.

### Bad Example: One Class, Three Jobs


```python
# BAD: This class has multiple responsibilities
class Employee:
    def __init__(self, name: str, salary: float):
        self.name = name
        self.salary = salary
    
    def calculate_pay(self) -> float:
        """Calculate monthly pay - HR responsibility"""
        return self.salary / 12
    
    def save_to_database(self):
        """Save employee to database - Database responsibility"""
        print(f"Saving {self.name} to database...")
    
    def generate_report(self) -> str:
        """Generate employee report - Reporting responsibility"""
        return f"Employee Report: {self.name}, Annual Salary: ${self.salary}"

# Usage
emp = Employee("John Doe", 60000)
print(emp.calculate_pay())
print(emp.generate_report())
```

    5000.0
    Employee Report: John Doe, Annual Salary: $60000


This works, but look at who would ask us to edit `Employee`:

- HR changes how pay is calculated, so we edit `calculate_pay`.
- We move from one database to another, so we edit `save_to_database`.
- The manager wants a new report layout, so we edit `generate_report`.

Three different reasons to change one class. Every edit risks breaking the other two jobs.

### Good Example: Split by Responsibility


```python
# GOOD: Each class has a single responsibility

class Employee:
    """Only responsible for employee data"""
    def __init__(self, name: str, salary: float):
        self.name = name
        self.salary = salary


class PayrollCalculator:
    """Responsible for pay calculations"""
    @staticmethod
    def calculate_monthly_pay(employee: Employee) -> float:
        return employee.salary / 12
    
    @staticmethod
    def calculate_bonus(employee: Employee, percentage: float) -> float:
        return employee.salary * percentage / 100


class EmployeeRepository:
    """Responsible for database operations"""
    def save(self, employee: Employee):
        print(f"Saving {employee.name} to database...")
    
    def find_by_name(self, name: str) -> Employee | None:
        # Database lookup logic would go here
        return None


class EmployeeReportGenerator:
    """Responsible for generating reports"""
    @staticmethod
    def generate_summary(employee: Employee) -> str:
        return f"Employee Report: {employee.name}, Annual Salary: ${employee.salary}"
    
    @staticmethod
    def generate_detailed_report(employee: Employee) -> str:
        monthly = PayrollCalculator.calculate_monthly_pay(employee)
        return f"Detailed Report\nName: {employee.name}\nAnnual: ${employee.salary}\nMonthly: ${monthly:.2f}"


# Usage
emp = Employee("John Doe", 60000)
print(PayrollCalculator.calculate_monthly_pay(emp))
print(EmployeeReportGenerator.generate_detailed_report(emp))
```

    5000.0
    Detailed Report
    Name: John Doe
    Annual: $60000
    Monthly: $5000.00


Now each class has one job:

- `Employee` just holds the data.
- `PayrollCalculator` knows the pay rules.
- `EmployeeRepository` talks to the database.
- `EmployeeReportGenerator` builds reports.

If the report layout changes, we only touch `EmployeeReportGenerator`. Payroll can't break by accident.

SRP does **not** mean "one method per class". `PayrollCalculator` has two methods, and that's fine, because both are about pay.

**Quick recap**

- SRP: a class should have one reason to change, i.e. one job.
- Ask *who* would request a change. Several different people means several responsibilities.
- Fix it by moving each job into its own small class.
- One responsibility can still mean several related methods.

---

## 2. Open/Closed Principle (OCP)

> *"Software entities should be open for extension, but closed for modification."*

In plain words: when a new requirement arrives, you should be able to **add** a new class instead of **editing** code that already works and is already tested.

### Bad Example: A Growing `if/elif` Chain


```python
# BAD: Adding new discount types requires modifying this class
class DiscountCalculator:
    def calculate_discount(self, customer_type: str, amount: float) -> float:
        if customer_type == "regular":
            return amount * 0.1
        elif customer_type == "premium":
            return amount * 0.2
        elif customer_type == "vip":
            return amount * 0.3
        # Every new customer type requires modifying this method!
        else:
            return 0

calc = DiscountCalculator()
print(f"Regular discount: ${calc.calculate_discount('regular', 100)}")
print(f"VIP discount: ${calc.calculate_discount('vip', 100)}")
```

    Regular discount: $10.0
    VIP discount: $30.0


Every new customer type (student, staff, festival offer...) means opening `calculate_discount` and adding another `elif`. The method keeps growing, and each edit can break the cases that already worked.

### Good Example: One Class per Discount


```python
from abc import ABC, abstractmethod

# GOOD: Open for extension (new discount strategies), closed for modification

class DiscountStrategy(ABC):
    """Abstract base class for discount strategies"""
    @abstractmethod
    def calculate(self, amount: float) -> float:
        pass


class RegularDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return amount * 0.1


class PremiumDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return amount * 0.2


class VIPDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return amount * 0.3


# Easy to add new discount types without modifying existing code!
class SeasonalDiscount(DiscountStrategy):
    def __init__(self, seasonal_rate: float = 0.15):
        self.seasonal_rate = seasonal_rate
    
    def calculate(self, amount: float) -> float:
        return amount * self.seasonal_rate


class DiscountCalculator:
    """Calculator that works with any discount strategy"""
    def __init__(self, strategy: DiscountStrategy):
        self.strategy = strategy
    
    def apply_discount(self, amount: float) -> float:
        discount = self.strategy.calculate(amount)
        return amount - discount


# Usage
amount = 100

regular_calc = DiscountCalculator(RegularDiscount())
print(f"Regular: ${amount} -> ${regular_calc.apply_discount(amount)}")

vip_calc = DiscountCalculator(VIPDiscount())
print(f"VIP: ${amount} -> ${vip_calc.apply_discount(amount)}")

seasonal_calc = DiscountCalculator(SeasonalDiscount(0.25))
print(f"Seasonal (25%): ${amount} -> ${seasonal_calc.apply_discount(amount)}")
```

    Regular: $100 -> $90.0
    VIP: $100 -> $70.0
    Seasonal (25%): $100 -> $75.0


What just happened:

- `DiscountStrategy` is an **abstract base class**. It says "every discount must have a `calculate` method" but doesn't say how.
- Each discount type is its own small class.
- `DiscountCalculator` only knows about `DiscountStrategy`. It has no idea which discount it was given.

We added `SeasonalDiscount` **without touching** `DiscountCalculator`. That is the Open/Closed principle in action. (This shape is also called the *Strategy pattern*; you'll meet it again in the Design Patterns notebook.)

**Quick recap**

- OCP: extend behaviour by adding new code, not by editing working code.
- A long `if/elif` on a "type" string is the classic warning sign.
- Fix it with an abstract base class and one subclass per variation.
- The class that *uses* the strategies never needs to change when a new one is added.

---

## 3. Liskov Substitution Principle (LSP)

> *"Objects of a superclass should be replaceable with objects of its subclasses without breaking the application."*

If `B` inherits from `A`, any code written for an `A` must still work when you hand it a `B`. Same methods, same behaviour that the caller expects, no surprises.

### Bad Example: Square Inherits from Rectangle


```python
# BAD: Square violates the expected behavior of Rectangle
class Rectangle:
    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height
    
    @property
    def width(self) -> int:
        return self._width
    
    @width.setter
    def width(self, value: int):
        self._width = value
    
    @property
    def height(self) -> int:
        return self._height
    
    @height.setter
    def height(self, value: int):
        self._height = value
    
    def area(self) -> int:
        return self._width * self._height


class Square(Rectangle):
    def __init__(self, size: int):
        super().__init__(size, size)
    
    @Rectangle.width.setter
    def width(self, value: int):
        # This breaks LSP - changing width also changes height
        self._width = value
        self._height = value
    
    @Rectangle.height.setter
    def height(self, value: int):
        # This breaks LSP - changing height also changes width
        self._width = value
        self._height = value


def print_area(shape: Rectangle):
    shape.width = 5
    shape.height = 10
    # We expect area to be 50 for any Rectangle
    print(f"Expected area: 50, Actual area: {shape.area()}")

# This works correctly
rect = Rectangle(2, 3)
print_area(rect)

# This violates LSP - we get 100 instead of 50!
square = Square(5)
print_area(square)
```

    Expected area: 50, Actual area: 50
    Expected area: 50, Actual area: 100


What just happened: `print_area` sets the width to 5 and the height to 10 and expects an area of 50. That's a fair expectation for any rectangle.

But `Square` overrides the setters so that changing one side changes both. Setting the height to 10 also sets the width to 10, so we get 100.

In maths a square *is* a rectangle. In code, it doesn't **behave** like our `Rectangle` (whose sides can change independently), so it shouldn't inherit from it.

### Good Example: A Shared `Shape` Base Class


```python
import math
from abc import ABC, abstractmethod

# GOOD: Use a common abstraction that both shapes can properly implement

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        pass


class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height
    
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


class Square(Shape):
    def __init__(self, side: float):
        self.side = side
    
    def area(self) -> float:
        return self.side ** 2
    
    def perimeter(self) -> float:
        return 4 * self.side


class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius
    
    def area(self) -> float:
        return math.pi * self.radius ** 2
    
    def perimeter(self) -> float:
        return 2 * math.pi * self.radius


def print_shape_info(shape: Shape):
    """Works correctly with any Shape subclass"""
    print(f"Area: {shape.area():.2f}, Perimeter: {shape.perimeter():.2f}")


# All shapes work correctly - LSP is satisfied
shapes = [
    Rectangle(5, 10),
    Square(7),
    Circle(5)
]

for shape in shapes:
    print(f"{shape.__class__.__name__}: ", end="")
    print_shape_info(shape)
```

    Rectangle: Area: 50.00, Perimeter: 30.00
    Square: Area: 49.00, Perimeter: 28.00
    Circle: Area: 78.54, Perimeter: 31.42


Now `Rectangle`, `Square` and `Circle` are siblings. They all promise the same thing (`area()` and `perimeter()`), and they all keep that promise. `print_shape_info` works for every one of them with no special cases.

A useful test for LSP: if you ever write `if isinstance(shape, Square): ...` to work around a subclass, the design probably breaks LSP.

**Quick recap**

- LSP: a subclass must work anywhere its parent works, with no surprises.
- "Is-a" in real life doesn't automatically mean "is-a" in code. Check the *behaviour*.
- Warning signs: overridden methods that change the meaning, or `isinstance` checks to handle one subclass.
- Fix it by inheriting from a common, more general base class instead.

---

## 4. Interface Segregation Principle (ISP)

> *"Clients should not be forced to depend on interfaces they do not use."*

Python has no `interface` keyword. An abstract base class full of `@abstractmethod`s plays that role. ISP says: keep those small and focused, so a class only signs up for the methods it can really provide.

### Bad Example: One Big `Worker` Interface


```python
from abc import ABC, abstractmethod

# BAD: One large interface that forces classes to implement methods they don't need
class Worker(ABC):
    @abstractmethod
    def work(self):
        pass
    
    @abstractmethod
    def eat(self):
        pass
    
    @abstractmethod
    def sleep(self):
        pass
    
    @abstractmethod
    def code(self):
        pass
    
    @abstractmethod
    def manage(self):
        pass


class Developer(Worker):
    def work(self):
        print("Developer is working")
    
    def eat(self):
        print("Developer is eating")
    
    def sleep(self):
        print("Developer is sleeping")
    
    def code(self):
        print("Developer is coding")
    
    def manage(self):
        # Developers don't manage! But forced to implement this
        raise NotImplementedError("Developers don't manage!")


class Robot(Worker):
    def work(self):
        print("Robot is working")
    
    def eat(self):
        # Robots don't eat! But forced to implement this
        raise NotImplementedError("Robots don't eat!")
    
    def sleep(self):
        # Robots don't sleep!
        raise NotImplementedError("Robots don't sleep!")
    
    def code(self):
        print("Robot is coding")
    
    def manage(self):
        raise NotImplementedError("Robots don't manage!")


dev = Developer()
dev.code()
```

    Developer is coding


`Robot` has to write `eat()` and `sleep()` just to satisfy the abstract class, so it raises `NotImplementedError`. Any code that loops over workers and calls `worker.eat()` will crash on a robot. A method that only raises is a strong sign the interface is too big.

### Good Example: Small, Focused Interfaces


```python
from abc import ABC, abstractmethod

# GOOD: Small, specific interfaces

class Workable(ABC):
    @abstractmethod
    def work(self):
        pass


class Eatable(ABC):
    @abstractmethod
    def eat(self):
        pass


class Sleepable(ABC):
    @abstractmethod
    def sleep(self):
        pass


class Codeable(ABC):
    @abstractmethod
    def code(self):
        pass


class Manageable(ABC):
    @abstractmethod
    def manage(self):
        pass


# Developer implements only what it needs
class Developer(Workable, Eatable, Sleepable, Codeable):
    def work(self):
        print("Developer is working")
    
    def eat(self):
        print("Developer is eating")
    
    def sleep(self):
        print("Developer is sleeping")
    
    def code(self):
        print("Developer is coding")


# Manager implements only what it needs
class Manager(Workable, Eatable, Sleepable, Manageable):
    def work(self):
        print("Manager is working")
    
    def eat(self):
        print("Manager is eating")
    
    def sleep(self):
        print("Manager is sleeping")
    
    def manage(self):
        print("Manager is managing the team")


# Robot only implements what robots can do
class Robot(Workable, Codeable):
    def work(self):
        print("Robot is working")
    
    def code(self):
        print("Robot is coding")


# Usage
dev = Developer()
dev.work()
dev.code()

robot = Robot()
robot.work()
robot.code()
```

    Developer is working
    Developer is coding
    Robot is working
    Robot is coding


Each class now picks only the interfaces it needs through multiple inheritance. `Robot` is `Workable` and `Codeable`, nothing more. Code that needs something that can eat should ask for an `Eatable`, and a robot simply won't be one.

**Quick recap**

- ISP: don't force a class to implement methods it can't use.
- A method whose only job is `raise NotImplementedError` is a red flag.
- Split one big abstract class into several small ones.
- A class can inherit from several small interfaces at once.

---

## 5. Dependency Inversion Principle (DIP)

> *"High-level modules should not depend on low-level modules. Both should depend on abstractions."*
>
> *"Abstractions should not depend on details. Details should depend on abstractions."*

- **High-level** code is your business logic, e.g. "create a user and welcome them".
- **Low-level** code is the details, e.g. "talk to MySQL", "send an email".

DIP says the business logic shouldn't be glued to one particular database or email service.

### Bad Example: `UserService` Creates Its Own Dependencies


```python
# BAD: High-level module directly depends on low-level modules

class MySQLDatabase:
    def connect(self):
        print("Connecting to MySQL...")
    
    def execute(self, query: str):
        print(f"MySQL executing: {query}")


class EmailService:
    def send_email(self, to: str, message: str):
        print(f"Sending email to {to}: {message}")


class UserService:
    """High-level module directly depends on concrete implementations"""
    def __init__(self):
        # Tightly coupled to specific implementations
        self.database = MySQLDatabase()
        self.email_service = EmailService()
    
    def create_user(self, name: str, email: str):
        self.database.connect()
        self.database.execute(f"INSERT INTO users VALUES ('{name}', '{email}')")
        self.email_service.send_email(email, f"Welcome, {name}!")


# Hard to test, hard to switch databases or email providers
service = UserService()
service.create_user("John", "john@example.com")
```

    Connecting to MySQL...
    MySQL executing: INSERT INTO users VALUES ('John', 'john@example.com')
    Sending email to john@example.com: Welcome, John!


`UserService` builds a `MySQLDatabase` and an `EmailService` inside `__init__`. To switch to PostgreSQL or SMS, we'd have to edit `UserService`. Worse, we can't test it without a real MySQL server and a real mail server.

(Side note: we build SQL with an f-string here only to keep the demo short. Real code must use parameterised queries to avoid SQL injection.)

### Good Example: Depend on Abstractions


```python
from abc import ABC, abstractmethod

# GOOD: Depend on abstractions

# Abstractions (Interfaces)
class Database(ABC):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def execute(self, query: str):
        pass


class NotificationService(ABC):
    @abstractmethod
    def send(self, to: str, message: str):
        pass


# Concrete implementations
class MySQLDatabase(Database):
    def connect(self):
        print("Connecting to MySQL...")
    
    def execute(self, query: str):
        print(f"MySQL executing: {query}")


class PostgreSQLDatabase(Database):
    def connect(self):
        print("Connecting to PostgreSQL...")
    
    def execute(self, query: str):
        print(f"PostgreSQL executing: {query}")


class EmailNotification(NotificationService):
    def send(self, to: str, message: str):
        print(f"Email to {to}: {message}")


class SMSNotification(NotificationService):
    def send(self, to: str, message: str):
        print(f"SMS to {to}: {message}")


class PushNotification(NotificationService):
    def send(self, to: str, message: str):
        print(f"Push notification to {to}: {message}")


# High-level module depends on abstractions
class UserService:
    def __init__(self, database: Database, notifier: NotificationService):
        self.database = database
        self.notifier = notifier
    
    def create_user(self, name: str, contact: str):
        self.database.connect()
        self.database.execute(f"INSERT INTO users VALUES ('{name}', '{contact}')")
        self.notifier.send(contact, f"Welcome, {name}!")


# Easy to switch implementations!
print("Using MySQL + Email:")
service1 = UserService(MySQLDatabase(), EmailNotification())
service1.create_user("John", "john@example.com")

print("\nUsing PostgreSQL + SMS:")
service2 = UserService(PostgreSQLDatabase(), SMSNotification())
service2.create_user("Jane", "+1234567890")
```

    Using MySQL + Email:
    Connecting to MySQL...
    MySQL executing: INSERT INTO users VALUES ('John', 'john@example.com')
    Email to john@example.com: Welcome, John!
    
    Using PostgreSQL + SMS:
    Connecting to PostgreSQL...
    PostgreSQL executing: INSERT INTO users VALUES ('Jane', '+1234567890')
    SMS to +1234567890: Welcome, Jane!


What just happened:

- `Database` and `NotificationService` are abstractions (abstract base classes).
- `UserService` asks for them in `__init__` instead of creating them. Passing dependencies in like this is called **dependency injection**.
- The caller decides which concrete classes to use. Swapping MySQL + email for PostgreSQL + SMS needed **zero** changes to `UserService`.

### Testing with Mock Implementations

The biggest everyday benefit of DIP is testing. We can hand `UserService` fake objects that just record what happened.


```python
# DIP makes testing easy with mock implementations

class MockDatabase(Database):
    def __init__(self):
        self.queries = []
    
    def connect(self):
        print("Mock DB connected")
    
    def execute(self, query: str):
        self.queries.append(query)
        print(f"Mock DB recorded query: {query}")


class MockNotification(NotificationService):
    def __init__(self):
        self.sent_messages = []
    
    def send(self, to: str, message: str):
        self.sent_messages.append((to, message))
        print(f"Mock notification recorded: {to} -> {message}")


# Testing with mocks
print("Testing UserService:")
mock_db = MockDatabase()
mock_notifier = MockNotification()

test_service = UserService(mock_db, mock_notifier)
test_service.create_user("TestUser", "test@test.com")

# Verify behavior
print(f"\nQueries executed: {mock_db.queries}")
print(f"Notifications sent: {mock_notifier.sent_messages}")
```

    Testing UserService:
    Mock DB connected
    Mock DB recorded query: INSERT INTO users VALUES ('TestUser', 'test@test.com')
    Mock notification recorded: test@test.com -> Welcome, TestUser!
    
    Queries executed: ["INSERT INTO users VALUES ('TestUser', 'test@test.com')"]
    Notifications sent: [('test@test.com', 'Welcome, TestUser!')]


No database, no emails, but we still checked that `create_user` ran the right query and sent the right message. This is exactly how unit tests for real applications are written (Python's `unittest.mock` makes it even shorter).

**Quick recap**

- DIP: business logic should depend on abstractions, not on specific databases or services.
- Pass dependencies in through `__init__` (dependency injection) instead of creating them inside.
- Swapping an implementation then needs no change to the high-level class.
- Fake/mock implementations make testing easy.

---

## 6. Putting It Together: Order Processing System

Now let's use all five principles in one small system. As you read each cell, look for the principle named in its first comment:

| Cell | Principle on show |
|---|---|
| Data classes | **SRP**: each class just holds one kind of data |
| Interfaces | **ISP**: one small abstract class per job |
| Concrete implementations | **OCP**: add new payment or discount types without editing old ones |
| `OrderService` | **DIP**: depends only on the abstractions |
| Any implementation can replace another | **LSP** |


```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


# === Data Classes (Single Responsibility) ===
@dataclass
class Product:
    id: str
    name: str
    price: float


@dataclass
class OrderItem:
    product: Product
    quantity: int
    
    @property
    def total(self) -> float:
        return self.product.price * self.quantity


@dataclass
class Order:
    id: str
    items: List[OrderItem]
    customer_email: str
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def subtotal(self) -> float:
        return sum(item.total for item in self.items)
```


```python
# === Interfaces (Interface Segregation) ===

class PaymentProcessor(ABC):
    @abstractmethod
    def process_payment(self, amount: float) -> bool:
        pass


class DiscountCalculator(ABC):
    @abstractmethod
    def calculate_discount(self, order: Order) -> float:
        pass


class TaxCalculator(ABC):
    @abstractmethod
    def calculate_tax(self, amount: float) -> float:
        pass


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None:
        pass
    
    @abstractmethod
    def find_by_id(self, order_id: str) -> Order:
        pass


class Notifier(ABC):
    @abstractmethod
    def notify(self, recipient: str, message: str) -> None:
        pass
```


```python
# === Concrete Implementations (Open/Closed - can add new ones without modifying existing) ===

class CreditCardProcessor(PaymentProcessor):
    def process_payment(self, amount: float) -> bool:
        print(f"Processing ${amount:.2f} via Credit Card")
        return True


class PayPalProcessor(PaymentProcessor):
    def process_payment(self, amount: float) -> bool:
        print(f"Processing ${amount:.2f} via PayPal")
        return True


class PercentageDiscount(DiscountCalculator):
    def __init__(self, percentage: float):
        self.percentage = percentage
    
    def calculate_discount(self, order: Order) -> float:
        return order.subtotal * (self.percentage / 100)


class BulkDiscount(DiscountCalculator):
    def calculate_discount(self, order: Order) -> float:
        total_items = sum(item.quantity for item in order.items)
        if total_items >= 10:
            return order.subtotal * 0.15
        elif total_items >= 5:
            return order.subtotal * 0.10
        return 0


class StandardTax(TaxCalculator):
    def __init__(self, rate: float = 0.13):
        self.rate = rate
    
    def calculate_tax(self, amount: float) -> float:
        return amount * self.rate


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders = {}
    
    def save(self, order: Order) -> None:
        self._orders[order.id] = order
        print(f"Order {order.id} saved to memory")
    
    def find_by_id(self, order_id: str) -> Order:
        return self._orders.get(order_id)


class EmailNotifier(Notifier):
    def notify(self, recipient: str, message: str) -> None:
        print(f"Email sent to {recipient}: {message}")
```


```python
# === Order Service (Dependency Inversion - depends on abstractions) ===

class OrderService:
    """High-level module that orchestrates order processing"""
    
    def __init__(
        self,
        payment_processor: PaymentProcessor,
        discount_calculator: DiscountCalculator,
        tax_calculator: TaxCalculator,
        repository: OrderRepository,
        notifier: Notifier
    ):
        self.payment_processor = payment_processor
        self.discount_calculator = discount_calculator
        self.tax_calculator = tax_calculator
        self.repository = repository
        self.notifier = notifier
    
    def process_order(self, order: Order) -> bool:
        """Process an order: calculate totals, payment, save, notify"""
        print(f"\n{'='*50}")
        print(f"Processing Order: {order.id}")
        print(f"{'='*50}")
        
        # Calculate totals
        subtotal = order.subtotal
        discount = self.discount_calculator.calculate_discount(order)
        after_discount = subtotal - discount
        tax = self.tax_calculator.calculate_tax(after_discount)
        total = after_discount + tax
        
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Discount: -${discount:.2f}")
        print(f"Tax: +${tax:.2f}")
        print(f"Total: ${total:.2f}")
        
        # Process payment
        if self.payment_processor.process_payment(total):
            self.repository.save(order)
            self.notifier.notify(
                order.customer_email,
                f"Your order {order.id} has been confirmed! Total: ${total:.2f}"
            )
            return True
        return False
```

Notice that `OrderService` never mentions credit cards, PayPal, percentages or e-mail. It only talks to the five abstractions. Let's give it some real parts and run an order.


```python
# === Putting it all together ===

# Create products
laptop = Product("P001", "Laptop", 999.99)
mouse = Product("P002", "Mouse", 49.99)
keyboard = Product("P003", "Keyboard", 79.99)

# Create order
order = Order(
    id="ORD-001",
    items=[
        OrderItem(laptop, 1),
        OrderItem(mouse, 2),
        OrderItem(keyboard, 1)
    ],
    customer_email="customer@example.com"
)

# Create service with specific implementations
order_service = OrderService(
    payment_processor=CreditCardProcessor(),
    discount_calculator=PercentageDiscount(10),  # 10% discount
    tax_calculator=StandardTax(0.13),  # 13% tax
    repository=InMemoryOrderRepository(),
    notifier=EmailNotifier()
)

# Process the order
order_service.process_order(order)
```

    
    ==================================================
    Processing Order: ORD-001
    ==================================================
    Subtotal: $1179.96
    Discount: -$118.00
    Tax: +$138.06
    Total: $1200.02
    Processing $1200.02 via Credit Card
    Order ORD-001 saved to memory
    Email sent to customer@example.com: Your order ORD-001 has been confirmed! Total: $1200.02





    True



What just happened, step by step:

1. Subtotal: 999.99 + 2 × 49.99 + 79.99 = **1179.96**
2. 10% discount: **118.00**, leaving 1061.96
3. 13% tax on that: **138.06**
4. Total: **1200.02**, charged to the credit card, saved, and the customer is emailed.

Now the same `OrderService` class with a completely different set of parts:


```python
# Easy to swap implementations!
# Process same type of order with different configurations

bulk_order = Order(
    id="ORD-002",
    items=[
        OrderItem(mouse, 5),
        OrderItem(keyboard, 5)
    ],
    customer_email="bulk@example.com"
)

# Different service configuration - PayPal + Bulk discount
bulk_order_service = OrderService(
    payment_processor=PayPalProcessor(),
    discount_calculator=BulkDiscount(),
    tax_calculator=StandardTax(0.08),  # Different tax rate
    repository=InMemoryOrderRepository(),
    notifier=EmailNotifier()
)

bulk_order_service.process_order(bulk_order)
```

    
    ==================================================
    Processing Order: ORD-002
    ==================================================
    Subtotal: $649.90
    Discount: -$97.48
    Tax: +$44.19
    Total: $596.61
    Processing $596.61 via PayPal
    Order ORD-002 saved to memory
    Email sent to bulk@example.com: Your order ORD-002 has been confirmed! Total: $596.61





    True



This order has 10 items, so `BulkDiscount` gives 15% off. We switched payment method, discount rule and tax rate without changing a single line of `OrderService`.

**Quick recap**

- Real designs use all five principles together; they support each other.
- Small classes (SRP) behind small interfaces (ISP) are easy to extend (OCP) and swap (LSP).
- The high-level `OrderService` depends only on abstractions (DIP), so it's easy to configure and test.

---

## 7. Practice Exercises

Four short exercises, one or two principles each. Write your code in the cell, uncomment the tests, and run it. Only then open the solution.

### Exercise 1 (SRP): Split the Invoice

The class below calculates a total **and** formats text. Split it into:

- `Invoice`: holds `customer` and `items` (a list of `(name, price)` tuples) and has a `total()` method
- `InvoiceFormatter`: has a `format(invoice)` method returning `"Invoice for <customer>: Rs <total>"`

```python
class InvoiceEverything:
    def __init__(self, customer, items):
        self.customer = customer
        self.items = items

    def total(self):
        return sum(price for _, price in self.items)

    def as_text(self):
        return f"Invoice for {self.customer}: Rs {self.total()}"
```


```python
# Exercise 1: Your code here
class Invoice:
    def __init__(self, customer: str, items: list[tuple[str, float]]):
        # TODO
        pass

    def total(self) -> float:
        # TODO
        pass


class InvoiceFormatter:
    def format(self, invoice: Invoice) -> str:
        # TODO
        pass

# Test your code (uncomment to run):
# inv = Invoice("Asha", [("Pen", 20), ("Book", 150)])
# assert inv.total() == 170
# assert InvoiceFormatter().format(inv) == "Invoice for Asha: Rs 170"
# assert not hasattr(inv, "format")
# print("Exercise 1 passed!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
class Invoice:
    def __init__(self, customer: str, items: list[tuple[str, float]]):
        self.customer = customer
        self.items = items

    def total(self) -> float:
        return sum(price for _, price in self.items)


class InvoiceFormatter:
    def format(self, invoice: Invoice) -> str:
        return f"Invoice for {invoice.customer}: Rs {invoice.total()}"
```

</details>

### Exercise 2 (OCP): Add New Discounts Without Editing Old Code

Using the `DiscountStrategy` base class from Section 2, add two **new** classes. Don't change any existing class.

- `StudentDiscount`: 15% off
- `FlatDiscount(amount)`: a fixed amount off, but never more than the bill itself


```python
# Exercise 2: Your code here
class StudentDiscount(DiscountStrategy):
    # TODO
    pass


class FlatDiscount(DiscountStrategy):
    # TODO
    pass

# Test your code (uncomment to run):
# assert StudentDiscount().calculate(200) == 30
# assert FlatDiscount(50).calculate(200) == 50
# assert FlatDiscount(50).calculate(30) == 30
# print("Exercise 2 passed!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
class StudentDiscount(DiscountStrategy):
    def calculate(self, amount: float) -> float:
        return amount * 0.15


class FlatDiscount(DiscountStrategy):
    def __init__(self, amount: float):
        self.amount = amount

    def calculate(self, amount: float) -> float:
        return min(self.amount, amount)
```

</details>

### Exercise 3 (LSP + ISP): Birds That Can't Fly

A common mistake is a `Bird` class with a `fly()` method, and then a `Penguin` whose `fly()` raises an error. Fix the design:

- `Bird` (base class) has `eat()` returning `"<name> is eating"`
- `FlyingBird(Bird)` adds `fly()` returning `"<name> is flying"`
- `Sparrow` is a `FlyingBird`; `Penguin` is a plain `Bird` with a `swim()` method returning `"<name> is swimming"`

Each bird gets its name through `__init__`.


```python
# Exercise 3: Your code here
class Bird:
    # TODO
    pass


class FlyingBird(Bird):
    # TODO
    pass


class Sparrow(FlyingBird):
    pass


class Penguin(Bird):
    # TODO
    pass

# Test your code (uncomment to run):
# birds = [Sparrow("Jack"), Penguin("Pingu")]
# assert [b.eat() for b in birds] == ["Jack is eating", "Pingu is eating"]
# assert Sparrow("Jack").fly() == "Jack is flying"
# assert Penguin("Pingu").swim() == "Pingu is swimming"
# assert not hasattr(Penguin("Pingu"), "fly")
# print("Exercise 3 passed!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
class Bird:
    def __init__(self, name: str):
        self.name = name

    def eat(self) -> str:
        return f"{self.name} is eating"


class FlyingBird(Bird):
    def fly(self) -> str:
        return f"{self.name} is flying"


class Sparrow(FlyingBird):
    pass


class Penguin(Bird):
    def swim(self) -> str:
        return f"{self.name} is swimming"
```

</details>

### Exercise 4 (DIP): A Testable Weather Reporter

`WeatherReporter` should not call a real weather API directly. Instead:

- Write an abstract class `TemperatureSource` with an abstract method `read_celsius()`
- Write `WeatherReporter`, which receives a `TemperatureSource` in `__init__` and has `report()` returning `"It is <temp>°C"`
- Write `FakeSource(value)`, a `TemperatureSource` that always returns `value`, so we can test without the internet


```python
# Exercise 4: Your code here
from abc import ABC, abstractmethod


class TemperatureSource(ABC):
    # TODO
    pass


class WeatherReporter:
    # TODO
    pass


class FakeSource(TemperatureSource):
    # TODO
    pass

# Test your code (uncomment to run):
# assert WeatherReporter(FakeSource(25)).report() == "It is 25°C"
# assert WeatherReporter(FakeSource(-3)).report() == "It is -3°C"
# print("Exercise 4 passed!")
```

<details markdown="1">
<summary>Show solution</summary>

```python
from abc import ABC, abstractmethod


class TemperatureSource(ABC):
    @abstractmethod
    def read_celsius(self) -> float:
        pass


class WeatherReporter:
    def __init__(self, source: TemperatureSource):
        self.source = source

    def report(self) -> str:
        return f"It is {self.source.read_celsius()}°C"


class FakeSource(TemperatureSource):
    def __init__(self, value: float):
        self.value = value

    def read_celsius(self) -> float:
        return self.value
```

</details>

---

## Summary & Cheat Sheet

| Principle | Remember this | Warning sign | Usual fix |
|---|---|---|---|
| **SRP** | One class, one job | Many unrelated reasons to edit a class | Split it into smaller classes |
| **OCP** | Add code, don't edit working code | A long `if/elif` on a type name | Abstract base class + one subclass per case |
| **LSP** | Subclasses must keep the parent's promises | Overrides that change meaning, `isinstance` workarounds | Inherit from a more general base class |
| **ISP** | Small, focused interfaces | Methods that only `raise NotImplementedError` | Split the big interface |
| **DIP** | Depend on abstractions | Classes creating their own database/email objects | Pass dependencies in through `__init__` |

### Tips for Real Projects

1. **Start simple.** Don't add abstractions "just in case". Apply SOLID when the code starts to hurt.
2. **Use `ABC`** to describe what a class must be able to do.
3. **Inject dependencies** instead of creating them inside the class.
4. **Prefer composition over inheritance.** It's usually more flexible.
5. **Write tests.** Code that is easy to test usually follows SOLID already.

### What's Next

The **Design Patterns** notebook shows ready-made solutions (Strategy, Factory, Observer and more) that are built directly on these principles. You've already used the Strategy pattern in Section 2.
