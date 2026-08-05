# NHRILS Kubernetes and GitOps Deployment Readiness

Date: 2026-08-04

## Purpose

Define the deployment documentation baseline for running NHRILS under the NIMR Kubernetes cluster managed from:

```text
git@github.com:nimr-tz/platform-gitops.git
```

Canonical application domain:

```text
nhrils.apps.nimr.or.tz
```

This document is a readiness and runbook baseline. It does not authorize manual cluster changes, secret commits, production cutover, or direct changes in the GitOps repository without a separate reviewed implementation task.

## Current Deployment Decision

NHRILS should be deployed as one product boundary for the first release:

- application source: `nimr-tz/nhrils`;
- cluster configuration: `nimr-tz/platform-gitops`;
- canonical host: `nhrils.apps.nimr.or.tz`;
- public catalogue route: `/nhrils/catalogue`;
- backoffice and authenticated staff routes under the same host unless a later architecture decision separates them.

The first deployment should prove the catalogue, search, record detail, branded public pages, seed review path, and basic staff access. Circulation, acquisitions, integrations, and full digital object workflows remain later phases unless explicitly brought into scope.

## Domain Strategy

Use `nhrils.apps.nimr.or.tz` as the canonical host for the first release.

The catalogue should initially live under the same host, for example:

```text
https://nhrils.apps.nimr.or.tz/
https://nhrils.apps.nimr.or.tz/nhrils/catalogue
https://nhrils.apps.nimr.or.tz/search
```

Do not start with `catalogue.nhrils.apps.nimr.or.tz`.

Reasoning:

- NHRILS is the product; catalogue discovery is the first major capability, not a separate product.
- One host simplifies TLS, cookies, OAuth/session handling, CORS, API URLs, search links, and user support.
- InvenioILS already expects one UI/API application boundary, with the React catalogue frontend and REST API configured against a base host.
- A separate catalogue subdomain adds routing and certificate work without solving a current problem.

Reserve a catalogue subdomain only if a future architecture requires one of these:

- a separately deployed public catalogue frontend;
- a public discovery portal isolated from staff/backoffice traffic;
- a communications requirement for a short public URL;
- different authentication/cookie/CORS boundaries;
- different scaling, caching, or CDN behavior for public search.

If that future need appears, prefer:

```text
catalogue.nhrils.apps.nimr.or.tz
```

as an alias or separate frontend host, while keeping `nhrils.apps.nimr.or.tz` as the canonical system host.

## GitOps Target

Expected GitOps structure:

```text
clusters/msmt-02/research/nhrils/
  namespace.yaml
  values.invenio.yaml
  values.frontend.yaml
  kustomization.yaml
  overrides/
```

Exact structure must follow existing conventions in `nimr-tz/platform-gitops`, especially the current Invenio deployment pattern used by NHRDM.

Source-side skeleton guidance is documented in `docs/NHRILS_GITOPS_SKELETON_20260805.md`. Treat that file as a blueprint for the future GitOps PR, not as a substitute for checking the current `platform-gitops` main branch.

All cluster state must be owned by GitOps. Avoid manual pod edits, hand-applied manifests, or one-off shell fixes except for approved break-glass recovery. If a running-pod change is needed during diagnosis, convert it into a GitOps change before considering the issue resolved.

## Ownership Boundary

The NHRILS repository owns:

- application source code;
- Dockerfiles and build-time defaults;
- catalogue frontend customizations;
- static public pages;
- seed data and seed validation scripts;
- local harness scripts and tests;
- deployment readiness documentation.

The `platform-gitops` repository owns:

- namespace, ingress, TLS, and service exposure;
- deployment chart or manifests;
- image tag pins;
- ConfigMaps and non-secret runtime values;
- Kubernetes Secret references;
- ExternalSecret, SealedSecret, or equivalent secret wiring;
- storage classes, PVCs, and backup integration;
- environment-specific overrides.

Do not duplicate environment-specific cluster configuration in the application repo.

## Runtime Components

NHRILS requires:

