#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 NIMR.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Prepare a guarded NHRILS seed import plan.

The default mode is a dry run. It validates the seed bundle and prints the
ordered entity operations required for a later approved InvenioILS importer.

This command intentionally does not bootstrap Flask, connect to a database,
write records, upload files, rebuild indexes, or change permissions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_seed_bundle import validate_seed_bundle


IMPORT_ORDER = (
    ("locations", "Location"),
    ("internal_locations", "InternalLocation"),
    ("documents", "Document"),
    ("eitems", "EItem"),
    ("items", "Item"),
)


class ApplyBlockedError(RuntimeError):
    """Raised when an unsafe apply request is made."""


def _load_bundle(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_import_plan(seed_path: Path) -> dict[str, Any]:
    """Build a serializable dry-run import plan for a seed bundle."""
    validation = validate_seed_bundle(seed_path)
    plan: dict[str, Any] = {
        "mode": "dry-run",
        "seed_path": str(seed_path),
        "validation": validation,
        "operations": [],
        "blocked_operations": [
            "database writes",
            "OpenSearch indexing or reindexing",
            "file upload",
            "permission changes",
            "circulation or patron data changes",
        ],
    }

    if not validation["ok"]:
        return plan

    bundle = _load_bundle(seed_path)
    for key, entity_name in IMPORT_ORDER:
        records = bundle.get(key, [])
        plan["operations"].append(
            {
                "section": key,
                "entity": entity_name,
                "count": len(records) if isinstance(records, list) else 0,
                "action": "would validate and upsert by PID",
            }
        )

    return plan


def _print_human(plan: dict[str, Any]) -> None:
    validation = plan["validation"]
    status = "ok" if validation["ok"] else "failed"
    print(f"NHRILS seed import dry-run: {status}")
    print(f"Seed bundle: {plan['seed_path']}")

    if validation["counts"]:
        print("Validated counts:")
        for key in ["locations", "internal_locations", "documents", "eitems", "items"]:
            print(f"  {key}: {validation['counts'].get(key, 0)}")

    if plan["operations"]:
        print("Planned import order:")
        for operation in plan["operations"]:
            print(
                "  - {entity}: {count} from {section} ({action})".format(
                    **operation
                )
            )

    print("Blocked in this command:")
    for blocked in plan["blocked_operations"]:
        print(f"  - {blocked}")

    if validation["warnings"]:
        print("Warnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")

    if validation["errors"]:
        print("Errors:")
        for error in validation["errors"]:
            print(f"  - {error}")


def main(argv: list[str] | None = None) -> int:
    """Run the guarded seed import command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "seed_path",
        nargs="?",
        default="docs/seed-data/nimr-publications-seed.json",
        help="Path to the NHRILS seed bundle JSON file.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Reserved for a future approved database importer.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON import-plan output.",
    )
    args = parser.parse_args(argv)

    if args.apply:
        raise ApplyBlockedError(
            "--apply is intentionally blocked until the database importer, "
            "idempotency checks, rollback procedure, and indexing plan are approved."
        )

    plan = build_import_plan(Path(args.seed_path))
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        _print_human(plan)
    return 0 if plan["validation"]["ok"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApplyBlockedError as exc:
        print(f"NHRILS seed import blocked: {exc}", file=sys.stderr)
        sys.exit(2)
