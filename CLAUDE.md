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
