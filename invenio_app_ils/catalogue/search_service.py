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
from math import ceil
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
    source: str = ""
    language: str = ""
    subject: str = ""
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
            source=str(values.get("source", "")).strip(),
            language=str(values.get("language", "")).strip(),
            subject=str(values.get("subject", "")).strip(),
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
            "source": self.source,
            "language": self.language,
            "subject": self.subject,
        }


@dataclass(frozen=True)
class CatalogueSearchResult:
    """Template-ready catalogue search response."""

    query: CatalogueSearchQuery
    result_count: int
    results: list[dict[str, Any]]
    facets: dict[str, list[dict[str, Any]]]
    pagination: dict[str, Any]
    backend: str


@dataclass(frozen=True)
class CatalogueRecordResult:
    """Template-ready catalogue record response."""

    record: dict[str, Any]
    backend: str


@dataclass(frozen=True)
class CatalogueCollectionsResult:
    """Template-ready catalogue collections response."""

    collections: list[dict[str, Any]]
    summary: dict[str, Any]
    backend: str


@dataclass(frozen=True)
class SeedCatalogueReviewResult:
    """Template-ready catalogue seed review response."""

    summary: dict[str, Any]
    review_actions: list[dict[str, Any]]
    readiness_checks: list[dict[str, Any]]
    records_missing_digital_access: list[dict[str, Any]]
    records_with_identifiers: list[dict[str, Any]]
    source_distribution: list[dict[str, Any]]
    language_distribution: list[dict[str, Any]]
    subject_cleanup: list[dict[str, Any]]
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

    def collections(self) -> CatalogueCollectionsResult:
        """Return public catalogue collection cards."""
        raise NotImplementedError

    def seed_review(self) -> SeedCatalogueReviewResult:
        """Return a read-only seed review summary."""
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
        eitems_by_document_pid = self._eitems_by_document_pid(seed.get("eitems", []))
        eitem_document_pids = {
            eitem["document_pid"] for eitem in seed.get("eitems", [])
        }
        filtered_documents = self._filter_documents(
            documents,
            query=query,
            eitem_document_pids=eitem_document_pids,
        )
        pagination = self._build_pagination(
            result_count=len(filtered_documents),
            requested_page=query.page,
            page_size=query.size,
        )
        offset = (pagination["page"] - 1) * query.size
        page_documents = filtered_documents[offset : offset + query.size]

        return CatalogueSearchResult(
            query=query,
            result_count=len(filtered_documents),
            results=[
                self._present_document(
                    document,
                    eitems_by_document_pid.get(document["pid"], []),
                )
                for document in page_documents
            ],
            facets={
                "availability": self._build_availability_facets(
                    documents,
                    eitem_document_pids,
                ),
                "type": self._build_count_facets(documents, "document_type"),
                "year": self._build_count_facets(documents, "publication_year"),
                "source": self._build_count_facets(documents, "source"),
                "language": self._build_language_facets(documents),
                "subject": self._build_keyword_facets(documents),
            },
            pagination=pagination,
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

    def collections(self) -> CatalogueCollectionsResult:
        """Return seed-backed public collection cards without side effects."""
        seed = self._load_seed_bundle()
        documents = seed["documents"]
        definitions = [
            {
                "key": "peer-reviewed-papers",
                "title": "Peer-reviewed papers",
                "material_type": "ARTICLE",
                "summary": (
                    "Published NIMR research articles and collaborative papers "
                    "for scientific discovery."
                ),
                "action_label": "Browse papers",
            },
            {
                "key": "reports",
                "title": "Reports",
                "material_type": "BOOK",
                "summary": (
                    "Institutional reports and book-like records prepared for "
                    "library review."
                ),
                "action_label": "Browse reports",
            },
            {
                "key": "journals",
                "title": "Journals",
                "material_type": "SERIAL_ISSUE",
                "summary": (
                    "Journal issues and serial publications relevant to health "
                    "research users."
                ),
                "action_label": "Browse journals",
            },
            {
                "key": "guidelines-standards",
                "title": "Guidelines and standards",
                "material_type": "STANDARD",
                "summary": (
                    "Guidelines, standards, and technical reference materials "
                    "for applied health research."
                ),
                "action_label": "Browse guidelines",
            },
            {
                "key": "proceedings",
                "title": "Proceedings",
                "material_type": "PROCEEDINGS",
                "summary": (
                    "Conference and meeting proceedings connected to NIMR "
                    "research work."
                ),
                "action_label": "Browse proceedings",
            },
        ]
        collections = [
            {
                **definition,
                "count": self._count_documents_by_type(
                    documents,
                    definition["material_type"],
                ),
                "href": "/nhrils/catalogue/search?type={}".format(
                    definition["material_type"]
                ),
            }
            for definition in definitions
        ]

        return CatalogueCollectionsResult(
            collections=collections,
            summary={
                "collection_count": len(collections),
                "record_count": len(documents),
                "digital_link_count": len(seed.get("eitems", [])),
            },
            backend=self.name,
        )

    def seed_review(self) -> SeedCatalogueReviewResult:
        """Return template-ready seed review diagnostics without side effects."""
        seed = self._load_seed_bundle()
        documents = seed["documents"]
        eitems = seed.get("eitems", [])
        items = seed.get("items", [])
        eitems_by_document_pid = self._eitems_by_document_pid(eitems)
        item_document_pids = {
            item.get("document_pid")
            for item in items
            if item.get("document_pid")
        }
        records_missing_digital_access = []
        records_with_identifiers = []
        records_missing_physical_holdings = []

        for document in documents:
            pid = document["pid"]
            presented = self._present_document(
                document,
                eitems_by_document_pid.get(pid, []),
            )
            identifiers = document.get("identifiers", [])
            if not presented["has_online_access"]:
                records_missing_digital_access.append(presented)
            if identifiers:
                records_with_identifiers.append(
                    {
                        **presented,
                        "identifiers": self._present_identifiers(identifiers),
                    }
                )
            if pid not in item_document_pids:
                records_missing_physical_holdings.append(presented)

        source_distribution = self._build_distribution(documents, "source")
        language_distribution = self._build_language_facets(documents)
        subject_cleanup = [
            {
                **facet,
                "review_note": (
                    "Confirm spelling, capitalization, and controlled subject vocabulary."
                ),
            }
            for facet in self._build_keyword_facets(documents)
            if facet["count"] == 1
        ][:8]
        summary = {
            "record_count": len(documents),
            "digital_link_count": len(eitems),
            "records_with_digital_access": len(documents)
            - len(records_missing_digital_access),
            "records_needing_review": len(records_missing_digital_access),
            "material_type_count": len(
                {
                    document.get("document_type")
                    for document in documents
                    if document.get("document_type")
                }
            ),
            "identifier_record_count": len(records_with_identifiers),
            "physical_item_count": len(items),
            "physical_holdings_missing_count": len(records_missing_physical_holdings),
            "subject_cleanup_count": len(subject_cleanup),
        }

        return SeedCatalogueReviewResult(
            summary=summary,
            review_actions=self._build_seed_review_actions(summary),
            readiness_checks=self._build_seed_readiness_checks(summary),
            records_missing_digital_access=records_missing_digital_access[:10],
            records_with_identifiers=records_with_identifiers[:10],
            source_distribution=source_distribution,
            language_distribution=language_distribution,
            subject_cleanup=subject_cleanup,
            backend=self.name,
        )

    def _build_seed_review_actions(
        self,
        summary: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """Return reviewer action links for the seed review page."""
        return [
            {
                "label": "Missing digital access",
                "count": summary["records_needing_review"],
                "summary": "Open records that need a public, licensed, or internal source decision.",
                "href": "/nhrils/catalogue/search?availability=review",
                "status": "Needs review",
            },
            {
                "label": "Records with identifiers",
                "count": summary["identifier_record_count"],
                "summary": "Check DOI, ISSN, ISBN, and local identifier coverage before import.",
                "href": "#nhrils-identifiers",
                "status": "Review",
            },
            {
                "label": "Physical holdings missing",
                "count": summary["physical_holdings_missing_count"],
                "summary": "Confirm whether each record has no shelf copy or needs holdings added.",
                "href": "#nhrils-readiness",
                "status": "Confirm",
            },
            {
                "label": "All seed records",
                "count": summary["record_count"],
                "summary": "Browse the full provisional catalogue dataset.",
                "href": "/nhrils/catalogue/search",
                "status": "Browse",
            },
        ]

    def _build_seed_readiness_checks(
        self,
        summary: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """Return plain-language readiness checks for reviewers."""
        return [
            {
                "label": "Digital access",
                "value": "{} of {} linked".format(
                    summary["records_with_digital_access"],
                    summary["record_count"],
                ),
                "status": "Needs review"
                if summary["records_needing_review"]
                else "Ready",
            },
            {
                "label": "Identifiers",
                "value": "{} records have identifiers".format(
                    summary["identifier_record_count"]
                ),
                "status": "Review",
            },
            {
                "label": "Physical holdings",
                "value": "{} items attached".format(summary["physical_item_count"]),
                "status": "Confirm",
            },
            {
                "label": "Controlled subjects",
                "value": "{} low-frequency terms listed".format(
                    summary["subject_cleanup_count"]
                ),
                "status": "Review",
            },
        ]

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
            if query.source and document.get("source") != query.source:
                continue
            if query.language and query.language not in self._document_languages(document):
                continue
            if query.subject and query.subject not in self._document_keywords(document):
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

    def _document_languages(self, document: Mapping[str, Any]) -> list[str]:
        """Return normalized language codes from a seed document."""
        return [
            str(language).strip()
            for language in document.get("languages", [])
            if str(language).strip()
        ]

    def _document_keywords(self, document: Mapping[str, Any]) -> list[str]:
        """Return keyword values from a seed document."""
        return [
            keyword.get("value", "").strip()
            for keyword in document.get("keywords", [])
            if keyword.get("value", "").strip()
        ]

    def _present_document(
        self,
        document: Mapping[str, Any],
        eitems: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Shape a seed document for the catalogue results template."""
        authors = [
            author.get("full_name", "") for author in document.get("authors", [])
        ]
        keywords = [
            keyword.get("value", "") for keyword in document.get("keywords", [])
        ]
        access = self._present_result_access(eitems)
        return {
            "pid": document["pid"],
            "title": document["title"],
            "authors": "; ".join(authors[:3]) + ("; + more" if len(authors) > 3 else ""),
            "publication_year": document.get("publication_year", "Unknown year"),
            "document_type": document.get("document_type", "Document").replace("_", " "),
            "abstract": document.get("abstract", "No abstract available for review."),
            "keywords": keywords[:4],
            "languages": self._document_languages(document),
            "source": document.get("source", "NIMR seed bundle"),
            "has_online_access": bool(access["online_url"]),
            "access": access,
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
            eitems,
        )
        presented.update(
            {
                "access": self._present_access(eitems),
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

    def _eitems_by_document_pid(
        self,
        eitems: Sequence[Mapping[str, Any]],
    ) -> dict[str, list[Mapping[str, Any]]]:
        """Group review seed e-items by parent document PID."""
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        for eitem in eitems:
            document_pid = eitem.get("document_pid")
            if document_pid:
                grouped.setdefault(str(document_pid), []).append(eitem)
        return grouped

    def _present_result_access(
        self,
        eitems: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Shape compact access state for search result cards."""
        urls = [
            url
            for eitem in eitems
            for url in eitem.get("urls", [])
            if url.get("value")
        ]
        primary_url = urls[0] if urls else None
        if primary_url:
            return {
                "tone": "online",
                "label": "Online access",
                "summary": "Public digital source attached",
                "online_url": primary_url,
            }
        return {
            "tone": "review",
            "label": "Metadata review needed",
            "summary": "No digital source attached",
            "online_url": None,
        }

    def _present_access(self, eitems: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Shape access and availability state for the catalogue detail page."""
        urls = [
            url
            for eitem in eitems
            for url in eitem.get("urls", [])
            if url.get("value")
        ]
        primary_url = urls[0] if urls else None
        if primary_url:
            status = {
                "tone": "online",
                "label": "Digital access available",
                "summary": "A public online source is attached to this review record.",
            }
        else:
            status = {
                "tone": "review",
                "label": "Metadata review required",
                "summary": "No digital access link is attached to this review record yet.",
            }

        return {
            "status": status,
            "online_url": primary_url,
            "physical_holding": {
                "label": "No physical holding attached",
                "summary": (
                    "Physical item, barcode, shelf, and circulation details are "
                    "not yet part of the review seed."
                ),
            },
            "request": {
                "enabled": False,
                "label": "Request item",
                "summary": (
                    "Request workflow will be enabled after holdings and circulation "
                    "rules are approved."
                ),
            },
            "contact": {
                "enabled": False,
                "label": "Ask librarian",
                "summary": (
                    "Librarian contact workflow is pending NIMR service desk routing."
                ),
            },
        }

    def _present_identifiers(
        self,
        identifiers: Sequence[Mapping[str, Any]],
    ) -> list[str]:
        """Return compact identifier strings for seed review tables."""
        values = []
        for identifier in identifiers:
            scheme = str(identifier.get("scheme", "")).strip()
            value = str(identifier.get("value", "")).strip()
            if scheme and value:
                values.append("{}: {}".format(scheme, value))
            elif value:
                values.append(value)
        return values

    def _build_distribution(
        self,
        documents: Sequence[Mapping[str, Any]],
        field: str,
    ) -> list[dict[str, Any]]:
        """Build an uncapped distribution for a seed document field."""
        counts: dict[str, int] = {}
        for document in documents:
            value = str(document.get(field, "")).strip()
            if value:
                counts[value] = counts.get(value, 0) + 1
        return [
            {"value": value, "label": value.replace("_", " ").title(), "count": count}
            for value, count in sorted(
                counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]

    def _count_documents_by_type(
        self,
        documents: Sequence[Mapping[str, Any]],
        material_type: str,
    ) -> int:
        """Return the number of seed documents for a material type."""
        return sum(
            1
            for document in documents
            if document.get("document_type") == material_type
        )

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

    def _build_pagination(
        self,
        *,
        result_count: int,
        requested_page: int,
        page_size: int,
    ) -> dict[str, Any]:
        """Build template-ready pagination metadata."""
        total_pages = ceil(result_count / page_size) if result_count else 0
        current_page = min(requested_page, total_pages) if total_pages else 1
        first_item = ((current_page - 1) * page_size) + 1 if result_count else 0
        last_item = min(current_page * page_size, result_count)
        return {
            "page": current_page,
            "requested_page": requested_page,
            "size": page_size,
            "total_pages": total_pages,
            "first_item": first_item,
            "last_item": last_item,
            "has_previous": current_page > 1,
            "has_next": bool(total_pages and current_page < total_pages),
            "previous_page": current_page - 1 if current_page > 1 else None,
            "next_page": current_page + 1
            if total_pages and current_page < total_pages
            else None,
        }

    def _build_language_facets(
        self,
        documents: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build language facets from seed language code arrays."""
        counts: dict[str, int] = {}
        for document in documents:
            for language in self._document_languages(document):
                counts[language] = counts.get(language, 0) + 1
        return [
            {"value": value, "label": value, "count": count}
            for value, count in sorted(
                counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ][:8]

    def _build_keyword_facets(
        self,
        documents: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build subject facets from seed keyword values."""
        counts: dict[str, int] = {}
        for document in documents:
            for keyword in self._document_keywords(document):
                counts[keyword] = counts.get(keyword, 0) + 1
        return [
            {"value": value, "label": value.title(), "count": count}
            for value, count in sorted(
                counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ][:12]


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

    def collections(self) -> CatalogueCollectionsResult:
        """Block native collections until import/indexing are approved."""
        raise NotImplementedError(
            "Native InvenioILS collections require approved record import, "
            "OpenSearch mapping/index readiness, and a reindex rollout plan."
        )

    def seed_review(self) -> SeedCatalogueReviewResult:
        """Block native seed review for non-seed backends."""
        raise NotImplementedError(
            "Native InvenioILS seed review requires approved record import, "
            "OpenSearch mapping/index readiness, and a reindex rollout plan."
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
