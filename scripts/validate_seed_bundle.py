#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 NIMR.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Dry-run validation for provisional NHRILS seed bundles.

This script intentionally performs no database writes, no index writes, and no
Invenio application bootstrapping. It checks whether a seed bundle is structurally
ready for a later approved importer.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REQUIRED_TOP_LEVEL_KEYS = {
    "bundle",
    "locations",
    "internal_locations",
    "documents",
    "eitems",
    "items",
}

REQUIRED_DOCUMENT_FIELDS = {
    "$schema",
    "pid",
    "title",
    "authors",
    "publication_year",
    "document_type",
    "created_by",
}

REQUIRED_EITEM_FIELDS = {
    "$schema",
    "pid",
    "document_pid",
    "eitem_type",
    "open_access",
    "created_by",
}

REQUIRED_LOCATION_FIELDS = {"pid", "name"}
REQUIRED_INTERNAL_LOCATION_FIELDS = {"pid", "location_pid", "name"}
REQUIRED_ITEM_FIELDS = {"pid", "document_pid", "internal_location_pid"}

SUPPORTED_DOCUMENT_TYPES = {
    "ARTICLE",
    "BOOK",
    "PROCEEDINGS",
    "STANDARD",
    "SERIAL_ISSUE",
}

PID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
DOI_PATTERN = re.compile(r"^10\.\S+/\S+$")


