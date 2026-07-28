# Issue tracker: none (opted out)

This repo does **not** use an agent-driven issue tracker. The maintainer has opted out of issue tracking for the engineering skills.

## What this means for skills

- Skills that would normally read from or write to an issue tracker (`to-issues`, `triage`, `to-prd`, `qa`, etc.) must **not** create issues, PRDs, or triage records anywhere — not on GitHub, not under `.scratch/`, not in any external tool.
- When a skill's workflow says "publish to the issue tracker" or "fetch the relevant ticket", treat that step as **not applicable**. Do the underlying work (e.g. produce the analysis, the plan, the fix) and return it directly in the conversation instead of persisting it as an issue.
- Do not prompt the user to set up an issue tracker. If issue tracking is wanted later, re-run `/setup-matt-pocock-skills`.

## Triage

Because there is no issue queue, the triage state machine and its label vocabulary do not apply. There is no `docs/agents/triage-labels.md`.
