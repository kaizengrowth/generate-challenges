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

Always generate `src/App.css` alongside `App.tsx` / `App.vue`. Keep all layout styles in the CSS file — no inline styles in App.

### `src/App.css`

```css
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
```

### React `src/App.tsx`

```tsx
import { ComponentName } from "./ComponentName";
// import { OtherComponent } from "./OtherComponent";
import "./App.css";

function App() {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>Challenge Title</h1>
        <p>Short description of the challenge set</p>
      </header>

      <section className="card challenge-section">
        <h2>Component Name</h2>
        <ComponentName />
      </section>

      {/* Add one <section className="card challenge-section"> per challenge component */}
    </div>
  );
}

export default App;
```

### Vue `src/App.vue`

Use a `<style>` block — no inline styles on elements.

```vue
<script setup lang="ts">
import ComponentName from "./ComponentName.vue";
</script>

<template>
  <div class="app-layout">
    <header class="app-header">
      <h1>Challenge Title</h1>
      <p>Short description of the challenge set</p>
    </header>

    <section class="card challenge-section">
      <h2>Component Name</h2>
      <ComponentName />
    </section>

    <!-- Add one <section class="card challenge-section"> per challenge component -->
  </div>
</template>

<style>
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
</style>
```

### Angular `src/app/app.component.ts`

Add layout styles to `src/styles.css` (already loaded globally). The template uses only class names.

```typescript
import { Component } from "@angular/core";

@Component({
  selector: "app-root",
  template: `
    <div class="app-layout">
      <header class="app-header">
        <h1>Challenge Title</h1>
        <p>Short description of the challenge set</p>
      </header>
      <section class="card challenge-section">
        <h2>Challenge Component</h2>
        <app-challenge></app-challenge>
      </section>
    </div>
  `,
})
export class AppComponent {}
```

---

## Styling Challenge Skeleton Components

**Keep component files clean**: no inline `style={{...}}` objects. Put all component-specific styles in a companion CSS file and use `className` / `class` attributes only.

### React — two files per component

**`src/ClickCounter.css`**

```css
.click-counter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem 0;
}

.click-counter__count {
  font-size: 4rem;
  font-weight: 700;
  color: var(--color-accent);
  min-width: 4rem;
  text-align: center;
}

.click-counter__buttons {
  display: flex;
  gap: 0.75rem;
}
```

**`src/ClickCounter.tsx`** (skeleton — no logic, no inline styles)

```tsx
import "./ClickCounter.css";

export function ClickCounter() {
  // TODO: add state here

  return (
    <div className="click-counter">
      <div className="click-counter__count">0</div>
      <div className="click-counter__buttons">
        <button className="btn-primary">Increment</button>
        <button className="btn-secondary">Reset</button>
      </div>
    </div>
  );
}
```

### Vue — `<style scoped>` block in the `.vue` file

```vue
<script setup lang="ts">
// TODO: add state here
</script>

<template>
  <div class="click-counter">
    <div class="count">0</div>
    <div class="buttons">
      <button class="btn-primary">Increment</button>
      <button class="btn-secondary">Reset</button>
    </div>
  </div>
</template>

<style scoped>
.click-counter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem 0;
}
.count {
  font-size: 4rem;
  font-weight: 700;
  color: var(--color-accent);
  text-align: center;
}
.buttons {
  display: flex;
  gap: 0.75rem;
}
</style>
```

### Vanilla HTML — separate `style.css` file

Generate `style.css` in the project root (or `src/`), link it from `index.html`. No inline styles on elements.

**`style.css`**

```css
/* imports index.css design system variables, then adds page-specific styles */
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}
/* ... component-specific rules ... */
```

**`index.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Challenge</title>
    <link rel="stylesheet" href="index.css" />
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <div class="container">
      <!-- challenge content here -->
    </div>
  </body>
</html>
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
