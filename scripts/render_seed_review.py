#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 NIMR.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Render a reviewer-friendly summary of the provisional NHRILS seed bundle.

The command is intentionally offline and read-only by default. It validates the
seed bundle, summarizes review-critical metadata, and prints Markdown or CSV for
NIMR library/documentation staff review before any database import is approved.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from validate_seed_bundle import validate_seed_bundle


DEFAULT_SEED_PATH = Path("docs/seed-data/nimr-publications-seed.json")


def _load_seed(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _author_name(author: Any) -> str:
    if isinstance(author, dict):
        return str(
            author.get("full_name")
            or author.get("name")
            or author.get("family_name")
            or author.get("given_name")
            or ""
        ).strip()
    return str(author).strip()


def _author_preview(authors: list[Any], limit: int = 3) -> str:
    names = [_author_name(author) for author in authors]
    names = [name for name in names if name]
    if not names:
        return "Missing"
    preview = "; ".join(names[:limit])
    if len(names) > limit:
        preview = f"{preview}; +{len(names) - limit} more"
    return preview


def _identifier_preview(identifiers: list[Any]) -> str:
    values: list[str] = []
    for identifier in identifiers:
        if not isinstance(identifier, dict):
            continue
        scheme = str(identifier.get("scheme") or "").strip()
        value = str(identifier.get("value") or "").strip()
        if scheme and value:
            values.append(f"{scheme}: {value}")
        elif value:
            values.append(value)
    return "; ".join(values) if values else "None"


def build_review_rows(seed_path: Path = DEFAULT_SEED_PATH) -> list[dict[str, str]]:
    """Build normalized document review rows from a seed bundle."""
    seed = _load_seed(seed_path)
    eitems_by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for eitem in seed.get("eitems", []):
        if isinstance(eitem, dict):
            eitems_by_document[str(eitem.get("document_pid", ""))].append(eitem)

    rows: list[dict[str, str]] = []
    for document in seed.get("documents", []):
        if not isinstance(document, dict):
            continue
        pid = str(document.get("pid", ""))
        eitems = eitems_by_document.get(pid, [])
        rows.append(
            {
                "pid": pid,
                "title": str(document.get("title", "")),
                "publication_year": str(document.get("publication_year", "")),
                "document_type": str(document.get("document_type", "")),
                "authors": _author_preview(document.get("authors", [])),
                "source": str(document.get("source", "")),
                "identifiers": _identifier_preview(document.get("identifiers", [])),
                "digital_links": str(len(eitems)),
                "review_status": "Needs NIMR review",
            }
        )
    return rows


def build_review_summary(seed_path: Path = DEFAULT_SEED_PATH) -> dict[str, Any]:
    """Build a serializable review summary for a seed bundle."""
    validation = validate_seed_bundle(seed_path)
    seed = _load_seed(seed_path) if validation["ok"] else {"documents": []}
    document_type_counts = Counter(
        str(document.get("document_type", ""))
        for document in seed.get("documents", [])
        if isinstance(document, dict)
    )
    year_counts = Counter(
        str(document.get("publication_year", ""))
        for document in seed.get("documents", [])
        if isinstance(document, dict)
    )
    rows = build_review_rows(seed_path) if validation["ok"] else []
    return {
        "seed_path": str(seed_path),
        "validation": validation,
        "document_type_counts": dict(sorted(document_type_counts.items())),
        "year_counts": dict(sorted(year_counts.items(), reverse=True)),
        "rows": rows,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a Markdown review report."""
    validation = summary["validation"]
    lines = [
        "# NHRILS Seed Review",
        "",
        f"Seed bundle: `{summary['seed_path']}`",
        f"Validation: {'passed' if validation['ok'] else 'failed'}",
        "",
        "## Counts",
        "",
    ]
    for key in ["locations", "internal_locations", "documents", "eitems", "items"]:
        lines.append(f"- {key}: {validation['counts'].get(key, 0)}")

    lines.extend(["", "## Document Types", ""])
    for document_type, count in summary["document_type_counts"].items():
        lines.append(f"- {document_type}: {count}")

    lines.extend(
        [
            "",
            "## Review Table",
            "",
            "| PID | Year | Type | Title | Authors | Digital links | Status |",
            "| --- | --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for row in summary["rows"]:
        lines.append(
            "| {pid} | {publication_year} | {document_type} | {title} | {authors} | {digital_links} | {review_status} |".format(
                **{key: _escape_markdown_table(str(value)) for key, value in row.items()}
            )
        )

    if validation["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in validation["warnings"])
    if validation["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in validation["errors"])

    return "\n".join(lines) + "\n"


def render_csv(summary: dict[str, Any]) -> str:
    """Render the review rows as CSV."""
    output = io.StringIO()
    fieldnames = [
        "pid",
        "title",
        "publication_year",
        "document_type",
        "authors",
        "source",
        "identifiers",
        "digital_links",
        "review_status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(summary["rows"])
    return output.getvalue()


def _escape_markdown_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def main(argv: list[str] | None = None) -> int:
    """Render the provisional seed review report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "seed_path",
        nargs="?",
        default=str(DEFAULT_SEED_PATH),
        help="Path to the NHRILS seed bundle JSON file.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "csv", "json"),
        default="markdown",
        help="Output format for the review report.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to stdout.",
    )
    args = parser.parse_args(argv)

    summary = build_review_summary(Path(args.seed_path))
    if args.format == "csv":
        rendered = render_csv(summary)
    elif args.format == "json":
        rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    else:
        rendered = render_markdown(summary)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0 if summary["validation"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
