# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

This is a **single-context** repo — one `CONTEXT.md` and one `docs/adr/` at the repo root.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — the project's glossary / ubiquitous language.
- **`docs/adr/`** — read the ADRs that touch the area you're about to work in.

If any of these files don't exist yet, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-<decision>.md
│   └── 0002-<decision>.md
└── saleor/            ← application code
```

## ADR tags

Every ADR carries a `**Tags:**` line directly under its title — a short, comma-separated list of the areas it relates to (e.g. `gift card`, `security`, `concurrency`, `checkout`). Tags are for discovery: use them to find the ADRs that touch the area you're about to work in, rather than reading every file.

- When you add a new ADR, give it tags.
- Reuse existing tag names where one fits; only coin a new tag when nothing existing applies.
- Prefer stable, area-level tags (a domain like `gift card`, or a cross-cutting concern like `security`) over narrow, one-off labels.

ADRs describe **business / high-level decisions and their rationale** — why a choice was made and what the alternative would have cost. Keep implementation detail out; it goes stale and lives in the code. Include a code reference only when it is essential to understand the decision.

## Use the glossary's vocabulary

When your output names a domain concept (in a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (…) — but worth reopening because…_
