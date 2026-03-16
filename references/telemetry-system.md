# Telemetry System Reference

This document describes how to generate telemetry-enabled challenge projects. The telemetry system tracks student learning progress through six integrated mechanisms.

---

## Overview

The telemetry system consists of:

1. **Test-Run Telemetry** — Automatic logging of test executions
2. **AI Evaluation Layer** — AI-powered code review, error analysis, and personalized hints
3. **Git Commit Analysis** — Post-hoc analysis of commit patterns
4. **AI Interaction Logging** — Tracking Claude Code assistance usage
5. **Progress Dashboard** — Visual progress tracker
6. **Pre/Post Assessment** — Knowledge self-assessment

All telemetry is **opt-out by default** (enabled unless student disables it).

Data is stored locally in `.telemetry/` and can optionally sync to a remote endpoint.

---

## Configuration

Generate a `telemetry.config.json` at the project root:

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

Students can disable telemetry by setting `"enabled": false`.

Instructors can pre-configure `studentId`, `cohortId`, and `remoteEndpoint` before distributing.

### AI Evaluation Configuration

| Field | Values | Description |
|-------|--------|-------------|
| `provider` | `"anthropic"`, `"openai"`, `"ollama"` | AI provider to use |
| `apiKeyEnvVar` | string | Environment variable containing API key |
| `model` | string | Model identifier (provider-specific) |
| `trigger` | `"on_test_run"`, `"on_demand"`, `"on_completion"` | When to run AI evaluation |
| `features.codeQuality` | boolean | Analyze style, readability, best practices |
| `features.errorPatterns` | boolean | Identify common mistakes and misconceptions |
| `features.learningProgress` | boolean | Track skill gaps and mastery |
| `features.hints` | boolean | Generate contextual hints for failing tests |

---

## 1. Test-Run Telemetry

### Event Schema

Each test run produces a JSON event in `.telemetry/test-runs.jsonl`:

```json
{
  "type": "test_run",
  "timestamp": "2025-03-12T14:30:00.000Z",
  "sessionId": "abc123",
  "challenge": "Stack",
  "testFile": "src/Stack/Stack.test.ts",
  "results": [
    {
      "name": "should push and pop in LIFO order",
      "status": "passed",
      "duration": 12
    },
    {
      "name": "should return undefined when popping empty stack",
      "status": "failed",
      "duration": 5,
      "error": "Expected undefined, got null"
    }
  ],
  "summary": {
    "total": 2,
    "passed": 1,
    "failed": 1,
    "duration": 17
  }
}
```

### Implementation by Language

#### TypeScript/JavaScript (Vitest)

Generate `src/telemetry/telemetry.ts`:

```typescript
import { writeFileSync, appendFileSync, existsSync, mkdirSync, readFileSync } from "fs";
import { join } from "path";

interface TestResult {
  name: string;
  status: "passed" | "failed" | "skipped";
  duration: number;
  error?: string;
}

interface TestRunEvent {
  type: "test_run";
  timestamp: string;
  sessionId: string;
  challenge: string;
  testFile: string;
  results: TestResult[];
  summary: {
    total: number;
    passed: number;
    failed: number;
    duration: number;
  };
}

interface TelemetryConfig {
  enabled: boolean;
  studentId: string | null;
  cohortId: string | null;
  remoteEndpoint: string | null;
  syncInterval: number;
  trackTestRuns: boolean;
  trackGitCommits: boolean;
  trackAIInteractions: boolean;
  trackAssessments: boolean;
}

const TELEMETRY_DIR = ".telemetry";
const CONFIG_FILE = "telemetry.config.json";
const TEST_RUNS_FILE = "test-runs.jsonl";

let sessionId: string | null = null;

function getSessionId(): string {
  if (!sessionId) {
    sessionId = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  }
  return sessionId;
}

function getConfig(): TelemetryConfig {
  const configPath = join(process.cwd(), CONFIG_FILE);
  if (existsSync(configPath)) {
    try {
      return JSON.parse(readFileSync(configPath, "utf-8"));
    } catch {
      // Fall through to defaults
    }
  }
  return {
    enabled: true,
    studentId: null,
    cohortId: null,
    remoteEndpoint: null,
    syncInterval: 300000,
    trackTestRuns: true,
    trackGitCommits: true,
    trackAIInteractions: true,
    trackAssessments: true,
  };
}

function ensureTelemetryDir(): void {
  const dir = join(process.cwd(), TELEMETRY_DIR);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

export function logTestRun(event: Omit<TestRunEvent, "type" | "timestamp" | "sessionId">): void {
  const config = getConfig();
  if (!config.enabled || !config.trackTestRuns) return;

  ensureTelemetryDir();

  const fullEvent: TestRunEvent = {
    type: "test_run",
    timestamp: new Date().toISOString(),
    sessionId: getSessionId(),
    ...event,
  };

  const filePath = join(process.cwd(), TELEMETRY_DIR, TEST_RUNS_FILE);
  appendFileSync(filePath, JSON.stringify(fullEvent) + "\n");

  // Async sync to remote if configured
  if (config.remoteEndpoint) {
    syncToRemote(config.remoteEndpoint, fullEvent).catch(() => {
      // Silently fail - local data is preserved
    });
  }
}

async function syncToRemote(endpoint: string, event: TestRunEvent): Promise<void> {
  const config = getConfig();
  await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...event,
      studentId: config.studentId,
      cohortId: config.cohortId,
    }),
  });
}

export { TestResult, TestRunEvent, TelemetryConfig };
```

Generate `src/telemetry/vitest-reporter.ts`:

```typescript
import type { Reporter, File, Task } from "vitest";
import { logTestRun, TestResult } from "./telemetry";

function extractChallengeName(filepath: string): string {
  // Extract challenge name from path like "src/Stack/Stack.test.ts" -> "Stack"
  const parts = filepath.split("/");
  const filename = parts[parts.length - 1];
  return filename.replace(/\.test\.(ts|tsx|js|jsx)$/, "");
}

function collectResults(tasks: Task[]): TestResult[] {
  const results: TestResult[] = [];

  for (const task of tasks) {
    if (task.type === "test") {
      results.push({
        name: task.name,
        status: task.result?.state === "pass" ? "passed" : task.result?.state === "skip" ? "skipped" : "failed",
        duration: task.result?.duration ?? 0,
        error: task.result?.errors?.[0]?.message,
      });
    } else if (task.type === "suite" && task.tasks) {
      results.push(...collectResults(task.tasks));
    }
  }

  return results;
}

export default class TelemetryReporter implements Reporter {
  onFinished(files?: File[]) {
    if (!files) return;

    for (const file of files) {
      const results = collectResults(file.tasks);
      const passed = results.filter((r) => r.status === "passed").length;
      const failed = results.filter((r) => r.status === "failed").length;
      const totalDuration = results.reduce((sum, r) => sum + r.duration, 0);

      logTestRun({
        challenge: extractChallengeName(file.filepath),
        testFile: file.filepath,
        results,
        summary: {
          total: results.length,
          passed,
          failed,
          duration: totalDuration,
        },
      });
    }
  }
}
```

