# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 NIMR.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Catalogue search bridge for the NHRILS public catalogue shell.

The current implementation reads the provisional NIMR seed bundle only. The
service boundary keeps the public catalogue views independent from that review
fixture so a later approved slice can plug in native InvenioILS indexed search
without reshaping templates or route code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_SEED_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "seed-data"
    / "nimr-publications-seed.json"
)
DEFAULT_PAGE_SIZE = 25


@dataclass(frozen=True)
class CatalogueSearchQuery:
    """Validated catalogue search parameters from request args."""

    query: str = ""
    material_type: str = ""
    year: str = ""
    availability: str = ""
    page: int = 1
    size: int = DEFAULT_PAGE_SIZE

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "CatalogueSearchQuery":
        """Build search parameters from a Flask/MultiDict-style mapping."""
        page = _positive_int(values.get("page"), default=1)
        size = min(_positive_int(values.get("size"), default=DEFAULT_PAGE_SIZE), 100)
        return cls(
            query=str(values.get("q", "")).strip(),
            material_type=str(values.get("type", "")).strip(),
            year=str(values.get("year", "")).strip(),
            availability=str(values.get("availability", "")).strip(),
            page=page,
            size=size,
        )

    @property
    def selected_filters(self) -> dict[str, str]:
        """Return selected filters in the shape expected by templates."""
        return {
            "availability": self.availability,
            "type": self.material_type,
            "year": self.year,
        }


@dataclass(frozen=True)
class CatalogueSearchResult:
    """Template-ready catalogue search response."""

    query: CatalogueSearchQuery
    result_count: int
    results: list[dict[str, Any]]
    facets: dict[str, list[dict[str, Any]]]
    backend: str


@dataclass(frozen=True)
class CatalogueRecordResult:
    """Template-ready catalogue record response."""

    record: dict[str, Any]
    backend: str


class CatalogueSearchBackend:
    """Search backend contract for catalogue route adapters."""

    name = "base"

    def search(self, query: CatalogueSearchQuery) -> CatalogueSearchResult:
        """Search catalogue records."""
        raise NotImplementedError

    def get_record(self, pid: str) -> CatalogueRecordResult | None:
        """Return a single catalogue record by public PID."""
        raise NotImplementedError


