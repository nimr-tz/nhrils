# NHRILS Catalogue MVP

Date: 2026-08-04

## Purpose

Define the smallest deployable National Health Research Integrated Library System catalogue that can be shown, tested, and improved before deeper NIMR-specific customization.

The first MVP should deliver a useful, branded catalogue experience inspired by CERN Library Catalogue while remaining aligned with NIMR's national health research mandate.

## Evidence Reviewed

- NIMR institutional context: `https://nimr.or.tz/`
- NIMR institute profile: `https://nimr.or.tz/institute-profile/`
- NIMR resources and publications areas: `https://nimr.or.tz/resources/`, `https://nimr.or.tz/publications/`
- CERN Library Catalogue: `https://catalogue.library.cern/`
- CERN Catalogue search page and facets: `https://catalogue.library.cern/search`
- CERN Catalogue About page: `https://catalogue.library.cern/about`
- CERN Catalogue FAQ: `https://catalogue.library.cern/faq`
- CERN Catalogue Search Guide: `https://catalogue.library.cern/guide/search`
- InvenioILS documentation: `https://invenioils.docs.cern.ch/`
- InvenioILS data model: `https://invenioils.docs.cern.ch/reference/data_model/`
- Existing rollout plan: `docs/NHRILS_INITIAL_CUSTOMIZATION_AND_ROLLOUT_PLAN.md`

## Product Positioning

NHRILS is not only a lending/circulation system. It should begin as a national health research discovery and library catalogue, then grow into the broader research documentation, preservation, access, and library-operation platform.

For the first deployable version, the system should answer:

1. What health research library materials does NIMR hold?
2. Can users search, filter, and open a record confidently?
3. Can librarians create or import enough records to prove catalogue operations?
4. Can NIMR show a branded, deployable system foundation at the intended hostname?

## Reference Lessons From CERN Catalogue

CERN's catalogue first presents a focused search experience for books, e-books, journals, series, standards, and proceedings. It separates the catalogue from the institutional repository and offers clear help, search guide, request path, availability status, and filters such as format, literature type, availability, tags, and languages.

For NHRILS, copy the product pattern, not the CERN domain:

- Put search at the center of the first experience.
- Use facets for practical filtering.
- Show record cards with title, contributors, year, publisher/source, material type, availability, and online access when available.
- Provide a record-detail page with identifiers, subjects, holdings, e-items, and request guidance.
- Keep help and search guide visible.
- Keep institutional repository/research-document archive as a later integration unless NIMR decides to include selected grey literature in the catalogue MVP.

## MVP Scope

### In Scope

1. NIMR-branded public catalogue shell.
2. Public search and browse for catalogue records, beginning with a review-results shell backed by the provisional seed bundle.
3. Faceted filtering for:
   - material type;
   - format;
   - availability;
   - language;
   - subject/tag;
   - publication year.
4. Record detail page for documents.
5. Basic item/e-item visibility:
   - physical copy availability;
   - location/internal location;
   - digital link where the resource is licensed or publicly accessible.
6. Librarian backoffice access for creating/editing records using existing InvenioILS capabilities.
7. Seed/import of a small representative NIMR catalogue dataset.
8. Static help pages:
   - About NHRILS;
   - Search guide;
   - Contact / request support.
9. Production-aware configuration:
   - NIMR logo and favicon;
   - system name: `National Health Research Integrated Library System`;
   - hostname: `nhrils.apps.nimr.or.tz` unless changed;
   - no `127.0.0.1` production frontend/API references.
10. Deployable infrastructure baseline using the rollout plan.

### Out of Scope For MVP

- Full circulation policy customization.
- Self-checkout.
- Acquisition workflows.
- Interlibrary loan workflows.
- Deep NHRMIS integration.
- EBSCO proxy/remote-access integration.
- Tanzania Journal of Health Research integration.
- Research ethics, data/material transfer, or permission-to-publish workflows.
- Full research data repository or institutional repository replacement.
- Advanced analytics dashboards.

These are future phases after the catalogue proof is stable.

## Data Model MVP

Use InvenioILS native concepts first:

- Location: NIMR Library or the first agreed library location.
- Internal location: shelf/building/unit details.
- Literature: public discovery aggregation of documents/series.
- Document: bibliographic metadata for books, reports, proceedings, standards, guidelines, journals, and selected grey literature.
- Item: physical copies.
- E-item: digital/online access records.
- Patron: only for authenticated workflows if request/loan testing is enabled.

Do not add custom models for the MVP unless native InvenioILS entities cannot represent the minimum catalogue data.

## Minimum Metadata

Each seed record should include where available:

