# NHRILS Seed Data: NIMR Publications

Date: 2026-08-04

## Purpose

Prepare a provisional seed dataset for the first NHRILS catalogue demonstration using publication categories visible from the NIMR website.

This is not a production import. It is a reviewable seed bundle to support catalogue search, filtering, record detail, and librarian backoffice smoke testing.

## Sources Reviewed

- NIMR homepage and Publications menu: `https://nimr.or.tz/`
- Publications listing: `https://nimr.or.tz/publications/`
- Annual Reports: `https://nimr.or.tz/annual-reports/`
- Recent Policy Briefs: `https://nimr.or.tz/recent-policy-briefs/`
- Book Chapter: `https://nimr.or.tz/book-chapter/`
- Conference Proceedings: `https://nimr.or.tz/conference-proceedings-2/`
- Newsletter: `https://nimr.or.tz/newsletter/`
- Peer Reviewed Papers index: `https://nimr.or.tz/peer-reviewed-papers/`
- 2025/2026 Peer Reviewed Papers: `https://nimr.or.tz/2025-papers/`
- 2025/2026 quarter pages:
  - `https://nimr.or.tz/2025-1st-quarter/`
  - `https://nimr.or.tz/2025-2nd-quarter/`
  - `https://nimr.or.tz/2025-3rd-quarter/`
  - `https://nimr.or.tz/2025-4th-quarter/`

## Seed Bundle

Path: `docs/seed-data/nimr-publications-seed.json`

Contents:

- 42 `documents`
- 21 `eitems`
- 1 `location`
- 2 `internal_locations`
- 0 physical `items`

The first records cover:

- peer reviewed papers;
- annual reports;
- policy briefs / research summaries;
- book chapter;
- conference proceedings;
- newsletters;
- Tanzania Journal of Health Research.
- 2025/2026 peer-reviewed article records with DOI or source links.

## Mapping To InvenioILS

| NIMR website category | InvenioILS entity | Document type |
| --- | --- | --- |
| Peer Reviewed Papers | Document + optional EItem | `ARTICLE` |
| Annual Reports | Document | `STANDARD` |
| Policy Briefs / Research Summaries | Document | `STANDARD` |
| Book and Book Chapter | Document | `BOOK` |
| Conference Proceedings | Document | `PROCEEDINGS` |
| Newsletter | Document | `SERIAL_ISSUE` |
| Tanzania Health Research Journal | Document + EItem | `SERIAL_ISSUE` |

## Limitations

- Some website pages intermittently returned verification pages to browser-based crawlers, so the peer-reviewed expansion uses captured NIMR page snapshots for the peer-reviewed index, 2025/2026 year index, and quarter pages.
- Authors are shortened for long multi-author articles where the source page exposed many contributors. Full author lists should be imported from DOI, PubMed, Crossref, Koha, MARC, RIS, BibTeX, or an official NIMR spreadsheet in a later data-quality pass.
- This slice expands the seed with selected 2025/2026 peer-reviewed records for catalogue MVP review. It is not a complete historical import of all year pages.
- Publication years are inferred where the NIMR page did not expose an explicit year. These records are marked as seed data and must be reviewed before production import.
- Physical item records are intentionally empty until NIMR confirms shelves, accession numbers, barcodes, and location vocabulary.

## Acceptance Criteria

- Seed file is valid JSON.
- Seed file contains at least 40 document records.
- Each document has the required InvenioILS fields: `$schema`, `pid`, `title`, `authors`, `publication_year`, `document_type`, and `created_by`.
- PIDs are unique across documents and e-items.
- E-items point only to reviewable public source/DOI URLs.
- No import, migration, permission, or index rebuild is executed by this slice.

## Verification Summary

Completed:

- `PYTHONPYCACHEPREFIX=/tmp/nhrils_pycache python3 -m json.tool docs/seed-data/nimr-publications-seed.json`
- `PYTHONPYCACHEPREFIX=/tmp/nhrils_pycache python3 -m py_compile tests/test_catalogue_shell.py`
- `git diff --check`
- direct seed-shape validation:
  - `documents=42`
  - `eitems=21`
  - unique document PIDs
  - unique e-item PIDs
  - required document fields present
  - e-item `document_pid` values reference seeded documents

Not completed:

- No database import was run.
- No OpenSearch indexing or reindexing was run.
- `pytest` was not run because the local `.venv` does not yet have test dependencies installed.

## Next Steps

1. Review records with NIMR library/documentation staff.
2. Replace provisional entries with an authoritative export if available.
3. Add physical `items` only after locations, internal locations, barcodes, and circulation status are confirmed.
4. Create an approved importer or transform command for the selected source format.
5. Run import and reindex only in a controlled test environment.
