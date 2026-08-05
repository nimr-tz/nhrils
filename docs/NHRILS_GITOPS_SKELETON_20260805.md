# NHRILS GitOps Deployment Skeleton

Date: 2026-08-05

## Purpose

Provide a reviewable source-side blueprint for the future `nimr-tz/platform-gitops` pull request that deploys NHRILS to the NIMR Kubernetes cluster.

This document is not a live GitOps change. Do not copy it blindly into production. Before opening the platform PR, re-check the current `platform-gitops` main branch and adapt the skeleton to the latest cluster convention.

## Reference Pattern Inspected

Reference checkout inspected:

```text
/home/jmduda/KodeX.2026/lims/.scratch/platform-gitops
```

Reference files:

```text
clusters/msmt-02/apps.yaml
clusters/msmt-02/research/nhrdm/README.md
clusters/msmt-02/research/nhrdm/values.invenio.yaml
clusters/msmt-02/research/nhrdm/overrides/kustomization.yaml
clusters/msmt-02/research/nhrdm/overrides/certificate.yaml
clusters/msmt-02/research/nhrdm/overrides/traefik-middleware.yaml
clusters/msmt-02/research/nhrdm/overrides/instance-config-configmap.yaml
clusters/msmt-02/research/nhrdm/db-init/sequence-job.yaml
clusters/msmt-02/databases/postgres/nhrdm-cluster.yaml
clusters/msmt-02/databases/postgres/nhrdm-pooler.yaml
clusters/msmt-02/databases/postgres/app.yaml
```

Observed pattern:

- `helm-invenio` chart release is registered from `clusters/msmt-02/apps.yaml`.
- App-specific Helm values live under `clusters/msmt-02/research/<app>/values.invenio.yaml`.
- App-specific overrides are a separate ArgoCD application under `clusters/msmt-02/research/<app>/overrides`.
- Optional bootstrap jobs can live under `clusters/msmt-02/research/<app>/db-init`.
- PostgreSQL is managed in `clusters/msmt-02/databases/postgres` with a CNPG `Cluster` and `Pooler`.
- Runtime services reuse shared Redis, RabbitMQ, and OpenSearch where available.
- Invenio secrets are stable existing Kubernetes Secrets, not chart-generated random secrets.
- Traefik handles ingress and request buffering middleware.

## Target NHRILS Files

Create these files in `nimr-tz/platform-gitops` on a deployment branch, for example `feature/nhrils-rollout`:

```text
clusters/msmt-02/research/nhrils/
  README.md
  values.invenio.yaml
  overrides/
    kustomization.yaml
    certificate.yaml
    traefik-middleware.yaml
    instance-config-configmap.yaml
    templates-configmap.yaml
  db-init/
    README.md
    kustomization.yaml
    bootstrap-job.yaml

clusters/msmt-02/databases/postgres/
  nhrils-cluster.yaml
  nhrils-pooler.yaml
```

Also update:

```text
clusters/msmt-02/apps.yaml
clusters/msmt-02/databases/postgres/app.yaml
```

Only add NHRILS resources. Avoid broad formatting changes to existing GitOps files.

## ArgoCD Application Skeleton

Add the chart application to `clusters/msmt-02/apps.yaml`:

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: msmt-02-nhrils
  namespace: argocd
spec:
  project: default

  sources:
    - repoURL: https://inveniosoftware.github.io/helm-invenio/
      chart: invenio
      targetRevision: 0.10.0
      helm:
        releaseName: nhrils
        valueFiles:
          - $values/clusters/msmt-02/research/nhrils/values.invenio.yaml
    - repoURL: git@github.com:nimr-tz/platform-gitops.git
      targetRevision: main
      ref: values

  destination:
    server: https://kubernetes.default.svc
    namespace: nhrils

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Add overrides as a separate application so ConfigMaps, certificate, and middleware can be managed independently:

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: msmt-02-nhrils-overrides
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "0"
spec:
  project: default

  source:
    repoURL: git@github.com:nimr-tz/platform-gitops.git
    targetRevision: main
    path: clusters/msmt-02/research/nhrils/overrides

  destination:
    server: https://kubernetes.default.svc
    namespace: nhrils

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

