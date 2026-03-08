# OOP Design Patterns

A practical introduction for developers who know how to write code, but want to write code that _scales_.

---

## What Are Design Patterns?

Design patterns are reusable solutions to problems that keep showing up in software development. They're not libraries you install or code you copy — they're **blueprints for thinking** about how to structure your code.

The term was popularized by the "Gang of Four" book (1994), which catalogued 23 patterns across three categories:

| Category       | Purpose                  | Examples                    |
| -------------- | ------------------------ | --------------------------- |
| **Creational** | How objects are created  | Singleton, Factory, Builder |
| **Structural** | How objects are composed | Adapter, Decorator, Facade  |
| **Behavioral** | How objects communicate  | Observer, Strategy, Command |

You don't need to memorize all 23. Learning a handful well will change how you design systems.

---

## Core Concepts to Understand First

Before diving into patterns, make sure these ideas are solid. Every pattern below leans on them.

### Encapsulation

Keep internal state private. Expose only what's needed. This prevents outside code from depending on your implementation details — making changes safer.

Java enforces this at the language level with access modifiers. Use them.

```java
// Bad: anyone can break this
public class BankAccount {
    public double balance = 1000;
}
account.balance = -999999; // oops

// Better
public class BankAccount {
    private double balance = 1000;

    public void deposit(double amount) {
        if (amount > 0) balance += amount;
    }

    public double getBalance() {
        return balance;
    }
}
```

### Composition Over Inheritance

Inheritance creates tight coupling between parent and child. When the parent changes, children break. Java's `interface` system makes composition natural — build classes by implementing multiple focused behaviors instead of extending a rigid chain.

```java
// Inheritance: fragile chain
abstract class Animal { abstract void breathe(); }
abstract class Bird extends Animal { abstract void fly(); }
class Penguin extends Bird {
    public void breathe() { /* ok */ }
    public void fly() { /* penguins can't fly — but we're forced to implement this */ }
}

// Composition with interfaces: mix only what you need
interface Flyable  { void fly(); }
interface Swimmable { void swim(); }

class Eagle implements Flyable {
    public void fly() { System.out.println("Soaring!"); }
}

class Penguin implements Swimmable {
    public void swim() { System.out.println("Swimming!"); }
}

class Duck implements Flyable, Swimmable {
    public void fly()  { System.out.println("Flap flap!"); }
    public void swim() { System.out.println("Splash!"); }
}
```

### Programming to Interfaces, Not Implementations

Write code that depends on _what something does_, not _what something is_. Java's `interface` keyword makes this explicit. If a method only needs a `.save()` call, declare its parameter as the interface — not the concrete class.

```java
// Bad: tightly coupled to one implementation
public void saveData(MySQLDatabase db, String data) {
    db.save(data);
}

// Good: works with any DataStore
public interface DataStore {
    void save(String data);
}

public class MySQLDatabase implements DataStore {
    public void save(String data) { /* MySQL logic */ }
}

public class FileStore implements DataStore {
    public void save(String data) { /* file I/O logic */ }
}

public void saveData(DataStore store, String data) {
    store.save(data); // swap implementations without changing this method
}
```

This is the foundation of the **Strategy** and **Adapter** patterns.

### The Open/Closed Principle

Classes should be **open for extension, closed for modification**. Instead of editing existing code to add new behavior (risking bugs), extend it — through new implementations of an interface, subclassing, or delegation. If adding a feature requires you to change a class that already works, that's a design smell.

---

## The Patterns

### Singleton

**Problem:** You need exactly one instance of something — a config manager, a database connection, a logger — shared across your entire app.

**Solution:** Make the constructor `private` and control instantiation through a static method.

