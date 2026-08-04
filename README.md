# NHRILS

National Health Research Integrated Library System

## Purpose

NHRILS is the National Institute for Medical Research library and research-knowledge catalogue platform. It is built from Invenio-App-ILS and customized for NIMR's role as Tanzania's national health research institution.

The first deployable product is a NIMR-branded public discovery catalogue for health research library materials. The longer-term platform should support research documentation, preservation, access, library operations, and controlled integration with NIMR research information systems.

## Institutional Context

NIMR is mandated to conduct, regulate, coordinate, promote, monitor, evaluate, document, and disseminate health research in Tanzania. That mandate makes NHRILS broader than a generic book-lending catalogue.

The system should support:

- discovery of health research library materials;
- preservation and access to institutional research documents where approved;
- documentation and dissemination of research outputs;
- librarian and documentation-officer workflows;
- future links with NIMR publications, reports, guidelines, data repositories, and research information systems.

## Product Direction

NHRILS follows a catalogue-first delivery path inspired by CERN Library Catalogue:

- search is the primary user action;
- results are filterable by practical facets;
- records expose title, contributors, year, source, identifiers, subjects, availability, and online access notes;
- users can understand whether a resource is physical, electronic, public, restricted, available, or requestable;
- librarians can curate the catalogue through the InvenioILS backoffice.

The first release should prove discovery and catalogue operations before deeper circulation, acquisition, interlibrary loan, analytics, or institutional-repository integration.

## MVP Scope

The first MVP includes:

- NIMR-branded public catalogue shell;
- public search and browse;
- faceted filtering by material type, format, availability, language, subject/tag, and publication year;
- record detail pages for documents;
- physical item and e-item visibility;
- basic librarian backoffice curation;
- a representative seed catalogue dataset;
- static About, Search Guide, Contact/Request, Terms, and Privacy surfaces;
- production-aware configuration for `nhrils.apps.nimr.or.tz` unless the hostname changes.

The MVP intentionally defers:

- full circulation policy customization;
- acquisitions;
- interlibrary loan;
- self-checkout;
- EBSCO/remote-access integration;
- NHRMIS integration;
- Tanzania Journal of Health Research integration;
- advanced analytics;
- full institutional repository replacement.

## System Design Principles

### 1. Catalogue First

The first useful system is the one that helps users find material. Search, browse, facets, and record details are the primary surfaces.

### 2. Native InvenioILS Before Custom Models

Use InvenioILS native entities first:

- Location;
- Internal Location;
- Literature;
- Series;
- Document;
- Item;
- E-item;
- Patron;
- Loan, only when circulation testing is in scope.

Do not introduce custom data models until NIMR requirements prove the native model cannot represent the needed workflow.

### 3. NIMR Mandate, Not Generic Library Copy

Design decisions should map back to NIMR's health research documentation and dissemination mandate. Catalogue records, taxonomies, access rules, and future integrations should support national health research visibility.

### 4. Public Discovery With Controlled Access

The public catalogue may expose metadata, but access to licensed files, restricted reports, patron information, loans, and staff workflows must remain permission-controlled.

### 5. Deployment Must Be Reproducible

Branding, configuration, seed data, search indexes, and infrastructure should be version-controlled and deployable through the NIMR GitOps path. Avoid manual pod edits.

### 6. Evidence Before Customization

Before changing circulation rules, metadata schemas, authentication, permissions, or search mappings, inspect the NHRILS rollout plan, user-provided library documents, InvenioILS documentation, and current repository code.

## Architecture Baseline

NHRILS is based on Invenio-App-ILS.

Core application areas:

- `invenio_app_ils/documents`
- `invenio_app_ils/items`
- `invenio_app_ils/eitems`
- `invenio_app_ils/series`
- `invenio_app_ils/literature`
- `invenio_app_ils/locations`
- `invenio_app_ils/internal_locations`
- `invenio_app_ils/patrons`
- `invenio_app_ils/circulation`
- `invenio_app_ils/acquisition`
- `invenio_app_ils/ill`
- `invenio_app_ils/vocabularies`

Runtime dependencies:

- PostgreSQL;
- Redis;
- RabbitMQ;
- OpenSearch;
- Invenio backend and worker services;
- React/InvenioILS frontend.

## Repository Remotes

This repository is the NIMR fork/customization baseline.

```text
origin   git@github.com:nimr-tz/nhrils.git
upstream git@github.com:inveniosoftware/invenio-app-ils.git
```

Current known branch state:

- `origin/master`: NIMR baseline with the initial rollout plan.
- `upstream/master`: upstream Invenio-App-ILS vendor branch.
- The branches diverge. Do not merge upstream into NIMR work until the rollout plan and requirements are reviewed.

## Documentation

Start here:

- `docs/NHRILS_INITIAL_CUSTOMIZATION_AND_ROLLOUT_PLAN.md`
- `docs/NHRILS_CATALOGUE_MVP_20260804.md`
- `docs/NHRILS_UX_DESIGN_SYSTEM_20260804.md`
- `docs/NHRILS_DEVELOPMENT_ENVIRONMENT_20260804.md`
- `docs/NHRILS_KUBERNETES_DEPLOYMENT_20260804.md`
- `README.rst` for upstream Invenio-App-ILS provenance.

External references:

- NIMR: https://nimr.or.tz/
- CERN Library Catalogue: https://catalogue.library.cern/
- InvenioILS documentation: https://invenioils.docs.cern.ch/

## Initial Delivery Path

1. Confirm the first catalogue seed dataset.
2. Confirm material types, locations, and internal locations.
3. Confirm public metadata and restricted-access policy.
4. Add NIMR logo, favicon, site name, footer, and static pages.
5. Fix production frontend/API URL configuration.
6. Load seed records.
7. Initialize indexes and verify search/facets/detail pages.
8. Verify librarian backoffice create/edit.
9. Deploy to the NIMR environment through the GitOps path.

## Development Notes

Install and run commands must be verified against the current Invenio-App-ILS version before use. Do not assume commands from another Invenio project.

Useful discovery commands:

```bash
python --version
pip --version
docker compose config
ils --help
pytest
```

The exact local development setup will be documented after the first environment setup pass.

## Safety Rules

- Do not commit secrets or `.env` values.
- Do not change authentication or permissions without approval.
- Do not add migrations or OpenSearch mapping changes without explicit review.
- Do not run destructive database or index commands without approval.
- Do not import real patron, loan, or restricted document data until privacy and data ownership are confirmed.
- Do not overwrite the NIMR fork with upstream history.

## Current Open Questions

- What is the first authoritative catalogue dataset?
- Which NIMR office owns daily catalogue curation?
- Which users need librarian/admin accounts first?
- What digital resources may be public, restricted, or link-only?
- Which NIMR centres and internal locations should appear in the MVP?
- Should request/loan workflows be enabled in the first release or deferred?

## License

This project is based on Invenio-App-ILS, which is distributed under the MIT License. See `LICENSE` and `README.rst` for upstream license and provenance details.
