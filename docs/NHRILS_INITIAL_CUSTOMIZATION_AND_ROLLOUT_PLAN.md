# NHRILS Initial Customization and Rollout Plan

## Objective

Deploy NHRILS, the National Health Research Integrated Library System, on the MS MT-02 research cluster from `git@github.com:nimr-tz/nhrils.git`.

The first rollout should be a branded, production-ready Invenio-ILS deployment inspired by CERN's library catalogue while using NIMR identity assets and the blue visual direction from `https://nimr.or.tz/`.

Recommended initial hostname: `nhrils.apps.nimr.or.tz`.

## References Reviewed

- CERN catalogue reference: `https://catalogue.library.cern/`
- NIMR visual reference: `https://nimr.or.tz/`
- Invenio-ILS documentation: `https://invenioils.docs.cern.ch/`
- Helm chart used by existing cluster Invenio deployment: `https://inveniosoftware.github.io/helm-invenio/`
- Existing cluster reference app: `clusters/msmt-02/research/nhrdm` in `platform-gitops`
- NHRILS source repository: `/home/jmduda/apps/nhrils`

## Research Findings

The `nhrils` repository is an Invenio App ILS codebase with backend and frontend Dockerfiles. It is not yet a NIMR-branded application scaffold.

The backend image builds the Python package, installs Invenio-ILS dependencies, collects assets, and builds webpack assets through:

- `scripts/bootstrap`
- `scripts/build_assets`
- `docker/backend/Dockerfile`

The frontend image currently clones `react-invenio-app-ils` from upstream during build and hardcodes development URLs such as `https://127.0.0.1`. This must be corrected before production rollout.

Runtime requirements are visible in `docker-services.yml`:

- PostgreSQL database
- Redis cache/session/result backend
- RabbitMQ broker
- OpenSearch
- Invenio stable secret key and salts
- Backend, worker, and frontend services

The cluster already has an Invenio deployment pattern in `nhrdm`. It uses the upstream `helm-invenio` chart with GitOps values, external shared services, stable Kubernetes secrets, Traefik ingress, TLS, and separate overrides mounted as ConfigMaps. NHRILS should reuse this pattern instead of inventing a new deployment model.

## Customization Requirements

Brand identity:

- Site short name: `NHRILS`
- Full name: `National Health Research Integrated Library System`
- Use the official NIMR logo in the header and login-facing surfaces.
- Use a NIMR favicon or ICO.
- Replace upstream/CERN/example wording in page titles, headers, footers, notification footers, and email templates.
- Use NIMR contact and institutional text where required.

Visual direction:

- Use a restrained NIMR blue palette inspired by `nimr.or.tz`.
- Keep the catalogue interface practical and readable, with strong contrast and clear search/filter states.
- Avoid CERN branding, demo labels, and local development URLs.
- Ensure mobile and desktop layouts do not clip text or hide catalogue controls.

Implementation surface in the repo:

- Add official logo/favicon assets under the application static assets.
- Add Semantic UI/LESS or theme overrides under `invenio_app_ils/assets/semantic-ui`.
- Update package templates where branding is server-rendered, especially:
  - `invenio_app_ils/templates/logged_out.html`
  - `invenio_app_ils/templates/invenio_app_ils/mail/footer.html`
  - `invenio_app_ils/templates/invenio_app_ils/notifications/footer.html`
- Configure Invenio theme values through `invenio.cfg` or Helm extra config:
  - `INVENIO_THEME_SITENAME`
  - `INVENIO_THEME_LOGO`
  - `INVENIO_THEME_FRONTPAGE_TITLE`
  - `INVENIO_SEARCH_INDEX_PREFIX`
- Make frontend build configuration production-aware:
  - `REACT_APP_INVENIO_UI_URL=https://nhrils.apps.nimr.or.tz`
  - `REACT_APP_INVENIO_REST_ENDPOINTS_BASE_URL=https://nhrils.apps.nimr.or.tz/api`
  - `REACT_APP_ENV_NAME=production`

## Deployment Requirements

Kubernetes/GitOps:

- Namespace: `nhrils`
- Hostname: `nhrils.apps.nimr.or.tz`
- TLS secret: `nhrils-tls`
- ArgoCD application: `msmt-02-nhrils`
- Optional override application: `msmt-02-nhrils-overrides`
- Optional bootstrap/database-init application: `msmt-02-nhrils-db-init`

Container images:

- Prefer GHCR under the organization namespace:
  - `ghcr.io/nimr-tz/nhrils`
  - optionally `ghcr.io/nimr-tz/nhrils-frontend` if the separate frontend image remains required
- Add GitHub Actions to build, push, and update the GitOps image tag after merge.

Deployment automation:

- Use the same automation model as the other cluster apps:
  - GitHub Actions builds and pushes immutable image tags to GHCR.
  - The workflow updates the matching image tag in `nimr-tz/platform-gitops`.
  - ArgoCD detects the GitOps commit and applies the deployment.
  - Manual ArgoCD sync remains available for urgent rollout or recovery.
