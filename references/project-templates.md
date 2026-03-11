# Project Templates

Select the template that matches the detected language/framework. When a template doesn't exist for a language, reason from first principles: what is the standard build tool and test runner for that ecosystem?

---

## JavaScript / TypeScript (plain — no UI framework)

### `package.json`

```json
{
  "type": "module",
  "scripts": {
    "test": "vitest --bail 1"
  },
  "dependencies": {
    "vitest": "^3.1.1"
  }
}
```

Add `tsx` and a `start` script only if the README mentions running a file directly:
```json
{
  "type": "module",
  "scripts": {
    "start": "tsx src/FileName.ts",
    "test": "vitest --bail 1"
  },
  "dependencies": {
    "tsx": "^4.19.4",
    "vitest": "^3.1.1"
  }
}
```

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": false,
    "allowJs": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

`"strict": false` is intentional — students work with `any` types; strict mode produces distracting errors on incomplete stubs.

### Running

```
npm install
npm test      # stops at first failure (--bail 1); fix one test at a time
```

---

## React

### `package.json`

```json
{
  "type": "module",
  "scripts": {
    "dev": "vite",
    "test": "vitest --bail 1"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "jsdom": "^24.0.0",
    "vite": "^5.4.0",
    "vitest": "^3.1.1"
  }
}
```

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": false,
    "allowJs": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

### `vite.config.ts`

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
  },
});
```

### `src/setupTests.ts`

```typescript
import "@testing-library/jest-dom";
```

### Running

```
npm install
npm test        # stops at first failure (--bail 1); fix one test at a time
npm run dev     # open in browser for visual testing
```

---

## Angular

Angular projects are scaffolded with the Angular CLI. Generate the following files assuming a standard Angular CLI project structure.

### `package.json`

```json
{
  "scripts": {
    "ng": "ng",
    "start": "ng serve",
    "test": "ng test --watch=false --karma-config=karma.conf.js"
  },
  "dependencies": {
    "@angular/animations": "^17.0.0",
    "@angular/common": "^17.0.0",
    "@angular/compiler": "^17.0.0",
    "@angular/core": "^17.0.0",
    "@angular/forms": "^17.0.0",
    "@angular/platform-browser": "^17.0.0",
    "@angular/platform-browser-dynamic": "^17.0.0",
    "@angular/router": "^17.0.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.6.0",
    "zone.js": "~0.14.0"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^17.0.0",
    "@angular/cli": "^17.0.0",
    "@angular/compiler-cli": "^17.0.0",
    "@types/jasmine": "~5.1.0",
    "jasmine-core": "~5.1.0",
    "karma": "~6.4.0",
    "karma-chrome-launcher": "~3.2.0",
    "karma-coverage": "~2.2.0",
    "karma-jasmine": "~5.1.0",
    "karma-jasmine-html-reporter": "~2.1.0",
    "typescript": "~5.2.0"
  }
}
```

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "dom"],
    "module": "ES2022",
    "moduleResolution": "bundler",
    "experimentalDecorators": true,
    "strict": false,
    "skipLibCheck": true
  }
}
```

### `karma.conf.js`

Generate this file at the project root. The `bail: true` option stops the run after the first test failure.

```javascript
module.exports = function (config) {
  config.set({
    basePath: "",
    frameworks: ["jasmine", "@angular-devkit/build-angular"],
    plugins: [
      require("karma-jasmine"),
      require("karma-chrome-launcher"),
      require("karma-jasmine-html-reporter"),
      require("karma-coverage"),
      require("@angular-devkit/build-angular/plugins/karma"),
    ],
    reporters: ["progress"],
    browsers: ["ChromeHeadless"],
    singleRun: true,
    bail: true,   // stop after the first test failure
  });
};
```

### Running

```
npm install
npm test        # stops at first failure (bail: true); fix one test at a time
ng serve        # open in browser for visual testing
```

---

## Python

No `package.json`. Generate a `requirements.txt` and standard pytest layout.

### `requirements.txt`

```
pytest
```

### File layout

```
src/
  challenge_name.py      # skeleton implementation
tests/
  test_challenge_name.py # pytest tests
```

### Running

```
pip install -r requirements.txt
pytest -x       # stops at first failure (-x); fix one test at a time
pytest -x -v    # same but verbose — shows each test name with pass/fail
```

---

## Java

Use Maven as the default build tool.