- backend web application running the Invenio application;
- worker/Celery process for asynchronous work;
- scheduler/beat process if enabled by the final chart values;
- optional separate frontend/nginx container while the React InvenioILS frontend remains separate;
- PostgreSQL;
- Redis;
- RabbitMQ;
- OpenSearch;
- Kubernetes secrets for stable Invenio keys/salts;
- persistent file/object storage if electronic files, covers, attachments, exports, or uploads are enabled;
- email relay if account, request, or notification mail is enabled;
- TLS ingress for `nhrils.apps.nimr.or.tz`.

The current local harness uses PostgreSQL, Redis, RabbitMQ, and OpenSearch through Docker Compose. Production must not rely on local harness defaults.

## Image Strategy

Use GHCR under the NIMR organization:

```text
ghcr.io/nimr-tz/nhrils:<git-sha>
ghcr.io/nimr-tz/nhrils-frontend:<git-sha>
```

Use a separate frontend image only while the repository still builds the React frontend from `docker/frontend/Dockerfile`.

Every deployable image must be pinned by immutable Git SHA or digest in GitOps. Do not deploy mutable tags such as `latest` to the cluster.

Recommended source-to-cluster flow:

1. Merge a reviewed application change into the approved source branch.
2. Build backend and frontend images from that exact commit.
3. Push images to GHCR.
4. Update only the NHRILS image pin(s) in `platform-gitops`.
5. Run the GitOps render/validation command used by the platform repository.
6. Merge the GitOps change.
7. Let the GitOps controller apply the deployment.

## Required Configuration

Production values must override development defaults:

```text
INVENIO_THEME_SITENAME=NHRILS
INVENIO_SEARCH_INDEX_PREFIX=nhrils-
REACT_APP_INVENIO_UI_URL=https://nhrils.apps.nimr.or.tz
REACT_APP_INVENIO_REST_ENDPOINTS_BASE_URL=https://nhrils.apps.nimr.or.tz/api
REACT_APP_ENV_NAME=production
```

Do not allow production-facing builds to call `https://127.0.0.1` for frontend or API requests.

The repository currently exposes frontend build arguments in `docker/frontend/Dockerfile`. Backend runtime configuration must be verified against `invenio_app_ils/config.py`, the final image, and the selected Helm/chart conventions before release. At minimum, production overrides must cover:

- site name and public UI URL;
- REST/API base URL;
- allowed hosts and proxy headers;
- database connection;
- Redis cache/session URLs;
- RabbitMQ/Celery broker URL;
- Celery result backend;
- OpenSearch hosts and index prefix;
- secret key and security salts;
- mail server and sender policy;
- file/object storage location if uploads are enabled;
- logging level and error reporting destination;
- initial admin user bootstrap path.

Treat exact environment variable names as implementation details of the deployment chart and Invenio configuration. Verify them in the built image before adding GitOps values.

## Secrets

Create Kubernetes secrets out-of-band; do not commit secret values.

Required secret groups:

- `ghcr-pull`;
- `nhrils-secrets` for Invenio secret key and salts;
- `nhrils-db`;
- `nhrils-broker`;
- `nhrils-admin`;
- SMTP/error-alert settings if not stored as non-secret ConfigMap values.

Preferred secret handling is the platform's existing mechanism: Kubernetes Secrets, SealedSecrets, ExternalSecrets, or another approved controller. The app repo must never contain real passwords, secret keys, SMTP credentials, access tokens, or private keys.

## Email

Use the EGA relay from inside the cluster unless NIMR chooses another approved relay:

```text
MAIL_SERVER=smtp4.eganet.go.tz
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USE_TLS=False
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@nimr.or.tz
```

Do not configure SMTP authentication for the EGA relay from cluster workloads unless the infrastructure team changes that policy.

## Local Readiness Gates

Before opening a GitOps deployment PR, run the local gates that match the changed surface:

```bash
./scripts/local-harness preflight
./scripts/local-harness test-local
./scripts/local-harness validate-seed
./scripts/local-harness seed-dry-run
```

For backend, service, database, search, or seed import behavior:

```bash
./scripts/local-harness test-services
```

For frontend changes:

```bash
./scripts/local-harness build-assets
```

Record the command results in the delivery note. If a gate is skipped, document the reason and residual risk.

## GitOps Readiness Gates

Before merging the platform GitOps change:

