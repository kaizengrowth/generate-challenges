import type { Reporter, File, Task } from "vitest";
import { logTestRun } from "./telemetry";
import type { TestResult } from "./telemetry";

function extractChallengeName(filepath: string): string {
  const filename = filepath.split("/").pop() ?? filepath;
  return filename.replace(/\.test\.(ts|tsx|js|jsx)$/, "");
}

function collectResults(tasks: Task[]): TestResult[] {
  const results: TestResult[] = [];
  for (const task of tasks) {
    if (task.type === "test") {
      results.push({
        name: task.name,
        status:
          task.result?.state === "pass"
            ? "passed"
            : task.result?.state === "skip"
            ? "skipped"
            : "failed",
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
      const results = collectResults(file.tasks);
      const passed   = results.filter((r) => r.status === "passed").length;
      const failed   = results.filter((r) => r.status === "failed").length;
      const duration = results.reduce((sum, r) => sum + r.duration, 0);

      logTestRun({
        challenge: extractChallengeName(file.filepath),
        testFile:  file.filepath,
        results,
        summary:   { total: results.length, passed, failed, duration },
      });
    }
  }
}