class ValidationReport:
    """Collect validation errors and warnings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def _load_json(path: Path, report: ValidationReport) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error(f"Seed bundle not found: {path}")
        return {}
    except json.JSONDecodeError as exc:
        report.error(f"Seed bundle is not valid JSON: {exc}")
        return {}

    if not isinstance(data, dict):
        report.error("Seed bundle root must be a JSON object.")
        return {}

    return data


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_pid(pid: Any, label: str, report: ValidationReport) -> None:
    if not isinstance(pid, str) or not pid:
        report.error(f"{label} PID must be a non-empty string.")
        return
    if not PID_PATTERN.match(pid):
        report.error(f"{label} PID has unsupported characters: {pid}")


def _validate_required_fields(
    record: dict[str, Any],
    required: set[str],
    label: str,
    report: ValidationReport,
) -> None:
    missing = sorted(required.difference(record))
    if missing:
        report.error(f"{label} is missing required fields: {', '.join(missing)}")


def _validate_source_pages(bundle: dict[str, Any], report: ValidationReport) -> None:
    source_pages = bundle.get("source_pages", [])
    if not isinstance(source_pages, list) or not source_pages:
        report.warning("Bundle has no source_pages list.")
        return

    for index, url in enumerate(source_pages):
        if not isinstance(url, str) or not _is_http_url(url):
            report.error(f"bundle.source_pages[{index}] is not an HTTP(S) URL.")


def _validate_documents(
    documents: list[dict[str, Any]],
    report: ValidationReport,
) -> set[str]:
    document_pids: set[str] = set()

    for index, document in enumerate(documents):
        label = f"documents[{index}]"
        _validate_required_fields(document, REQUIRED_DOCUMENT_FIELDS, label, report)

        pid = document.get("pid")
        _validate_pid(pid, label, report)
        if isinstance(pid, str):
            if pid in document_pids:
                report.error(f"Duplicate document PID: {pid}")
            document_pids.add(pid)

        if document.get("document_type") not in SUPPORTED_DOCUMENT_TYPES:
            report.error(
                f"{label} has unsupported document_type: "
                f"{document.get('document_type')}"
            )

        authors = document.get("authors")
        if not isinstance(authors, list) or not authors:
            report.error(f"{label} must have at least one author.")

        year = document.get("publication_year")
        if not isinstance(year, str) or not re.match(r"^\d{4}$", year):
            report.error(f"{label} publication_year must be a four-digit string.")

        for identifier_index, identifier in enumerate(document.get("identifiers", [])):
            if not isinstance(identifier, dict):
                report.error(f"{label}.identifiers[{identifier_index}] must be object.")
                continue
            if identifier.get("scheme") == "DOI":
                value = identifier.get("value")
                if not isinstance(value, str) or not DOI_PATTERN.match(value):
                    report.error(f"{label}.identifiers[{identifier_index}] DOI is invalid.")

    return document_pids


def _validate_locations(
    locations: list[dict[str, Any]],
    internal_locations: list[dict[str, Any]],
    report: ValidationReport,
) -> tuple[set[str], set[str]]:
    location_pids: set[str] = set()
    internal_location_pids: set[str] = set()

    for index, location in enumerate(locations):
        label = f"locations[{index}]"
        _validate_required_fields(location, REQUIRED_LOCATION_FIELDS, label, report)
        pid = location.get("pid")
        _validate_pid(pid, label, report)
        if isinstance(pid, str):
            if pid in location_pids:
                report.error(f"Duplicate location PID: {pid}")
            location_pids.add(pid)

    for index, internal_location in enumerate(internal_locations):
        label = f"internal_locations[{index}]"
        _validate_required_fields(
            internal_location,
            REQUIRED_INTERNAL_LOCATION_FIELDS,
            label,
            report,
        )
        pid = internal_location.get("pid")
        _validate_pid(pid, label, report)
        if isinstance(pid, str):
            if pid in internal_location_pids:
                report.error(f"Duplicate internal location PID: {pid}")
            internal_location_pids.add(pid)

        location_pid = internal_location.get("location_pid")
        if isinstance(location_pid, str) and location_pid not in location_pids:
            report.error(f"{label} references unknown location_pid: {location_pid}")

    return location_pids, internal_location_pids


def _validate_eitems(
    eitems: list[dict[str, Any]],
    document_pids: set[str],
    report: ValidationReport,
) -> set[str]:
    eitem_pids: set[str] = set()

    for index, eitem in enumerate(eitems):
        label = f"eitems[{index}]"
        _validate_required_fields(eitem, REQUIRED_EITEM_FIELDS, label, report)
        pid = eitem.get("pid")
        _validate_pid(pid, label, report)
        if isinstance(pid, str):
            if pid in eitem_pids:
                report.error(f"Duplicate eitem PID: {pid}")
            eitem_pids.add(pid)

        document_pid = eitem.get("document_pid")
        if isinstance(document_pid, str) and document_pid not in document_pids:
            report.error(f"{label} references unknown document_pid: {document_pid}")

        urls = eitem.get("urls", [])
        if urls is not None:
            if not isinstance(urls, list):
                report.error(f"{label}.urls must be a list when present.")
            for url_index, url in enumerate(urls if isinstance(urls, list) else []):
                value = url.get("value") if isinstance(url, dict) else None
                if not isinstance(value, str) or not _is_http_url(value):
                    report.error(f"{label}.urls[{url_index}] is not an HTTP(S) URL.")

    return eitem_pids


def _validate_items(
    items: list[dict[str, Any]],
    document_pids: set[str],
    internal_location_pids: set[str],
    report: ValidationReport,
) -> set[str]:
    item_pids: set[str] = set()

    for index, item in enumerate(items):
        label = f"items[{index}]"
        _validate_required_fields(item, REQUIRED_ITEM_FIELDS, label, report)
        pid = item.get("pid")
        _validate_pid(pid, label, report)
        if isinstance(pid, str):
            if pid in item_pids:
                report.error(f"Duplicate item PID: {pid}")
            item_pids.add(pid)

        document_pid = item.get("document_pid")
        if isinstance(document_pid, str) and document_pid not in document_pids:
            report.error(f"{label} references unknown document_pid: {document_pid}")

        internal_location_pid = item.get("internal_location_pid")
        if (
            isinstance(internal_location_pid, str)
            and internal_location_pid not in internal_location_pids
        ):
            report.error(
                f"{label} references unknown internal_location_pid: "
                f"{internal_location_pid}"
            )

    return item_pids


def validate_seed_bundle(path: Path) -> dict[str, Any]:
    """Validate a seed bundle and return a serializable report."""
    report = ValidationReport()
    data = _load_json(path, report)

    if not data:
        return _build_result(report, {})

    missing = sorted(REQUIRED_TOP_LEVEL_KEYS.difference(data))
    if missing:
        report.error(f"Seed bundle missing top-level keys: {', '.join(missing)}")

    for key in REQUIRED_TOP_LEVEL_KEYS.intersection(data):
        if key != "bundle" and not isinstance(data.get(key), list):
            report.error(f"Top-level key {key} must be a list.")

    bundle = data.get("bundle", {})
    if not isinstance(bundle, dict):
        report.error("Top-level key bundle must be an object.")
        bundle = {}
    _validate_source_pages(bundle, report)

    locations = data.get("locations", [])
    internal_locations = data.get("internal_locations", [])
    documents = data.get("documents", [])
    eitems = data.get("eitems", [])
    items = data.get("items", [])

    if isinstance(locations, list) and isinstance(internal_locations, list):
        _, internal_location_pids = _validate_locations(
            locations,
            internal_locations,
            report,
        )
    else:
        internal_location_pids = set()

    if isinstance(documents, list):
        document_pids = _validate_documents(documents, report)
    else:
        document_pids = set()

    if isinstance(eitems, list):
        eitem_pids = _validate_eitems(eitems, document_pids, report)
    else:
        eitem_pids = set()

    if isinstance(items, list):
        item_pids = _validate_items(items, document_pids, internal_location_pids, report)
    else:
        item_pids = set()

    duplicate_cross_entity_pids = (
        document_pids.intersection(eitem_pids)
        | document_pids.intersection(item_pids)
        | eitem_pids.intersection(item_pids)
    )
    if duplicate_cross_entity_pids:
        report.error(
            "PIDs must be unique across documents, eitems, and items: "
            + ", ".join(sorted(duplicate_cross_entity_pids))
        )

    return _build_result(
        report,
        {
            "documents": len(documents) if isinstance(documents, list) else 0,
            "eitems": len(eitems) if isinstance(eitems, list) else 0,
            "locations": len(locations) if isinstance(locations, list) else 0,
            "internal_locations": (
                len(internal_locations) if isinstance(internal_locations, list) else 0
            ),
            "items": len(items) if isinstance(items, list) else 0,
        },
    )


def _build_result(report: ValidationReport, counts: dict[str, int]) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "counts": counts,
        "errors": report.errors,
        "warnings": report.warnings,
    }


def _print_human(result: dict[str, Any]) -> None:
    status = "ok" if result["ok"] else "failed"
    print(f"NHRILS seed validation: {status}")
    if result["counts"]:
        print("Counts:")
        for key in ["documents", "eitems", "locations", "internal_locations", "items"]:
            print(f"  {key}: {result['counts'].get(key, 0)}")
    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "seed_path",
        nargs="?",
        default="docs/seed-data/nimr-publications-seed.json",
        help="Path to the NHRILS seed bundle JSON file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON validation output.",
    )
    args = parser.parse_args(argv)

    result = validate_seed_bundle(Path(args.seed_path))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_human(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