Add a bootstrap application only after the bootstrap job is reviewed and confirmed idempotent:

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: msmt-02-nhrils-db-init
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "5"
spec:
  project: default

  source:
    repoURL: git@github.com:nimr-tz/platform-gitops.git
    targetRevision: main
    path: clusters/msmt-02/research/nhrils/db-init

  destination:
    server: https://kubernetes.default.svc
    namespace: nhrils

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Helm Values Skeleton

Create `clusters/msmt-02/research/nhrils/values.invenio.yaml`:

```yaml
image:
  registry: ghcr.io
  repository: nimr-tz/nhrils-backend
  tag: "sha-<short-sha>"
  pullPolicy: IfNotPresent
  pullSecrets:
    - name: ghcr-pull

invenio:
  hostname: nhrils.apps.nimr.or.tz
  existingSecret: nhrils-secrets
  extraConfig:
    INVENIO_THEME_SITENAME: "NHRILS"
    INVENIO_THEME_LOGO: "images/nimr.svg"
    INVENIO_THEME_FRONTPAGE_TITLE: "National Health Research Integrated Library System"
    INVENIO_SEARCH_INDEX_PREFIX: "nhrils-"

terminal:
  enabled: true
  replicas: 0
  extraEnvFrom:
    - secretRef:
        name: nhrils-admin

redis:
  enabled: false
redisExternal:
  hostname: redis.cache.svc.cluster.local

rabbitmq:
  enabled: false
rabbitmqExternal:
  username: invenio
  hostname: rabbitmq.messaging.svc.cluster.local
  amqpPort: 5672
  managementPort: 15672
  protocol: amqp
  vhost: "/"
  existingSecret: nhrils-broker
  existingSecretPasswordKey: password
  existingPasswordSecret: nhrils-broker

postgresql:
  enabled: false
postgresqlExternal:
  hostname: nhrils-pg-pooler.databases.svc.cluster.local
  port: 5432
  username: nhrils
  database: nhrils
  existingSecret: nhrils-db
  existingSecretPasswordKey: password

opensearch:
  enabled: false
opensearchExternal:
  hostname: opensearch.search.svc.cluster.local
externalOpensearch:
  hostname: opensearch.search.svc.cluster.local

ingress:
  enabled: true
  class: traefik
  annotations:
    traefik.ingress.kubernetes.io/router.middlewares: nhrils-nhrils-buffering@kubernetescrd
  tlsSecretNameOverride: "nhrils-tls"

persistence:
  enabled: false

web:
  replicas: 1
  extraVolumes:
    - name: instance-templates
      configMap:
        name: nhrils-instance-templates
        items:
          - key: footer.html
            path: semantic-ui/invenio_app_ils/footer.html
    - name: instance-config
      configMap:
        name: nhrils-instance-config
        items:
          - key: invenio.cfg
            path: invenio.cfg
  extraVolumeMounts:
    - name: instance-templates
      mountPath: /opt/invenio/var/instance/templates
      readOnly: true
    - name: instance-config
      mountPath: /opt/invenio/var/instance/invenio.cfg
      subPath: invenio.cfg
      readOnly: true

worker:
  replicas: 1
```

Notes:

- Replace `sha-<short-sha>` with an immutable source commit image tag from the `Publish Images` workflow.
- Confirm `helm-invenio` chart version against the current platform convention before PR.
- Confirm the template override paths for Invenio-App-ILS before mounting any template ConfigMap.
- Keep `terminal.replicas: 0` except during approved bootstrap.
- Keep persistence disabled only if uploads/files are out of scope for first deployment.

## Override Skeleton

Create `clusters/msmt-02/research/nhrils/overrides/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: nhrils

resources:
  - certificate.yaml
  - traefik-middleware.yaml
  - templates-configmap.yaml
  - instance-config-configmap.yaml
```

Create `certificate.yaml`:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: nhrils-tls
  namespace: nhrils
spec:
  secretName: nhrils-tls
  issuerRef:
    kind: ClusterIssuer
    name: letsencrypt-prod
  dnsNames:
    - nhrils.apps.nimr.or.tz
```

Create `traefik-middleware.yaml`:

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: nhrils-buffering
  namespace: nhrils
spec:
  buffering:
    maxRequestBodyBytes: 104857600
    memRequestBodyBytes: 1048576
```

