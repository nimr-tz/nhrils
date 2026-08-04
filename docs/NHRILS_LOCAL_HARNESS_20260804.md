# NHRILS Local Harness

Date: 2026-08-04

## Purpose

Set up the NHRILS local development harness using the official InvenioILS install guide as the governing reference, adapted to this cloned `nimr-tz/nhrils` repository.

Official reference:

- `https://invenioils.docs.cern.ch/install/`

## Official Flow

The InvenioILS guide defines this local loop:

1. install prerequisites;
2. start PostgreSQL, search, Redis, and RabbitMQ with Docker Compose;
3. run backend setup;
4. run the backend server;
5. run the Celery worker;
6. install and run the UI development server;
7. stop Docker services when finished.

## NHRILS Adaptation

This repository is already a cloned Invenio-App-ILS codebase, so we do not run `invenio-cli init ils`.

Use the repo equivalents:

| Official install step | NHRILS local command |
| --- | --- |
| Check local runtime readiness | `./scripts/local-harness preflight` |
| Start dependent services | `./scripts/local-harness start-services` |
| Build static assets and setup backend | `./scripts/local-harness setup-backend` |
| Build static assets only | `./scripts/local-harness build-assets` |
| Run backend server | `./scripts/local-harness run-backend` |
| Run Celery worker | `./scripts/local-harness run-worker` |
| Stop services | `./scripts/local-harness stop-services` |
| Check services | `./scripts/local-harness status` |

## Prerequisites

Required locally:

- Python 3.10 through `.venv`;
- Node.js 14.x for repeatable asset builds;
- Docker with Compose v2;
- enough memory for OpenSearch;
- local ports available: `5432`, `6379`, `5672`, `9200`, `9300`, and optionally `15672`.

The repository pins local runtime intent with:

- `.python-version`: `3.10`;
- `.nvmrc`: `14.21.3`;
- `.node-version`: `14.21.3`.

Create the Python environment first:

```bash
./scripts/setup-test-venv
```

Then check the local harness state:

```bash
./scripts/local-harness preflight
```

The preflight is a developer readiness check. It fails for missing hard
requirements such as the Python virtual environment, `invenio-app-ils`, Docker,
or Docker Compose v2. It warns for recoverable development gaps such as stopped
services, missing assets, or a Node version that differs from the official
InvenioILS Node 14 expectation.

## Start Services

```bash
./scripts/local-harness start-services
./scripts/local-harness status
```

Services started:

- PostgreSQL 14;
- OpenSearch 3.2.0;
- Redis 6;
- RabbitMQ 3 management image.

OpenSearch should become available at:

```text
http://127.0.0.1:9200
```

## Backend Setup

After Docker services are healthy:

```bash
./scripts/local-harness setup-backend
```

This first delegates to the existing asset builder:

```bash
ils collect -v
ils webpack buildall
```

Then it delegates to the existing `./scripts/setup`, which runs:

```bash
ils setup --verbose
```

This is local development setup only. Do not use it against shared, staging, or production services.

If browser routes fail with a missing `static/dist/manifest.json`, rerun:

```bash
./scripts/local-harness build-assets
```

## Run Backend

```bash
./scripts/local-harness run-backend
```

The backend uses the repo's existing self-signed certificate command and should be available at:

```text
https://127.0.0.1:5000
```

Accept the local self-signed certificate warning in the browser.

## Run Worker

In a second terminal:

```bash
./scripts/local-harness run-worker
```

This delegates to the existing Celery worker command:

```bash
celery -A invenio_app.celery worker -l INFO
```

## Test Levels

No-service checks:

```bash
./scripts/local-harness test-local
```

Service-backed pytest is deliberately separated from the seeded runtime harness:

```bash
./scripts/local-harness test-services
```

That command explains why it does not execute pytest directly after `setup-backend`.
The local runtime setup creates seeded database rows and OpenSearch indexes. The
pytest service fixtures expect clean database/search state and will fail with
duplicate indexes or records if they are pointed at the seeded runtime.

Full API tests:

```bash
./run-tests.sh ils
```

The full API command uses `docker-services-cli` and manages service lifecycle itself.

## Current Harness Fix

The local Compose file previously referenced:

```text
opensearchproject/opensearch::3.2.0
```

The image reference has been corrected to:

```text
opensearchproject/opensearch:3.2.0
```

## Troubleshooting

If tests fail with OpenSearch connection errors:

1. run `./scripts/local-harness status`;
2. confirm `search` is running;
3. check `docker compose -f docker-compose.yml logs search`;
4. confirm the host can reach `http://127.0.0.1:9200`;
5. ensure port `9200` is not already occupied by another search service.

If OpenSearch exits immediately, check available memory and Docker resource limits.

If backend setup fails after a previous partial setup, stop services and inspect the local database volume before deleting anything. Do not run destructive cleanup without confirming what will be removed.

## Verification on 2026-08-04

Completed locally:

- `docker compose -f docker-compose.yml config` renders a valid Compose model.
- `./scripts/local-harness start-services` pulled and started PostgreSQL, OpenSearch, Redis, and RabbitMQ.
- `./scripts/local-harness setup-backend` completed successfully and seeded demo users, pages, vocabularies, records, and indexes.
- `./scripts/local-harness build-assets` completed successfully and created the webpack manifest.
- `curl -fsS http://127.0.0.1:9200` returned OpenSearch `3.2.0`.
- `curl -k -I https://127.0.0.1:5000/nhrils/catalogue` returned `200 OK` while the development server was running.
- `./scripts/local-harness test-local` passed: `3 passed, 2 deselected`.

Observed warnings:

- Webpack/npm reported upstream dependency deprecation and audit warnings from the Invenio asset stack.
- Current local Node was `v24.14.1`; the official InvenioILS guide lists NodeJS v14. The asset build still completed, but the project should use a pinned Node runtime for repeatable development and CI.
