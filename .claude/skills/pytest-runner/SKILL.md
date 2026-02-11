---
name: pytest-runner
description: Run pytest tests with automatic virtual environment activation. Use this skill whenever running tests, executing pytest, or when asked to "run tests", "test this", or any test execution task. Ensures venv is always activated before pytest runs.
---

# Pytest Runner

Always activate the virtualenv before running pytest. Look for `.venv` in the project directory:

```bash
source .venv/bin/activate && pytest <test-path> --reuse-db -n <N>
```

## Test Selection

Always specify which tests to run. Never run the entire suite without reason.

Run most-likely-to-fail first:
1. New/changed test file specifically
2. Entire module the changes belong to
3. Entire project (only if needed)

## `--reuse-db`

Always pass `--reuse-db` — unless you made model (database) changes beforehand, then omit it so the DB is recreated.

## Concurrency (`-n` flag)

- **1 test**: `-n0`
- **2-7 tests**: `-n` matching count (e.g. 3 tests → `-n 3`)
- **8+ tests**: omit `-n` entirely
