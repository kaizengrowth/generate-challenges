"""
Boilerplate config-file templates for each ecosystem.

These are infrastructure/config files that are essentially identical across all
challenges in the same ecosystem. The Builder LLM focuses on creative files
(README, skeletons, tests, App wrapper) while these are generated here in code.

MAINTENANCE NOTE: Template strings here are extracted from
  references/project-templates.md  and  references/ui-styling.md
If you update those reference docs, update the corresponding templates here too.
"""

# ── .gitignore fragments ─────────────────────────────────────────────────────

_JS_GITIGNORE = """\
node_modules/
dist/
.DS_Store
*.env
"""

_PYTHON_GITIGNORE = """\
__pycache__/
*.pyc
.pytest_cache/
venv/
.DS_Store
*.env
"""

_JAVA_GITIGNORE = """\
target/
*.class
.DS_Store
*.env
"""

_CPP_GITIGNORE = """\
build/
.DS_Store
*.env
"""

_COBOL_GITIGNORE = """\
*.so
*.dylib
.DS_Store
*.env
"""

# ── Shared UI CSS ─────────────────────────────────────────────────────────────

_INDEX_CSS = """\
/* src/index.css */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  --color-bg:        #0f172a;
  --color-surface:   #1e293b;
  --color-border:    #334155;
  --color-text:      #f1f5f9;
  --color-muted:     #94a3b8;
  --color-accent:    #6366f1;
  --color-accent-hover: #4f46e5;
  --color-success:   #22c55e;
  --color-danger:    #ef4444;
  --color-warning:   #f59e0b;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;

  --shadow-sm: 0 1px 3px rgba(0,0,0,0.4);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.5);
}

body {
  background-color: var(--color-bg);
  color: var(--color-text);
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  min-height: 100vh;
}

h1 { font-size: 2rem;   font-weight: 700; letter-spacing: -0.5px; }
h2 { font-size: 1.4rem; font-weight: 600; letter-spacing: -0.3px; }
h3 { font-size: 1.1rem; font-weight: 600; }

/* Buttons */
button {
  cursor: pointer;
  border: none;
  border-radius: var(--radius-sm);
  padding: 0.5rem 1.2rem;
  font-size: 0.95rem;
  font-weight: 500;
  transition: background 0.15s, transform 0.1s;
}
button:active { transform: scale(0.97); }

.btn-primary {
  background: var(--color-accent);
  color: #fff;
}
.btn-primary:hover { background: var(--color-accent-hover); }

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
.btn-secondary:hover { background: var(--color-border); }

.btn-danger {
  background: var(--color-danger);
  color: #fff;
}

/* Inputs */
input, textarea, select {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.5rem 0.8rem;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
}
input:focus, textarea:focus, select:focus {
  border-color: var(--color-accent);
}

label {
  display: block;
  font-size: 0.85rem;
  color: var(--color-muted);
  margin-bottom: 0.3rem;
}

/* Cards / containers */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

/* Status badges */
.badge {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
}
.badge-success { background: rgba(34,197,94,0.15); color: var(--color-success); }
.badge-danger  { background: rgba(239,68,68,0.15);  color: var(--color-danger);  }
.badge-warning { background: rgba(245,158,11,0.15); color: var(--color-warning); }
.badge-accent  { background: rgba(99,102,241,0.15); color: var(--color-accent);  }

/* Lists */
ul, ol { padding-left: 1.2rem; }
li + li { margin-top: 0.3rem; }

/* Utility */
.text-muted  { color: var(--color-muted); }
.text-center { text-align: center; }
.mt-1 { margin-top: 0.5rem; }
.mt-2 { margin-top: 1rem; }
.mt-3 { margin-top: 1.5rem; }
.gap-1 { gap: 0.5rem; }
.gap-2 { gap: 1rem; }
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
"""

_APP_CSS = """\
.app-layout {
  max-width: 800px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem;
}

.app-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.app-header p {
  color: var(--color-muted);
  margin-top: 0.3rem;
}

.challenge-section {
  margin-bottom: 1.5rem;
}

.challenge-section h2 {
  margin-bottom: 1rem;
}
"""

