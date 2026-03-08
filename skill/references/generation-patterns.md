# Generation Patterns: Skeleton and Test Examples

These are **illustrative examples** — use them as structural guides, not rigid prescriptions. The README is always the source of truth for what to generate.

The goal is always the same regardless of language:

1. **Skeleton files** — give students just enough structure to start; no solutions
2. **Test files** — fail at first (✗ red), turn green (✓) as students implement

---

## Universal Skeleton Principles

Good skeleton files in any language:

- Comment at top: the challenge description from the README
- Imports/includes the student will likely need (leave room for them to add more)
- The **shape** of the solution without any logic: empty functions, empty class bodies, stub methods
- Comments inside stubs: what the code should do, not how
- Return placeholder values where required (`return null`, `return 0`, `return None`, `pass`)
- No implementation, unless the README provides starter code (e.g., a hash function to copy in)

---

## TypeScript / JavaScript Skeletons

### Single class, `export default`

```typescript
// do not use the built-in array type or its methods
export default class Erray {
  contents: {};
  length: number;

  constructor() {
    this.contents = {};
    this.length = 0;
  }

  // adds element(s) to the end of the array
  push(...args: any[]) {}

  // removes and returns the last element
  pop() {}
}
```

### Multiple classes, folder per class, named export

```typescript
// src/Stack/Stack.ts
class Stack {
  storage: Record<number, any>;
  index: number;

  constructor() {
    this.storage = {};
    this.index = 0;
  }

  // adds an element to the top of the stack
  push(value: any) {}

  // removes AND returns the element at the top of the stack
  pop() {}
}

export { Stack };
```

### Node class + container

```typescript
class ListNode {
  value: any;
  next: any;

  constructor(val: any) {
    this.value = val;
    this.next = null;
  }
}

class LinkedList {
  head: any;
  tail: any;

  constructor() {
    this.head = null;
    this.tail = null;
  }

  // adds a node to the end of the list
  push(value: any) {}

  // returns true if value is present anywhere in the list
  contains(value: any) {}
}

export { ListNode, LinkedList };
```

---

## React Skeletons

### Simple component (props only)

```tsx
// Challenge 1: Greeting
// Create a component that accepts a `name` prop and displays a greeting.

function Greeting({ name }: { name: string }) {
  // return JSX that displays a greeting using the name prop
}

export { Greeting };
```

### Component with state

```tsx
// Challenge 2: Click Counter
// Create a component with a button. Each click increments the displayed count.

import { useState } from "react";

function Counter() {
  // add state for count here
  // return JSX with a button and the current count displayed
}

export { Counter };
```

### Component with useEffect (data fetching)

```tsx
// Challenge 7: Fetch and Display
// Fetch data from a public API on mount. Display results in a list.

import { useState, useEffect } from "react";

function FetchAndDisplay() {
  // add state for data and loading status
  // use useEffect to fetch from the API on mount
  // return JSX: loading indicator while fetching, then a list of results
}

export { FetchAndDisplay };
```

### Multiple components in one file (state sharing)

```tsx
// Challenge 9: Shared State
// Slider and Display are siblings sharing state through a parent.

function Slider({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  // return a range input bound to value and onChange
}

function Display({ value }: { value: number }) {
  // return JSX displaying the current value
}

function SharedState() {
  // add state for the slider value
  // return Slider and Display as siblings, passing state and setter as props
}

export { Slider, Display, SharedState };
```

---

## Python Skeletons

### Single class

```python
# Challenge: Stack
# Implement a Stack using a dictionary as the backing store.
# Do not use Python's built-in list methods.

class Stack:
    def __init__(self):
        self.storage = {}
        self.index = 0

    def push(self, value):
        # add value to the top of the stack
        pass

    def pop(self):
        # remove and return the top value; return None if empty
        pass

    def size(self):
        # return the number of elements in the stack
        pass
```

### Module-level functions (no class)

```python
# Challenge: Binary Search
# Implement binary search without using built-in search functions.

def binary_search(arr, target):
    # return the index of target in arr, or -1 if not found
    pass

def recursive_binary_search(arr, target, low=0, high=None):
    # recursive version — return the index or -1
    pass
```

---

## Java Skeletons