Create `instance-config-configmap.yaml` with only reviewed, non-secret config:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nhrils-instance-config
  namespace: nhrils
data:
  invenio.cfg: |-
    from invenio_app_ils.config import *  # noqa

    THEME_SITENAME = "NHRILS"
    THEME_FRONTPAGE_TITLE = "National Health Research Integrated Library System"
```

Do not put passwords, API tokens, OAuth secrets, SMTP credentials, or private keys in this ConfigMap.

## PostgreSQL Skeleton

Create `clusters/msmt-02/databases/postgres/nhrils-cluster.yaml`:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: nhrils-pg
  namespace: databases
spec:
  instances: 1

  imageName: ghcr.io/cloudnative-pg/postgresql:16.1

  bootstrap:
    initdb:
      database: nhrils
      owner: nhrils
      encoding: UTF8
      localeCollate: C
      localeCType: C

  storage:
    size: 100Gi
    resizeInUseVolumes: true

  monitoring:
    enablePodMonitor: false

  postgresql:
    parameters:
      max_connections: "300"
      shared_buffers: "256MB"
      work_mem: "16MB"
      maintenance_work_mem: "128MB"
      wal_keep_size: "512MB"

  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "2"
      memory: "4Gi"
```

Create `nhrils-pooler.yaml`:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Pooler
metadata:
  name: nhrils-pg-pooler
  namespace: databases
spec:
  cluster:
    name: nhrils-pg

  instances: 2
  type: rw

  pgbouncer:
    poolMode: session
```

Update the PostgreSQL app resources according to the current `clusters/msmt-02/databases/postgres` convention so the new cluster and pooler are rendered.

## Required Secrets

Create secrets out-of-band using the approved NIMR secret-management method:

```text
namespace nhrils:
  ghcr-pull
  nhrils-secrets
  nhrils-db
  nhrils-broker
  nhrils-admin
  nhrils-tls
```

Required `nhrils-secrets` keys:

```text
INVENIO_SECRET_KEY
INVENIO_SECURITY_LOGIN_SALT
INVENIO_SECURITY_PASSWORD_SALT
INVENIO_SECURITY_CONFIRM_SALT
INVENIO_SECURITY_RESET_SALT
INVENIO_SECURITY_CHANGE_SALT
INVENIO_SECURITY_REMEMBER_SALT
INVENIO_CSRF_SECRET_SALT
```

Required password keys:

```text
nhrils-db: password
nhrils-broker: password
```

Initial admin bootstrap secret:

```text
nhrils-admin:
  NHRILS_ADMIN_EMAIL
  NHRILS_ADMIN_PASSWORD
```

Do not commit real secret values or generated secret manifests containing live data.

## Bootstrap Job Position

Do not add a live bootstrap job until the exact NHRILS image commands are verified:

```bash
ils --help
flask --help
invenio --help
```

Bootstrap should be idempotent and should not reset or destroy existing data. For a fresh database, expect reviewed commands for:

- database initialization and migration;
- default files location if files are enabled;
- OpenSearch index initialization;
- first admin creation;
- seed record loading or review-only seed import.

## GitOps PR Checklist

Before opening the platform PR:

- Pull the latest `nimr-tz/platform-gitops` main branch.
- Re-check the NHRDM pattern against current files.
- Confirm `helm-invenio` chart version.
- Confirm image tag exists in GHCR.
- Confirm DNS for `nhrils.apps.nimr.or.tz`.
- Confirm TLS issuer and certificate strategy.
- Confirm PostgreSQL sizing.
- Confirm Redis database allocation or dedicated Redis decision.
- Confirm RabbitMQ vhost/user/password ownership.
- Confirm OpenSearch version compatibility.
- Confirm whether persistence remains disabled.
- Confirm initial admin email.
- Confirm runtime email policy.
- Confirm seed data import owner.
- Run the platform render/dry-run validation command.

## Rollback Checklist

Rollback should change only GitOps-owned state:

- revert the NHRILS image pin to the last known-good tag;
- revert narrow NHRILS ConfigMap/values changes if they caused the failure;
- do not delete database resources during ordinary rollback;
- do not run destructive database commands;
- verify web, worker, search, login, and catalogue smoke routes after rollback.

If a release includes schema or data migration, add a release-specific rollback plan before deployment approval.
