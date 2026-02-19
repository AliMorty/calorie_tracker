# Calorie Tracker - Project Instructions

## Session Summaries

When the user says **"add the summary"** (or similar), create a session summary file:

- Location: `agentic_conversation_summaries/`
- Naming format: `YYYY-MM-DD_session-NNN.md` (e.g., `2026-02-16_session-001.md`). If multiple sessions happen on the same date, increment the session number. This keeps files sortable by date.
- The summary must contain these sections in order:
  1. **What was done this session** - concrete list of changes, files created/modified, features built
  2. **Next steps** - what should be tackled in the next session(s), in priority order
  3. **High-level notes for the developer** - things the vibe coder (Ali) needs to know: architecture decisions, trade-offs made, things that might surprise you later
  4. **Current challenges and anticipated risks** - any blockers right now, plus things that could become problems as the project grows
- Always commit the summary file after creating it.

## Issue Tracking

Every bug or problem gets tracked in two places simultaneously.

### 1. GitHub Issues
- Open a GitHub issue for every bug using the `gh` CLI
- Reference the issue number in every related commit message (e.g. `Fix search crash, closes #3`)
- Close the issue in the same commit that contains the confirmed fix

### 2. issue_documentations/BUGS.md (in-repo record)
- Location: `issue_documentations/BUGS.md`
- Contains a summary table at the top for quick scanning, followed by a full entry per issue

**Table format:**

| # | Title | Opened | Closed | Status |
|---|-------|--------|--------|--------|
| 1 | Short title | YYYY-MM-DD | YYYY-MM-DD | fixed |

**Full entry format per issue:**

```
## Issue #N - Short title
**Opened:** YYYY-MM-DD
**Closed:** YYYY-MM-DD (or "open")
**Status:** open / fixed / workaround

### What happened
Describe the bug and exact steps to reproduce it.

### Root cause
Which file(s) and line(s) were involved. Why it was broken.
If unknown, say so honestly.

### Fix attempts
For each attempt:
- **Files changed:** list with line numbers
- **What was changed and why:** the reasoning behind the change
- **Confidence level:** how confident was the agent that this would work and why
- **Outcome:** worked / partially worked / didn't work / caused issue #N

### Final fix
What actually solved it and the full reasoning.

### Lessons
What a future agent should know before touching this area of code again.
Any warnings about fragile or confusing parts nearby.
```

- Always update `BUGS.md` in the same commit as the fix - never separately
- If a fix causes a new issue, note it explicitly in the original issue entry under "Outcome" and open a new issue

## Bug Clarification Rules

When Ali reports a bug, **do not immediately try to fix it.** First make sure you both have the same understanding of the problem. A fix built on a wrong understanding wastes everyone's time and can make things worse.

**Always ask before touching code:**
- What device and browser is Ali testing on? (iPhone Safari, Android Chrome, desktop Chrome, etc.) - this is the single most important question for UI/layout bugs
- What exactly happens, step by step? ("the panel moves" is different from "the panel shrinks")
- What did you expect to happen instead?
- Does it happen every time, or only sometimes?
- Did it work before a recent change, or has it never worked?

**Confirm your understanding before proceeding:**
- After reading the bug description, restate what you think the problem is in your own words and ask Ali to confirm
- If the bug description is ambiguous about desired behaviour (e.g. "either X or Y"), always ask which one - never choose unilaterally
- If you have a hypothesis, state it clearly: "I think the cause is X because Y - does that match what you're seeing?"

**Why this matters:**
Bug #1 (iOS Safari panel drift) took 3 attempts because the testing environment (iPhone Safari) was not established upfront. If the first question had been "what device/browser are you testing on?", the iOS Safari keyboard/viewport issue would have been suspected immediately and the fix might have been found in one attempt. See `insights/collaborative_debugging.md` for the full story.

**Screenshots are extremely valuable - ask for them:**
- If a layout or visual bug is reported, ask Ali to share a screenshot before trying anything
- A screenshot often tells you more than a paragraph of text description
- Windows vs iPhone screenshots helped isolate bug #1 as iOS-specific in seconds

## Honesty and Caution Rules

These rules exist to prevent the slow destruction of a working codebase through overconfident or poorly reasoned fixes.

**Before making any change:**
- If you don't understand why something is broken, say so explicitly before touching any code. Do not guess silently.
- If a fix requires changing more than 2-3 lines, pause and explain the plan first.
- Do not refactor, clean up, or "improve" code that is not directly related to the bug being fixed.
- Pinpoint the exact location in the code you suspect is the cause before making any change. State it out loud in the conversation.

**When making changes:**
- Change the smallest possible thing that could fix the bug. Prefer targeted edits over rewrites.
- Make one change at a time. Do not bundle multiple speculative fixes into a single commit.
- Do not remove, rename, or restructure UI elements that are not part of the bug report. If the request is "swap A and B", the fix is swapping A and B - not redesigning how A and B work. If you think additional changes are needed, describe them and ask Ali before doing them.
- If a fix feels like a hack - it works but you're not sure why - say that explicitly in both the commit message and BUGS.md.
- If there are two plausible causes and it's genuinely unclear which one is responsible, say so and discuss with Ali before proceeding. Fix one at a time and test between each.
- After making a change, re-read your diff and ask yourself: "Did I change anything that was not requested?" If yes, revert the extra changes and explain why you thought they were needed. Let Ali decide.

**When reporting:**
- Always include your confidence level (e.g. "I'm fairly confident because...", "I'm not sure why this works but it does", "I genuinely don't know the root cause").
- If something is confusing about the codebase, flag it to Ali during the conversation, not just in documentation.
- If something feels risky - like a change that could have unexpected side effects elsewhere - warn Ali before proceeding.
- Never present a guess as a fact.
- If anything seems worrying or fragile, raise it proactively during the conversation. Don't wait to be asked.

**When a fix doesn't work:**
- Stop. Do not keep trying random changes.
- Document what was tried and why it didn't work in BUGS.md.
- Ask Ali how to proceed rather than escalating changes.

## Bash Command Explanations

Whenever you give the user a bash command to run, always follow it immediately with a brief explanation of what each term/part of the command means. The goal is to help the user gradually learn the command line. For example:

```bash
cd /home/alimorty/calorie_tracker && python3 -m http.server 8080
```
- `cd` - "change directory", moves you into that folder
- `/home/alimorty/calorie_tracker` - the path to the folder
- `&&` - run the next command only if the previous one succeeded
- `python3` - run Python 3
- `-m http.server` - use Python's built-in web server module
- `8080` - the port number to serve on
