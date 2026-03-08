# Introduction to COBOL

## What Is COBOL?

COBOL — **Common Business-Oriented Language** — was created in 1959 and is one of the oldest programming languages still in active use. Despite its age, COBOL runs an estimated **$3 trillion in daily commerce**, powering the core systems of banks, insurance companies, government agencies, and retailers. If you've used an ATM, filed taxes, or collected a paycheck, there's a good chance COBOL processed it.

COBOL was designed to be readable by non-programmers. Its syntax resembles plain English, which was a deliberate choice: in 1959, computing resources were expensive and rare, and business managers needed to be able to audit the code running their operations.

---

## Program Structure

Every COBOL program is divided into four **divisions**, always in this order:

```cobol
IDENTIFICATION DIVISION.
ENVIRONMENT DIVISION.
DATA DIVISION.
PROCEDURE DIVISION.
```

Think of divisions like chapters in a book — each one has a specific purpose.

### 1. IDENTIFICATION DIVISION

This is the metadata section. At minimum, it contains the program name.

```cobol
IDENTIFICATION DIVISION.
PROGRAM-ID. HELLO-WORLD.
```

### 2. ENVIRONMENT DIVISION

Describes the computing environment — what machine the program runs on and any files it uses. For simple programs, this division is often empty or omitted.

```cobol
ENVIRONMENT DIVISION.
```

### 3. DATA DIVISION

This is where you declare all variables. COBOL calls them **data items**. They live in sections — the most common is the **WORKING-STORAGE SECTION**.

```cobol
DATA DIVISION.
WORKING-STORAGE SECTION.
01 MY-NAME     PIC A(20).
01 MY-AGE      PIC 9(3).
01 MY-SALARY   PIC 9(7)V99.
```

### 4. PROCEDURE DIVISION

This is where the actual logic lives — the code that runs.

```cobol
PROCEDURE DIVISION.
    DISPLAY "HELLO, WORLD!"
    STOP RUN.
```

---

## The DATA DIVISION in Depth

### PICTURE Clauses

The `PIC` (short for `PICTURE`) clause defines the shape and type of a variable. It's one of the most important concepts in COBOL.

| Symbol | Meaning              | Example          |
|--------|----------------------|------------------|
| `9`    | Numeric digit        | `PIC 9(5)` → up to 99999 |
| `A`    | Alphabetic character | `PIC A(10)` → 10 letters |
| `X`    | Alphanumeric (any)   | `PIC X(30)` → 30 any chars |
| `V`    | Implied decimal point | `PIC 9(5)V99` → 99999.99 |
| `S`    | Signed number        | `PIC S9(4)` → -9999 to 9999 |

The number in parentheses is the **repetition count** — how many of that character.

```cobol
WORKING-STORAGE SECTION.
01 CUSTOMER-NAME    PIC X(40).
01 ITEM-COUNT       PIC 9(3).
01 UNIT-PRICE       PIC 9(5)V99.
01 TOTAL-COST       PIC 9(7)V99.
```

### Level Numbers

Every data item starts with a **level number**. Level `01` is the top level. Higher numbers (02–49) create sub-items within a group, similar to fields within a struct.

```cobol
01 CUSTOMER-RECORD.
   05 CUST-FIRST-NAME   PIC X(20).
   05 CUST-LAST-NAME    PIC X(20).
   05 CUST-AGE          PIC 9(3).
```

Here, `CUSTOMER-RECORD` is a group item, and you can refer to it as a whole or access individual fields by their names.

### VALUE Clause

Use `VALUE` to set an initial value when a variable is declared.

```cobol
01 COUNTER      PIC 9(3) VALUE 0.
01 GREETING     PIC X(10) VALUE "HELLO".
01 TAX-RATE     PIC V99 VALUE .08.
```

---

## The PROCEDURE DIVISION in Depth

### DISPLAY

`DISPLAY` prints output to the screen.

```cobol
DISPLAY "THE COUNT IS: " COUNTER.
DISPLAY "HELLO, " CUSTOMER-NAME.
```

### ACCEPT