Update `vite.config.ts` to include the reporter:

```typescript
import { defineConfig } from "vite";
// ... other imports

export default defineConfig({
  // ... other config
  test: {
    // ... other test config
    reporters: ["default", "./src/telemetry/vitest-reporter.ts"],
  },
});
```

#### Python (pytest)

Generate `src/telemetry/telemetry.py`:

```python
"""Telemetry module for tracking student learning progress."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

TELEMETRY_DIR = ".telemetry"
CONFIG_FILE = "telemetry.config.json"
TEST_RUNS_FILE = "test-runs.jsonl"

_session_id: Optional[str] = None


def get_session_id() -> str:
    global _session_id
    if _session_id is None:
        _session_id = f"{int(datetime.now().timestamp() * 1000)}-{uuid.uuid4().hex[:7]}"
    return _session_id


def get_config() -> dict:
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except Exception:
            pass
    return {
        "enabled": True,
        "studentId": None,
        "cohortId": None,
        "remoteEndpoint": None,
        "syncInterval": 300000,
        "trackTestRuns": True,
        "trackGitCommits": True,
        "trackAIInteractions": True,
        "trackAssessments": True,
    }


def ensure_telemetry_dir() -> Path:
    telemetry_path = Path(TELEMETRY_DIR)
    telemetry_path.mkdir(exist_ok=True)
    return telemetry_path


def log_test_run(challenge: str, test_file: str, results: list, summary: dict) -> None:
    config = get_config()
    if not config.get("enabled") or not config.get("trackTestRuns"):
        return

    telemetry_dir = ensure_telemetry_dir()

    event = {
        "type": "test_run",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sessionId": get_session_id(),
        "challenge": challenge,
        "testFile": test_file,
        "results": results,
        "summary": summary,
    }

    file_path = telemetry_dir / TEST_RUNS_FILE
    with open(file_path, "a") as f:
        f.write(json.dumps(event) + "\n")

    # Async sync to remote if configured
    if config.get("remoteEndpoint"):
        _sync_to_remote(config["remoteEndpoint"], event, config)


def _sync_to_remote(endpoint: str, event: dict, config: dict) -> None:
    try:
        import urllib.request

        data = {
            **event,
            "studentId": config.get("studentId"),
            "cohortId": config.get("cohortId"),
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Silently fail - local data is preserved
```

Generate `src/telemetry/conftest.py` (pytest plugin):

```python
"""Pytest plugin for telemetry collection."""

import time
from pathlib import Path
import pytest
from .telemetry import log_test_run


class TelemetryPlugin:
    def __init__(self):
        self.results = []
        self.current_file = None
        self.start_time = None

    def pytest_collection_modifyitems(self, items):
        if items:
            self.current_file = str(items[0].fspath)

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.results.append({
                "name": report.nodeid.split("::")[-1],
                "status": "passed" if report.passed else "failed" if report.failed else "skipped",
                "duration": int(report.duration * 1000),
                "error": str(report.longrepr) if report.failed else None,
            })

    def pytest_sessionfinish(self, session, exitstatus):
        if not self.results:
            return

        # Extract challenge name from test file path
        test_file = self.current_file or "unknown"
        challenge = Path(test_file).stem.replace("test_", "")

        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        total_duration = sum(r["duration"] for r in self.results)

        log_test_run(
            challenge=challenge,
            test_file=test_file,
            results=self.results,
            summary={
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "duration": total_duration,
            },
        )


def pytest_configure(config):
    config.pluginmanager.register(TelemetryPlugin(), "telemetry_plugin")
```

#### Java (JUnit 5)

Generate `src/test/java/com/challenge/telemetry/TelemetryListener.java`:

```java
package com.challenge.telemetry;

import org.junit.platform.engine.TestExecutionResult;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;
import org.junit.platform.launcher.TestPlan;

import java.io.*;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

public class TelemetryListener implements TestExecutionListener {

    private static final String TELEMETRY_DIR = ".telemetry";
    private static final String TEST_RUNS_FILE = "test-runs.jsonl";

    private final List<Map<String, Object>> results = new ArrayList<>();
    private String currentClass = null;
    private final String sessionId;

    public TelemetryListener() {
        this.sessionId = System.currentTimeMillis() + "-" +
            UUID.randomUUID().toString().substring(0, 7);
    }

    @Override
    public void executionStarted(TestIdentifier id) {
        if (!id.isTest() && id.getParentId().isPresent()) {
            currentClass = id.getDisplayName();
            results.clear();
        }
    }

    @Override
    public void executionFinished(TestIdentifier id, TestExecutionResult result) {
        if (id.isTest()) {
            Map<String, Object> testResult = new HashMap<>();
            testResult.put("name", id.getDisplayName().replace("()", ""));
            testResult.put("status", result.getStatus() == TestExecutionResult.Status.SUCCESSFUL ? "passed" : "failed");
            testResult.put("duration", 0); // JUnit doesn't provide duration in listener

            result.getThrowable().ifPresent(t ->
                testResult.put("error", t.getMessage())
            );

            results.add(testResult);
        } else if (id.getDisplayName().equals(currentClass)) {
            writeTestRun();
        }
    }

    private void writeTestRun() {
        if (!isEnabled()) return;

        try {
            Path telemetryDir = Paths.get(TELEMETRY_DIR);
            Files.createDirectories(telemetryDir);

            long passed = results.stream().filter(r -> "passed".equals(r.get("status"))).count();
            long failed = results.stream().filter(r -> "failed".equals(r.get("status"))).count();

            Map<String, Object> event = new LinkedHashMap<>();
            event.put("type", "test_run");
            event.put("timestamp", Instant.now().toString());
            event.put("sessionId", sessionId);
            event.put("challenge", currentClass);
            event.put("testFile", currentClass + "Test.java");
            event.put("results", results);

            Map<String, Object> summary = new HashMap<>();
            summary.put("total", results.size());
            summary.put("passed", passed);
            summary.put("failed", failed);
            summary.put("duration", 0);
            event.put("summary", summary);

            Path filePath = telemetryDir.resolve(TEST_RUNS_FILE);
            Files.write(filePath,
                (toJson(event) + "\n").getBytes(),
                StandardOpenOption.CREATE,
                StandardOpenOption.APPEND);

        } catch (IOException e) {
            // Silently fail
        }
    }

    private boolean isEnabled() {
        Path configPath = Paths.get("telemetry.config.json");
        if (Files.exists(configPath)) {
            try {
                String content = Files.readString(configPath);
                return !content.contains("\"enabled\": false") &&
                       !content.contains("\"trackTestRuns\": false");
            } catch (IOException e) {
                return true;
            }
        }
        return true;
    }

    private String toJson(Map<String, Object> map) {
        StringBuilder sb = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            if (!first) sb.append(",");
            first = false;
            sb.append("\"").append(entry.getKey()).append("\":");
            sb.append(valueToJson(entry.getValue()));
        }
        sb.append("}");
        return sb.toString();
    }

    private String valueToJson(Object value) {
        if (value == null) return "null";
        if (value instanceof String) return "\"" + escapeJson((String) value) + "\"";
        if (value instanceof Number) return value.toString();
        if (value instanceof Boolean) return value.toString();
        if (value instanceof List) {
            StringBuilder sb = new StringBuilder("[");
            boolean first = true;
            for (Object item : (List<?>) value) {
                if (!first) sb.append(",");
                first = false;
                if (item instanceof Map) {
                    sb.append(toJson((Map<String, Object>) item));
                } else {
                    sb.append(valueToJson(item));
                }
            }
            sb.append("]");
            return sb.toString();
        }
        if (value instanceof Map) return toJson((Map<String, Object>) value);
        return "\"" + value.toString() + "\"";
    }

    private String escapeJson(String s) {
        return s.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
```