### `pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <groupId>com.challenge</groupId>
  <artifactId>challenge</artifactId>
  <version>1.0-SNAPSHOT</version>

  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>

  <dependencies>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>5.10.0</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.junit.platform</groupId>
      <artifactId>junit-platform-launcher</artifactId>
      <version>1.10.0</version>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.2</version>
        <configuration>
          <!-- stop after the first test failure -->
          <skipAfterFailureCount>1</skipAfterFailureCount>
          <!-- stream output to console (required for custom listener output to appear) -->
          <useFile>false</useFile>
          <reportFormat>plain</reportFormat>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

### File layout

```
src/
  main/java/com/challenge/ClassName.java                          # skeleton implementation
  test/java/com/challenge/ClassNameTest.java                      # JUnit 5 tests
  test/java/com/challenge/support/ChallengeTestListener.java      # custom test reporter (always generate)
  test/resources/META-INF/services/
    org.junit.platform.launcher.TestExecutionListener             # ServiceLoader registration (always generate)
```

### `src/test/java/com/challenge/support/ChallengeTestListener.java`

Always generate this file. It auto-registers via ServiceLoader and prints ✓/✗ per test to the console with passing tests listed before failing ones.

```java
package com.challenge.support;

import org.junit.platform.engine.TestExecutionResult;
import org.junit.platform.engine.TestExecutionResult.Status;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;

import java.util.ArrayList;
import java.util.List;

public class ChallengeTestListener implements TestExecutionListener {

    private static final String GREEN = "\u001B[32m";
    private static final String RED   = "\u001B[31m";
    private static final String RESET = "\u001B[0m";

    private final List<String> passes   = new ArrayList<>();
    private final List<String> failures = new ArrayList<>();
    private String currentClassId   = null;
    private String currentClassName = null;

    @Override
    public void executionStarted(TestIdentifier id) {
        if (!id.isTest() && id.getParentId().isPresent()) {
            passes.clear();
            failures.clear();
            currentClassId   = id.getUniqueId();
            currentClassName = id.getDisplayName();
        }
    }

    @Override
    public void executionFinished(TestIdentifier id, TestExecutionResult result) {
        if (id.isTest()) {
            String name = id.getDisplayName();
            if (name.endsWith("()")) name = name.substring(0, name.length() - 2);

            if (result.getStatus() == Status.SUCCESSFUL) {
                passes.add(GREEN + "  ✓ " + name + RESET);
            } else {
                StringBuilder sb = new StringBuilder(RED + "  ✗ " + name + RESET);
                result.getThrowable().ifPresent(t -> {
                    String msg = t.getMessage();
                    if (msg == null) msg = t.getClass().getSimpleName();
                    if (msg.length() > 120) msg = msg.substring(0, 120) + "…";
                    sb.append("\n      → ").append(msg);
                });
                failures.add(sb.toString());
            }
        } else if (id.getUniqueId().equals(currentClassId)) {
            System.out.println("\n── " + currentClassName + " " + "─".repeat(40));
            passes.forEach(System.out::println);
            failures.forEach(System.out::println);
        }
    }
}
```

### `src/test/resources/META-INF/services/org.junit.platform.launcher.TestExecutionListener`

```
com.challenge.support.ChallengeTestListener
```

### Running

```
mvn test                        # all challenges; stops after first failing challenge
mvn test -Dtest=ClassNameTest   # single challenge by test class name
```

---

## C++

Use CMake with Google Test.

### `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.14)
project(challenge)

set(CMAKE_CXX_STANDARD 17)

include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
)
FetchContent_MakeAvailable(googletest)

add_library(challenge_lib src/ClassName.cpp)
target_include_directories(challenge_lib PUBLIC include)

add_executable(tests tests/ClassNameTest.cpp)
target_link_libraries(tests challenge_lib GTest::gtest_main)

include(GoogleTest)
gtest_discover_tests(tests)
```

### File layout

```
include/
  ClassName.h             # class declaration
src/
  ClassName.cpp           # skeleton implementation
tests/
  ClassNameTest.cpp       # Google Test tests
CMakeLists.txt
```

### Running

```
cmake -S . -B build
cmake --build build
cd build && ctest --stop-on-failure --output-on-failure
```

`--stop-on-failure` (CMake 3.16+) stops after the first failing test.

---

## Vue

### `package.json`

```json
{
  "type": "module",
  "scripts": {
    "dev": "vite",
    "test": "vitest --bail 1"
  },
  "dependencies": {
    "vue": "^3.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "@vue/test-utils": "^2.4.0",
    "jsdom": "^24.0.0",
    "vite": "^5.4.0",
    "vitest": "^3.1.1"
  }
}
```

### `vite.config.ts`

```typescript
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    globals: true,
  },
});
```

### Running

```
npm install
npm test        # stops at first failure (--bail 1); fix one test at a time
npm run dev     # open in browser for visual testing
```

---

## COBOL (GnuCOBOL)

COBOL has no standard unit-test framework. Generate a bash test runner that compiles each `.cbl` file with `cobc` and pipes input through the binary, then checks stdout with `grep`.

### File layout

```
src/
  01-challenge-name.cbl     # skeleton (one per challenge)
  02-...
