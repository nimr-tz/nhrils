# NHRILS GitOps Deployment Readiness

Date: 2026-08-05

## Purpose

Define the next deployment boundary after image publishing: a reviewed `nimr-tz/platform-gitops` pull request that deploys NHRILS to `nhrils.apps.nimr.or.tz`.

This is a readiness artifact only. It does not change cluster state, secrets, ArgoCD applications, or image pins.

## Evidence

Inspected NHRILS artifacts:

- `docs/NHRILS_KUBERNETES_DEPLOYMENT_20260804.md`
- `docs/NHRILS_GITOPS_SKELETON_20260805.md`
- `docs/NHRILS_GITHUB_ACTIONS_AND_ERROR_REPORTING_REVIEW_20260805.md`
- `.github/workflows/image-build-validation.yml`
- `.github/workflows/publish-images.yml`

Inspected local GitOps reference:

- `/home/jmduda/KodeX.2026/lims/.scratch/platform-gitops/clusters/msmt-02/apps.yaml`
- `/home/jmduda/KodeX.2026/lims/.scratch/platform-gitops/clusters/msmt-02/research/nhrdm/values.invenio.yaml`
- `/home/jmduda/KodeX.2026/lims/.scratch/platform-gitops/clusters/msmt-02/research/nhrdm/overrides/kustomization.yaml`
- `/home/jmduda/KodeX.2026/lims/.scratch/platform-gitops/clusters/msmt-02/databases/postgres/app.yaml`

## Deployment Contract

Application source:

```text
nimr-tz/nhrils
```

Cluster source:

```text
nimr-tz/platform-gitops
```

Canonical host:

```text
nhrils.apps.nimr.or.tz
```

Namespace:

```text
nhrils
```

Images published by NHRILS:

```text
ghcr.io/nimr-tz/nhrils-backend:sha-<short-sha>
ghcr.io/nimr-tz/nhrils-frontend:sha-<short-sha>
```

The first GitOps PR should consume these exact package names. Do not introduce `ghcr.io/nimr-tz/nhrils` unless the publish workflow is deliberately changed first.

## First GitOps PR Scope

The first platform PR should add only the NHRILS deployment skeleton:

- `clusters/msmt-02/research/nhrils/values.invenio.yaml`
- `clusters/msmt-02/research/nhrils/overrides/*`
- `clusters/msmt-02/research/nhrils/db-init/*` only if the bootstrap job is confirmed idempotent
- `clusters/msmt-02/databases/postgres/nhrils-cluster.yaml`
- `clusters/msmt-02/databases/postgres/nhrils-pooler.yaml`
- ArgoCD application registration in `clusters/msmt-02/apps.yaml`
- PostgreSQL registration in `clusters/msmt-02/databases/postgres/app.yaml`

Keep the PR narrow. Do not reformat unrelated GitOps files.

## Required Runtime Dependencies

- PostgreSQL through CloudNativePG and pooler.
- Shared Redis service.
- Shared RabbitMQ service.
- Shared OpenSearch service.
- Traefik ingress and TLS.
- GHCR pull secret in the `nhrils` namespace.
- Stable Invenio secret values supplied through an existing Kubernetes Secret.
- Email relay only after NIMR confirms sender policy.

## Secret Readiness

The platform PR may reference secret names, but must not commit real values.

Required secret names:

- `ghcr-pull`
- `nhrils-secrets`
- `nhrils-db`
- `nhrils-broker`
- `nhrils-admin`
- `nhrils-tls`

The NHRDM GitOps pattern shows why `existingSecret` matters: ArgoCD should not continuously drift because Helm regenerated Invenio secret values.

## Image Pin Rule

Use immutable SHA tags from the `Publish Images` workflow:

```text
sha-<short-sha>
```

Do not deploy `latest`.

For rollback, revert only the NHRILS image tag or digest in GitOps.

## Validation Before GitOps PR

In NHRILS:

```bash
./scripts/local-harness preflight
./scripts/local-harness test-local
./scripts/local-harness validate-seed
./scripts/local-harness seed-dry-run
./scripts/local-harness build-assets
```

In GitHub Actions:

- `Image Build Validation` passes.
- `Publish Images` publishes both backend and frontend images.
- The image digests are visible in the Actions summary.

In `platform-gitops`:

- run the repository's render, lint, or dry-run command after adding the NHRILS manifests;
- confirm ArgoCD applications render without missing value files;
- confirm Kubernetes Secret references point to existing out-of-band secrets;
- confirm ingress host and TLS secret are correct.

## Non-Goals

- No deployment from the NHRILS repository in this slice.
- No direct Kubernetes commands.
- No committed secrets.
- No production database migration execution.
- No OpenSearch index initialization or reindexing.

## Next Slice

Prepare the actual `platform-gitops` branch and PR skeleton, using `docs/NHRILS_GITOPS_SKELETON_20260805.md` as the source-side blueprint and the current `platform-gitops` main branch as the authority.