```java
public class Logger {
    private static Logger instance = null;
    private List<String> logs = new ArrayList<>();

    private Logger() {} // prevent direct instantiation

    public static Logger getInstance() {
        if (instance == null) {
            instance = new Logger();
        }
        return instance;
    }

    public void log(String message) {
        logs.add(message);
        System.out.println("[LOG] " + message);
    }

    public List<String> getLogs() {
        return Collections.unmodifiableList(logs);
    }
}

// Usage
Logger a = Logger.getInstance();
Logger b = Logger.getInstance();
System.out.println(a == b); // true — same object
```

> **Note:** In multi-threaded applications, use `synchronized` or initialize eagerly (`private static Logger instance = new Logger()`) to avoid race conditions.

**When to use it:** Shared resources where multiple instances would cause conflicts or inconsistency (connection pools, caches, config).

**Watch out:** Singletons are global state. Overusing them makes code hard to test and reason about.

---

### Factory

**Problem:** You need to create objects, but the exact type depends on runtime conditions — and you don't want the caller to know or care about the details.

**Solution:** Delegate object creation to a factory method. Callers get back an interface, not a concrete class.

```java
public interface Shape {
    double area();
}

public class Circle implements Shape {
    private double radius;
    Circle(double radius) { this.radius = radius; }
    public double area() { return Math.PI * radius * radius; }
}

public class Square implements Shape {
    private double side;
    Square(double side) { this.side = side; }
    public double area() { return side * side; }
}

public class ShapeFactory {
    public static Shape create(String type, double size) {
        switch (type) {
            case "circle": return new Circle(size);
            case "square": return new Square(size);
            default: throw new IllegalArgumentException("Unknown shape: " + type);
        }
    }
}

// Usage — caller only knows about Shape, not Circle or Square
Shape shape = ShapeFactory.create("circle", 5);
System.out.println(shape.area()); // 78.53...
```

**When to use it:** When object creation logic is complex, conditional, or should be centralized. Adding a new shape only requires a new class and one new `case` — no callers change.

---

### Observer

**Problem:** One object changes state, and several other objects need to react — but you don't want the first object tightly coupled to all the others.

**Solution:** Define an `Observer` interface. Objects subscribe by registering themselves. When state changes, the subject notifies all subscribers automatically.

```java
public interface Observer {
    void update(String event, Object data);
}

public class EventEmitter {
    private Map<String, List<Observer>> listeners = new HashMap<>();

    public void on(String event, Observer observer) {
        listeners.computeIfAbsent(event, k -> new ArrayList<>()).add(observer);
    }

    public void emit(String event, Object data) {
        List<Observer> obs = listeners.getOrDefault(event, Collections.emptyList());
        for (Observer o : obs) o.update(event, data);
    }
}

public class Store extends EventEmitter {
    private Map<String, Object> state = new HashMap<>();

    public void setState(String key, Object value) {
        state.put(key, value);
        emit("change", state);
    }
}

// Usage
Store store = new Store();
store.on("change", (event, data) -> System.out.println("UI updated: " + data));
store.on("change", (event, data) -> System.out.println("Analytics: " + data));

store.setState("user", "Alice");
// Both observers fire — Store doesn't know or care about either one
```

**When to use it:** Any "one-to-many" relationship where the source shouldn't know its dependents — event systems, reactive UIs, notification pipelines.

---

### Strategy

**Problem:** You have a behavior that needs to vary — sorting algorithms, payment methods, validation rules — and you want to swap implementations without changing the code that uses them.

**Solution:** Define a `@FunctionalInterface` (or regular interface) for the behavior. Inject the implementation you want at runtime.

```java
@FunctionalInterface
public interface SortStrategy {
    int[] sort(int[] arr);
}

public class Sorter {
    private SortStrategy strategy;

    public Sorter(SortStrategy strategy) {
        this.strategy = strategy;
    }

    public void setStrategy(SortStrategy strategy) {
        this.strategy = strategy;
    }

    public int[] sort(int[] data) {
        return strategy.sort(data);
    }
}

// Usage — swap strategies without touching Sorter
Sorter sorter = new Sorter(arr -> bubbleSort(arr));
sorter.sort(new int[]{3, 1, 4, 1, 5});

sorter.setStrategy(arr -> quickSort(arr));
sorter.sort(new int[]{3, 1, 4, 1, 5});
```

