---
name: saleor-pr-checklist
description: Final self-review gate before opening or updating a Saleor pull request — CHANGELOG placement, pre-commit, schema regen, and a pass over the review standards that reviewers most often enforce. Use when finishing a change and about to request review.
---

# Saleor PR checklist

Run this before opening or updating a PR. It catches the process/hygiene issues and the recurring
review comments that otherwise cost a round trip. (For schema-specific and migration-specific work,
also use `saleor-graphql-api-change` and `saleor-migrations`.)

## Process gate

- **Run pre-commit** and fix everything it flags (formatting, lint, mypy). PRs regularly bounce for
  this alone.
- **Ensure new/changed tests pass locally** before requesting review (see AGENTS.md
  for how to run tests).
- Remove debug/test scaffolding (stray `str(...)` casts, prints, unused imports).
- If you touched the GraphQL schema, **regenerate `schema.graphql`**.
- For dependency changes, use the pinned `uv` version and change only the target dependency so
  `uv.lock` doesn't churn.

## CHANGELOG

- Add an entry **under the correct section/heading** — don't blind-append to the end of the file.
- **Never add or edit a CHANGELOG entry for an already-released version.** Released fixes surface via
  the release description; a re-added entry is noise. (This is a frequent porting mistake.)
- Keep the changelog diff scoped to your change — don't drop unrelated entries. Proofread the prose.
- Add a migration-guide entry for any behavior change that could be breaking for some API consumers,
  even one intended as a feature.

## Self-review against the standards reviewers enforce

Skim your own diff for the top recurring review comments (all detailed in AGENTS.md):

- **Tests:** exact-value assertions (no `> 0` / `assert not errors`); negative tests assert the side
  effect didn't happen; no asserting a value the test just set; design tests so a shared input can't
  mutate the expected value, rather than papering over it with an expensive `copy.deepcopy`; real
  fixtures over mocked internals; the fix has a regression test reproducing the *real* bug.
- **Layering:** business logic in the domain layer, not the mutation; no `graphql`-layer imports from
  non-GraphQL code; validate at the point of production.
- **DB / scaling:** no N+1 in loops; bulk `update`/`delete`; only-needed columns; `on_commit` for task
  scheduling; no blocking in request threads.
- **Naming:** no cryptic abbreviations; positive booleans; `legacy_` prefix on deprecated-behavior flags.
- **Error handling:** specific exceptions (not bare `Exception`); retryable vs terminal distinguished;
  precise, field-attributed messages.
- **Dead code / types:** delete code a refactor made dead; fix types at the source instead of `cast()`.

## PR description

- Explain *why*, and for anything non-obvious (a deprecation path, a deferred cleanup, a concurrency
  decision) state it explicitly so a reviewer doesn't have to ask.
- Link tracked follow-up issues for any deferred work (column drops, legacy removals).