@dataclass
class SeedCatalogueSearchBackend(CatalogueSearchBackend):
    """Read-only search backend backed by the provisional NIMR seed bundle."""

    seed_path: Path = DEFAULT_SEED_PATH
    name: str = "seed-review"
    _seed_cache: dict[str, Any] | None = field(default=None, init=False, repr=False)

    def search(self, query: CatalogueSearchQuery) -> CatalogueSearchResult:
        """Search the review seed bundle and return template-ready results."""
        seed = self._load_seed_bundle()
        documents = seed["documents"]
        eitem_document_pids = {
            eitem["document_pid"] for eitem in seed.get("eitems", [])
        }
        filtered_documents = self._filter_documents(
            documents,
            query=query,
            eitem_document_pids=eitem_document_pids,
        )
        offset = (query.page - 1) * query.size
        page_documents = filtered_documents[offset : offset + query.size]

        return CatalogueSearchResult(
            query=query,
            result_count=len(filtered_documents),
            results=[
                self._present_document(document, eitem_document_pids)
                for document in page_documents
            ],
            facets={
                "availability": self._build_availability_facets(
                    documents,
                    eitem_document_pids,
                ),
                "type": self._build_count_facets(documents, "document_type"),
                "year": self._build_count_facets(documents, "publication_year"),
            },
            backend=self.name,
        )

    def get_record(self, pid: str) -> CatalogueRecordResult | None:
        """Return a review seed record by PID, or ``None`` when missing."""
        seed = self._load_seed_bundle()
        document = next(
            (document for document in seed["documents"] if document["pid"] == pid),
            None,
        )
        if document is None:
            return None

        eitems = [
            eitem for eitem in seed.get("eitems", []) if eitem.get("document_pid") == pid
        ]
        return CatalogueRecordResult(
            record=self._present_document_detail(document, eitems),
            backend=self.name,
        )

    def _load_seed_bundle(self) -> dict[str, Any]:
        """Load the review seed bundle without database or index side effects."""
        if self._seed_cache is None:
            self._seed_cache = json.loads(self.seed_path.read_text(encoding="utf-8"))
        return self._seed_cache

    def _filter_documents(
        self,
        documents: Sequence[dict[str, Any]],
        *,
        query: CatalogueSearchQuery,
        eitem_document_pids: set[str],
    ) -> list[dict[str, Any]]:
        """Apply lightweight read-only search filters to seed documents."""
        normalized_query = query.query.lower()
        filtered = []
        for document in documents:
            if query.material_type and document.get("document_type") != query.material_type:
                continue
            if query.year and str(document.get("publication_year", "")) != query.year:
                continue
            has_online_access = document["pid"] in eitem_document_pids
            if query.availability == "online" and not has_online_access:
                continue
            if query.availability == "review" and has_online_access:
                continue
            if normalized_query and normalized_query not in self._document_text(document):
                continue
            filtered.append(document)
        return filtered

    def _document_text(self, document: Mapping[str, Any]) -> str:
        """Return searchable text for a review seed document."""
        values = [
            document.get("pid", ""),
            document.get("title", ""),
            document.get("abstract", ""),
            document.get("document_type", ""),
            str(document.get("publication_year", "")),
            document.get("source", ""),
        ]
        values.extend(
            author.get("full_name", "") for author in document.get("authors", [])
        )
        values.extend(
            keyword.get("value", "") for keyword in document.get("keywords", [])
        )
        values.extend(
            identifier.get("value", "")
            for identifier in document.get("identifiers", [])
        )
        return " ".join(values).lower()

    def _present_document(
        self,
        document: Mapping[str, Any],
        eitem_document_pids: set[str],
    ) -> dict[str, Any]:
        """Shape a seed document for the catalogue results template."""
        authors = [
            author.get("full_name", "") for author in document.get("authors", [])
        ]
        keywords = [
            keyword.get("value", "") for keyword in document.get("keywords", [])
        ]
        return {
            "pid": document["pid"],
            "title": document["title"],
            "authors": "; ".join(authors[:3]) + ("; + more" if len(authors) > 3 else ""),
            "publication_year": document.get("publication_year", "Unknown year"),
            "document_type": document.get("document_type", "Document").replace("_", " "),
            "abstract": document.get("abstract", "No abstract available for review."),
            "keywords": keywords[:4],
            "has_online_access": document["pid"] in eitem_document_pids,
            "detail_url": "/nhrils/catalogue/records/{}".format(document["pid"]),
        }

    def _present_document_detail(
        self,
        document: Mapping[str, Any],
        eitems: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Shape a seed document for the catalogue detail template."""
        presented = self._present_document(
            document,
            {eitem["document_pid"] for eitem in eitems},
        )
        presented.update(
            {
                "all_authors": [
                    author.get("full_name", "")
                    for author in document.get("authors", [])
                ],
                "identifiers": document.get("identifiers", []),
                "languages": document.get("languages", []),
                "source": document.get("source", "NIMR seed bundle"),
                "urls": [
                    url
                    for eitem in eitems
                    for url in eitem.get("urls", [])
                    if url.get("value")
                ],
            }
        )
        return presented

    def _build_count_facets(
        self,
        documents: Sequence[Mapping[str, Any]],
        field: str,
    ) -> list[dict[str, Any]]:
        """Build count facets for a seed document field."""
        counts: dict[str, int] = {}
        for document in documents:
            value = str(document.get(field, "")).strip()
            if value:
                counts[value] = counts.get(value, 0) + 1
        return [
            {
                "value": value,
                "label": value.replace("_", " ").title(),
                "count": count,
            }
            for value, count in sorted(
                counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ][:8]

    def _build_availability_facets(
        self,
        documents: Sequence[Mapping[str, Any]],
        eitem_document_pids: set[str],
    ) -> list[dict[str, Any]]:
        """Build simple access facets for the seed search shell."""
        online_count = sum(
            1 for document in documents if document["pid"] in eitem_document_pids
        )
        review_count = len(documents) - online_count
        return [
            {"value": "online", "label": "Digital access", "count": online_count},
            {"value": "review", "label": "Review record", "count": review_count},
        ]


class InvenioCatalogueSearchBackend(CatalogueSearchBackend):
    """Placeholder for a later approved native InvenioILS search backend."""

    name = "invenio-native"

    def search(self, query: CatalogueSearchQuery) -> CatalogueSearchResult:
        """Block native search until mappings/indexing/import are approved."""
        raise NotImplementedError(
            "Native InvenioILS catalogue search requires approved record import, "
            "OpenSearch mapping/index readiness, and a reindex rollout plan."
        )

    def get_record(self, pid: str) -> CatalogueRecordResult | None:
        """Block native record lookup until import/indexing are approved."""
        raise NotImplementedError(
            "Native InvenioILS catalogue record lookup requires approved record "
            "import, OpenSearch mapping/index readiness, and a reindex rollout plan."
        )


def get_catalogue_search_backend() -> CatalogueSearchBackend:
    """Return the active catalogue search backend for review routes."""
    return SeedCatalogueSearchBackend()


def _positive_int(value: Any, *, default: int) -> int:
    """Parse a positive integer request value."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