**When to use it:** Anywhere you'd otherwise write a long `if/else` or `switch` to pick between algorithms or behaviors. In Java, `Comparator` is the classic example of this pattern in the standard library.

---

### Decorator

**Problem:** You want to add behavior to an object without modifying its class — and without creating a subclass explosion.

**Solution:** Define a shared interface. Write "decorator" classes that wrap any object implementing that interface and add behavior before/after delegating.

```java
public interface Coffee {
    double cost();
    String description();
}

public class PlainCoffee implements Coffee {
    public double cost()        { return 2.0; }
    public String description() { return "Coffee"; }
}

public class MilkDecorator implements Coffee {
    private Coffee coffee;
    MilkDecorator(Coffee coffee) { this.coffee = coffee; }
    public double cost()        { return coffee.cost() + 0.50; }
    public String description() { return coffee.description() + ", Milk"; }
}

public class SyrupDecorator implements Coffee {
    private Coffee coffee;
    SyrupDecorator(Coffee coffee) { this.coffee = coffee; }
    public double cost()        { return coffee.cost() + 0.75; }
    public String description() { return coffee.description() + ", Syrup"; }
}

// Usage — stack decorators freely
Coffee order = new PlainCoffee();
order = new MilkDecorator(order);
order = new SyrupDecorator(order);

System.out.println(order.description()); // Coffee, Milk, Syrup
System.out.println(order.cost());        // 3.25
```

**When to use it:** Adding optional, stackable features to objects. Java's own I/O library is built entirely on this pattern — `new BufferedReader(new InputStreamReader(new FileInputStream(file)))`.

---

### Adapter

**Problem:** You have two interfaces that don't match — an old API you can't change, a third-party library with unexpected method names — but you need them to work together.

**Solution:** Write an adapter class that implements the interface your code expects, and internally delegates to the incompatible one.

```java
// Old third-party class you can't modify
public class LegacyLogger {
    public void writeLog(String msg) {
        System.out.println("[LEGACY] " + msg);
    }
}

// The interface your application uses everywhere
public interface Logger {
    void log(String msg);
}

// Adapter: bridges the gap
public class LoggerAdapter implements Logger {
    private LegacyLogger legacy;

    LoggerAdapter(LegacyLogger legacy) {
        this.legacy = legacy;
    }

    public void log(String msg) {
        legacy.writeLog(msg); // translate the call
    }
}

// Existing application code — never has to change
public void doWork(Logger logger) {
    logger.log("Starting work...");
}

// Plug in the adapter
Logger adapter = new LoggerAdapter(new LegacyLogger());
doWork(adapter); // works without touching LegacyLogger or doWork
```

**When to use it:** Integrating third-party code, migrating legacy systems, or making incompatible interfaces work together. Also useful when writing tests — adapters can wrap test doubles to match production interfaces.

---

### Command

**Problem:** You want to encapsulate a request as an object — so you can queue it, log it, undo it, or retry it.

**Solution:** Define a `Command` interface with `execute()` and `undo()`. Each action becomes a concrete class that knows how to perform and reverse itself.

```java
public interface Command {
    void execute();
    void undo();
}

public class TextEditor {
    private StringBuilder content = new StringBuilder();

    public void append(String text)     { content.append(text); }
    public void removeLast(int length)  { content.delete(content.length() - length, content.length()); }
    public String getContent()          { return content.toString(); }
}

public class TypeCommand implements Command {
    private TextEditor editor;
    private String text;

    TypeCommand(TextEditor editor, String text) {
        this.editor = editor;
        this.text = text;
    }

    public void execute() { editor.append(text); }
    public void undo()    { editor.removeLast(text.length()); }
}

// Usage
TextEditor editor = new TextEditor();
Deque<Command> history = new ArrayDeque<>();

Command c1 = new TypeCommand(editor, "Hello");
c1.execute();
history.push(c1);

Command c2 = new TypeCommand(editor, ", World");
c2.execute();
history.push(c2);

System.out.println(editor.getContent()); // "Hello, World"

history.pop().undo();
System.out.println(editor.getContent()); // "Hello"
```

