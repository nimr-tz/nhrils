# NHRILS Kubernetes Deployment Plan

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

## Runtime Components

NHRILS requires:

- backend web application;
- worker/Celery process;
- optional separate frontend/nginx container if the React InvenioILS frontend remains separate;
- PostgreSQL;
- Redis;
- RabbitMQ;
- OpenSearch;
- Kubernetes secrets for stable Invenio keys/salts;
- TLS ingress for `nhrils.apps.nimr.or.tz`.

## Image Strategy

Use GHCR under the NIMR organization:

```text
ghcr.io/nimr-tz/nhrils:<git-sha>
ghcr.io/nimr-tz/nhrils-frontend:<git-sha>
```

Use a separate frontend image only while the repository still builds the React frontend from `docker/frontend/Dockerfile`.

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

## Secrets

Create Kubernetes secrets out-of-band; do not commit secret values.

Required secret groups:

- `ghcr-pull`;
- `nhrils-secrets` for Invenio secret key and salts;
- `nhrils-db`;
- `nhrils-broker`;
- `nhrils-admin`;
- SMTP/error-alert settings if not stored as non-secret ConfigMap values.

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

## Open Decisions

- Whether to keep a separate frontend image or fold the catalogue shell into the backend-hosted route for the first release.
- Initial admin email.
- Error alert recipients.
- Whether catalogue seed data comes from spreadsheet, MARC, RIS/BibTeX, Zotero, Koha, DSpace, or manual sample.
- Whether digital files require persistent storage in the first release.
