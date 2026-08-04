# NHRILS Customization Slice: Catalogue Defaults

Date: 2026-08-04

## Task Classification

Frontend and catalogue content customization.

This slice affects the public catalogue help surface and frontend image build configuration. It does not change authentication, permissions, database schema, OpenSearch mappings, circulation policy, patron data, or deployment manifests.

## Product Requirements

- The catalogue should read as a NIMR National Health Research Integrated Library System, not as an upstream InvenioILS or CERN demo.
- Search help should use health research examples that match likely NIMR library users: researchers, librarians, students, programme teams, and institutional stakeholders.
- Production-facing frontend builds must not hardcode localhost API or UI endpoints.
- The change should preserve existing InvenioILS search syntax and field names.

## UX Description

The search guide remains a practical reference page. Copy should be plain, task-oriented, and domain-appropriate:

- use public health, malaria, maternal health, clinical trial, guideline, and health policy examples;
- avoid physics/CERN examples in visible instructional copy;
- explain query operators without implying custom NHRILS search semantics that do not exist yet.

## Accessibility Checklist

- Preserve semantic headings.
- Preserve links with visible query examples.
- Preserve code formatting for query syntax.
- Avoid introducing visual-only instructions.
- Avoid removing the field reference table used by advanced users.

## Acceptance Criteria

- Search guide introduction mentions NHRILS and health research resources.
- Search guide examples no longer use visible CERN/physics demo terms.
- Frontend Docker build uses configurable build arguments for UI URL, API URL, and environment name.
- Focused static checks pass.

## Artifact Readiness

References inspected:

- `docs/NHRILS_CATALOGUE_MVP_20260804.md`
- `docs/NHRILS_UX_DESIGN_SYSTEM_20260804.md`
- `docs/NHRILS_INITIAL_CUSTOMIZATION_AND_ROLLOUT_PLAN.md`
- `invenio_app_ils/static_pages/search_guide.html`
- `docker/frontend/Dockerfile`

Approval gates:

- No authentication change.
- No permission change.
- No schema or index change.
- No deployment execution.
- Frontend build defaults are made configurable for the planned deployment host.

## Verification Plan

- Run Python syntax compilation for touched test/content-adjacent files where applicable.
- Run static grep checks to confirm no upstream demo terms remain in the search guide.
- Run focused tests if the local virtual environment dependencies are available; otherwise record the environment blocker.

## Verification Summary

Completed:

- `PYTHONPYCACHEPREFIX=/tmp/nhrils_pycache python3 -m py_compile tests/test_catalogue_shell.py`
- `git diff --check`
- static grep check for frontend build args in `docker/frontend/Dockerfile`
- static grep check for NHRILS health research examples in `invenio_app_ils/static_pages/search_guide.html`
- static grep check for removed demo terms: `dark matter`, `Albert Einstein`, `affiliated to CERN`, `CHEP`, `collision theory`, `crab cavit`, `physletb`, and `Nucl. Instrum`

Not completed:

- `pytest tests/test_catalogue_shell.py -q` did not run because the local `.venv` does not yet contain pytest/test dependencies. The test environment setup script exists, but dependency installation is intentionally deferred because it requires network-heavy package installation.

## Render Evidence

No browser screenshot was captured in this slice because the local Invenio runtime is not installed yet. The visible search-guide customization was verified by static content checks and a regression test added to `tests/test_catalogue_shell.py`.