tests/
  run_tests.sh              # bash test runner
.gitignore
```

No `package.json`, `pom.xml`, or other build file is needed.

### `tests/run_tests.sh` structure

```bash
#!/usr/bin/env bash
# Requires: GnuCOBOL (cobc)
#   macOS:   brew install gnucobol
#   Ubuntu:  sudo apt install gnucobol
#
# Usage: bash tests/run_tests.sh

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0

if ! command -v cobc &>/dev/null; then
    echo "ERROR: GnuCOBOL (cobc) not found."
    echo "  macOS:   brew install gnucobol"
    echo "  Ubuntu:  sudo apt install gnucobol"
    exit 1
fi

BINDIR=$(mktemp -d)
trap 'rm -rf "$BINDIR"' EXIT

# CRITICAL: macOS ships with bash 3.2, which does NOT support declare -A
# (associative arrays). Never use declare -A in this script.
# Cache compiled binaries by checking for file existence instead:
run_test() {
    local name="$1"
    local src="$2"
    local input="$3"
    local pattern="$4"

    local binary="$BINDIR/$(basename "${src%.cbl}")"
    if [ ! -f "$binary" ]; then
        if ! cobc -x -free -o "$binary" "$src" 2>/tmp/cobc_error; then
            binary="ERROR"
        fi
    fi

    if [ "$binary" = "ERROR" ]; then
        printf "${RED}✗${NC}  %s\n" "$name"
        echo "   COMPILE ERROR:"
        sed 's/^/     /' /tmp/cobc_error | head -10
        echo ""
        printf "${YELLOW}Fix the compile error above, then run: bash tests/run_tests.sh${NC}\n"
        exit 1
    fi

    local output
    if command -v timeout &>/dev/null; then
        output=$(printf "%s" "$input" | timeout 5 "$binary" 2>/dev/null || true)
    else
        output=$(printf "%s" "$input" | "$binary" 2>/dev/null || true)
    fi

    if echo "$output" | grep -qE "$pattern"; then
        printf "${GREEN}✓${NC}  %s\n" "$name"
        PASS=$((PASS + 1))
    else
        printf "${RED}✗${NC}  %s\n" "$name"
        echo "   Expected output matching: $pattern"
        if [ -n "$output" ]; then
            echo "   Actual output:"
            echo "$output" | head -5 | sed 's/^/     /'
        else
            echo "   Actual output: (empty — add DISPLAY statements)"
        fi
        echo ""
        printf "${YELLOW}Fix the failing test above, then run: bash tests/run_tests.sh${NC}\n"
        exit 1
    fi
}

echo ""
echo "COBOL Challenges"
echo "════════════════════════════════════"
echo ""

# --- tests go here ---
# run_test "1a. Label" "src/01-file.cbl" "user input" "grep pattern"
# For multi-line input: $'line1\nline2'
# For no input: ""

echo ""
echo "════════════════════════════════════"
printf "${GREEN}All $PASS tests passed!${NC}\n"
echo ""
```

### Key behaviours to know when writing test patterns

| Situation | What to expect | Pattern approach |
|---|---|---|
| Numeric variable `PIC 9(5)` displaying 8 | Output: `00008` | Pattern `8` — substring match works |
| String variable `PIC X(20)` storing "ALICE" | Output: `ALICE               ` (space-padded) | Pattern `ALICE` — substring match works |
| Single letter grade "C" | "C" appears in words like "SCORE" | Use `\bC\b` for word-boundary match |
| Test input appears in output | e.g., input `1000` → output may echo `001000` | Pick test inputs whose expected result does NOT appear as a substring of the inputs |

### Running

```
brew install gnucobol     # macOS (one-time setup)
bash tests/run_tests.sh   # stops at first failure; fix one challenge at a time
```

---

## `.gitignore` (all projects)

Adapt as appropriate for the language:

```
# JavaScript / TypeScript
node_modules/
dist/

# Python
__pycache__/
*.pyc
.pytest_cache/
venv/

# Java / Maven
target/
*.class

# C++
build/

# General
.DS_Store
*.env
```