# ── React ─────────────────────────────────────────────────────────────────────

_REACT_PACKAGE_JSON = """\
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
}"""

_REACT_TSCONFIG = """\
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
}"""

_REACT_VITE_CONFIG = """\
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
  },
});"""

_REACT_SETUP_TESTS = """\
import "@testing-library/jest-dom";"""

_REACT_INDEX_HTML = """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Challenge</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>"""

_REACT_MAIN_TSX = """\
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);"""


def react_boilerplate() -> dict[str, str]:
    return {
        "package.json": _REACT_PACKAGE_JSON,
        "tsconfig.json": _REACT_TSCONFIG,
        "vite.config.ts": _REACT_VITE_CONFIG,
        "src/setupTests.ts": _REACT_SETUP_TESTS,
        "index.html": _REACT_INDEX_HTML,
        "src/main.tsx": _REACT_MAIN_TSX,
        "src/index.css": _INDEX_CSS,
        "src/App.css": _APP_CSS,
        ".gitignore": _JS_GITIGNORE,
    }


# ── TypeScript / JavaScript (plain — no UI framework) ────────────────────────

_TS_PACKAGE_JSON = """\
{
  "type": "module",
  "scripts": {
    "test": "vitest --bail 1"
  },
  "dependencies": {
    "vitest": "^3.1.1"
  }
}"""

_TS_TSCONFIG = """\
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
}"""


def typescript_boilerplate() -> dict[str, str]:
    return {
        "package.json": _TS_PACKAGE_JSON,
        "tsconfig.json": _TS_TSCONFIG,
        ".gitignore": _JS_GITIGNORE,
    }


# ── Vue ───────────────────────────────────────────────────────────────────────

_VUE_PACKAGE_JSON = """\
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
}"""

_VUE_VITE_CONFIG = """\
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    globals: true,
  },
});"""

_VUE_INDEX_HTML = """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Challenge</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>"""

_VUE_MAIN_TS = """\
import { createApp } from "vue";
import App from "./App.vue";
import "./index.css";

createApp(App).mount("#app");"""


def vue_boilerplate() -> dict[str, str]:
    return {
        "package.json": _VUE_PACKAGE_JSON,
        "vite.config.ts": _VUE_VITE_CONFIG,
        "index.html": _VUE_INDEX_HTML,
        "src/main.ts": _VUE_MAIN_TS,
        "src/index.css": _INDEX_CSS,
        ".gitignore": _JS_GITIGNORE,
    }


# ── Angular ───────────────────────────────────────────────────────────────────

_ANGULAR_PACKAGE_JSON = """\
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
}"""

_ANGULAR_TSCONFIG = """\
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
}"""

_ANGULAR_KARMA_CONF = """\
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
    bail: true,
  });
};"""

_ANGULAR_INDEX_HTML = """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Challenge</title>
  </head>
  <body>
    <app-root></app-root>
  </body>
</html>"""

_ANGULAR_MAIN_TS = """\
import { platformBrowserDynamic } from "@angular/platform-browser-dynamic";
import { AppModule } from "./app/app.module";

platformBrowserDynamic().bootstrapModule(AppModule).catch(console.error);"""

_ANGULAR_JSON = """\
{
  "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
  "version": 1,
  "newProjectRoot": "projects",
  "projects": {
    "challenge": {
      "projectType": "application",
      "root": "",
      "sourceRoot": "src",
      "architect": {
        "build": {
          "builder": "@angular-devkit/build-angular:browser",
          "options": {
            "outputPath": "dist",
            "index": "src/index.html",
            "main": "src/main.ts",
            "tsConfig": "tsconfig.json",
            "assets": [],
            "styles": ["src/styles.css"],
            "scripts": []
          }
        },
        "serve": {
          "builder": "@angular-devkit/build-angular:dev-server",
          "options": { "buildTarget": "challenge:build" }
        },
        "test": {
          "builder": "@angular-devkit/build-angular:karma",
          "options": {
            "main": "src/main.ts",
            "tsConfig": "tsconfig.json",
            "karmaConfig": "karma.conf.js"
          }
        }
      }
    }
  }
}"""


