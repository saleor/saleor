---
name: port-changes
description: Port a change (PR or branch) onto the currently checked-out Saleor branch — forward-port UP (3.22 → 3.23 → main) or backport DOWN (main → 3.23 → 3.22). Use when asked to port, forward-port, backport, or cherry-pick a change to this branch/version.
---

# Porting a change onto this branch

**One run = one port, onto the branch already checked out.** The current branch is the destination —
never switch, create, or rename branches, and never chain hops. A multi-hop port
(`3.22 → 3.23 → main`) is separate runs on separate workspaces; if the user asks for more than one
hop, do the one that matches this branch and tell them to ask again on the next branch.

## 1. Establish source and direction

- The user points at a PR (`gh pr view <n> --json baseRefName,files`, `gh pr diff <n>`) or a branch.
- Source = where the change was **originally authored** (PR base). Destination = the current branch
  (`git branch --show-current`; `main` is the next unreleased version — check
  `# 3.X.0 [Unreleased]` at the top of `CHANGELOG.md`).
- **UP (forward-port):** source older than destination (`3.22` → `3.23`/`main`).
- **DOWN (backport):** source newer than destination (`main` → `3.23`).
- State the direction you inferred in your first message, so a wrong guess is caught early.

## 2. GraphQL: pin to the oldest version that ships it

The `ADDED_IN_*` marker names when the field/mutation first became available, not which branch you
are editing. Constants live in `saleor/graphql/core/descriptions.py`.

- A change first released in 3.22 keeps `ADDED_IN_322` here too, even on `main`.
- A DOWN port to a version older than the marker makes the field ship earlier than the marker
  claims — use the older version's marker here, and tell the user the source branch's marker needs
  the same correction (don't go edit it yourself).
- If the introducing version is ambiguous, **ask the user**. Don't guess.
- Regenerate `saleor/graphql/schema.graphql` — see `saleor-graphql-api-change`.

## 3. Migrations: keep the oldest branch's identity, merge on top

Migration numbering diverges per branch, so a straight cherry-pick produces a broken graph.

- The migration keeps the **file name and number it has on the oldest branch that ships it** —
  never renumber or rewrite a migration that already shipped.
- On an UP port, if that number now collides with migrations that landed only here, resolve the two
  leaves with a **merge migration** (`python manage.py makemigrations --merge`) — see existing
  `*_merge_*.py` files for the shape.
- On a DOWN port where this branch is now the oldest to ship it, pick the number that fits here and
  tell the user the newer branches must reuse this name.
- Zero-downtime rules still apply: `CREATE INDEX CONCURRENTLY` in its own `atomic = False`
  migration, schema and data migrations split. See `saleor-migrations`.

## 4. CHANGELOG: only on the branch that introduces the change

- Edit `CHANGELOG.md` **only if this branch is the first release to ship the change**.
- UP port of something already released in 3.23 → **no CHANGELOG edit here**; it was already
  announced.
- DOWN port → add the entry here (this release now introduces it) and tell the user to drop it from
  `main`'s `[Unreleased]` section.
- `main`'s CHANGELOG is edited only when the change debuts in `[Unreleased]` and is not backported.

## 5. Before finishing

- Tests for the ported code pass (`pytest --reuse-db <paths>`, see `pytest-runner`).
- Schema file regenerated if GraphQL changed; `pre-commit` clean.
- If this branch lacks a dependency the source relied on, **stop and report it** — don't invent a
  partial port.
- Report anything the user must fix on the other branches (marker corrections, migration names,
  CHANGELOG moves) — you are not touching those branches.

Do not push. Commit only if explicitly asked.