`ACCEPT` reads input from the user (or system).

```cobol
ACCEPT CUSTOMER-NAME.
ACCEPT MY-AGE.
```

### MOVE

`MOVE` copies a value into a variable. This is COBOL's primary assignment statement.

```cobol
MOVE "ALICE"   TO CUSTOMER-NAME.
MOVE 42        TO MY-AGE.
MOVE MY-AGE    TO ANOTHER-VAR.
```

COBOL does not use `=` for assignment — it uses `MOVE ... TO`.

---

## Arithmetic

COBOL has dedicated verbs for arithmetic operations:

```cobol
ADD 5 TO COUNTER.
ADD PRICE TAX GIVING TOTAL.

SUBTRACT 10 FROM BALANCE.
SUBTRACT DISCOUNT FROM PRICE GIVING NET-PRICE.

MULTIPLY QUANTITY BY UNIT-PRICE GIVING TOTAL-COST.

DIVIDE TOTAL BY COUNT GIVING AVERAGE.
DIVIDE TOTAL BY COUNT GIVING AVERAGE REMAINDER LEFT-OVER.
```

For more complex expressions, use `COMPUTE`:

```cobol
COMPUTE TOTAL = (PRICE * QUANTITY) - DISCOUNT + TAX.
COMPUTE AVERAGE = TOTAL / COUNT.
```

`COMPUTE` lets you write arithmetic similarly to how you would in most modern languages.

---

## Conditionals

### IF / ELSE / END-IF

```cobol
IF MY-AGE > 18
    DISPLAY "ADULT"
ELSE
    DISPLAY "MINOR"
END-IF.
```

Note the `END-IF` terminator — most COBOL blocks use these explicit terminators. You can also nest conditions:

```cobol
IF SCORE >= 90
    DISPLAY "A"
ELSE IF SCORE >= 80
    DISPLAY "B"
ELSE IF SCORE >= 70
    DISPLAY "C"
ELSE
    DISPLAY "F"
END-IF.
```

### Condition Names (88-Level Items)

One of COBOL's most elegant features is the **88-level condition name**. It lets you assign human-readable names to specific values:

```cobol
01 EMPLOYMENT-STATUS   PIC X VALUE "U".
   88 EMPLOYED         VALUE "E".
   88 UNEMPLOYED       VALUE "U".
   88 RETIRED          VALUE "R".
```

Now you can write:

```cobol
IF EMPLOYED
    DISPLAY "PROCESSING PAYROLL"
END-IF.

SET EMPLOYED TO TRUE.
```

This is far more readable than checking raw values like `"E"`.

---

## Loops with PERFORM

COBOL's loop construct is `PERFORM`. There are several forms.

### PERFORM a Paragraph

You can define a **paragraph** (a labeled block of code) and call it like a subroutine:

```cobol
PROCEDURE DIVISION.
    PERFORM PRINT-HEADER
    PERFORM PROCESS-DATA
    STOP RUN.

PRINT-HEADER.
    DISPLAY "=== REPORT ===".

PROCESS-DATA.
    DISPLAY "PROCESSING...".
```

### PERFORM TIMES

```cobol
PERFORM 10 TIMES
    DISPLAY "LOOPING"
END-PERFORM.
```

### PERFORM UNTIL

```cobol
MOVE 1 TO COUNTER.
PERFORM UNTIL COUNTER > 10
    DISPLAY COUNTER
    ADD 1 TO COUNTER
END-PERFORM.
```

### PERFORM VARYING

This is COBOL's classic for-loop:

```cobol
PERFORM VARYING COUNTER FROM 1 BY 1 UNTIL COUNTER > 10
    DISPLAY COUNTER
END-PERFORM.
```

This reads naturally: "Perform, varying COUNTER from 1, incrementing by 1, until COUNTER is greater than 10."

---

## Paragraphs and Program Flow

In COBOL, you organize logic into **paragraphs** — named blocks within the PROCEDURE DIVISION. The program starts at the top and executes sequentially until `STOP RUN`.

