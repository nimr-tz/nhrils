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

## Seed Bundle

Path: `docs/seed-data/nimr-publications-seed.json`

Contents:

- 26 `documents`
- 5 `eitems`
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

- Some website pages intermittently returned verification pages to the crawler, so the seed file uses only titles and metadata that were visible from accessible page content or search-visible page snippets.
- Authors are shortened for long multi-author articles where the source page exposed many contributors. Full author lists should be imported from DOI, PubMed, Crossref, Koha, MARC, RIS, BibTeX, or an official NIMR spreadsheet in a later data-quality pass.
- Publication years are inferred where the NIMR page did not expose an explicit year. These records are marked as seed data and must be reviewed before production import.
- Physical item records are intentionally empty until NIMR confirms shelves, accession numbers, barcodes, and location vocabulary.

## Acceptance Criteria

- Seed file is valid JSON.
- Seed file contains at least 25 document records.
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
  - `documents=26`
  - `eitems=5`
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
