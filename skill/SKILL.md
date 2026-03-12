---
name: generate-challenges
description: This skill should be used when the user wants to "generate a challenge", "create challenges from this readme", "scaffold challenges", "generate student exercises from readme", "create skeleton files from readme", "build challenge files", or when asked to generate implementation skeletons and test files for a coding school challenge based on a README.
version: 5.0.0
user-invocable: true
---

# Generate Coding Challenges from README

This skill reads `README.md` from the current directory and generates a complete project scaffold for a student coding challenge. The output always includes:

1. **Config / build files** so the project runs out of the box
2. **Skeleton implementation files** — just enough structure to start, no solutions
3. **Test files** — failing at first (✗ red), turning green (✓) as students implement
4. **Telemetry system** — tracks learning progress, test runs, AI usage, and assessments

This skill handles any language or framework. Adapt every step to what the README actually describes.

---

## Step 0: Detect Language and Framework

Read the README and classify the challenge. Look for these signals:

| Language / Framework        | Key signals                                                                                                            |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **React**                   | JSX/TSX, hooks (`useState`, `useEffect`), Vite, React DOM, `.tsx` files                                                |
| **Angular**                 | `ng generate`, `@Component`, `NgModule`, `TestBed`, Angular CLI, `ng test`                                             |
| **Vue**                     | `<template>`, `<script setup>`, Vue CLI/Vite, `@vue/test-utils`                                                        |
| **TypeScript / JS (plain)** | `.ts` files, class methods to implement, data structures, algorithms                                                   |
| **Python**                  | `.py` files, `pip`, `pytest`, Python syntax in code blocks                                                             |
| **Java**                    | `.java` files, Maven/Gradle, `public class`, `@Test` (JUnit), `extends`                                                |
| **C++**                     | `.cpp`/`.h` files, CMake, `#include`, `std::`, Google Test or Catch2                                                   |
| **Other**                   | Check code block syntax; apply the closest matching pattern; generate tests using the ecosystem's standard test runner |

If unsure, choose the framework whose toolchain most closely matches what the README describes. Never refuse to generate — always produce the best scaffold you can.

---

## Step 1: Parse the README

The README is the **single source of truth**. Do not invent requirements not mentioned in it.

### Find the challenge list

Challenge items may appear as:

- A numbered or bulleted list (`## Challenges`, `## Part 1`, `## Learning Goals`)
- Checkboxes (`- [ ] implement push`)
- Bolded challenge names (`**1. Hello, You**`)
- Section headings that are themselves challenge names (`### Stack`, `### Counter`)

Each item is one of:

- **Something to implement** (a method, component, function, class) → generate a skeleton stub
- **A property or field to track** → declare it in the skeleton with a placeholder value
- **A behavior or feature** (not a named method) → add a guiding comment in the skeleton
- **A bonus / extension** → still generate skeleton + tests; mark clearly with a BONUS comment

### Identify names and file structure

- Look for explicit class/component/file names in the README (inline code, `## Project Structure` sections)
- Derive names from challenge titles when not explicit (e.g., "Click Counter" → `Counter`)
- Use the language's naming conventions (PascalCase for classes/components, snake_case for Python modules, etc.)
- **Single challenge** → single file; **multiple independent challenges** → one folder per challenge

---

## Step 2: Generate Config and Build Files

See `references/project-templates.md` for templates.

Choose the appropriate template for the detected language/framework. Always generate:

- A build/dependency file (`package.json`, `pom.xml`, `requirements.txt`, `CMakeLists.txt`, etc.)
- A language config file where applicable (`tsconfig.json`, etc.)
- Framework-specific config (`vite.config.ts`, `angular.json` stub, etc.)
- `.gitignore`

Configure the test command to **stop after the first failure** if the framework supports it (e.g. `--bail 1` in Vitest, `-x` in pytest, `skipAfterFailureCount` in Maven Surefire, `--stop-on-failure` in ctest). This keeps students focused on one problem at a time. See `references/project-templates.md` for the exact flag per framework.

---

## Step 3: Generate Skeleton Implementation Files

See `references/generation-patterns.md` for examples by language.

Skeleton files share these principles regardless of language:

- A comment at the top stating the challenge description (from the README)
- Import/include statements for whatever the student will likely need
- The **shape** of the solution without the logic: empty function bodies, empty component shells, stub methods
- Comments inside stubs that say **what** the code should do, not **how**
- No implementation at all — not even partial — unless the README explicitly provides starter code (e.g., a pre-built hash function)
- Return placeholder values where the language requires a return type (e.g., `return null`, `return 0`, `pass`)

---

## Step 4: Generate Test Files

See `references/generation-patterns.md` for examples by language.

Test files share these principles regardless of language:

- Use the language's **standard test runner** for the detected ecosystem
- Import the skeleton using the same export/import style as the implementation file
- **Fresh instance per test** — use `beforeEach` / `setUp` / fixtures to reset state between tests
- Tests begin **failing** because the skeleton is empty — that's intentional and expected
- Do not test bonus items in the main test file

