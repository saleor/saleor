---
name: saleor-commit
description: Commit changes in the Saleor codebase with pre-commit hook error handling. Use when asked to "commit", "commit changes", "make a commit", or any git commit task in the Saleor project. Handles virtual env activation, staging, commit message writing, and automatic resolution of pre-commit hook failures (ruff, mypy, schema, migrations).
---

# Saleor Commit

## Workflow

1. Activate virtual env: `source .venv/bin/activate` (look for `.venv` dir in project root)
2. Run `git status` and `git diff` (staged + unstaged) to understand all changes
3. Stage relevant files with `git add` (specific files, not `git add -A`)
4. Write a comprehensive commit message describing what changed and why
5. Run `git commit`
6. If pre-commit hooks fail, follow error resolution below and retry

## Commit Message Format

Use a HEREDOC for the message:

```bash
git commit -m "$(cat <<'EOF'
Short summary of changes

Detailed description of what was changed and why.
List specific modifications when multiple files are affected.

EOF
)"
```

## Pre-commit Hook Error Resolution

The project runs these hooks: trailing-whitespace, end-of-file-fixer, ruff (lint + format), mypy, deptry, semgrep, uv-lock, migrations-check, gql-schema-check.

### Ruff errors (lint/format)

Ruff auto-fixes and auto-formats on commit. After a failure:
1. Stage the auto-formatted files: `git add <files>`
2. Retry the commit
3. If it fails again, read the error output — some issues require manual fixes (unused imports, type annotations, etc.)

### Mypy errors

Read the error output carefully. Fix the typing issues in the reported files. Stage and retry.

### Outdated GraphQL schema (`gql-schema-check`)

Regenerate the schema and stage it:
```bash
python manage.py get_graphql_schema > saleor/graphql/schema.graphql
git add saleor/graphql/schema.graphql
```

### Missing migrations (`migrations-check`)

Create the missing migration:
```bash
python manage.py makemigrations
git add saleor/**/migrations/*.py
```

### Other hooks

- **trailing-whitespace / end-of-file-fixer**: Auto-fix applied. Stage changed files and retry.
- **deptry**: Fix dependency issues in pyproject.toml.
- **semgrep**: Read the finding, fix the flagged code pattern.
- **uv-lock**: Stage the updated `uv.lock` file.
