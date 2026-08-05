# NHRILS GitHub Actions and Error Reporting Review

Date: 2026-08-05

## Purpose

Review how nearby NIMR applications automate deployment and report errors so NHRILS can adopt the same operating model before container/image build work and the future `platform-gitops` pull request.

This is an assessment and planning artifact. It does not add or modify workflows, secrets, deployment manifests, or runtime error handlers.

## Evidence Reviewed

NHRILS current workflows:

```text
.github/workflows/tests.yml
.github/workflows/pypi-release.yml
```

Local NIMR workflow references:

```text
/home/jmduda/KodeX.2026/lims/.github/workflows/build-and-deploy.yml
/home/jmduda/KodeX.2026/nimr-billing/.github/workflows/build-and-deploy.yml
/home/jmduda/KodeX.2026/lims/.scratch/platform-gitops/.github/workflows/redeploy-notify.yml
```

Local runtime alerting references:

```text
/home/jmduda/KodeX.2026/lims/config/settings.py
/home/jmduda/KodeX.2026/mtafiti/docs/operations-dashboards-alerts.md
/home/jmduda/KodeX.2026/mtafiti/docs/operations-runbooks.md
/home/jmduda/KodeX.2026/nhrils/invenio_app_ils/config.py
/home/jmduda/KodeX.2026/nhrils/invenio_app_ils/notifications/backends/mail.py
```

## Current NHRILS State

NHRILS still has upstream-oriented workflows:

- `tests.yml`: runs upstream test chunks against Python 3.9, PostgreSQL 14, and OpenSearch 2.
- `pypi-release.yml`: publishes package releases through upstream Invenio workflows on `v*` tags.

These are not enough for NIMR deployment because they do not:

- build GHCR deployment images;
- push backend/frontend images;
- update `nimr-tz/platform-gitops`;
- notify deployment outcome;
- validate production build arguments;
- record immutable image tag/digest evidence.

## Patterns Observed

### LIMS

The LIMS workflow:

- triggers on pushes to `main` or `master` and manual dispatch;
- builds a Docker image using Buildx;
- pushes to GHCR;
- tags image as `sha-<short-sha>`;
- updates `clusters/msmt-02/research/lims/kustomization.yaml` in `platform-gitops`;
- supports GitHub App credentials for GitOps writes and token fallback;
- commits the GitOps image update directly to `platform-gitops` main;
- sends a deployment result email when SMTP secrets exist.

Limitations to avoid copying directly:

- the GitOps update uses text processing for a Kustomize image tag; NHRILS uses Helm values, so the update command must target `values.invenio.yaml` safely;
- SMTP notification is optional in LIMS, so a missing notification path can silently skip emails.

### NIMR Billing

The NIMR Billing workflow is the stronger pattern:

- has explicit `run-name`;
- uses concurrency to prevent overlapping deploys;
- computes both `image_tag` and `image_ref`;
- captures image digest from `docker/build-push-action`;
- uses Buildx cache;
- validates GitOps authentication before checkout;
- writes richer GitOps commit messages with source commit and workflow URL;
- records build, GitOps, and notification summaries in the GitHub Actions step summary;
- validates SMTP notification secrets before emailing;
- includes app URL, image digest, GitOps commit, changed files, and workflow URL in the notification email.

This is the best primary model for NHRILS.

### Platform GitOps

The platform-gitops notification workflow:

- triggers on changes under `clusters/**`, `templates/**`, `bootstrap/**`, and workflow files;
- summarizes changed files, commits, and impacted app areas;
- sends a separate GitOps change email;
- uses `continue-on-error` for email send so notification failure does not block the GitOps repository workflow.

This should remain separate from NHRILS application deployment notification. NHRILS should notify that an application image and GitOps tag update happened; platform-gitops should notify that cluster desired state changed.

## Error Reporting Findings

### CI/CD Notification Is Not Runtime Error Reporting

GitHub Actions email tells us whether build, push, and GitOps update succeeded. It does not detect:

- web request exceptions;
- API 500 errors;
- worker task failures;
- queue backlog;
- OpenSearch/database/broker connectivity failures;
- mail delivery failures inside the application;
- login or staff access failures.

NHRILS needs both:

- GitHub Actions deployment notifications;
- in-cluster runtime error reporting and observability.

### LIMS Runtime Error Pattern

LIMS uses environment-driven email configuration and Django's `AdminEmailHandler` for request/security errors when `DEBUG=False`.

Reusable principle:

- keep SMTP values environment-driven;
- log errors to console and notify admins;
- only send admin email outside debug mode.

NHRILS is Flask/Invenio, not Django, so it cannot copy `AdminEmailHandler`. It should implement equivalent Flask/Invenio logging behavior only after approval.

### Mtafiti Operational Pattern

Mtafiti documents operational dashboards, severity levels, alert thresholds, and alert-to-runbook mapping.

Reusable principle:

- alerts should map to clear runbooks;
- payloads should include route/task labels and top failing dimensions;
- runtime health should cover web, worker, queue, dependency, and auth failures.

### NHRILS Current Mail Defaults

NHRILS currently has development/upstream defaults such as:

- `MAIL_SUPPRESS_SEND = True`;
- upstream sender defaults;
- notification backend driven by InvenioILS config;
- account email sender configured through Invenio security settings.

Production deployment must override these through reviewed runtime configuration. Do not assume emails will work until a smoke test confirms account, request, notification, and error paths.

