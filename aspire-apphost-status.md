# Saleor Aspire Python AppHost status

## Resources modeled in `apphost.py`

- `db`: PostgreSQL 15 with a persistent volume
- `cache`: Valkey 8.1 with a persistent volume
- `mailpit`: SMTP + HTTP developer mail sink
- `dashboard`: Saleor dashboard container image
- `saleor-image-build`: local `docker build` step for `.devcontainer/Dockerfile`
- `saleor-migrate`: `uv run python manage.py migrate`
- `saleor-api`: `uv run uvicorn saleor.asgi:application --reload --host 0.0.0.0 --port 8000`
- `saleor-worker`: Celery worker
- `saleor-scheduler`: Celery beat scheduler

## What was achieved

- Converted the strongest temporary Saleor AppHost shape into a checked-in **Python AppHost scaffold** for the Saleor repository.
- Preserved the second-pass refinement work from the stronger TypeScript harness:
  - local-source backend containers built from `.devcontainer/Dockerfile`
  - Aspire parameters/secrets for Saleor and Postgres settings
  - endpoint-derived runtime URLs instead of hard-coded backend hostnames
  - OTEL exporter wiring for the Saleor backend containers
- Added the supporting Python AppHost files that Aspire source currently expects:
  - `apphost.py`
  - `aspire.config.json`
  - `apphost.run.json`
  - `pylock.apphost.toml`
  - `apphost_requirements.txt`

## Current limitations

### Primary blocker: Python AppHost support in the current Aspire dev CLI build

Using Aspire CLI `13.3.0-preview.1.26221.2+b94ddc9209f110bf02934345a04361183a73cc95`:

- `aspire init --language python` fails with `Unknown language: 'python'`
- even after enabling `experimentalPolyglot:python` with `aspire config set experimentalPolyglot:python true`
- and even with an explicit `aspire.config.json` that points to `apphost.py`

`aspire run` still fails with:

```text
Unrecognized app host type.
```

That means the checked-in Python AppHost files cannot currently be executed by this dev CLI build, even though Python polyglot support exists in Aspire source and the Python code-generation package is present there.

### Secondary environment note

The Python AppHost scaffold expects Python `>=3.11` (`pylock.apphost.toml`), while the default `python3` on this machine is `3.9.6`. A separate `python3.12` executable is available, so the runtime environment would still need PATH/tooling cleanup even after the CLI-side Python AppHost blocker is fixed.

## Strongest validated result so far

The strongest validated harness remains the temporary **TypeScript AppHost** created outside this repository during evaluation. That harness successfully validated:

- local Saleor startup from local-source backend containers
- GraphQL and health endpoints
- Docker Compose publish artifact generation
- parameter/secret refactoring
- endpoint-derived URL composition
- OTEL wiring

The remaining unresolved runtime issue from that refined harness is narrower: under `aspire run`, the local-source Saleor backend containers can remain stuck in `Waiting` after dependencies are healthy, while the Python AppHost is blocked earlier at CLI recognition/discovery time.
