# UI Styling Guide

Use these styles for any challenge that has a browser UI (React, Vue, Angular, or vanilla HTML/JS).
The goal: clean, modern, visually interesting — not plain browser defaults.

---

## When to Apply

Apply this guide whenever a challenge requires:
- A React, Vue, or Angular component the student renders in a browser
- A vanilla HTML/JS challenge with a UI
- Any challenge where `npm run dev` or a browser preview matters

---

## Global CSS (`src/index.css`)

Generate this file for every UI challenge. Import it in `src/main.tsx` / `src/main.ts`:

```css
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
```

---

## How to Import the CSS

### React (`src/main.tsx`)

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

### Vue (`src/main.ts`)

```typescript
import { createApp } from "vue";
import App from "./App.vue";
import "./index.css";

createApp(App).mount("#app");
```

### Angular — add to `src/styles.css` (referenced in `angular.json` under `styles`)

---

## App Wrapper Pattern

Replace the plain `div` wrappers in App.tsx / App.vue / app.component.ts with this styled layout:

### React `src/App.tsx`

```tsx
import { ComponentName } from "./ComponentName";
// import { OtherComponent } from "./OtherComponent";

function App() {
  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "2.5rem 1.5rem" }}>
      <header style={{ marginBottom: "2rem", borderBottom: "1px solid var(--color-border)", paddingBottom: "1rem" }}>
        <h1>Challenge Title</h1>
        <p style={{ color: "var(--color-muted)", marginTop: "0.3rem" }}>
          Short description of the challenge set
        </p>
      </header>

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ marginBottom: "1rem" }}>Component Name</h2>
        <ComponentName />
      </section>

      {/* Add one <section className="card"> per challenge component */}
    </div>
  );
}

export default App;
```

### Vue `src/App.vue`

```vue
<script setup lang="ts">
import ComponentName from "./ComponentName.vue";
</script>

<template>
  <div style="max-width: 800px; margin: 0 auto; padding: 2.5rem 1.5rem;">
    <header style="margin-bottom: 2rem; border-bottom: 1px solid var(--color-border); padding-bottom: 1rem;">
      <h1>Challenge Title</h1>
      <p style="color: var(--color-muted); margin-top: 0.3rem;">
        Short description of the challenge set
      </p>
    </header>

    <section class="card" style="margin-bottom: 1.5rem;">
      <h2 style="margin-bottom: 1rem;">Component Name</h2>
      <ComponentName />
    </section>

    <!-- Add one <section class="card"> per challenge component -->
  </div>
</template>
```

### Angular `src/app/app.component.ts`

```typescript
import { Component } from "@angular/core";

@Component({
  selector: "app-root",
  template: `
    <div style="max-width: 800px; margin: 0 auto; padding: 2.5rem 1.5rem;">
      <header style="margin-bottom: 2rem; border-bottom: 1px solid var(--color-border); padding-bottom: 1rem;">
        <h1>Challenge Title</h1>
        <p style="color: var(--color-muted); margin-top: 0.3rem;">
          Short description of the challenge set
        </p>
      </header>
      <section class="card" style="margin-bottom: 1.5rem;">
        <h2 style="margin-bottom: 1rem;">Challenge Component</h2>
        <app-challenge></app-challenge>
      </section>
    </div>
  `,
})
export class AppComponent {}
```

---

## Styling Challenge Skeleton Components

When writing skeleton components, include structural `div`s and `className`/`class` attributes that use the design system — but **no logic**. Examples:

### React skeleton with layout

```tsx
export function ClickCounter() {
  // TODO: add state here

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1.5rem", padding: "1rem 0" }}>
      <div style={{
        fontSize: "4rem",
        fontWeight: 700,
        color: "var(--color-accent)",
        minWidth: "4rem",
        textAlign: "center",
      }}>
        0
      </div>
      <div style={{ display: "flex", gap: "0.75rem" }}>
        <button className="btn-primary">Increment</button>
        <button className="btn-secondary">Reset</button>
      </div>
    </div>
  );
}
```

### Vanilla HTML with inline styles

For plain HTML challenges, inline the CSS variables as fallback hex values since `:root` may not load:

```html
<div style="max-width:800px;margin:0 auto;padding:2rem;background:#0f172a;color:#f1f5f9;font-family:system-ui,sans-serif;min-height:100vh;">
  <h1 style="font-size:2rem;font-weight:700;margin-bottom:1.5rem;">Challenge Title</h1>
  <div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:1.5rem;">
    <!-- challenge content here -->
  </div>
</div>
```

---

## Quick Reference: CSS Variable Cheat Sheet

| Variable               | Value     | Use For                        |
|------------------------|-----------|--------------------------------|
| `--color-bg`           | `#0f172a` | Page background                |
| `--color-surface`      | `#1e293b` | Cards, inputs, panels          |
| `--color-border`       | `#334155` | Borders, dividers              |
| `--color-text`         | `#f1f5f9` | Primary text                   |
| `--color-muted`        | `#94a3b8` | Secondary text, labels         |
| `--color-accent`       | `#6366f1` | Primary buttons, highlights    |
| `--color-accent-hover` | `#4f46e5` | Button hover state             |
| `--color-success`      | `#22c55e` | Success states, passing tests  |
| `--color-danger`       | `#ef4444` | Error states, delete buttons   |
| `--color-warning`      | `#f59e0b` | Warnings, caution states       |