## Recommended NHRILS Automation Model

NHRILS should adopt three separate automation layers.

## 1. Pull Request CI

Keep PR validation separate from deployment.

Recommended jobs:

- Python tests using the local harness where feasible;
- seed data validation;
- static catalogue shell tests;
- optional backend service test with PostgreSQL, Redis, RabbitMQ, and OpenSearch;
- frontend asset/build validation when frontend files change.

Recommended command mapping:

```bash
./scripts/local-harness preflight
./scripts/local-harness test-local
./scripts/local-harness validate-seed
./scripts/local-harness seed-dry-run
```

For service-affecting changes:

```bash
./scripts/local-harness test-services
```

## 2. Build, Deploy, and Notify Workflow

Use the NIMR Billing workflow as the base pattern.

Recommended NHRILS workflow shape:

- trigger on `main` after PR merge and `workflow_dispatch`;
- use `concurrency` per branch;
- permission scope: `contents: read`, `packages: write`;
- build backend image `ghcr.io/nimr-tz/nhrils:sha-<short-sha>`;
- build frontend image only if the separate frontend image remains in use;
- pass production frontend build args:
  - `REACT_APP_INVENIO_UI_URL=https://nhrils.apps.nimr.or.tz`;
  - `REACT_APP_INVENIO_REST_ENDPOINTS_BASE_URL=https://nhrils.apps.nimr.or.tz/api`;
  - `REACT_APP_ENV_NAME=production`;
- capture image digest(s);
- checkout `nimr-tz/platform-gitops` using GitHub App credentials first and PAT fallback only if approved;
- update only NHRILS image tag fields in `clusters/msmt-02/research/nhrils/values.invenio.yaml`;
- validate the changed GitOps file contains the expected tag;
- run the platform render/dry-run command once confirmed from `platform-gitops`;
- commit with source repo, source SHA, workflow URL, and image digest;
- email build/deploy outcome with app URL, image tag, digest, GitOps commit, changed files, and workflow URL.

Use structured YAML-aware editing for `values.invenio.yaml` when practical. Avoid brittle global text replacement that could update the wrong `tag` field once frontend/backend images both exist.

## 3. Platform GitOps Notification

Keep platform-gitops' own notification workflow active as the cluster-level audit signal.

NHRILS should not duplicate the platform-gitops notification logic. Instead:

- NHRILS workflow reports source build and GitOps update result;
- platform-gitops workflow reports desired-state changes across the cluster;
- ArgoCD remains the source of truth for sync/health after the GitOps commit.

## Recommended Runtime Error Reporting Model

Runtime error reporting should be implemented separately from GitHub Actions.

Initial production approach:

- keep all application logs on stdout/stderr for cluster log collection;
- add readiness and health smoke checks for web and worker;
- configure mail through approved in-cluster relay settings;
- add a Flask/Invenio exception logging handler only after approval;
- include request path, method, user/anonymous marker, pod name, image tag, exception type, and traceback;
- add deduplication to avoid repeated identical emails;
- define a controlled test command or endpoint for sending one test alert;
- document runbooks for:
  - web/API 5xx;
  - worker task failure;
  - queue backlog;
  - database unavailable;
  - OpenSearch unavailable;
  - mail delivery failure;
  - login/access failure.

Recommended email policy:

- GitHub Actions: use external SMTP credentials available to GitHub runners.
- Runtime app inside cluster: use the approved in-cluster relay, likely EGA SMTP, without authentication if NIMR confirms the same network policy used by other apps.

Do not use GitHub Actions SMTP credentials as runtime application SMTP credentials.

## Secrets Required For NHRILS Workflow

Recommended repository secrets:

```text
GHCR_TOKEN
PLATFORM_GITOPS_APP_ID
PLATFORM_GITOPS_APP_PRIVATE_KEY
PLATFORM_GITOPS_TOKEN
SMTP_SERVER
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM
DEPLOY_NOTIFY_TO
```

Preferred GitOps authentication:

1. GitHub App with access only to `nimr-tz/platform-gitops`;
2. PAT fallback only if the GitHub App cannot be configured.

`DEPLOY_NOTIFY_TO` should be a configurable recipient list. Avoid hard-coding a personal email in the final NHRILS workflow.

## Required Follow-Up Slices

1. **Workflow Requirements and ADR**
   - Decide backend-only vs backend+frontend image build.
   - Decide GitHub App vs PAT fallback.
   - Decide whether missing SMTP should fail deploy notification or only warn.
   - Decide exact GitOps render validation command.

2. **Implement NHRILS Build Workflow**
   - Add `.github/workflows/build-and-deploy.yml`.
   - Keep it disabled/manual or branch-gated until platform secrets exist.
   - Add structured tag update for `values.invenio.yaml`.

3. **Implement Runtime Error Reporting**
   - Add approved Flask/Invenio logging integration.
   - Add tests for enabled/disabled error alert config.
   - Add a smoke-test command for a controlled alert.

4. **Add Operations Runbook**
   - Document alert severity, triage, verification, and rollback.
   - Link alerts to dashboard/log queries once cluster tooling is confirmed.

## Recommendation

Adopt the NIMR Billing workflow structure for NHRILS, not the older LIMS workflow, because it has stronger concurrency, summaries, digest capture, authentication validation, and notification validation.

Keep the platform-gitops notification workflow as a second independent audit signal.

Treat runtime error reporting as a separate Invenio application feature, not as a GitHub Actions feature.