Register in `src/test/resources/META-INF/services/org.junit.platform.launcher.TestExecutionListener`:

```text
com.challenge.telemetry.TelemetryListener
com.challenge.support.ChallengeTestListener
```

---

## 2. AI Evaluation Layer

The AI Evaluation Layer provides intelligent analysis of student code, building on top of raw test-run telemetry. It uses LLMs to provide:

- **Code Quality Review** — Style, readability, naming, best practices
- **Error Pattern Analysis** — Common mistakes, misconceptions, root cause identification
- **Learning Progress Tracking** — Skill gaps, concept mastery, personalized recommendations
- **Contextual Hints** — Targeted suggestions for failing tests without giving away solutions

### Event Schema

AI evaluations are stored in `.telemetry/ai-evaluations.jsonl`:

```json
{
  "type": "ai_evaluation",
  "timestamp": "2025-03-12T14:30:05.000Z",
  "sessionId": "abc123",
  "challenge": "Stack",
  "testRunId": "abc123-1710251400000",
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "trigger": "on_test_run",
  "evaluation": {
    "codeQuality": {
      "score": 7,
      "strengths": ["Good variable naming", "Consistent formatting"],
      "improvements": ["Consider using const instead of let for immutable values"],
      "details": "The code is readable but could benefit from..."
    },
    "errorPatterns": {
      "identified": ["off-by-one-error", "undefined-vs-null-confusion"],
      "misconceptions": ["Student may not understand stack index management"],
      "rootCause": "The pop() method decrements index after accessing, should decrement before"
    },
    "learningProgress": {
      "conceptsMastered": ["class-structure", "method-definition"],
      "conceptsStruggling": ["index-management", "edge-cases"],
      "recommendedReview": ["Array indexing fundamentals", "Boundary conditions"]
    },
    "hints": [
      {
        "testName": "should return undefined when popping empty stack",
        "hint": "Think about what index value means 'empty'. What should pop() check before accessing storage?",
        "severity": "gentle"
      }
    ]
  },
  "tokensUsed": {
    "input": 1250,
    "output": 450
  }
}
```

### Implementation

#### TypeScript/JavaScript

Generate `src/telemetry/ai-evaluator.ts`:

```typescript
import { readFileSync, appendFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

interface AIEvaluationConfig {
  enabled: boolean;
  provider: "anthropic" | "openai" | "ollama";
  apiKeyEnvVar: string;
  model: string;
  trigger: "on_test_run" | "on_demand" | "on_completion";
  features: {
    codeQuality: boolean;
    errorPatterns: boolean;
    learningProgress: boolean;
    hints: boolean;
  };
}

interface TestRunEvent {
  type: string;
  timestamp: string;
  sessionId: string;
  challenge: string;
  testFile: string;
  results: Array<{
    name: string;
    status: string;
    duration: number;
    error?: string;
  }>;
  summary: {
    total: number;
    passed: number;
    failed: number;
  };
}

interface AIEvaluation {
  codeQuality?: {
    score: number;
    strengths: string[];
    improvements: string[];
    details: string;
  };
  errorPatterns?: {
    identified: string[];
    misconceptions: string[];
    rootCause: string;
  };
  learningProgress?: {
    conceptsMastered: string[];
    conceptsStruggling: string[];
    recommendedReview: string[];
  };
  hints?: Array<{
    testName: string;
    hint: string;
    severity: "gentle" | "moderate" | "direct";
  }>;
}

const TELEMETRY_DIR = ".telemetry";
const AI_EVALUATIONS_FILE = "ai-evaluations.jsonl";
const CONFIG_FILE = "telemetry.config.json";

function getConfig(): { aiEvaluation?: AIEvaluationConfig } {
  const configPath = join(process.cwd(), CONFIG_FILE);
  if (existsSync(configPath)) {
    try {
      return JSON.parse(readFileSync(configPath, "utf-8"));
    } catch {
      return {};
    }
  }
  return {};
}

function getSourceCode(challenge: string): string {
  // Try common patterns to find source file
  const patterns = [
    `src/${challenge}/${challenge}.tsx`,
    `src/${challenge}/${challenge}.ts`,
    `src/${challenge}.tsx`,
    `src/${challenge}.ts`,
    `src/${challenge.toLowerCase()}.ts`,
  ];

  for (const pattern of patterns) {
    const filePath = join(process.cwd(), pattern);
    if (existsSync(filePath)) {
      return readFileSync(filePath, "utf-8");
    }
  }
  return "";
}

function buildPrompt(
  testRun: TestRunEvent,
  sourceCode: string,
  features: AIEvaluationConfig["features"]
): string {
  const failedTests = testRun.results.filter((r) => r.status === "failed");

  let prompt = `You are an expert coding instructor analyzing a student's work on a coding challenge.

## Challenge: ${testRun.challenge}