**When to use it:** Undo/redo systems, task queues, audit logging, macro recording, transactional operations.

---

## Patterns in the Wild

You've already used these patterns without knowing it:

| You've used...                                   | That's the... pattern |
| ------------------------------------------------ | --------------------- |
| `java.util.EventListener`                        | Observer              |
| `new BufferedReader(new InputStreamReader(...))` | Decorator             |
| `Collections.sort(list, comparator)`             | Strategy              |
| `Runtime.getRuntime()`                           | Singleton             |
| `StringBuilder.append().append().toString()`     | Builder               |
| `java.sql.DriverManager.getConnection(url)`      | Factory               |

---

## A Few Rules of Thumb

1. **Don't reach for a pattern before you feel the pain.** Patterns solve real problems. If you haven't hit the problem yet, the pattern is just complexity.
2. **Names matter.** Calling something an `Adapter` or `Observer` communicates intent to your teammates instantly. Use these names in your class names.
3. **Patterns can combine.** A Singleton Factory. A Decorator that emits Observer events. Real systems mix and match.
4. **YAGNI.** "You aren't gonna need it." Don't over-engineer. A well-named interface with two implementations is often better than a pattern.

---

## Challenges

Work through these to build intuition. Each one is small enough to finish in a sitting, but will force you to think through the tradeoff the pattern is solving.

1. **Singleton Logger** — Build a `Logger` class with a `private` constructor and a `getInstance()` method. Retrieve the instance from three different classes and confirm they all share the same log history.

2. **Shape Factory** — Write a `ShapeFactory` with a `create(String type, double size)` method that returns `Circle`, `Rectangle`, or `Triangle` objects. Each should implement a `Shape` interface with an `area()` method.

3. **Payment Strategy** — Build a checkout system where the payment method (credit card, PayPal, crypto) is a swappable `PaymentStrategy` interface. The `Checkout` class should never need to change when you add a new payment type.

4. **Observer from Scratch** — Implement your own `Observer` interface and `EventEmitter` class with `on`, `off`, and `emit` methods. Then model a stock ticker that notifies multiple display components whenever the price changes.

5. **Coffee Shop Decorator** — Model a coffee ordering system using decorators. Start with a `PlainCoffee` base and let customers stack add-ons (milk, sugar, syrup, oat milk). Each add-on should modify both `cost()` and `description()`.

6. **Legacy API Adapter** — You have a `WeatherServiceV1` with a `fetchTempFahrenheit(String city)` method. Your app uses a `WeatherService` interface with `getTemperatureCelsius(String city)`. Write an adapter.

7. **Undo/Redo Text Editor** — Use the Command pattern to build a text editor that supports unlimited undo and redo. Maintain two stacks: a history stack and a redo stack. Each `TypeCommand` and `DeleteCommand` should know how to reverse itself.

8. **Observable Store** — Build a simple generic state container (like a mini-Redux) using the Observer pattern. It should hold a `Map<String, Object>` state, expose a `setState` method, and notify all registered `Observer`s on every change.

9. **Builder Pattern for Query Construction** — Write a `QueryBuilder` class with chainable methods — `.select(String... cols)`, `.from(String table)`, `.where(String condition)`, `.limit(int n)` — and a final `.build()` method that returns the SQL string.

10. **Combining Patterns** — Build a notification system that uses: a **Singleton** to hold the notification center, a **Factory** to create different notification types (`EmailNotification`, `SmsNotification`, `PushNotification`), and an **Observer** to let services subscribe to notification events.
