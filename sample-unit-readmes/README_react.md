# Introduction to React

React is a JavaScript library for building user interfaces. It was created by Facebook and is now one of the most widely used frontend tools in the industry. At its core, React lets you build UIs by composing small, reusable pieces called **components**.

---

## 1. Components

A component is just a JavaScript function that returns some UI. In React, that UI is written in **JSX** — a syntax that looks like HTML but lives inside your JavaScript.

```jsx
function Greeting() {
  return <h1>Hello, world!</h1>;
}
```

That's a valid React component. Component names must start with a capital letter. You can use it like an HTML tag:

```jsx
<Greeting />
```

React is *component-based* — you build complex UIs by composing many small components together, rather than writing one giant HTML file.

---

## 2. JSX

JSX is not HTML. It compiles down to `React.createElement()` calls under the hood. That means there are a few differences you need to know:

- Use `className` instead of `class`
- All tags must be closed (including self-closing ones like `<img />`)
- You can embed JavaScript expressions using curly braces `{}`

```jsx
const name = "Alex";

function Greeting() {
  return <h1>Hello, {name}!</h1>;
}
```

Anything inside `{}` is evaluated as a JavaScript expression — variables, function calls, ternaries, arithmetic, etc.

---

## 3. Props

Props (short for *properties*) are how you pass data into a component. They work like arguments to a function.

```jsx
function Greeting({ name }) {
  return <h1>Hello, {name}!</h1>;
}

// Usage:
<Greeting name="Alex" />
<Greeting name="Jordan" />
```

Props are **read-only** — a component should never modify its own props. Data flows one direction in React: from parent to child.

You can pass any JavaScript value as a prop: strings, numbers, booleans, arrays, objects, or even other components and functions.

---

## 4. State

While props come from outside a component, **state** is data that lives *inside* a component and can change over time. When state changes, React re-renders the component automatically.

You create state with the `useState` hook:

```jsx
import { useState } from "react";

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

`useState` returns a pair: the current value and a setter function. You never modify state directly — always use the setter. This is what tells React to re-render.

---

## 5. Event Handling

React handles events similarly to HTML, but with a few differences:

- Event names are camelCase (`onClick`, `onChange`, `onSubmit`)
- You pass a function, not a string

```jsx
function Button() {
  function handleClick() {
    console.log("Clicked!");
  }

  return <button onClick={handleClick}>Click me</button>;
}
```

You can also define handlers inline:

```jsx
<button onClick={() => console.log("Clicked!")}>Click me</button>
```

Event handlers receive a synthetic event object (`e`) if you need it:

```jsx
<input onChange={(e) => console.log(e.target.value)} />
```

---

## 6. Conditional Rendering

You can render different UI based on conditions using standard JavaScript:

```jsx
function Status({ isLoggedIn }) {
  if (isLoggedIn) {
    return <p>Welcome back!</p>;
  }
  return <p>Please log in.</p>;
}
```

Or inline with a ternary:

```jsx
function Status({ isLoggedIn }) {
  return <p>{isLoggedIn ? "Welcome back!" : "Please log in."}</p>;
}
```

Or with `&&` for "render if true" patterns:

```jsx
{hasError && <p style={{ color: "red" }}>Something went wrong.</p>}
```

---

## 7. Lists and Keys

To render a list of items, use `.map()` to transform an array into JSX elements. Each element in a list needs a unique `key` prop so React can track which items change.

```jsx
function FruitList({ fruits }) {
  return (
    <ul>
      {fruits.map((fruit) => (
        <li key={fruit}>{fruit}</li>
      ))}
    </ul>
  );
}

// Usage:
<FruitList fruits={["Apple", "Banana", "Cherry"]} />
```

The `key` should be a stable, unique identifier — ideally an ID from your data. Avoid using the array index as a key when the list can be reordered.

---

## 8. useEffect

`useEffect` lets you run side effects in your component — things like fetching data, setting up subscriptions, or manually touching the DOM.

```jsx
import { useState, useEffect } from "react";

function Timer() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds((s) => s + 1);
    }, 1000);

    return () => clearInterval(interval); // cleanup
  }, []); // empty array = run once on mount

  return <p>Seconds elapsed: {seconds}</p>;
}
```

The second argument to `useEffect` is a **dependency array**:

- `[]` — run once when the component mounts
- `[value]` — re-run whenever `value` changes
- No array — run after every render (usually not what you want)

The function returned from `useEffect` is a cleanup function that runs before the component unmounts or before the effect re-runs.

---

## 9. Component Composition

One of React's greatest strengths is composability. You build complex UIs by nesting components inside other components.

```jsx
function Avatar({ name }) {
  return <div className="avatar">{name[0]}</div>;
}

function UserCard({ name, role }) {
  return (
    <div className="card">
      <Avatar name={name} />
      <p>{name}</p>
      <p>{role}</p>
    </div>
  );
}

function App() {
  return (
    <div>
      <UserCard name="Alex" role="Engineer" />
      <UserCard name="Jordan" role="Designer" />
    </div>
  );
}
```

A special prop called `children` lets a component render whatever is passed between its opening and closing tags:

```jsx
function Card({ children }) {
  return <div className="card">{children}</div>;
}

// Usage:
<Card>
  <h2>Title</h2>
  <p>Some content here.</p>
</Card>
```

---

## 10. Lifting State Up

When multiple components need to share the same state, move that state to their closest common ancestor and pass it down as props. This is called *lifting state up*.

```jsx
function App() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <Display count={count} />
      <Controls onIncrement={() => setCount(count + 1)} />
    </div>
  );
}

function Display({ count }) {
  return <p>Count: {count}</p>;
}

function Controls({ onIncrement }) {
  return <button onClick={onIncrement}>Increment</button>;
}
```

This pattern keeps a single source of truth for your data and avoids components getting out of sync.

---

## Key Takeaways

- React UIs are built from **components** — functions that return JSX
- **Props** pass data from parent to child (read-only)
- **State** is local, mutable data that triggers re-renders when changed
- **useEffect** handles side effects like data fetching and timers
- Compose components together to build complex UIs from simple pieces
- When siblings need to share state, **lift it up** to their parent

---

## Challenges

Work through these in order. Each one targets a core concept from the lecture above.

**1. Hello, You**
Create a `Greeting` component that accepts a `name` prop and displays a personalized greeting message.

**2. Click Counter**
Create a component with a button and a counter. Each click should increment the count displayed on the page.

**3. Toggle Visibility**
Create a component with a button that shows and hides a block of text. The button label should change to reflect the current state ("Show" / "Hide").

**4. Live Input Preview**
Create a component with a text input. As the user types, display what they've typed in real time below the input.

**5. Card Gallery**
Create a `Card` component that accepts `title` and `description` as props. Render at least 4 `Card` components in an `App`, each with different content.

**6. Dynamic List**
Create a component with a text input and an "Add" button. Each time the user clicks Add, append the input value to a list displayed on the page.

**7. Fetch and Display**
Use `useEffect` to fetch data from a public API when the component mounts (e.g. `https://jsonplaceholder.typicode.com/users`). Display the results in a list.

**8. Stopwatch**
Build a stopwatch with Start, Stop, and Reset buttons. The elapsed time should update every second while running.

**9. Shared State Siblings**
Create two sibling components — a `Slider` (range input) and a `Display` — that share state through a parent. Moving the slider should update the value shown in the Display.

**10. Multi-step Form**
Build a form split into three steps: collect a name, then an email, then show a confirmation screen with both values. Only one step should be visible at a time, with Next/Back buttons to navigate between them.
