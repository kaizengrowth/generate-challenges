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
    try {
      return JSON.parse(readFileSync(configPath, "utf-8"));
    } catch {
      // fall through to defaults
    }
  }
  return { enabled: true, studentId: null, cohortId: null, remoteEndpoint: null, trackTestRuns: true };
}

function ensureTelemetryDir(): void {
  const dir = join(process.cwd(), TELEMETRY_DIR);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

export function logTestRun(event: Omit<TestRunEvent, "type" | "timestamp" | "sessionId" | "studentId" | "cohortId">): void {
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

  // Always write locally first
  const filePath = join(process.cwd(), TELEMETRY_DIR, TEST_RUNS_FILE);
  appendFileSync(filePath, JSON.stringify(fullEvent) + "\n");

  // Fire-and-forget POST to server if configured — never blocks or throws
  if (config.remoteEndpoint) {
    syncToRemote(config.remoteEndpoint, fullEvent).catch(() => {});
  }
}

async function syncToRemote(endpoint: string, event: TestRunEvent): Promise<void> {
  await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  });
}

export type { TestResult, TestRunEvent, TelemetryConfig };