```cobol
PROCEDURE DIVISION.
    PERFORM INITIALIZE-VARS
    PERFORM GET-USER-INPUT
    PERFORM CALCULATE-RESULT
    PERFORM DISPLAY-RESULT
    STOP RUN.

INITIALIZE-VARS.
    MOVE 0 TO TOTAL.
    MOVE 0 TO COUNTER.

GET-USER-INPUT.
    DISPLAY "ENTER A NUMBER: ".
    ACCEPT USER-INPUT.

CALCULATE-RESULT.
    ADD USER-INPUT TO TOTAL.
    ADD 1 TO COUNTER.

DISPLAY-RESULT.
    DISPLAY "TOTAL: " TOTAL.
```

Structuring code into paragraphs is the COBOL equivalent of breaking logic into functions. It keeps programs readable and maintainable.

---

## A Complete Example

Here's a full program that reads two numbers and displays their sum:

```cobol
IDENTIFICATION DIVISION.
PROGRAM-ID. ADD-TWO-NUMS.

DATA DIVISION.
WORKING-STORAGE SECTION.
01 NUM-A    PIC 9(5) VALUE 0.
01 NUM-B    PIC 9(5) VALUE 0.
01 RESULT   PIC 9(6) VALUE 0.

PROCEDURE DIVISION.
    DISPLAY "ENTER FIRST NUMBER: "
    ACCEPT NUM-A
    DISPLAY "ENTER SECOND NUMBER: "
    ACCEPT NUM-B
    COMPUTE RESULT = NUM-A + NUM-B
    DISPLAY "SUM: " RESULT
    STOP RUN.
```

A few things to notice:
- All variable declarations happen in `WORKING-STORAGE`, before any logic
- `PIC 9(6)` for RESULT gives us one extra digit to handle the maximum sum
- There are no imports, no main function signatures — just the four divisions

---

## Key Things to Remember

- **Columns matter.** Traditional COBOL uses fixed-format columns (code starts in column 8 or 12). Modern compilers often support free-format, but be aware of this if you see alignment in old code.
- **Periods are significant.** A period `.` ends a sentence in COBOL. Missing or misplaced periods are a common source of bugs.
- **COBOL is case-insensitive.** `DISPLAY` and `display` are the same. Convention is ALL CAPS for keywords, mixed or upper for identifiers.
- **Hyphens in names.** Variable names use hyphens (`MY-VARIABLE`), not underscores. The hyphen is part of the name, not subtraction.
- **Explicit terminators.** Always close blocks with `END-IF`, `END-PERFORM`, `END-EVALUATE`, etc. The period can close blocks too, but explicit terminators are clearer and safer.

---

## Challenges

Try writing these programs to practice what you've learned. Each program should be a complete COBOL program with all four divisions.

1. **Hello, You** — Display "ENTER YOUR NAME:", accept input from the user, then display "HELLO, [name]!".

2. **Simple Adder** — Accept two numbers from the user and display their sum.

3. **Rectangle Area** — Accept a width and a height from the user and display the area of the rectangle.

4. **Count to Ten** — Use `PERFORM VARYING` to display the numbers 1 through 10, one per line.

5. **Even or Odd** — Accept a number from the user and display whether it is EVEN or ODD. (Hint: use `DIVIDE ... REMAINDER` and check if the remainder is 0.)

6. **Countdown** — Accept a starting number from the user and count down to 1, displaying each number.

7. **Running Total** — Accept 5 numbers from the user one at a time (use a loop), add each to a running total, and display the final total after all 5 have been entered.

8. **Grade Letter** — Accept a numeric score (0–100) and display the corresponding letter grade: A (90–100), B (80–89), C (70–79), D (60–69), F (below 60).

9. **Multiplication Table** — Display the multiplication table for a number entered by the user (e.g., if the user enters 7, show 7x1=7, 7x2=14, ... 7x10=70).

10. **Simple Interest Calculator** — Accept a principal amount, an annual interest rate (as a whole number, e.g. 5 for 5%), and a number of years. Calculate and display the simple interest earned using the formula `INTEREST = PRINCIPAL * RATE / 100 * YEARS`.