```java
// src/main/java/com/challenge/Stack.java
// Challenge: Stack
// Implement a Stack. Do not use Java's built-in Stack or Deque.

package com.challenge;

public class Stack {
    // add your storage field(s) here

    public Stack() {
        // initialize storage
    }

    // adds value to the top of the stack
    public void push(Object value) {
        // TODO: implement
    }

    // removes and returns the top value; returns null if empty
    public Object pop() {
        // TODO: implement
        return null;
    }

    // returns the number of elements in the stack
    public int size() {
        // TODO: implement
        return 0;
    }
}
```

---

## Angular Skeletons

```typescript
// src/app/counter/counter.component.ts
// Challenge 2: Click Counter
// Create a component with a button. Each click increments the displayed count.

import { Component } from "@angular/core";

@Component({
  selector: "app-counter",
  template: `
    <!-- add your template here -->
    <!-- hint: display count, add a button with (click) handler -->
  `
})
export class CounterComponent {
  count = 0;

  // handle button click — increment count
  onClick() {
    // TODO: implement
  }
}
```

---

## C++ Skeletons

### Header file

```cpp
// include/Stack.h
// Challenge: Stack
// Implement a Stack. Do not use std::stack.

#pragma once
#include <unordered_map>

class Stack {
public:
    Stack();

    // adds value to the top of the stack
    void push(int value);

    // removes and returns the top value; returns -1 if empty
    int pop();

    // returns the number of elements in the stack
    int size();

private:
    std::unordered_map<int, int> storage;
    int index;
};
```

### Implementation file

```cpp
// src/Stack.cpp
#include "Stack.h"

Stack::Stack() : index(0) {}

void Stack::push(int value) {
    // TODO: implement
}

int Stack::pop() {
    // TODO: implement
    return -1;
}

int Stack::size() {
    // TODO: implement
    return 0;
}
```

---

## TypeScript / JS Test Patterns

### `describe` blocks (5+ methods or complex challenges)

```typescript
import { describe, beforeEach, it, expect } from "vitest";
import { Stack } from "./Stack";

let stack: Stack;

beforeEach(() => {
  stack = new Stack();
});

describe("Stack", () => {
  it("should instantiate correctly", () => {
    expect(stack).toBeInstanceOf(Stack);
  });
});

describe("push", () => {
  it("should be a function", () => {
    expect(typeof stack.push).toBe("function");
  });

  it("should add an element", () => {
    stack.push(1);
    expect(stack.storage[0]).toBe(1);
  });
});

describe("pop", () => {
  it("should remove and return the top element", () => {
    stack.push(1);
    expect(stack.pop()).toBe(1);
  });

  it("should return undefined when empty", () => {
    expect(stack.pop()).toBeUndefined();
  });
});
```

### Flat `it()` blocks (2–4 methods)

```typescript
import { beforeEach, it, expect } from "vitest";
import { Stack } from "./Stack";

let stack: Stack;

beforeEach(() => {
  stack = new Stack();
});

it("should push and pop in LIFO order", () => {
  stack.push(1);
  stack.push(2);
  expect(stack.pop()).toBe(2);
  expect(stack.pop()).toBe(1);
});

it("should return undefined when popping an empty stack", () => {
  expect(stack.pop()).toBeUndefined();
});
```

---

## React Test Patterns

### Basic render + interaction

```tsx
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Counter } from "./Counter";

describe("Counter", () => {
  it("should render without crashing", () => {
    render(<Counter />);
  });

  it("should display 0 initially", () => {
    render(<Counter />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("should increment on click", () => {
    render(<Counter />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByText("1")).toBeInTheDocument();
  });
});
```

### Async fetch (mock fetch + waitFor)

```tsx
import { vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { FetchAndDisplay } from "./FetchAndDisplay";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      json: () => Promise.resolve([{ id: 1, name: "Alice" }])
    })
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

it("should display fetched data", async () => {
  render(<FetchAndDisplay />);
  await waitFor(() => {
    expect(screen.getByText("Alice")).toBeInTheDocument();
  });
});
```

### Timer-based (fake timers + act)

```tsx
import { vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { Stopwatch } from "./Stopwatch";

beforeEach(() => {
  vi.useFakeTimers();
});
afterEach(() => {
  vi.useRealTimers();
});

it("should count up after Start is clicked", () => {
  render(<Stopwatch />);
  fireEvent.click(screen.getByRole("button", { name: /start/i }));
  act(() => {
    vi.advanceTimersByTime(3000);
  });
  expect(screen.getByText("3")).toBeInTheDocument();
});
```