## Student's Code:
\`\`\`
${sourceCode}
\`\`\`

## Test Results:
- Total: ${testRun.summary.total}
- Passed: ${testRun.summary.passed}
- Failed: ${testRun.summary.failed}

## Failed Tests:
${failedTests.map((t) => `- ${t.name}: ${t.error || "No error message"}`).join("\n")}

Analyze this submission and provide feedback in JSON format with the following structure:
{`;

  if (features.codeQuality) {
    prompt += `
  "codeQuality": {
    "score": <1-10>,
    "strengths": ["<strength1>", "<strength2>"],
    "improvements": ["<improvement1>", "<improvement2>"],
    "details": "<brief paragraph>"
  },`;
  }

  if (features.errorPatterns) {
    prompt += `
  "errorPatterns": {
    "identified": ["<pattern1>", "<pattern2>"],
    "misconceptions": ["<misconception1>"],
    "rootCause": "<explanation of the main issue>"
  },`;
  }

  if (features.learningProgress) {
    prompt += `
  "learningProgress": {
    "conceptsMastered": ["<concept1>", "<concept2>"],
    "conceptsStruggling": ["<concept1>"],
    "recommendedReview": ["<topic1>", "<topic2>"]
  },`;
  }

  if (features.hints) {
    prompt += `
  "hints": [
    {
      "testName": "<name of failing test>",
      "hint": "<helpful hint that guides without giving the answer>",
      "severity": "gentle|moderate|direct"
    }
  ],`;
  }

  prompt += `
}

Guidelines:
- Be encouraging but honest
- Hints should guide thinking, not provide solutions
- Focus on the most important issues first
- Use terminology appropriate for a learning environment
- Identify patterns that suggest conceptual misunderstandings`;

  return prompt;
}

async function callAnthropic(
  prompt: string,
  model: string,
  apiKey: string
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: 1024,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  const data = await response.json();
  return {
    content: data.content?.[0]?.text || "{}",
    inputTokens: data.usage?.input_tokens || 0,
    outputTokens: data.usage?.output_tokens || 0,
  };
}

async function callOpenAI(
  prompt: string,
  model: string,
  apiKey: string
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [{ role: "user", content: prompt }],
      max_tokens: 1024,
    }),
  });

  const data = await response.json();
  return {
    content: data.choices?.[0]?.message?.content || "{}",
    inputTokens: data.usage?.prompt_tokens || 0,
    outputTokens: data.usage?.completion_tokens || 0,
  };
}

async function callOllama(
  prompt: string,
  model: string
): Promise<{ content: string; inputTokens: number; outputTokens: number }> {
  const response = await fetch("http://localhost:11434/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      prompt,
      stream: false,
    }),
  });

  const data = await response.json();
  return {
    content: data.response || "{}",
    inputTokens: 0, // Ollama doesn't report token counts
    outputTokens: 0,
  };
}

export async function evaluateTestRun(testRun: TestRunEvent): Promise<void> {
  const config = getConfig();
  const aiConfig = config.aiEvaluation;

  if (!aiConfig?.enabled) return;

  // Check trigger condition
  if (aiConfig.trigger === "on_completion" && testRun.summary.failed > 0) {
    return; // Only evaluate when all tests pass
  }

  const sourceCode = getSourceCode(testRun.challenge);
  if (!sourceCode) {
    console.warn(`[AI Eval] Could not find source code for ${testRun.challenge}`);
    return;
  }

  const prompt = buildPrompt(testRun, sourceCode, aiConfig.features);

  let result: { content: string; inputTokens: number; outputTokens: number };
  const apiKey = process.env[aiConfig.apiKeyEnvVar] || "";

  try {
    switch (aiConfig.provider) {
      case "anthropic":
        result = await callAnthropic(prompt, aiConfig.model, apiKey);
        break;
      case "openai":
        result = await callOpenAI(prompt, aiConfig.model, apiKey);
        break;
      case "ollama":
        result = await callOllama(prompt, aiConfig.model);
        break;
      default:
        return;
    }

    // Parse the AI response
    let evaluation: AIEvaluation;
    try {
      // Extract JSON from response (handle markdown code blocks)
      const jsonMatch = result.content.match(/\{[\s\S]*\}/);
      evaluation = jsonMatch ? JSON.parse(jsonMatch[0]) : {};
    } catch {
      evaluation = { hints: [{ testName: "parse_error", hint: result.content, severity: "gentle" }] };
    }

    // Write evaluation to telemetry
    const telemetryDir = join(process.cwd(), TELEMETRY_DIR);
    if (!existsSync(telemetryDir)) {
      mkdirSync(telemetryDir, { recursive: true });
    }

    const event = {
      type: "ai_evaluation",
      timestamp: new Date().toISOString(),
      sessionId: testRun.sessionId,
      challenge: testRun.challenge,
      testRunId: `${testRun.sessionId}-${Date.now()}`,
      provider: aiConfig.provider,
      model: aiConfig.model,
      trigger: aiConfig.trigger,
      evaluation,
      tokensUsed: {
        input: result.inputTokens,
        output: result.outputTokens,
      },
    };

    appendFileSync(
      join(telemetryDir, AI_EVALUATIONS_FILE),
      JSON.stringify(event) + "\n"
    );

    // Print hints to console for immediate feedback
    if (evaluation.hints && evaluation.hints.length > 0) {
      console.log("\n💡 AI Hints:");
      for (const hint of evaluation.hints) {
        console.log(`   [${hint.testName}] ${hint.hint}`);
      }
      console.log("");
    }
  } catch (error) {
    console.warn(`[AI Eval] Evaluation failed: ${error}`);
  }
}

// On-demand evaluation command
export async function runOnDemandEvaluation(): Promise<void> {
  const config = getConfig();
  if (!config.aiEvaluation?.enabled) {
    console.log("AI evaluation is not enabled in telemetry.config.json");
    return;
  }

  // Read the most recent test run
  const testRunsPath = join(process.cwd(), TELEMETRY_DIR, "test-runs.jsonl");
  if (!existsSync(testRunsPath)) {
    console.log("No test runs found. Run tests first.");
    return;
  }

  const lines = readFileSync(testRunsPath, "utf-8").trim().split("\n");
  const lastRun = JSON.parse(lines[lines.length - 1]) as TestRunEvent;

  // Force evaluation regardless of trigger setting
  const originalTrigger = config.aiEvaluation.trigger;
  config.aiEvaluation.trigger = "on_test_run";

  await evaluateTestRun(lastRun);

  config.aiEvaluation.trigger = originalTrigger;
}
```

#### Integration with Vitest Reporter

Update `src/telemetry/vitest-reporter.ts` to call the AI evaluator:

```typescript
import type { Reporter, File, Task } from "vitest";
import { logTestRun, TestResult } from "./telemetry";
import { evaluateTestRun } from "./ai-evaluator";

// ... existing code ...

