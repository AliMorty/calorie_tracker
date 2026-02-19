# Open Problem: Agent Scope Creep and Silent Overconfident Changes

**Discovered:** Session 005 (Feb 19, 2026)
**Context:** Bug #2 - the request was "swap the order of two sections." The agent removed section labels, restructured the panel, and changed hiding logic instead.

---

## What happened

Ali reported that in the Add Food panel, the "RECENT" section appeared above "ALL FOODS" and wanted them swapped. That was the entire request.

Over two attempts, the previous agent:
1. Added a `.hidden` CSS rule (unrelated to the ordering problem)
2. Swapped the DOM order (correct) but also removed the "ALL FOODS" and "RECENT" section headings and added logic to hide the recent section during search (neither was requested)

The result was a flat, unlabeled list that mixed recent and search results together with no visual separation. The UI was worse than before the "fix."

The actual fix was two lines: add back the "All Foods" heading, and remove the unwanted hiding logic.

## Why this is an open problem

This is not a factual hallucination (the agent didn't claim something false). It is a **behavioral hallucination** - the agent silently expanded the scope of the task and made confident UX decisions that nobody asked for. Specifically:

- It decided section headings should be removed (never requested)
- It decided the recent section should hide during search (never requested)
- It made these decisions without asking, and presented them as part of the "fix"
- Each individual change looked reasonable in isolation, which made it hard to catch

This pattern is dangerous because:
- The agent appears to be working correctly (it commits, it explains, it sounds confident)
- The extra changes are bundled with the real fix, making it hard to separate good from bad
- The user only discovers the damage when testing, by which point multiple things have changed

## What we are doing about it

We added rules to CLAUDE.md:
- "Do not remove, rename, or restructure UI elements that are not part of the bug report"
- "After making a change, re-read your diff and ask yourself: did I change anything that was not requested?"

These rules help. They reduce the frequency. But they do not eliminate the problem. An agent that is prone to scope creep may also be prone to not following scope-creep rules consistently. This is fundamentally a model behavior issue, not just a prompting issue.

## Status: OPEN

We do not have a permanent fix for this. Guardrail rules in CLAUDE.md are the best mitigation we have right now. If better approaches are discovered, update this file.

---

## Related

- `issue_documentations/BUGS.md` - Bug #2 full history showing the three attempts
- `insights/collaborative_debugging.md` - related insight about agent-human collaboration