def angular_boilerplate() -> dict[str, str]:
    return {
        "package.json": _ANGULAR_PACKAGE_JSON,
        "tsconfig.json": _ANGULAR_TSCONFIG,
        "karma.conf.js": _ANGULAR_KARMA_CONF,
        "src/index.html": _ANGULAR_INDEX_HTML,
        "src/main.ts": _ANGULAR_MAIN_TS,
        "angular.json": _ANGULAR_JSON,
        "src/styles.css": _INDEX_CSS,
        ".gitignore": _JS_GITIGNORE,
    }


# ── Python ────────────────────────────────────────────────────────────────────

_PYTHON_REQUIREMENTS = """\
pytest"""


def python_boilerplate() -> dict[str, str]:
    return {
        "requirements.txt": _PYTHON_REQUIREMENTS,
        ".gitignore": _PYTHON_GITIGNORE,
    }


# ── Java ──────────────────────────────────────────────────────────────────────

_JAVA_POM_XML = """\
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
</project>"""

_JAVA_TEST_LISTENER = """\
package com.challenge.support;

import org.junit.platform.engine.TestExecutionResult;
import org.junit.platform.engine.TestExecutionResult.Status;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;

import java.util.ArrayList;
import java.util.List;

public class ChallengeTestListener implements TestExecutionListener {

    private static final String GREEN = "\\u001B[32m";
    private static final String RED   = "\\u001B[31m";
    private static final String RESET = "\\u001B[0m";

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
                passes.add(GREEN + "  \\u2713 " + name + RESET);
            } else {
                StringBuilder sb = new StringBuilder(RED + "  \\u2717 " + name + RESET);
                result.getThrowable().ifPresent(t -> {
                    String msg = t.getMessage();
                    if (msg == null) msg = t.getClass().getSimpleName();
                    if (msg.length() > 120) msg = msg.substring(0, 120) + "\\u2026";
                    sb.append("\\n      \\u2192 ").append(msg);
                });
                failures.add(sb.toString());
            }
        } else if (id.getUniqueId().equals(currentClassId)) {
            System.out.println("\\n\\u2500\\u2500 " + currentClassName + " " + "\\u2500".repeat(40));
            passes.forEach(System.out::println);
            failures.forEach(System.out::println);
        }
    }
}"""

_JAVA_SERVICE_LOADER = """\
com.challenge.support.ChallengeTestListener"""


def java_boilerplate() -> dict[str, str]:
    return {
        "pom.xml": _JAVA_POM_XML,
        "src/test/java/com/challenge/support/ChallengeTestListener.java": _JAVA_TEST_LISTENER,
        "src/test/resources/META-INF/services/org.junit.platform.launcher.TestExecutionListener": _JAVA_SERVICE_LOADER,
        ".gitignore": _JAVA_GITIGNORE,
    }


# ── C++ ───────────────────────────────────────────────────────────────────────
# CMakeLists.txt references specific source files, so it can't be fully static.
# The LLM generates it.

def cpp_boilerplate() -> dict[str, str]:
    return {
        ".gitignore": _CPP_GITIGNORE,
    }


# ── COBOL ─────────────────────────────────────────────────────────────────────
# The test runner script contains challenge-specific test calls, so the LLM
# generates the full script.

def cobol_boilerplate() -> dict[str, str]:
    return {
        ".gitignore": _COBOL_GITIGNORE,
    }


# ── Router ────────────────────────────────────────────────────────────────────

_BOILERPLATE_FN = {
    "react": react_boilerplate,
    "typescript": typescript_boilerplate,
    "vue": vue_boilerplate,
    "angular": angular_boilerplate,
    "python": python_boilerplate,
    "java": java_boilerplate,
    "cpp": cpp_boilerplate,
    "cobol": cobol_boilerplate,
}


def get_boilerplate(ecosystem: str) -> dict[str, str]:
    """Return {path: content} for all static config files in this ecosystem."""
    fn = _BOILERPLATE_FN.get(ecosystem)
    if fn is None:
        return {}
    return fn()