- Required GitHub repository secrets for `nimr-tz/nhrils`:
  - `GHCR_TOKEN` or equivalent package-write token.
  - `PLATFORM_GITOPS_TOKEN` with permission to push the GitOps tag update branch/commit.
  - Notification SMTP credentials for GitHub Actions, because GitHub runners are outside the cluster and cannot use the IP-authenticated EGA relay.
- Use a predictable workflow name such as `build-and-deploy.yml`.
- Tag images with the Git SHA and optionally a timestamp label for traceability.
- The GitOps update should be narrow: only the NHRILS image tag(s) in `clusters/msmt-02/research/nhrils/values.invenio.yaml`.
- The workflow should fail if the GitOps render check fails.
- Deployment notification should report:
  - repository and commit SHA
  - image tag
  - GitOps commit
  - target namespace and hostname
  - workflow URL

Secrets:

- `ghcr-pull`
- `nhrils-secrets` with stable Invenio keys:
  - `INVENIO_SECRET_KEY`
  - `INVENIO_SECURITY_LOGIN_SALT`
  - `INVENIO_SECURITY_PASSWORD_SALT`
  - `INVENIO_SECURITY_CONFIRM_SALT`
  - `INVENIO_SECURITY_RESET_SALT`
  - `INVENIO_SECURITY_CHANGE_SALT`
  - `INVENIO_SECURITY_REMEMBER_SALT`
  - `INVENIO_CSRF_SECRET_SALT`
- `nhrils-db` for PostgreSQL password
- `nhrils-broker` for RabbitMQ password
- `nhrils-admin` for initial admin bootstrap
- SMTP/error-reporting configuration once owner recipients are confirmed

Runtime email and error reporting:

- Runtime email from inside the cluster should use the EGA relay:
  - host: `smtp4.eganet.go.tz`
  - port: `465`
  - encryption: implicit TLS/SMTPS
  - username: empty
  - password: empty
  - sender: `noreply@nimr.or.tz`
- Do not configure SMTP AUTH for the EGA relay from cluster workloads. The relay is IP-authenticated, and setting a username/password causes authentication failures in other apps.
- Add NHRILS-specific configuration keys in GitOps, following the cluster convention:
  - `MAIL_SERVER=smtp4.eganet.go.tz`
  - `MAIL_PORT=465`
  - `MAIL_USE_SSL=True`
  - `MAIL_USE_TLS=False`
  - `MAIL_USERNAME=`
  - `MAIL_PASSWORD=`
  - `MAIL_DEFAULT_SENDER=noreply@nimr.or.tz`
  - `ERROR_ALERTS_ENABLED=true`
  - `ERROR_ALERT_RECIPIENTS=<confirmed recipients>`
  - `ERROR_ALERT_DEDUPE_MINUTES=15`
- Recommended initial runtime error recipients:
  - `john.a.mduda@gmail.com`
  - library/application owner to be confirmed
- Add application-level exception reporting for:
  - backend web requests
  - REST API failures
  - Celery worker exceptions
  - scheduled/background jobs
  - bootstrap/migration job failures
- The implementation should be version-controlled in the app or GitOps overrides, not patched manually into running pods.
- If Invenio/Flask does not already send exception emails from configuration alone, add a small logging setup that attaches a mail handler when `ERROR_ALERTS_ENABLED=true`.
- Error emails should include:
  - app name and environment
  - request method and URL when available
  - authenticated user or anonymous marker
  - source IP when available
  - exception type and traceback
  - pod name and image tag
  - dedupe window indicator

Shared services:

- PostgreSQL through CNPG in the `databases` namespace, with a pooler such as `nhrils-pg-pooler.databases.svc.cluster.local`.
- Redis through the shared cluster Redis if database number capacity is available. If not, create a dedicated Redis instance or use a separate agreed allocation strategy.
- RabbitMQ through `rabbitmq.messaging.svc.cluster.local`.
- OpenSearch through `opensearch.search.svc.cluster.local`, with index prefix `nhrils-`.

Ingress/TLS:

- Use Traefik ingress class.
- Prefer the established wildcard certificate path for `*.apps.nimr.or.tz` if available.
- If using cert-manager per-app issuance, follow the existing ACME troubleshooting guidance and avoid ingress annotations that block HTTP-01 challenges.

Persistence:

- The existing `nhrdm` deployment disables chart persistence. For NHRILS, confirm whether library files, covers, records exports, and attachments must be stored in the filesystem.
- If user-uploaded files are required, add persistent storage before production data entry begins.

## Initial Rollout Plan

### Phase 0: Confirm Decisions

Confirm before implementation:

- Final hostname: recommended `nhrils.apps.nimr.or.tz`.
- Official logo and favicon source files.
- Initial admin account email.
- Public catalogue access policy.
- Whether authentication starts as local accounts or integrates with another identity provider later.
- Runtime error recipients.

### Phase 1: Application Customization

