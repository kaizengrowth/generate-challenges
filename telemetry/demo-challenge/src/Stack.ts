/**
 * Stack Challenge
 *
 * Implement a generic Stack data structure using an array as internal storage.
 *
 * A Stack is a Last-In, First-Out (LIFO) collection.
 * The last item pushed onto the stack is the first item returned by pop().
 *
 * Run tests:   npm test
 * Watch mode:  npm run test:watch
 */

export class Stack<T> {
  private storage: T[] = [];

  /** Add an item to the top of the stack. */
  push(item: T): void {
    // TODO: add item to storage
  }

  /**
   * Remove and return the top item.
   * Returns undefined if the stack is empty.
   */
  pop(): T | undefined {
    // TODO: remove and return the last item; return undefined if empty
    return undefined;
  }

  /**
   * Return the top item without removing it.
   * Returns undefined if the stack is empty.
   */
  peek(): T | undefined {
    // TODO: return the last item without removing it; return undefined if empty
    return undefined;
  }

  /** Return true if the stack has no items. */
  isEmpty(): boolean {
    // TODO: return whether storage is empty
    return true;
  }

  /** Return the number of items in the stack. */
  get size(): number {
    // TODO: return the length of storage
    return 0;
  }
}