export default class TelemetryReporter implements Reporter {
  async onFinished(files?: File[]) {
    if (!files) return;

    for (const file of files) {
      const results = collectResults(file.tasks);
      const passed = results.filter((r) => r.status === "passed").length;
      const failed = results.filter((r) => r.status === "failed").length;
      const totalDuration = results.reduce((sum, r) => sum + r.duration, 0);

      const testRunEvent = {
        challenge: extractChallengeName(file.filepath),
        testFile: file.filepath,
        results,
        summary: {
          total: results.length,
          passed,
          failed,
          duration: totalDuration,
        },
      };

      // Log raw telemetry
      logTestRun(testRunEvent);

      // Run AI evaluation (async, non-blocking)
      evaluateTestRun({
        type: "test_run",
        timestamp: new Date().toISOString(),
        sessionId: getSessionId(),
        ...testRunEvent,
      }).catch(() => {
        // Silently fail - don't block test output
      });
    }
  }
}
```

#### CLI Command for On-Demand Evaluation

Generate `scripts/ai-evaluate.js`:

```javascript
#!/usr/bin/env node
/**
 * Run AI evaluation on demand.
 *
 * Usage: node scripts/ai-evaluate.js
 */

import { runOnDemandEvaluation } from "../src/telemetry/ai-evaluator.js";

runOnDemandEvaluation()
  .then(() => console.log("Evaluation complete."))
  .catch((err) => console.error("Evaluation failed:", err));
```

Add to `package.json`:

```json
{
  "scripts": {
    "evaluate": "node scripts/ai-evaluate.js"
  }
}
```

### Python Implementation

Generate `src/telemetry/ai_evaluator.py`:

```python
"""AI Evaluation Layer for student code analysis."""

import json
import os
from pathlib import Path
from typing import Optional
import urllib.request

TELEMETRY_DIR = ".telemetry"
AI_EVALUATIONS_FILE = "ai-evaluations.jsonl"
CONFIG_FILE = "telemetry.config.json"


def get_config() -> dict:
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}


def get_source_code(challenge: str) -> Optional[str]:
    patterns = [
        f"src/{challenge}.py",
        f"src/{challenge.lower()}.py",
        f"src/{challenge}/{challenge}.py",
    ]
    for pattern in patterns:
        path = Path(pattern)
        if path.exists():
            return path.read_text()
    return None


def build_prompt(test_run: dict, source_code: str, features: dict) -> str:
    failed_tests = [r for r in test_run["results"] if r["status"] == "failed"]

    prompt = f"""You are an expert coding instructor analyzing a student's work.

## Challenge: {test_run["challenge"]}

## Student's Code:
```python
{source_code}
```

## Test Results:
- Total: {test_run["summary"]["total"]}
- Passed: {test_run["summary"]["passed"]}
- Failed: {test_run["summary"]["failed"]}

## Failed Tests:
"""
    for t in failed_tests:
        prompt += f"- {t['name']}: {t.get('error', 'No error message')}\n"

    prompt += """
Analyze and provide feedback in JSON format:
{
  "codeQuality": {"score": 1-10, "strengths": [], "improvements": [], "details": ""},
  "errorPatterns": {"identified": [], "misconceptions": [], "rootCause": ""},
  "learningProgress": {"conceptsMastered": [], "conceptsStruggling": [], "recommendedReview": []},
  "hints": [{"testName": "", "hint": "", "severity": "gentle|moderate|direct"}]
}

Be encouraging but honest. Hints should guide without giving solutions."""

    return prompt


def call_anthropic(prompt: str, model: str, api_key: str) -> dict:
    data = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        return {
            "content": result.get("content", [{}])[0].get("text", "{}"),
            "input_tokens": result.get("usage", {}).get("input_tokens", 0),
            "output_tokens": result.get("usage", {}).get("output_tokens", 0)
        }


def call_openai(prompt: str, model: str, api_key: str) -> dict:
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        return {
            "content": result.get("choices", [{}])[0].get("message", {}).get("content", "{}"),
            "input_tokens": result.get("usage", {}).get("prompt_tokens", 0),
            "output_tokens": result.get("usage", {}).get("completion_tokens", 0)
        }


def evaluate_test_run(test_run: dict) -> None:
    config = get_config()
    ai_config = config.get("aiEvaluation", {})

    if not ai_config.get("enabled"):
        return

    if ai_config.get("trigger") == "on_completion" and test_run["summary"]["failed"] > 0:
        return

    source_code = get_source_code(test_run["challenge"])
    if not source_code:
        print(f"[AI Eval] Could not find source for {test_run['challenge']}")
        return

    prompt = build_prompt(test_run, source_code, ai_config.get("features", {}))
    api_key = os.environ.get(ai_config.get("apiKeyEnvVar", ""), "")

    try:
        provider = ai_config.get("provider", "anthropic")
        model = ai_config.get("model", "claude-sonnet-4-20250514")

        if provider == "anthropic":
            result = call_anthropic(prompt, model, api_key)
        elif provider == "openai":
            result = call_openai(prompt, model, api_key)
        else:
            return

        # Parse response
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', result["content"])
            evaluation = json.loads(json_match.group()) if json_match else {}
        except Exception:
            evaluation = {"hints": [{"testName": "parse_error", "hint": result["content"], "severity": "gentle"}]}

        # Write to telemetry
        telemetry_dir = Path(TELEMETRY_DIR)
        telemetry_dir.mkdir(exist_ok=True)

        event = {
            "type": "ai_evaluation",
            "timestamp": test_run.get("timestamp"),
            "sessionId": test_run.get("sessionId"),
            "challenge": test_run["challenge"],
            "provider": provider,
            "model": model,
            "trigger": ai_config.get("trigger"),
            "evaluation": evaluation,
            "tokensUsed": {
                "input": result["input_tokens"],
                "output": result["output_tokens"]
            }
        }

        with open(telemetry_dir / AI_EVALUATIONS_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Print hints
        hints = evaluation.get("hints", [])
        if hints:
            print("\n💡 AI Hints:")
            for hint in hints:
                print(f"   [{hint['testName']}] {hint['hint']}")
            print()

    except Exception as e:
        print(f"[AI Eval] Evaluation failed: {e}")
```

Update `src/telemetry/conftest.py` to integrate:

```python
# Add at the end of pytest_sessionfinish
from .ai_evaluator import evaluate_test_run

# In TelemetryPlugin.pytest_sessionfinish, after log_test_run():
try:
    evaluate_test_run({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sessionId": get_session_id(),
        "challenge": challenge,
        "testFile": test_file,
        "results": self.results,
        "summary": {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "duration": total_duration,
        }
    })
except Exception:
    pass  # Don't block test output
```

### Usage

```bash
# Automatic (if trigger is "on_test_run")
npm test

# On-demand
npm run evaluate

# Python
python -c "from src.telemetry.ai_evaluator import evaluate_test_run; ..."
```

### Dashboard Integration

The progress dashboard should display AI evaluation results. Add this section to `progress.html`:

```html
<div class="card">
  <h2>AI Insights</h2>
  <div id="ai-insights">
    <div class="no-data">No AI evaluations yet.</div>
  </div>
</div>
```

```javascript
// Add to loadData()
async function loadAIEvaluations() {
  try {
    const response = await fetch('.telemetry/ai-evaluations.jsonl');
    if (!response.ok) return;

    const text = await response.text();
    const events = text.trim().split('\n').filter(Boolean).map(JSON.parse);

    const container = document.getElementById('ai-insights');
    if (!events.length) return;

    const latest = events[events.length - 1];
    const eval_ = latest.evaluation;

    let html = '';

    if (eval_.codeQuality) {
      html += `<div class="insight">
        <strong>Code Quality:</strong> ${eval_.codeQuality.score}/10
        <p>${eval_.codeQuality.details}</p>
      </div>`;
    }

    if (eval_.hints && eval_.hints.length) {
      html += `<div class="insight"><strong>Hints:</strong><ul>`;
      for (const hint of eval_.hints) {
        html += `<li><em>${hint.testName}:</em> ${hint.hint}</li>`;
      }
      html += `</ul></div>`;
    }

    if (eval_.learningProgress) {
      const struggling = eval_.learningProgress.conceptsStruggling;
      if (struggling.length) {
        html += `<div class="insight"><strong>Focus Areas:</strong> ${struggling.join(', ')}</div>`;
      }
    }

    container.innerHTML = html || '<div class="no-data">No insights available.</div>';
  } catch (e) {
    // Silently fail
  }
}
```

---

## 3. Git Commit Analysis

Generate `scripts/analyze-git-progress.sh`:

```bash
#!/usr/bin/env bash
# Analyzes git commit history to understand student learning patterns
#
# Usage: bash scripts/analyze-git-progress.sh [--json]

set -euo pipefail

JSON_OUTPUT=false
if [[ "${1:-}" == "--json" ]]; then
    JSON_OUTPUT=true
fi

TELEMETRY_DIR=".telemetry"
OUTPUT_FILE="$TELEMETRY_DIR/git-analysis.json"

mkdir -p "$TELEMETRY_DIR"

# Check if we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get all commits with stats
analyze_commits() {
    local commits=()

    while IFS= read -r line; do
        if [[ $line =~ ^commit\ ([a-f0-9]+) ]]; then
            current_hash="${BASH_REMATCH[1]}"
        elif [[ $line =~ ^Date:\ +(.+) ]]; then
            current_date="$1"
        elif [[ $line =~ ^\ +(.+) ]] && [[ -n "${current_hash:-}" ]]; then
            current_message="${BASH_REMATCH[1]}"
        fi
    done < <(git log --format="commit %H%nDate: %aI%n    %s" --stat)
}

# Calculate time between commits
calculate_intervals() {
    git log --format="%aI" | while read -r timestamp; do
        echo "$timestamp"
    done
}

# Get files changed per commit
get_challenge_progress() {
    git log --name-only --format="COMMIT:%H|%aI|%s" | awk '
    BEGIN { FS="|" }
    /^COMMIT:/ {
        if (commit != "") {
            print commit "|" timestamp "|" message "|" files
        }
        split($0, parts, "|")
        commit = substr(parts[1], 8)
        timestamp = parts[2]
        message = parts[3]
        files = ""
    }
    /^src\// {
        if (files != "") files = files ","
        files = files $0
    }
    END {
        if (commit != "") {
            print commit "|" timestamp "|" message "|" files
        }
    }
    '
}

