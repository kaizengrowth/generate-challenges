"""
Telemetry boilerplate — injected into every generated challenge repo.

Returns {path: content} dicts of ready-to-use telemetry infrastructure files,
keyed by the repo's ecosystem.  These are merged into the repo's file dict
after the LLM-generated creative files and standard boilerplate, ensuring
every student challenge ships with learning telemetry out of the box.

Supported ecosystems
--------------------
typescript / react / vue   — Vitest reporter + TypeScript telemetry module
angular                    — same as react (jsdom + Vitest)
python                     — pytest conftest plugin + Python telemetry module
java / cpp / cobol         — config file only (full instrumentation is complex)

Configuration
-------------
Pass remote_endpoint=None for local-only mode (.telemetry/ writes only).
Pass remote_endpoint="http://..." to pre-configure server sync in every repo.
The student can override both in telemetry.config.json after cloning.
"""

import json


# ── Shared: telemetry.config.json ────────────────────────────────────────────

def _telemetry_config(remote_endpoint: str | None) -> str:
    cfg = {
        "enabled": True,
        "studentId": None,
        "cohortId": None,
        "remoteEndpoint": remote_endpoint,
        "trackTestRuns": True,
        "trackGitCommits": True,
        "trackAIInteractions": True,
        "trackAssessments": True,
    }
    return json.dumps(cfg, indent=2)


# ── TypeScript/JavaScript: telemetry module ───────────────────────────────────

_TS_TELEMETRY_TS = """\
import { appendFileSync, existsSync, mkdirSync, readFileSync } from "fs";
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
  studentId: string | null;
  cohortId: string | null;
  challenge: string;
  testFile: string;
  results: TestResult[];
  summary: { total: number; passed: number; failed: number; duration: number };
}

interface TelemetryConfig {
  enabled: boolean;
  studentId: string | null;
  cohortId: string | null;
  remoteEndpoint: string | null;
  trackTestRuns: boolean;
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
    try { return JSON.parse(readFileSync(configPath, "utf-8")); } catch {}
  }
  return { enabled: true, studentId: null, cohortId: null, remoteEndpoint: null, trackTestRuns: true };
}

function ensureTelemetryDir(): void {
  const dir = join(process.cwd(), TELEMETRY_DIR);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

export function logTestRun(
  event: Omit<TestRunEvent, "type" | "timestamp" | "sessionId" | "studentId" | "cohortId">
): void {
  const config = getConfig();
  if (!config.enabled || !config.trackTestRuns) return;
  ensureTelemetryDir();
  const fullEvent: TestRunEvent = {
    type: "test_run",
    timestamp: new Date().toISOString(),
    sessionId: getSessionId(),
    studentId: config.studentId,
    cohortId: config.cohortId,
    ...event,
  };
  appendFileSync(join(process.cwd(), TELEMETRY_DIR, TEST_RUNS_FILE), JSON.stringify(fullEvent) + "\\n");
  if (config.remoteEndpoint) {
    fetch(config.remoteEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fullEvent),
    }).catch(() => {});
  }
}

export type { TestResult, TestRunEvent, TelemetryConfig };
"""

_TS_VITEST_REPORTER_TS = """\
import type { Reporter, File, Task } from "vitest";
import { logTestRun } from "./telemetry";
import type { TestResult } from "./telemetry";

function extractChallengeName(filepath: string): string {
  const filename = filepath.split("/").pop() ?? filepath;
  return filename.replace(/\\.test\\.(ts|tsx|js|jsx)$/, "");
}

function collectResults(tasks: Task[]): TestResult[] {
  const results: TestResult[] = [];
  for (const task of tasks) {
    if (task.type === "test") {
      results.push({
        name: task.name,
        status: task.result?.state === "pass" ? "passed"
              : task.result?.state === "skip" ? "skipped" : "failed",
        duration: Math.round(task.result?.duration ?? 0),
        error: task.result?.errors?.[0]?.message,
      });
    } else if ("tasks" in task && task.tasks) {
      results.push(...collectResults(task.tasks));
    }
  }
  return results;
}

export default class TelemetryReporter implements Reporter {
  onFinished(files?: File[]) {
    if (!files) return;
    for (const file of files) {
      const results  = collectResults(file.tasks);
      const passed   = results.filter((r) => r.status === "passed").length;
      const failed   = results.filter((r) => r.status === "failed").length;
      const duration = results.reduce((sum, r) => sum + r.duration, 0);
      logTestRun({
        challenge: extractChallengeName(file.filepath),
        testFile:  file.filepath,
        results,
        summary: { total: results.length, passed, failed, duration },
      });
    }
  }
}
"""


# ── Vite configs: standard boilerplate + telemetry reporter ──────────────────

_TS_VITE_CONFIG_WITH_TELEMETRY = """\
import { defineConfig } from "vite";

export default defineConfig({
  test: {
    globals: true,
    reporters: ["default", "./src/telemetry/vitest-reporter.ts"],
  },
});"""

_REACT_VITE_CONFIG_WITH_TELEMETRY = """\
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
    reporters: ["default", "./src/telemetry/vitest-reporter.ts"],
  },
});"""