---

## Python Test Patterns (pytest)

```python
# tests/test_stack.py
import pytest
from src.stack import Stack

@pytest.fixture
def stack():
    return Stack()

def test_stack_exists(stack):
    assert stack is not None

def test_push_adds_element(stack):
    stack.push(1)
    assert stack.size() == 1

def test_pop_returns_top_element(stack):
    stack.push(1)
    stack.push(2)
    assert stack.pop() == 2

def test_pop_empty_stack_returns_none(stack):
    assert stack.pop() is None

def test_push_pop_multiple(stack):
    stack.push(10)
    stack.push(20)
    assert stack.pop() == 20
    assert stack.pop() == 10
```

---

## Java Test Patterns (JUnit 5)

```java
// src/test/java/com/challenge/StackTest.java
package com.challenge;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class StackTest {
    Stack stack;

    @BeforeEach
    void setUp() {
        stack = new Stack();
    }

    @Test
    void stackShouldExist() {
        assertNotNull(stack);
    }

    @Test
    void pushShouldIncreaseSize() {
        stack.push(1);
        assertEquals(1, stack.size());
    }

    @Test
    void popShouldReturnTopElement() {
        stack.push(1);
        stack.push(2);
        assertEquals(2, stack.pop());
    }

    @Test
    void popOnEmptyStackShouldReturnNull() {
        assertNull(stack.pop());
    }

    @Test
    void pushAndPopShouldFollowLIFOOrder() {
        stack.push(10);
        stack.push(20);
        assertEquals(20, stack.pop());
        assertEquals(10, stack.pop());
    }
}
```

---

## Angular Test Patterns (Jasmine + TestBed)

```typescript
// src/app/counter/counter.component.spec.ts
import { ComponentFixture, TestBed } from "@angular/core/testing";
import { CounterComponent } from "./counter.component";

describe("CounterComponent", () => {
  let component: CounterComponent;
  let fixture: ComponentFixture<CounterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CounterComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(CounterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });

  it("should display 0 initially", () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain("0");
  });

  it("should increment count when button is clicked", () => {
    const button = fixture.nativeElement.querySelector("button");
    button.click();
    fixture.detectChanges();
    expect(component.count).toBe(1);
  });
});
```

---

## C++ Test Patterns (Google Test)

```cpp
// tests/StackTest.cpp
#include <gtest/gtest.h>
#include "Stack.h"

class StackTest : public ::testing::Test {
protected:
    Stack stack;
};

TEST_F(StackTest, PushIncreasesSize) {
    stack.push(1);
    EXPECT_EQ(stack.size(), 1);
}

TEST_F(StackTest, PopReturnsTopElement) {
    stack.push(1);
    stack.push(2);
    EXPECT_EQ(stack.pop(), 2);
}

TEST_F(StackTest, PopEmptyStackReturnsMinusOne) {
    EXPECT_EQ(stack.pop(), -1);
}

TEST_F(StackTest, PushPopFollowsLIFO) {
    stack.push(10);
    stack.push(20);
    EXPECT_EQ(stack.pop(), 20);
    EXPECT_EQ(stack.pop(), 10);
}
```

---

## COBOL Skeletons (GnuCOBOL, free format)

Every COBOL skeleton includes all four divisions. Use `*>` for comments (free-format style — `*` in column 7 is only valid in fixed format). Declare the variables the student will need as hints; leave `PROCEDURE DIVISION` empty except for `STOP RUN.`.

### Single interactive program (the typical case)

```cobol
*> Challenge N: Title
*> One-line description from the README.

IDENTIFICATION DIVISION.
PROGRAM-ID. PROGRAM-NAME.

ENVIRONMENT DIVISION.

DATA DIVISION.
WORKING-STORAGE SECTION.
*> Declare variables with appropriate PIC clauses.
*> PIC 9(5)   — integer up to 99999
*> PIC X(20)  — 20-character alphanumeric string
*> PIC 9(7)V99 — decimal like 99999.99
    01 SOME-VAR     PIC X(20).
    01 SOME-NUM     PIC 9(5).

PROCEDURE DIVISION.
*> TODO: 1. (first step)
*> TODO: 2. (second step)
*> ...
    STOP RUN.
```