Test progression per challenge item:

1. **Existence / smoke** — does the class/component/function exist and not crash?
2. **Initial state** — does it start with the right default values?
3. **Basic behavior** — simplest happy path
4. **Return values / output** — correct value returned or displayed
5. **Edge cases** — empty state, null inputs, boundary values
6. **Interactions** — multiple operations working together correctly

Write tests that are **specific and predictable**:

- Test for concrete, exact values — not synonym patterns like `/hello|hi|greet/`
- Avoid vague structural assertions ("the container is not empty")
- Every test should have a clear failing state when the skeleton is unimplemented

---

## Step 5: Generate Telemetry Infrastructure

See `references/telemetry-system.md` for complete implementation details.

The telemetry system tracks student learning progress through six mechanisms. Generate these files:

### 5.1 Configuration

Generate `telemetry.config.json` at project root:

```json
{
  "enabled": true,
  "studentId": null,
  "cohortId": null,
  "remoteEndpoint": null,
  "syncInterval": 300000,
  "trackTestRuns": true,
  "trackGitCommits": true,
  "trackAIInteractions": true,
  "trackAssessments": true,
  "aiEvaluation": {
    "enabled": true,
    "provider": "anthropic",
    "apiKeyEnvVar": "ANTHROPIC_API_KEY",
    "model": "claude-sonnet-4-20250514",
    "trigger": "on_test_run",
    "features": {
      "codeQuality": true,
      "errorPatterns": true,
      "learningProgress": true,
      "hints": true
    }
  }
}
```

### 5.2 Test-Run Telemetry

Generate language-appropriate telemetry modules that hook into the test runner:

| Language | Files to generate |
|----------|-------------------|
| TypeScript/JS | `src/telemetry/telemetry.ts`, `src/telemetry/vitest-reporter.ts` |
| Python | `src/telemetry/telemetry.py`, `src/telemetry/conftest.py` |
| Java | `src/test/java/com/challenge/telemetry/TelemetryListener.java` |

Update test configuration to include the telemetry reporter.

### 5.3 AI Evaluation Layer

Generate AI-powered code analysis that provides:
- **Code quality review** — style, readability, best practices
- **Error pattern analysis** — common mistakes, misconceptions, root causes
- **Learning progress tracking** — skill gaps, concept mastery
- **Contextual hints** — guidance for failing tests without giving solutions

| Language | Files to generate |
|----------|-------------------|
| TypeScript/JS | `src/telemetry/ai-evaluator.ts` |
| Python | `src/telemetry/ai_evaluator.py` |

The AI evaluator is provider-agnostic (Anthropic, OpenAI, Ollama) and configurable via `aiEvaluation` in `telemetry.config.json`.

**Trigger options:**
- `on_test_run` — evaluate after every test run (real-time feedback)
- `on_demand` — student/instructor runs `npm run evaluate` manually
- `on_completion` — evaluate only when all tests pass (summary review)

### 5.4 Git Analysis Script

Generate `scripts/analyze-git-progress.sh` — a bash script that analyzes commit history to understand learning patterns (commit frequency, files changed, time between attempts).

### 5.5 Progress Dashboard

Generate `progress.html` — a self-contained HTML dashboard that reads from `.telemetry/` and displays:
- Tests passed/failed
- Total attempts
- Time active
- Per-challenge status
- Recent activity timeline

### 5.6 Pre/Post Assessments

Generate assessment templates based on README concepts:

- `assessment/pre-assessment.md` — confidence ratings and knowledge check before starting
- `assessment/post-assessment.md` — reflection, confidence delta, AI usage survey

Generate `scripts/parse-assessments.js` — parses completed assessments and writes to telemetry.

### 5.7 Update .gitignore

Add telemetry exclusions:

```
# Telemetry (local only)
.telemetry/
```

---

## Step 6: Report Results

After generating all files, output a summary:

- List every file created with its path
- Show the exact commands to install and run tests
- Remind students: tests start red (✗), turn green (✓) as they implement each challenge
- For UI frameworks (React, Angular, Vue): also show how to run the dev server

Include telemetry instructions:

```text
Telemetry Enabled
-----------------
Learning telemetry is ON by default. Data is stored locally in .telemetry/

To disable: set "enabled": false in telemetry.config.json
To view progress: open progress.html in browser (run `npx serve .` first)
To analyze git history: bash scripts/analyze-git-progress.sh

AI Evaluation
-------------
AI-powered feedback is enabled. Set your API key:
  export ANTHROPIC_API_KEY=your-key-here

Triggers: on_test_run (default), on_demand, on_completion
Run manually: npm run evaluate

Before starting:
1. Fill out assessment/pre-assessment.md

After finishing:
1. Fill out assessment/post-assessment.md
2. Run: node scripts/parse-assessments.js
```
