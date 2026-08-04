# NHRILS Development Environment

Date: 2026-08-04

## Python Version Decision

Use Python 3.10 for the project virtual environment.

Do not use the latest local/default Python automatically. On the current workstation, `python3` resolves to Python 3.14.4, while this Invenio-App-ILS codebase declares `python_requires >=3.8` and depends on the Invenio 3.x generation. Python 3.14 is too new to assume compatibility with the pinned Invenio, Flask, SQLAlchemy, pytest, and OpenSearch-related packages.

Python 3.10 is the conservative baseline because:

- it is available locally as `python3.10`;
- it satisfies `python_requires >=3.8`;
- it is more likely to work with the current Invenio dependency generation than Python 3.14;
- it gives us a stable test target while the deployment image is still based on CERN's Invenio AlmaLinux image.

Record this in `.python-version` and use `.venv` locally.

## Local Venv

Create the environment:

```bash
./scripts/setup-test-venv
```

Or manually:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[tests,opensearch2,lorem]"
```

Run focused tests:

```bash
source .venv/bin/activate
python -m pytest tests/test_catalogue_shell.py tests/test_post_logout_redirect.py
```

Run service-backed API tests:

```bash
source .venv/bin/activate
./run-tests.sh ils
```

`run-tests.sh` starts PostgreSQL, OpenSearch, Redis, and RabbitMQ through `docker-services-cli`; Docker must be available.

## Current Local State

A local `.venv` was created with:

```text
Python 3.10.20
```

Dependency installation was not run automatically in this slice because it can be network-heavy. Run `./scripts/setup-test-venv` when ready to install the full test dependencies.

## Rules

- Do not commit `.venv`.
- Do not use `python3` unless it resolves to the agreed baseline.
- Prefer `python3.10`, `.venv/bin/python`, or an explicitly documented deployment image Python.
- Revisit the baseline only after building and testing the full dependency set.