- title;
- material/literature type;
- contributors/authors/editors;
- publication year;
- publisher/source;
- language;
- identifiers: ISBN, ISSN, DOI, report number, or local accession number;
- subjects/keywords/tags;
- abstract/description where available;
- physical availability and location for item records;
- online URL or access note for e-items.

## User Stories

### Public / Research User

As a researcher, I want to search NIMR library materials by title, author, subject, identifier, and year so that I can quickly find relevant health research resources.

As a researcher, I want to filter search results by material type, availability, language, subject, and year so that I can narrow results without knowing exact catalogue terms.

As a researcher, I want to open a record and see location, availability, identifiers, and online-access links so that I know how to obtain the material.

### Librarian / Documentation Officer

As a librarian, I want to create or edit catalogue records in the backoffice so that the MVP can grow from seed data into a maintained system.

As a librarian, I want to assign items and e-items to records so that users can distinguish physical holdings from online resources.

### System Administrator

As an administrator, I want the catalogue deployed with NIMR branding, production URLs, and stable services so that it is credible as the first NHRILS release.

## Acceptance Criteria

1. The public catalogue loads at the agreed hostname with NIMR branding.
2. The landing page presents catalogue search as the primary action.
3. Searching by title, author/contributor, subject/tag, identifier, and year returns relevant seed records.
4. Search results display record type, title, contributors, year, availability/access status, and material/format indicators.
5. Users can filter results by at least material type, format, availability, language, subject/tag, and publication year.
6. Opening a record shows bibliographic metadata, identifiers, subjects/tags, item availability, location, and digital access link/note where available.
7. The site exposes About, Search guide, Contact/request support, Terms, and Privacy surfaces, even if the first copy is short.
8. Librarian/admin users can access the backoffice and create or update at least one record.
9. A seed dataset of at least 25 representative records is loaded or documented for loading.
10. Production build does not reference `127.0.0.1` for frontend/API calls.
11. OpenSearch indexing is initialized and search results are populated after seed import.
12. Deployment smoke test confirms web, API, worker, PostgreSQL, Redis, RabbitMQ, and OpenSearch connectivity.

## Requirements Traceability

| Requirement | Evidence | Implementation surface | Verification |
| --- | --- | --- | --- |
| Catalogue-first MVP | CERN catalogue home/search; NIMR documentation mandate | frontend shell, seed-backed review search route, record cards | Search and browse smoke test |
| Faceted discovery | CERN search facets | InvenioILS search UI/config/mappings | Facet results visible and usable |
| Native ILS data model | InvenioILS data model docs | documents, items, eitems, locations | Seed records render with holdings |
| NIMR branding | NIMR site and rollout plan | templates, static assets, config | Header/favicon/title inspection |
| Librarian curation | InvenioILS backoffice features | admin/backoffice | Create/edit record smoke test |
| Deployability | rollout plan | Docker/GitOps/Helm values | Deployment smoke test |

## Definition Of Done

The MVP is done when:

- the catalogue is deployed in a test or production-like NIMR environment;
- NIMR branding is visible;
- search, facets, record detail, and seeded catalogue records work;
- at least one librarian/admin user can create or edit records;
- no production-facing URL points to local development endpoints;
- basic system services are healthy;
- a short user/admin handover note exists.

## Delivery Slices

### Slice 1: Catalogue Product Baseline

- Confirm seed dataset shape.
- Confirm material types and first location/internal location.
- Confirm public access and authenticated admin access policy.
- Add NIMR catalogue MVP pages/content.

### Slice 2: Branding And Production Configuration

- Add NIMR assets.
- Replace upstream/demo/CERN-facing wording.
- Fix frontend production URLs.
- Build locally.

### Slice 3: Seed Catalogue And Backoffice Smoke Test

- Load/import representative records.
- Reindex.
- Confirm search/facets/detail.
- Create/edit one record from backoffice.

### Slice 4: Deployment Baseline

- Build image.
- Deploy to the agreed environment.
- Run smoke tests.
- Document operational next steps.

## Open Questions

- What is the first authoritative seed dataset: existing library export, spreadsheet, MARC records, RIS/BibTeX, Zotero, Koha, DSpace, or manual sample?
- Should selected NIMR reports/guidelines/policy briefs be part of catalogue MVP or remain as website/repository content for later integration?
- What is the public access policy for digital links and licensed resources?
- Who are the first librarian/admin users?
- What location/internal-location vocabulary should be used for NIMR headquarters and centres?
- Should user loan/request workflows be enabled in MVP or deferred until catalogue discovery is accepted?

## Verification Summary

This artifact is requirements/documentation only. No application code has been changed.

Reviewed sources include NIMR public site/resource context, CERN Catalogue public pages, InvenioILS documentation, and the existing NHRILS rollout plan.