- confirm target namespace and route follow the existing NIMR cluster convention;
- confirm TLS certificate coverage for `nhrils.apps.nimr.or.tz`;
- confirm image pull secret access to GHCR;
- confirm database, Redis, RabbitMQ, and OpenSearch endpoints;
- confirm Kubernetes secret references exist but no secret values are committed;
- confirm production overrides remove localhost defaults;
- run the platform repository's render, lint, or dry-run validation;
- confirm rollback is possible through image pin reversion;
- confirm backup/restore ownership for database and persistent files;
- confirm monitoring/log access for web and worker services.

## Bootstrap Runbook

After GitOps sync:

1. Confirm TLS and ingress.
2. Confirm backend, worker, frontend, database, Redis, RabbitMQ, and OpenSearch pods/services.
3. Exec into the backend pod.
4. Confirm commands with:

   ```bash
   ils --help
   flask --help
   ```

5. Run database initialization and migrations using commands confirmed from the built image.
6. Initialize OpenSearch indexes.
7. Create the first admin user.
8. Load approved seed catalogue records.
9. Reindex.
10. Smoke test:
    - catalogue shell;
    - `/search`;
    - one search result;
    - one record detail;
    - login/logout;
    - backoffice access for admin/librarian;
    - worker logs;
    - email path if enabled.

Do not run destructive initialization commands against an environment that already contains library records, circulation data, patron data, or uploaded files unless a reviewed migration/backup plan explicitly approves it.

## Smoke Test Routes

Smoke test these routes after deployment and after each meaningful release:

```text
https://nhrils.apps.nimr.or.tz/
https://nhrils.apps.nimr.or.tz/nhrils/catalogue
https://nhrils.apps.nimr.or.tz/nhrils/catalogue/search
https://nhrils.apps.nimr.or.tz/nhrils/catalogue/collections
https://nhrils.apps.nimr.or.tz/nhrils/catalogue/records/nimr-doc-0001
https://nhrils.apps.nimr.or.tz/nhrils/catalogue/about
https://nhrils.apps.nimr.or.tz/nhrils/catalogue/terms
https://nhrils.apps.nimr.or.tz/nhrils/catalogue/privacy
```

Also verify:

- search returns seeded records;
- record detail pages render availability and request guidance;
- staff login works for the initial librarian/admin user;
- static assets load from the production host;
- worker logs show no repeated startup errors;
- OpenSearch indexes are healthy.

## Deployment Gates

Do not mark deployment ready until:

- production host is `nhrils.apps.nimr.or.tz`;
- frontend/API base URLs do not reference localhost;
- NIMR logo and NHRILS name are visible;
- stable secrets are configured;
- OpenSearch indexes exist;
- seed data is searchable;
- at least one librarian/admin can create or edit a record;
- rollback path is documented through GitOps image tag reversion.

## Rollback

Rollback should be GitOps-first:

1. Identify the last known-good image pin and GitOps commit.
2. Revert only the NHRILS image pin or the narrow faulty NHRILS manifest change.
3. Let the GitOps controller apply the rollback.
4. Confirm web, worker, search, and login smoke tests.
5. Check whether the failed release ran database migrations or data jobs.
6. If data/schema changed, follow the approved backup and migration recovery plan rather than attempting ad hoc shell fixes.

Rollback is straightforward only when migrations are backward compatible or were not run. Any schema/data migration release must include a release-specific rollback note.

## Observability and Failure Modes

The first deployment should expose enough operational signal for NIMR support:

- web request errors;
- worker task failures;
- OpenSearch connectivity failures;
- database migration/bootstrap failures;
- mail delivery failures;
- failed login/admin access attempts;
- slow search or record-detail responses.

Use the cluster's existing logging and monitoring stack where possible. Add application-level error reporting only after approval of the destination, data retention, and privacy handling.

## Open Decisions

- Whether to keep a separate frontend image or fold the catalogue shell into the backend-hosted route for the first release.
- Initial admin email.
- Error alert recipients.
- Whether catalogue seed data comes from spreadsheet, MARC, RIS/BibTeX, Zotero, Koha, DSpace, or manual sample.
- Whether digital files require persistent storage in the first release.
- Whether PostgreSQL, Redis, RabbitMQ, and OpenSearch are provisioned per app or reused as managed/shared services.
- Whether seed data is imported automatically during bootstrap or reviewed and imported by a librarian/admin.
- Whether public catalogue traffic and authenticated staff traffic require separate ingress policy in a later phase.