### Program with a loop

```cobol
DATA DIVISION.
WORKING-STORAGE SECTION.
    01 LOOP-VAR     PIC 9(2).   *> loop counter
    01 INPUT-NUM    PIC 9(5).
    01 TOTAL        PIC 9(7) VALUE 0.

PROCEDURE DIVISION.
*> TODO: Use PERFORM VARYING or PERFORM N TIMES
*>
*> PERFORM VARYING LOOP-VAR FROM 1 BY 1 UNTIL LOOP-VAR > 10
*>     DISPLAY LOOP-VAR
*> END-PERFORM.
*>
*> Count down with a negative step:
*> PERFORM VARYING LOOP-VAR FROM START-NUM BY -1 UNTIL LOOP-VAR < 1
    STOP RUN.
```

---

## COBOL Test Patterns (bash)

Tests live in `tests/run_tests.sh`. See the COBOL section of `project-templates.md` for the full runner template.

### Writing `run_test` calls

```bash
# Basic: single input, check for a string in output
run_test "1a. Hello, You — greets by name" \
    "src/01-hello-you.cbl" \
    "ALICE" \
    "HELLO.*ALICE"

# Multi-line input: use $'...\n...'
run_test "2a. Simple Adder — 5 + 3 = 8" \
    "src/02-simple-adder.cbl" \
    $'5\n3' \
    "8"

# No input
run_test "4a. Count to Ten — shows 10" \
    "src/04-count-to-ten.cbl" \
    "" \
    "10"

# Word-boundary pattern to avoid false matches from common words
# (e.g., "C" appears in "SCORE" — use \bC\b to match only standalone C)
run_test "8c. Grade Letter — 73 → C" \
    "src/08-grade-letter.cbl" \
    "73" \
    "\bC\b"
```

### Choosing test inputs and patterns

- Numeric output is zero-padded to PIC width: `PIC 9(5)` VALUE 8 displays as `00008`. Pattern `8` matches as a substring. ✓
- String output is space-padded to PIC width: `PIC X(20)` storing "ALICE" displays as `ALICE               `. Pattern `ALICE` matches as a substring. ✓
- **Avoid false positives**: pick test inputs whose expected result does NOT appear as a substring in the input values themselves. E.g., to test principal=1000 → interest=100, note that "100" is a substring of "1000" — choose different inputs instead.
- **Single letter grades**: letters like `C`, `A` can appear in typical prompt words ("SCORE", "ENTER A"). Use `\bC\b` for word-boundary matching where needed.

---

## Decision Guide

| README signals                          | Skeleton                                       | Tests                                                |
| --------------------------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| TypeScript, single class                | `export default class`, single file            | Vitest `describe` blocks (5+ methods) or flat `it()` |
| TypeScript, multiple classes            | Folder per class, named export                 | Vitest flat `it()` per file                          |
| TypeScript, node-based structure        | Node helper class + container, same file       | Vitest flat `it()`                                   |
| React, props/display                    | Empty function component, named export         | RTL `render` + `getByRole`/`getByText`               |
| React, state + events                   | `useState` import, empty body + comments       | RTL `render` + `fireEvent`                           |
| React, `useEffect` + fetch              | `useState`+`useEffect` imports                 | `vi.stubGlobal("fetch")` + `waitFor`                 |
| React, timers                           | `useEffect` import + cleanup comment           | `vi.useFakeTimers()` + `act`                         |
| Angular, component                      | `@Component` decorator, empty handler          | `TestBed` + `ComponentFixture`                       |
| Python, class                           | `class Foo:` with `pass` stubs                 | `pytest` fixture + `assert`                          |
| Python, functions                       | Module-level `def`, `pass` body                | `pytest` plain functions                             |
| Java, class                             | `public class` with empty/null-returning stubs | JUnit 5 `@Test` + `assertEquals`                     |
| C++, class                              | `.h` declaration + `.cpp` stubs                | Google Test `TEST_F`                                 |
| README provides a hash/utility function | Include pre-implemented (not empty)            | Don't test the provided function                     |
| COBOL, interactive programs             | All 4 divisions, `*>` comments, empty PROCEDURE (just `STOP RUN.`) | bash runner: `cobc -x -free` + piped input + `grep -qE` |
