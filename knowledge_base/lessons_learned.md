# Lessons Learned

This file is updated by the Builder agent after each run with cross-cutting insights
about what works well (or poorly) when generating challenges.

---

<!-- Builder will append entries here as it gains experience -->

## Run: React hooks

### fix-stale-closure-bug (resolved after 2 iteration(s))
- Clarity: The hint 'Think about what values your setInterval callback closes over, and whether those values appear in the useEffect dependency array' basically tells me the exact fix — it felt less like a hint and more like the answer. I didn't feel like I had to figure much out on my own.
- Clarity: The TypeScript syntax `useState<number | null>` in the skeleton might trip up students who haven't seen generics yet, even though it's minor.