# Generate analysis
generate_analysis() {
    local total_commits=$(git rev-list --count HEAD 2>/dev/null || echo 0)
    local first_commit=$(git log --reverse --format="%aI" | head -1)
    local last_commit=$(git log --format="%aI" | head -1)

    # Get unique files modified
    local src_files=$(git log --name-only --format="" | grep "^src/" | sort -u | wc -l | tr -d ' ')

    # Get commit frequency by hour
    local commits_by_hour=$(git log --format="%aI" | cut -dT -f2 | cut -d: -f1 | sort | uniq -c | sort -rn)

    cat << EOF
{
  "type": "git_analysis",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "summary": {
    "totalCommits": $total_commits,
    "firstCommit": "$first_commit",
    "lastCommit": "$last_commit",
    "uniqueSourceFiles": $src_files
  },
  "commits": [
EOF

    local first=true
    get_challenge_progress | while IFS="|" read -r hash timestamp message files; do
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi

        # Escape message for JSON
        message=$(echo "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')

        printf '    {"hash": "%s", "timestamp": "%s", "message": "%s", "files": [%s]}' \
            "$hash" "$timestamp" "$message" \
            "$(echo "$files" | sed 's/,/", "/g; s/^/"/; s/$/"/' | sed 's/^""$//')"
    done

    cat << EOF

  ]
}
EOF
}

if $JSON_OUTPUT; then
    generate_analysis
else
    echo ""
    echo "📊 Git Learning Progress Analysis"
    echo "══════════════════════════════════════"
    echo ""

    total=$(git rev-list --count HEAD 2>/dev/null || echo 0)
    echo "Total commits: $total"

    if [ "$total" -gt 0 ]; then
        echo ""
        echo "Recent activity:"
        git log --oneline -10 | sed 's/^/  /'

        echo ""
        echo "Files most frequently modified:"
        git log --name-only --format="" | grep "^src/" | sort | uniq -c | sort -rn | head -5 | sed 's/^/  /'
    fi

    echo ""
fi

# Save JSON analysis
generate_analysis > "$OUTPUT_FILE"
echo "Analysis saved to $OUTPUT_FILE"
```

---

## 3. AI Interaction Logging

Generate `.claude/hooks/telemetry-hook.js`:

```javascript
#!/usr/bin/env node
/**
 * Claude Code hook for logging AI interactions.
 *
 * Install by adding to .claude/settings.json:
 * {
 *   "hooks": {
 *     "post_tool_use": [".claude/hooks/telemetry-hook.js"]
 *   }
 * }
 */

const fs = require("fs");
const path = require("path");

const TELEMETRY_DIR = ".telemetry";
const AI_INTERACTIONS_FILE = "ai-interactions.jsonl";
const CONFIG_FILE = "telemetry.config.json";

function getConfig() {
  const configPath = path.join(process.cwd(), CONFIG_FILE);
  if (fs.existsSync(configPath)) {
    try {
      return JSON.parse(fs.readFileSync(configPath, "utf-8"));
    } catch {
      return { enabled: true, trackAIInteractions: true };
    }
  }
  return { enabled: true, trackAIInteractions: true };
}

function getSessionId() {
  const sessionFile = path.join(TELEMETRY_DIR, ".session");
  if (fs.existsSync(sessionFile)) {
    return fs.readFileSync(sessionFile, "utf-8").trim();
  }
  const newSessionId = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  fs.mkdirSync(TELEMETRY_DIR, { recursive: true });
  fs.writeFileSync(sessionFile, newSessionId);
  return newSessionId;
}

function logInteraction(event) {
  const config = getConfig();
  if (!config.enabled || !config.trackAIInteractions) return;

  fs.mkdirSync(TELEMETRY_DIR, { recursive: true });

  const fullEvent = {
    type: "ai_interaction",
    timestamp: new Date().toISOString(),
    sessionId: getSessionId(),
    ...event,
  };

  const filePath = path.join(TELEMETRY_DIR, AI_INTERACTIONS_FILE);
  fs.appendFileSync(filePath, JSON.stringify(fullEvent) + "\n");
}

// Parse hook input from stdin
let input = "";
process.stdin.on("data", (chunk) => {
  input += chunk;
});

process.stdin.on("end", () => {
  try {
    const hookData = JSON.parse(input);

    // Extract relevant information
    const event = {
      tool: hookData.tool_name || "unknown",
      action: hookData.action || "unknown",
      file: hookData.file_path || null,
      challenge: extractChallenge(hookData.file_path),
    };

    // Categorize the interaction type
    if (hookData.tool_name === "Read") {
      event.category = "exploration";
    } else if (hookData.tool_name === "Edit" || hookData.tool_name === "Write") {
      event.category = "implementation";
    } else if (hookData.tool_name === "Bash" && hookData.command?.includes("test")) {
      event.category = "testing";
    } else {
      event.category = "other";
    }

    logInteraction(event);
  } catch (e) {
    // Silently fail - don't interrupt Claude Code
  }
});

function extractChallenge(filePath) {
  if (!filePath) return null;
  const match = filePath.match(/src\/([^/]+)/);
  return match ? match[1] : null;
}
```

---

## 4. Progress Dashboard

Generate `progress.html` at project root:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Challenge Progress Dashboard</title>
  <style>
    :root {
      --bg: #1a1a2e;
      --card-bg: #16213e;
      --text: #eee;
      --text-muted: #888;
      --green: #4ade80;
      --red: #f87171;
      --yellow: #fbbf24;
      --blue: #60a5fa;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 2rem;
      min-height: 100vh;
    }

    h1 {
      margin-bottom: 2rem;
      font-weight: 600;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .card {
      background: var(--card-bg);
      border-radius: 12px;
      padding: 1.5rem;
    }

    .card h2 {
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }

    .stat {
      font-size: 2.5rem;
      font-weight: 700;
    }

    .stat.green { color: var(--green); }
    .stat.red { color: var(--red); }
    .stat.yellow { color: var(--yellow); }
    .stat.blue { color: var(--blue); }

    .challenge-list {
      list-style: none;
    }

    .challenge-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 0;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    .challenge-item:last-child {
      border-bottom: none;
    }

    .status-icon {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    }

    .status-icon.passed { background: var(--green); color: #000; }
    .status-icon.failed { background: var(--red); color: #000; }
    .status-icon.pending { background: var(--text-muted); color: #000; }

    .challenge-name { flex: 1; }

    .challenge-stats {
      font-size: 0.875rem;
      color: var(--text-muted);
    }

    .timeline {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .timeline-item {
      display: flex;
      gap: 1rem;
      font-size: 0.875rem;
    }

    .timeline-time {
      color: var(--text-muted);
      min-width: 80px;
    }

    .no-data {
      color: var(--text-muted);
      font-style: italic;
      text-align: center;
      padding: 2rem;
    }

    .refresh-btn {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: var(--blue);
      color: #000;
      border: none;
      padding: 1rem 1.5rem;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
    }

    .refresh-btn:hover {
      opacity: 0.9;
    }
  </style>
</head>
<body>
  <h1>📊 Challenge Progress Dashboard</h1>

  <div class="grid">
    <div class="card">
      <h2>Tests Passed</h2>
      <div class="stat green" id="tests-passed">-</div>
    </div>
    <div class="card">
      <h2>Tests Failed</h2>
      <div class="stat red" id="tests-failed">-</div>
    </div>
    <div class="card">
      <h2>Total Attempts</h2>
      <div class="stat blue" id="total-attempts">-</div>
    </div>
    <div class="card">
      <h2>Time Active</h2>
      <div class="stat yellow" id="time-active">-</div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Challenges</h2>
      <ul class="challenge-list" id="challenge-list">
        <li class="no-data">No telemetry data yet. Run some tests!</li>
      </ul>
    </div>

    <div class="card">
      <h2>Recent Activity</h2>
      <div class="timeline" id="timeline">
        <div class="no-data">No activity recorded yet.</div>
      </div>
    </div>
  </div>

  <button class="refresh-btn" onclick="loadData()">↻ Refresh</button>

  <script>
    async function loadData() {
      try {
        // In a real setup, this would fetch from a local server
        // For now, we'll show instructions
        const testRunsPath = '.telemetry/test-runs.jsonl';

        // Try to load via fetch (works if served via local server)
        const response = await fetch(testRunsPath);
        if (!response.ok) throw new Error('File not found');

        const text = await response.text();
        const events = text.trim().split('\n').filter(Boolean).map(JSON.parse);

        processEvents(events);
      } catch (e) {
        console.log('Could not load telemetry data:', e.message);
        console.log('To view the dashboard, run: npx serve . (or python -m http.server)');
      }
    }

    function processEvents(events) {
      if (!events.length) return;

      // Calculate stats
      const challenges = new Map();
      let totalPassed = 0;
      let totalFailed = 0;
      let totalAttempts = events.length;

      let firstTimestamp = null;
      let lastTimestamp = null;

      for (const event of events) {
        if (!firstTimestamp) firstTimestamp = new Date(event.timestamp);
        lastTimestamp = new Date(event.timestamp);

        totalPassed += event.summary.passed;
        totalFailed += event.summary.failed;

        const challenge = event.challenge;
        if (!challenges.has(challenge)) {
          challenges.set(challenge, { attempts: 0, lastStatus: 'pending', passed: 0, failed: 0 });
        }
        const c = challenges.get(challenge);
        c.attempts++;
        c.passed = Math.max(c.passed, event.summary.passed);
        c.failed = event.summary.failed;
        c.lastStatus = event.summary.failed === 0 ? 'passed' : 'failed';
      }

      // Update UI
      document.getElementById('tests-passed').textContent = totalPassed;
      document.getElementById('tests-failed').textContent = totalFailed;
      document.getElementById('total-attempts').textContent = totalAttempts;

      if (firstTimestamp && lastTimestamp) {
        const minutes = Math.round((lastTimestamp - firstTimestamp) / 60000);
        document.getElementById('time-active').textContent =
          minutes < 60 ? `${minutes}m` : `${Math.floor(minutes/60)}h ${minutes%60}m`;
      }

      // Update challenge list
      const list = document.getElementById('challenge-list');
      list.innerHTML = '';
      for (const [name, data] of challenges) {
        const li = document.createElement('li');
        li.className = 'challenge-item';
        li.innerHTML = `
          <span class="status-icon ${data.lastStatus}">${data.lastStatus === 'passed' ? '✓' : '✗'}</span>
          <span class="challenge-name">${name}</span>
          <span class="challenge-stats">${data.attempts} attempts</span>
        `;
        list.appendChild(li);
      }

      // Update timeline
      const timeline = document.getElementById('timeline');
      timeline.innerHTML = '';
      const recentEvents = events.slice(-10).reverse();
      for (const event of recentEvents) {
        const time = new Date(event.timestamp).toLocaleTimeString();
        const div = document.createElement('div');
        div.className = 'timeline-item';
        div.innerHTML = `
          <span class="timeline-time">${time}</span>
          <span>${event.challenge}: ${event.summary.passed}/${event.summary.total} passed</span>
        `;
        timeline.appendChild(div);
      }
    }

    // Load on page load
    loadData();

    // Auto-refresh every 5 seconds
    setInterval(loadData, 5000);
  </script>
</body>
</html>
```

---

## 5. Pre/Post Assessment

Generate assessment files alongside challenges.

### `assessment/pre-assessment.md` template:

```markdown
# Pre-Challenge Assessment

Complete this before starting the challenges. Be honest — this helps track your learning!

## Self-Rated Confidence

Rate your confidence (1-5) for each concept:

| Concept | Confidence (1-5) | Notes |
|---------|------------------|-------|
| [Concept 1 from README] | | |
| [Concept 2 from README] | | |
| [Concept 3 from README] | | |

**1** = Never heard of it
**2** = Heard of it, don't understand
**3** = Understand basics
**4** = Can apply with some effort
**5** = Can teach it to others

## Quick Knowledge Check

1. [Question about core concept]
   - [ ] Option A
   - [ ] Option B
   - [ ] Option C
   - [ ] Option D

2. [Question about syntax/mechanics]
   - [ ] Option A
   - [ ] Option B
   - [ ] Option C
   - [ ] Option D

---

Save this file when done, then start the challenges!
```

### `assessment/post-assessment.md` template:

```markdown
# Post-Challenge Reflection

Complete this after finishing all challenges.

## Self-Rated Confidence (After)

Rate your confidence now (1-5):

| Concept | Before | After | Change |
|---------|--------|-------|--------|
| [Concept 1] | | | |
| [Concept 2] | | | |
| [Concept 3] | | | |

## Reflection Questions

### What was the hardest part?

[Your answer]

### What would you do differently next time?

[Your answer]

### How much did you use AI assistance?

- [ ] Not at all
- [ ] A little (1-2 questions)
- [ ] Moderate (3-5 questions)
- [ ] Heavy (6+ questions)
- [ ] AI wrote most of the code

### What concepts are still unclear?

[Your answer]

---

Save this file when done!
```

### Assessment Parser (generate `scripts/parse-assessments.js`):

```javascript
#!/usr/bin/env node
/**
 * Parses pre and post assessment markdown files and generates telemetry events.
 *
 * Usage: node scripts/parse-assessments.js
 */

const fs = require("fs");
const path = require("path");

const TELEMETRY_DIR = ".telemetry";
const ASSESSMENTS_FILE = "assessments.jsonl";

function parseMarkdownTable(content) {
  const lines = content.split("\n");
  const tableLines = lines.filter(line => line.includes("|") && !line.match(/^\|[-\s|]+\|$/));

  const results = [];
  for (let i = 1; i < tableLines.length; i++) {
    const cells = tableLines[i].split("|").map(c => c.trim()).filter(Boolean);
    if (cells.length >= 2) {
      results.push({
        concept: cells[0],
        rating: parseInt(cells[1]) || null,
      });
    }
  }
  return results;
}

function parseAssessment(filePath, type) {
  if (!fs.existsSync(filePath)) return null;

  const content = fs.readFileSync(filePath, "utf-8");
  const ratings = parseMarkdownTable(content);

  // Extract checkbox answers
  const checkboxes = content.match(/- \[x\] .+/gi) || [];
  const answers = checkboxes.map(c => c.replace(/- \[x\] /i, ""));

  return {
    type: `assessment_${type}`,
    timestamp: new Date().toISOString(),
    ratings,
    answers,
    aiUsage: content.match(/- \[x\] (Not at all|A little|Moderate|Heavy|AI wrote)/i)?.[1] || null,
  };
}

function main() {
  const preAssessment = parseAssessment("assessment/pre-assessment.md", "pre");
  const postAssessment = parseAssessment("assessment/post-assessment.md", "post");

  fs.mkdirSync(TELEMETRY_DIR, { recursive: true });
  const filePath = path.join(TELEMETRY_DIR, ASSESSMENTS_FILE);

  if (preAssessment) {
    fs.appendFileSync(filePath, JSON.stringify(preAssessment) + "\n");
    console.log("✓ Pre-assessment recorded");
  }

  if (postAssessment) {
    fs.appendFileSync(filePath, JSON.stringify(postAssessment) + "\n");
    console.log("✓ Post-assessment recorded");

    // Calculate learning delta
    if (preAssessment) {
      console.log("\n📊 Learning Progress:");
      for (let i = 0; i < preAssessment.ratings.length; i++) {
        const pre = preAssessment.ratings[i];
        const post = postAssessment.ratings[i];
        if (pre && post && pre.rating && post.rating) {
          const delta = post.rating - pre.rating;
          const arrow = delta > 0 ? "↑" : delta < 0 ? "↓" : "→";
          console.log(`  ${pre.concept}: ${pre.rating} → ${post.rating} (${arrow}${Math.abs(delta)})`);
        }
      }
    }
  }

  if (!preAssessment && !postAssessment) {
    console.log("No assessment files found in assessment/ directory");
  }
}

main();
```

---

## Integration with SKILL.md

Add these steps to the skill:

### Step 5.5: Generate Telemetry Infrastructure

After generating test files:

1. **Create telemetry config**: Generate `telemetry.config.json` with defaults
2. **Add telemetry module**: Generate appropriate telemetry code for the detected language
3. **Update test config**: Add telemetry reporter to test configuration
4. **Add progress dashboard**: Generate `progress.html`
5. **Add assessment templates**: Generate `assessment/pre-assessment.md` and `assessment/post-assessment.md`
6. **Add analysis scripts**: Generate `scripts/analyze-git-progress.sh`

### Updated Report (Step 6)

Include in the final summary:

```
📊 Telemetry Enabled
────────────────────
Telemetry is ON by default. Data is stored locally in .telemetry/

To disable: set "enabled": false in telemetry.config.json
To view progress: open progress.html in browser (via local server)
To analyze git history: bash scripts/analyze-git-progress.sh

Before starting:
1. Fill out assessment/pre-assessment.md

After finishing:
1. Fill out assessment/post-assessment.md
2. Run: node scripts/parse-assessments.js
```
