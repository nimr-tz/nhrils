# NHRILS Seed Import Readiness

Date: 2026-08-04

## Purpose

Define the controlled path from the provisional NIMR publication seed bundle to a future approved InvenioILS development import.

This slice does not import records. It prepares a validation gate so catalogue data can be reviewed before any database writes, OpenSearch indexing, or deployment work.

## Current Seed Bundle

Seed file:

- `docs/seed-data/nimr-publications-seed.json`

Current contents:

- 42 `documents`
- 21 `eitems`
- 1 `location`
- 2 `internal_locations`
- 0 physical `items`

## Entity Mapping

| Seed section | InvenioILS entity | Current status | Import note |
| --- | --- | --- | --- |
| `documents` | Document | Ready for dry-run validation | Bibliographic records only. Full author lists should be reviewed before production import. |
| `eitems` | EItem | Ready for dry-run validation | DOI and public source links only. No file upload or file access policy is included. |
| `locations` | Location | Ready for dry-run validation | Placeholder NIMR Library location for demonstration. |
| `internal_locations` | InternalLocation | Ready for dry-run validation | Digital Publications and Reference Collection placeholders. |
| `items` | Item | Empty by design | Add only after NIMR confirms shelves, barcodes, accession numbers, and circulation rules. |

## Dry-Run Validator

Command:

```bash
python3 scripts/validate_seed_bundle.py
```

Harness shortcut:

```bash
./scripts/local-harness validate-seed
```

Machine-readable output:

```bash
python3 scripts/validate_seed_bundle.py --json
```

The validator checks:

- required top-level bundle sections;
- required document, e-item, location, internal location, and item fields;
- PID format and uniqueness;
- e-item references to seeded document PIDs;
- internal location references to seeded location PIDs;
- future physical item references to seeded document and internal location PIDs;
- source page URL shape;
- e-item URL shape;
- DOI identifier shape;
- supported document type vocabulary used by the MVP seed.

The validator intentionally does not:

- initialize Flask or Invenio;
- connect to a database;
- create or update records;
- upload files;
- rebuild indexes;
- change permissions;
- trigger circulation behavior.

## Guarded Import Plan

Command:

```bash
python3 scripts/import_seed_bundle.py
```

Harness shortcut:

```bash
./scripts/local-harness seed-dry-run
```

Machine-readable output:

```bash
python3 scripts/import_seed_bundle.py --json
```

The import planner validates the bundle and prints the entity order that a later
approved importer would use:

1. `locations`
2. `internal_locations`
3. `documents`
4. `eitems`
5. `items`

The planner is intentionally read-only. It does not initialize Invenio, connect
to services, create records, upload files, rebuild indexes, or change
permissions.

The `--apply` option is reserved but blocked. It exits with code `2` until the
database importer, idempotency checks, rollback procedure, and indexing plan are
approved.

## Import Gates

An actual import remains blocked until these gates are satisfied:

1. NIMR library or documentation staff review the seed records.
2. NIMR confirms whether the seed should remain article-level, serial-level, or both for journals.
3. Full author lists are sourced from DOI, PubMed, Crossref, MARC, RIS, BibTeX, Koha, or an official spreadsheet.
4. Physical item metadata is confirmed if any physical holdings are included.
5. The target environment is confirmed as development or staging.
6. A reversible importer is implemented and reviewed.
7. Database write, index write, and reindex approval is granted.

## Proposed Import Order

When approved, import records in this order:

1. `locations`
2. `internal_locations`
3. `documents`
4. `eitems`
5. `items`

This order preserves reference integrity because e-items and items depend on document PIDs, while items also depend on internal location PIDs.

## Development-Only Import Plan

Future importer requirements:

- support `--dry-run` as the default;
- require an explicit `--write` flag for database mutation;
- fail fast when any PID or reference validation fails;
- produce a machine-readable import report;
- record created and skipped PIDs;
- be safe to rerun without duplicating existing records;
- document any OpenSearch indexing or reindexing command required after import.

Current guarded command shape:

```bash
./scripts/local-harness seed-dry-run
python3 scripts/import_seed_bundle.py --json
```

Future approved command shape:

```bash
ils nhrils seed import docs/seed-data/nimr-publications-seed.json --dry-run
ils nhrils seed import docs/seed-data/nimr-publications-seed.json --write
```

The future command above remains a design target only.

## Verification

Completed for this readiness slice:

- dry-run validator added;
- guarded dry-run import planner added;
- local harness shortcuts added for validation and import planning;
- seed-shape test updated to exercise the validator;
- duplicate PID and import-plan tests added;
- documentation added for mapping, gates, proposed order, and development-only import plan.

Not completed:

- no database import;
- no OpenSearch indexing;
- no migration;
- no deployment;
- no circulation or patron data change.
