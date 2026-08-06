# NHRILS Container Image Build Validation

Date: 2026-08-05

## Purpose

Validate whether the current NHRILS repository can produce local backend and frontend container images before wiring automated GitHub Actions publishing and GitOps deployment.

This slice does not push images and does not deploy to the NIMR cluster.

## Commands Run

Backend:

```bash
docker build -f docker/backend/Dockerfile -t nhrils-backend:build-validation-20260805 .
docker image inspect nhrils-backend:build-validation-20260805 --format '{{.Id}} {{.Size}}'
```

Frontend:

```bash
docker build \
  -f docker/frontend/Dockerfile \
  --build-arg REACT_APP_INVENIO_UI_URL=https://nhrils.apps.nimr.or.tz \
  --build-arg REACT_APP_INVENIO_REST_ENDPOINTS_BASE_URL=https://nhrils.apps.nimr.or.tz/api \
  --build-arg REACT_APP_ENV_NAME=production \
  -t nhrils-frontend:build-validation-20260805 .
docker image inspect nhrils-frontend:build-validation-20260805 --format '{{.Id}} {{.Size}}'
```

## Results

Backend image build passed.

- Image: `nhrils-backend:build-validation-20260805`
- Image ID: `sha256:366da951266c6129bdcc859fb6e183b6cde98bba1679200f4a84ed99f7f65152`
- Size: `1945132938` bytes

Frontend image build passed after aligning the Dockerfile with the current upstream React package.

- Image: `nhrils-frontend:build-validation-20260805`
- Image ID: `sha256:90a3753c1b4301bfd3c7bed488d8831121f01edff21d6222d4cdd93d14434082`
- Size: `60892127` bytes

## Changes Made

Added `.dockerignore` to keep local/generated files out of the Docker context. The backend context reduced from about `741 MB` to about `100 KB`.

Updated `docker/frontend/Dockerfile` because the current upstream `react-invenio-app-ils` package is no longer compatible with the old assumptions:

- changed frontend builder from `node:12` to `node:22`;
- changed install command to `CYPRESS_INSTALL_BINARY=0 npm install --legacy-peer-deps`;
- changed build command from `npm run build` to `npm run lib-build`;
- changed runtime copy path from `/code/build` to `/code/dist`.

## Risks Found

The backend Dockerfile runs broad OS upgrades and live dependency installation during build. This makes builds slow and less reproducible.

The backend build spends several minutes in recursive ownership and permission steps over generated assets and dependency trees. A later hardening slice should replace broad `chgrp`, `chmod`, and `chown` recursion with `COPY --chown` and targeted permission changes.

The backend asset build reports Node engine warnings and npm audit findings from the Invenio asset dependency tree.

The frontend Dockerfile clones `https://github.com/inveniosoftware/react-invenio-app-ils.git` during image build. This is not deterministic because it follows upstream `HEAD`. Production builds should pin a commit, tag, or vendored fork.

The frontend package currently reports `24` npm vulnerabilities during install. These are from the upstream React dependency tree and need review before production hardening.

The frontend runtime image still uses `nginx:1.18` and includes test certificate files. Cluster TLS should be terminated by the ingress route; the runtime image should be reviewed before production.

## Delivery Guidance

For the first GitHub Actions image build workflow:

- use Docker Buildx;
- enable registry-backed or GitHub Actions cache;
- build backend and frontend as separate jobs;
- keep verbose logs and upload build summaries;
- tag images with commit SHA first;
- do not update GitOps image pins unless both image builds pass.

Before production deployment:

- pin or fork the frontend source instead of cloning upstream `HEAD`;
- review dependency vulnerabilities;
- optimize backend ownership/permission steps;
- remove or justify test TLS assets in the frontend runtime image;
- define whether the React frontend library image is still required for the MVP catalogue shell.
