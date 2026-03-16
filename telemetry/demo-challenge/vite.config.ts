import { defineConfig } from "vite";

export default defineConfig({
  test: {
    environment: "node",
    reporters: ["default", "./src/telemetry/vitest-reporter.ts"],
  },
});