_VUE_VITE_CONFIG_WITH_TELEMETRY = """\
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    globals: true,
    reporters: ["default", "./src/telemetry/vitest-reporter.ts"],
  },
});"""


# ── Python: telemetry module + pytest plugin ──────────────────────────────────

_PYTHON_TELEMETRY_PY = """\
\"\"\"Telemetry module for tracking student learning progress.\"\"\"
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

TELEMETRY_DIR = Path(".telemetry")
CONFIG_FILE   = Path("telemetry.config.json")
TEST_RUNS_FILE = "test-runs.jsonl"

_session_id: Optional[str] = None


def get_session_id() -> str:
    global _session_id
    if _session_id is None:
        _session_id = f"{int(datetime.now(timezone.utc).timestamp() * 1000)}-{uuid.uuid4().hex[:7]}"
    return _session_id


def get_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {"enabled": True, "studentId": None, "cohortId": None,
            "remoteEndpoint": None, "trackTestRuns": True}


def log_test_run(challenge: str, test_file: str, results: list, summary: dict) -> None:
    config = get_config()
    if not config.get("enabled") or not config.get("trackTestRuns"):
        return

    TELEMETRY_DIR.mkdir(exist_ok=True)

    event = {
        "type":       "test_run",
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "sessionId":  get_session_id(),
        "studentId":  config.get("studentId"),
        "cohortId":   config.get("cohortId"),
        "challenge":  challenge,
        "testFile":   test_file,
        "results":    results,
        "summary":    summary,
    }

    with open(TELEMETRY_DIR / TEST_RUNS_FILE, "a") as f:
        f.write(json.dumps(event) + "\\n")

    if config.get("remoteEndpoint"):
        _sync_to_remote(config["remoteEndpoint"], event)


def _sync_to_remote(endpoint: str, event: dict) -> None:
    try:
        import urllib.request
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(event).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass
"""

_PYTHON_TELEMETRY_CONFTEST_PY = """\
\"\"\"Pytest plugin that records test results to .telemetry/test-runs.jsonl.\"\"\"
from pathlib import Path
import pytest
from src.telemetry.telemetry import log_test_run


class _TelemetryPlugin:
    def __init__(self):
        self.results   = []
        self.test_file = None

    def pytest_collection_modifyitems(self, items):
        if items:
            self.test_file = str(items[0].fspath)

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.results.append({
                "name":     report.nodeid.split("::")[-1],
                "status":   "passed" if report.passed else "failed" if report.failed else "skipped",
                "duration": int(report.duration * 1000),
                "error":    str(report.longrepr) if report.failed else None,
            })

    def pytest_sessionfinish(self, session, exitstatus):
        if not self.results:
            return
        test_file = self.test_file or "unknown"
        challenge = Path(test_file).stem.replace("test_", "")
        passed   = sum(1 for r in self.results if r["status"] == "passed")
        failed   = sum(1 for r in self.results if r["status"] == "failed")
        duration = sum(r["duration"] for r in self.results)
        log_test_run(
            challenge=challenge,
            test_file=test_file,
            results=self.results,
            summary={"total": len(self.results), "passed": passed,
                     "failed": failed, "duration": duration},
        )


def pytest_configure(config):
    config.pluginmanager.register(_TelemetryPlugin(), "telemetry_plugin")
"""


# ── Public API ────────────────────────────────────────────────────────────────

_JS_TELEMETRY_FILES = {
    "src/telemetry/telemetry.ts":          _TS_TELEMETRY_TS,
    "src/telemetry/vitest-reporter.ts":    _TS_VITEST_REPORTER_TS,
}

_VITE_CONFIGS = {
    "typescript": _TS_VITE_CONFIG_WITH_TELEMETRY,
    "react":      _REACT_VITE_CONFIG_WITH_TELEMETRY,
    "vue":        _VUE_VITE_CONFIG_WITH_TELEMETRY,
    "angular":    _REACT_VITE_CONFIG_WITH_TELEMETRY,  # angular also uses jsdom
}


def get_telemetry_boilerplate(
    ecosystem: str,
    remote_endpoint: str | None = None,
) -> dict[str, str]:
    """
    Return {path: content} of telemetry infrastructure files for this ecosystem.

    These are intended to be merged into a ChallengeRepo's files dict AFTER the
    standard boilerplate and LLM-generated files, so they take final precedence.
    The vite.config.ts override is safe: it adds only the reporter key to the
    existing test block.
    """
    files: dict[str, str] = {
        "telemetry.config.json": _telemetry_config(remote_endpoint),
    }

    if ecosystem in ("typescript", "react", "vue", "angular"):
        files.update(_JS_TELEMETRY_FILES)
        files["vite.config.ts"] = _VITE_CONFIGS[ecosystem]

    elif ecosystem == "python":
        files["src/telemetry/telemetry.py"]         = _PYTHON_TELEMETRY_PY
        files["src/telemetry/conftest.py"]          = _PYTHON_TELEMETRY_CONFTEST_PY

    # java / cpp / cobol: config only — full instrumentation is ecosystem-specific
    # and adds build complexity. Config ships so students can enable when ready.

    return files
