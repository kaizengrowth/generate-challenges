import { describe, it, expect, beforeEach } from "vitest";
import { Stack } from "../src/Stack";

describe("Stack", () => {
  let stack: Stack<number>;

  beforeEach(() => {
    stack = new Stack<number>();
  });

  // ── Existence / smoke ────────────────────────────────────────────────────

  it("should create an empty stack", () => {
    expect(stack).toBeDefined();
  });

  // ── Initial state ────────────────────────────────────────────────────────

  it("should report size as 0 when empty", () => {
    expect(stack.size).toBe(0);
  });

  it("should report isEmpty as true when empty", () => {
    expect(stack.isEmpty()).toBe(true);
  });

  // ── Basic behaviour ──────────────────────────────────────────────────────

  it("should push items and increase size", () => {
    stack.push(1);
    stack.push(2);
    expect(stack.size).toBe(2);
  });

  it("should pop items in LIFO order", () => {
    stack.push(10);
    stack.push(20);
    stack.push(30);
    expect(stack.pop()).toBe(30);
    expect(stack.pop()).toBe(20);
    expect(stack.pop()).toBe(10);
  });

  it("should peek at the top item without removing it", () => {
    stack.push(42);
    expect(stack.peek()).toBe(42);
    expect(stack.size).toBe(1); // peek must not remove
  });

  // ── Edge cases ───────────────────────────────────────────────────────────

  it("should return undefined when popping an empty stack", () => {
    expect(stack.pop()).toBeUndefined();
  });

  it("should return undefined when peeking an empty stack", () => {
    expect(stack.peek()).toBeUndefined();
  });

  it("should report isEmpty as false after a push, true after all pops", () => {
    stack.push(1);
    expect(stack.isEmpty()).toBe(false);
    stack.pop();
    expect(stack.isEmpty()).toBe(true);
  });
});