Create a branch in `nimr-tz/nhrils`, for example `feature/nimr-branding-bootstrap`.

Tasks:

- Add NIMR logo and favicon assets.
- Replace development frontend URLs with build args or environment-driven production values.
- Add NHRILS theme variables and template overrides.
- Replace footer, mail footer, notification footer, and login/logout branding.
- Add or expose runtime error-reporting configuration for Flask/Invenio and Celery.
- Build the backend and frontend images locally or through GitHub Actions.
- Verify static assets, API base URL, login pages, and catalogue entry points.

### Phase 2: GitOps Bootstrap

Create a branch in `nimr-tz/platform-gitops`, for example `feature/nhrils-rollout`.

Tasks:

- Add `clusters/msmt-02/research/nhrils/values.invenio.yaml`.
- Add `clusters/msmt-02/research/nhrils/overrides`.
- Add namespace resources.
- Add PostgreSQL database and pooler resources.
- Add ArgoCD applications in `clusters/msmt-02/apps.yaml`.
- Add secret documentation and non-secret placeholders.
- Add ConfigMap settings for EGA SMTP and runtime error recipients.
- Render manifests with `kubectl kustomize` before applying.

### Phase 3: Bootstrap Runtime

After GitOps resources are synced:

- Create stable Kubernetes secrets.
- Sync database resources first.
- Sync NHRILS chart and overrides.
- Run initial Invenio/ILS bootstrap commands from a terminal pod.
- Create default file location.
- Initialize database tables.
- Run migrations.
- Initialize search indexes.
- Create the first admin user.

The exact commands should be confirmed from the running NHRILS image before execution using `ils --help` and available Flask/Invenio commands. Do not assume the command names from another Invenio version without checking inside the built image.

### Phase 4: Validation

Validate:

- TLS certificate is valid for `nhrils.apps.nimr.or.tz`.
- Home/catalogue page loads.
- Static assets use the NIMR logo/favicon.
- Frontend API calls point to the production host and not `127.0.0.1`.
- Login/logout flows work.
- API health/basic endpoints respond.
- Worker pod connects to RabbitMQ and Redis.
- Search indexing connects to OpenSearch.
- Database migrations are applied.
- Error reporting is configured.
- A controlled test exception sends one deduplicated alert email to the configured recipients.
- GitHub Actions can build an image and update only the NHRILS GitOps image tag.
- ArgoCD shows healthy/synced.

### Phase 5: Automation

Add GitHub Actions in `nimr-tz/nhrils`:

- Build backend/frontend images on merge to `master` or `main`.
- Push images to GHCR.
- Update the GitOps image tag.
- Run a render check against the changed GitOps path.
- Notify on workflow failure using GitHub Actions SMTP credentials, not the EGA relay.
- Optionally trigger or watch ArgoCD sync after the GitOps commit if the app is not configured for automated sync.

Add runtime observability/error reporting:

- Configure EGA SMTP in the NHRILS ConfigMap with no authentication.
- Enable exception alerting for web, API, worker, and scheduled job paths.
- Set deduplication to reduce repeated identical alerts.
- Add a documented smoke test endpoint or management command for sending a controlled test alert.
- Confirm that a failed request and a failed worker task both produce alerts.

Add GitOps operational documentation:

- Secret creation commands.
- Bootstrap commands.
- Rollback process.
- Certificate troubleshooting notes.
- Admin/user bootstrap procedure.
- Error-reporting smoke test and recipient update procedure.

## Risks and Open Questions

- The frontend Dockerfile currently hardcodes development URLs. Production deployment should not proceed until this is fixed.
- The frontend image clones upstream React code during build. If deep branding is needed, the frontend should be vendored, forked, or patched deterministically.
- Redis database number availability must be checked before assigning DB indexes to NHRILS.
- OpenSearch version compatibility must be confirmed against the deployed cluster.
- File persistence must be decided before real library documents are uploaded.
- Stable Invenio secrets are mandatory. Randomly generated Helm secrets will cause ArgoCD drift and can break sessions/tokens.
- Initial bootstrap commands must be verified inside the built image because Invenio command names vary by version.
- GitHub Actions cannot use EGA SMTP unless the runner is inside the cluster network. Use Gmail or another external SMTP path for workflow notifications.
- Runtime error emails must be tested from inside the NHRILS namespace because the EGA relay permits mail by source network/IP.

## Recommended Branch and PR Order

1. `nimr-tz/nhrils`: `feature/nimr-branding-bootstrap`
   - Branding, production build config, image build workflow, app-level error reporting hooks.
2. `nimr-tz/platform-gitops`: `feature/nhrils-rollout`
   - Namespace, database, Helm values, overrides, ArgoCD apps, EGA SMTP/error-reporting config, secret docs.
3. Merge application PR first so an image exists.
4. Merge GitOps PR second.
5. Create secrets and sync ArgoCD.
6. Run bootstrap and validation.
7. Trigger one test deployment and one controlled error alert to confirm automation and reporting end to end.
