# Open Question: Debugging Limitations and Testing Strategy

**Status:** Unresolved - documented for future consideration
**Raised:** 2026-02-18
**Raised by:** Ali (during session 003)

---

## The Core Limitation: LLM Debugging vs Human Debugging

### How a human developer debugs
A human developer can:
- Run the app in debug mode (e.g. Chrome DevTools)
- Set a breakpoint at any line of code
- Pause execution at that exact line
- Inspect the value of every variable at that moment in time
- Step through code line by line, watching values change
- Immediately see where reality diverges from expectation

This is extremely powerful. The developer doesn't have to guess - they can *observe* the program's internal state directly.

### How an LLM agent (Claude) debugs
Claude cannot:
- Run the app
- Set breakpoints
- Inspect live variable values
- Step through code interactively

Claude can only:
- Read the source code and reason about what it *should* do
- Ask Ali to test specific scenarios and report back what happens
- Ask Ali to add `console.log()` statements at specific places and report what they print

### Why this matters
This means Claude's debugging is hypothesis-driven from static code reading alone. For straightforward bugs (a wrong variable name, a missing condition) this works fine. For subtle bugs involving timing, state, or unexpected interactions between parts of the code, Claude may not be able to identify the root cause without additional information from Ali.

**The risk:** if Claude can't identify the root cause clearly, there is a temptation to try multiple changes and see what sticks. This is explicitly forbidden by the Honesty and Caution Rules in CLAUDE.md. If Claude is stuck, it must say so and ask for help rather than guess.

---

## Conceptual Workaround: Collaborative Breakpoint Debugging

**Status:** Idea only - not yet tried in this project

A possible middle ground between full debugger access and pure code reading:

1. Claude identifies a specific line of code it wants to "inspect"
2. Claude asks Ali to temporarily add a `console.log()` at that exact line, logging specific variables
3. Ali opens the browser console (F12 -> Console tab), reproduces the bug, and pastes the output back
4. Claude uses that output to confirm or disprove its hypothesis
5. Repeat for 1-2 more points if needed
6. Remove all `console.log()` statements before committing the fix

This mirrors the human breakpoint process, just with Ali as the "hands." It is slower but more rigorous than pure code reading.

**This should be tried when:**
- The bug is not obvious from reading the code alone
- Claude has a hypothesis but is not confident enough to make a change
- A previous fix attempt didn't work and the cause is still unclear

---

## Open Question: Automated Testing

**Status:** Not implemented - noted for future consideration

As the codebase grows, manual testing (opening the browser and clicking around) becomes increasingly unreliable. Bugs can be introduced without anyone noticing until much later.

The right long-term solution is **automated unit tests** - small scripts that test individual functions in isolation without needing a browser. For example:

```js
// Test that calcFoodNutrition returns correct values
var result = Storage.calcFoodNutrition(chickenBreast, 100, gramUnit, conversions);
console.assert(result.calories === 165, 'Calories should be 165');
console.assert(result.protein === 31, 'Protein should be 31g');
```

This runs in Node.js without a browser. If the function is broken, the test fails immediately and tells you exactly which assertion failed.

### Why the current code isn't easily testable
The three modules (`Storage`, `UI`, `App`) have some separation but:
- `UI` is tightly coupled to the DOM - you can't run it without a browser
- `Storage` touches `localStorage` directly - you'd need to mock it for tests
- `App` orchestrates both - hard to test in isolation

### How object-oriented design helps
Ali raised this during session 003 and it's a valid insight. More modular, class-based design makes testing easier because:
- Each class has a clear responsibility
- Classes can be instantiated with fake/mock dependencies
- You test one class at a time, confirming it works before testing the whole system
- When a bug appears, you can narrow it down to a specific class quickly

The current module pattern (`const X = (function() { ... })()`) is already somewhat modular but not easily injectable with test doubles.

### Recommendation
Do not implement automated testing now - the project is too early stage and the overhead would slow down feature development. Revisit this when:
- Core features (add, edit, delete food, daily diary) are complete and stable
- Bugs start becoming harder to trace manually
- The codebase grows beyond ~5-6 files

At that point, consider adopting a simple test framework like **Jest** and writing tests for `Storage` and `calcFoodNutrition` first, since those are pure logic with no DOM dependency.

---

## Summary of What to Do When Debugging Gets Hard

In order of preference:

1. **Read the code carefully and form a hypothesis** - most bugs are findable this way
2. **Ask Ali a clarifying question** - "does it crash immediately or after typing the second character?" - to narrow down the cause
3. **Use collaborative console.log debugging** - ask Ali to add a specific log, reproduce, paste output
4. **If still stuck, stop and document** - write what was tried in BUGS.md, flag it in the conversation, do not guess
