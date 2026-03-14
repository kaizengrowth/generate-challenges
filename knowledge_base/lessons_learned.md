# Lessons Learned

This file is updated by the Builder agent after each run with cross-cutting insights
about what works well (or poorly) when generating challenges.

---

<!-- Builder will append entries here as it gains experience -->

## Run: React hooks

### fix-stale-closure-bug (resolved after 2 iteration(s))
- Clarity: The hint 'Think about what values your setInterval callback closes over, and whether those values appear in the useEffect dependency array' basically tells me the exact fix — it felt less like a hint and more like the answer. I didn't feel like I had to figure much out on my own.
- Clarity: The TypeScript syntax `useState<number | null>` in the skeleton might trip up students who haven't seen generics yet, even though it's minor.

## Run: React hooks

### fix-stale-closure-bug (resolved after 2 iteration(s))
- Clarity: The README says the fix is 'typically one word' but then lists the useRef approach as a valid alternative — that's definitely more than one word. These two hints contradict each other and could make me second-guess which path to take.
- Clarity: The README says the interval 'logs' the count, but I don't see a console panel in the browser preview — so 'logging' and 'updating the display' feel like two different things that are conflated.
- Clarity: The cleanup function `return () => clearInterval(id)` inside useEffect is in the skeleton code but never explained in the README. As a student I might not know what that return statement is doing or why.
- Clarity: The test file uses `vi.useFakeTimers()`, `vi.advanceTimersByTime()`, `act()`, and `vi.spyOn()` — these are advanced testing utilities I wouldn't have seen yet if I just learned useEffect. Reading the tests to understand what's expected would itself be confusing.
### react-debounce-hook (resolved after 2 iteration(s))
- Clarity: The README mentions 'renderHook' and explains it in detail, but as a student who just learned React hooks I might wonder why I need a special utility just to test a hook — the explanation helps but could feel overwhelming at first
- Clarity: The phrase 'Cleans up the timer when the component unmounts or when value or delay changes' — the word 'unmounts' is React jargon that might not have been covered yet, though it is implicitly handled by useEffect cleanup
- Clarity: The skeleton comment says 'return a cleanup function that clears the timer' — a student who hasn't seen cleanup functions before might not know the syntax (returning a function from useEffect)

## Run: JavaScript closures

### typescript-closure-patterns (resolved after 2 iteration(s))
- Clarity: The phrase 'functional pipeline composition' in the topic title sounds intimidating — I wouldn't know what that means before reading the README, but the README explains it well enough
- Clarity: The term 'middleware list' in the pipeline.ts comments might confuse me — 'middleware' is a backend/Express concept I may not have encountered yet in a closures lesson
- Clarity: The `ReturnType<typeof createBankAccount>` TypeScript utility type used in the test file (`let account: ReturnType<typeof createBankAccount>`) could be confusing if I look at the test source, even though I'm not supposed to modify it
- Clarity: The comment in pipeline.ts says `pipe(f, g, h)(x) === h(g(f(x)))` but that's actually the compose definition — pipe left-to-right would be `f(g(h(x)))` reversed, so `h(g(f(x)))` is correct for pipe but the visual order feels backwards and could cause a double-take
