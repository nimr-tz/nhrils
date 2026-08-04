# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 NIMR.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""NHRILS catalogue shell tests."""

from flask import url_for
import importlib.util
from pathlib import Path
import json
import sys

import pytest

from invenio_app_ils.catalogue.search_service import (
    CatalogueSearchQuery,
    InvenioCatalogueSearchBackend,
    SeedCatalogueSearchBackend,
)


def test_catalogue_shell_renders(client):
    """Test the NHRILS public catalogue shell route."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_shell_view"))

    assert res.status_code == 200
    assert b"NHRILS" in res.data
    assert b"National Health Research Integrated Library System" in res.data
    assert b"Search the catalogue" in res.data
    assert b"/nhrils/catalogue/search" in res.data
    assert b"/nhrils/catalogue/search-guide" in res.data
    assert b"/nhrils/catalogue/about" in res.data
    assert b"/nhrils/catalogue/contact" in res.data
    assert b"/search" in res.data
    assert b"nimr.svg" in res.data
    assert b"42" in res.data
    assert b"seed records" in res.data
    assert b"Featured records" in res.data
    assert b"Representative NIMR catalogue records" in res.data
    assert b"What needs confirmation" in res.data
    assert b"Artemisinin-resistant malaria" in res.data
    assert b"Tanzania Journal of Health Research" in res.data
    assert b"Digital access" in res.data
    assert b"Database import, indexing, and circulation remain gated" in res.data
    assert b"Seed data is ready for NIMR review" in res.data


def test_catalogue_about_page_renders(client):
    """Test the NHRILS catalogue about page."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_about_view"))

    assert res.status_code == 200
    assert b"About NHRILS" in res.data
    assert b"National health research discovery service" in res.data
    assert b"What the catalogue supports" in res.data
    assert b"Current MVP boundary" in res.data
    assert b"/nhrils/catalogue/search" in res.data
    assert b'aria-current="page">About' in res.data


def test_catalogue_help_page_renders(client):
    """Test the NHRILS catalogue search guide page."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_search_guide_view"))

    assert res.status_code == 200
    assert b"Search Guide" in res.data
    assert b"Search NIMR resources with practical health research terms" in res.data
    assert b"Recommended search patterns" in res.data
    assert b"malaria guidelines" in res.data
    assert b"Tanzania Journal of Health Research" in res.data
    assert b'aria-current="page">Search guide' in res.data


def test_catalogue_contact_page_renders(client):
    """Test the NHRILS catalogue contact page."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_contact_view"))

    assert res.status_code == 200
    assert b"Contact And Requests" in res.data
    assert b"Request catalogue support from the NIMR library team" in res.data
    assert b"When to contact the library" in res.data
    assert b"Information to include" in res.data
    assert b"Support status" in res.data
    assert b'aria-current="page">Contact' in res.data


def test_catalogue_terms_page_renders(client):
    """Test the NHRILS catalogue terms page."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_terms_view"))

    assert res.status_code == 200
    assert b"Terms Of Use" in res.data
    assert b"Catalogue use and access conditions" in res.data
    assert b"Using catalogue information" in res.data
    assert b"Service boundaries" in res.data
    assert b"Terms status" in res.data
    assert b"Draft MVP copy for review" in res.data
    assert b'aria-current="page">Terms' in res.data


def test_catalogue_privacy_page_renders(client):
    """Test the NHRILS catalogue privacy page."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_privacy_view"))

    assert res.status_code == 200
    assert b"Privacy Notice" in res.data
    assert b"Catalogue privacy and data handling" in res.data
    assert b"What the public catalogue shows" in res.data
    assert b"Future personal data handling" in res.data
    assert b"Privacy status" in res.data
    assert b"Patron identity, requests, loans, and notifications require separate approval" in res.data
    assert b'aria-current="page">Privacy' in res.data


def test_catalogue_review_page_renders(client):
    """Test the read-only seed review page."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_seed_review_view"))

    assert res.status_code == 200
    assert b"Seed Dataset Review" in res.data
    assert b"Review the catalogue seed before import" in res.data
    assert b"Total records" in res.data
    assert b"Digital links" in res.data
    assert b"Records needing review" in res.data
    assert b"Material types" in res.data
    assert b"Records missing digital access" in res.data
    assert b"Review workflow" in res.data
    assert b"Data quality workbench" in res.data
    assert b"Catalogue cleanup before import" in res.data
    assert b"Digital access cleanup" in res.data
    assert b"Identifier review" in res.data
    assert b"Physical holdings" in res.data
    assert b"Subject vocabulary" in res.data
    assert b"Missing digital access" in res.data
    assert b"Physical holdings missing" in res.data
    assert b"Source, language, and type coverage" in res.data
    assert b"Material type distribution" in res.data
    assert b"Source distribution" in res.data
    assert b"Language distribution" in res.data
    assert b"Browse all seed records" in res.data
    assert b"Subjects needing vocabulary review" in res.data
    assert b"/nhrils/catalogue/search?availability=review" in res.data
    assert b'aria-current="page">Seed review' in res.data
    assert b"Database and OpenSearch writes remain approval-gated" not in res.data


def test_catalogue_collections_page_renders(client):
    """Test the read-only catalogue collections page."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_collections_view"))

    assert res.status_code == 200
    assert b"Catalogue Collections" in res.data
    assert b"Browse NIMR resources by collection" in res.data
    assert b"Search all collections" in res.data
    assert b"Peer-reviewed papers" in res.data
    assert b"Reports" in res.data
    assert b"Journals" in res.data
    assert b"Guidelines and standards" in res.data
    assert b"Proceedings" in res.data
    assert b"/nhrils/catalogue/search?type=ARTICLE" in res.data
    assert b"/nhrils/catalogue/search?type=STANDARD" in res.data
    assert b'aria-current="page">Collections' in res.data
    assert b"Database import" not in res.data


def test_catalogue_search_results_shell_renders(client):
    """Test the NHRILS public review search results shell."""
    res = client.get(
        url_for("nhrils_catalogue_shell.catalogue_search_view"),
        query_string={"q": "malaria", "availability": "online"},
    )

    assert res.status_code == 200
    assert b"Catalogue results" in res.data
    assert b"Search NIMR health research resources" in res.data
    assert b"review seed catalogue" in res.data
    assert b"Refine results" in res.data
    assert b"/nhrils/catalogue/search-guide" in res.data
    assert b"Online access" in res.data
    assert b"Public digital source attached" in res.data
    assert b"View online" in res.data
    assert b"Material type" in res.data
    assert b"Source" in res.data
    assert b"Language" in res.data
    assert b"Subject" in res.data
    assert b"Artemisinin-resistant malaria" in res.data
    assert b"nimr-doc-0001" in res.data
    assert b"/nhrils/catalogue/records/nimr-doc-0001" in res.data
    assert b"Open record" in res.data
    assert b"Showing 1-" in res.data
    assert b"Database import" not in res.data


def test_catalogue_collection_search_context_renders(client):
    """Test collection-filtered searches render collection context."""
    res = client.get(
        url_for("nhrils_catalogue_shell.catalogue_search_view"),
        query_string={"type": "ARTICLE"},
    )

    assert res.status_code == 200
    assert b"Collection" in res.data
    assert b"Peer-reviewed papers" in res.data
    assert b"Published NIMR research articles" in res.data
    assert b"Back to Collections" in res.data
    assert b"/nhrils/catalogue/collections" in res.data
    assert b"Active filters" in res.data
    assert b"Articles" in res.data
    assert b"Quick filters" in res.data
    assert b"Digital access" in res.data
    assert b"Needs review" in res.data
    assert b"Peer-reviewed" in res.data
    assert b"name=\"type\" value=\"ARTICLE\"" in res.data


def test_catalogue_collection_empty_state_renders(client):
    """Test collection empty state sends users back to collection browsing."""
    res = client.get(
        url_for("nhrils_catalogue_shell.catalogue_search_view"),
        query_string={"type": "STANDARD", "q": "nonexistent-catalogue-query"},
    )

    assert res.status_code == 200
    assert b"Guidelines and standards" in res.data
    assert b"No records found in this collection" in res.data
    assert b"Try clearing filters or returning to Collections" in res.data
    assert b"Back to Collections" in res.data
    assert b"Reset search" not in res.data


def test_catalogue_search_review_only_result_card_renders(client):
    """Test review-only result cards expose clear metadata and no online action."""
    res = client.get(
        url_for("nhrils_catalogue_shell.catalogue_search_view"),
        query_string={"q": "schistosomiasis", "availability": "review"},
    )

    assert res.status_code == 200
    assert b"Metadata review needed" in res.data
    assert b"No digital source attached" in res.data
    assert b"View online" not in res.data
    assert b"Record summary" in res.data
    assert b"ARTICLE" in res.data
    assert b"ENG" in res.data
    assert b"Open record" in res.data


def test_catalogue_search_results_pagination_renders(client):
    """Test search result pagination preserves active query and filters."""
    res = client.get(
        url_for("nhrils_catalogue_shell.catalogue_search_view"),
        query_string={
            "q": "malaria",
            "language": "ENG",
            "subject": "malaria",
            "page": "1",
            "size": "5",
        },
    )

    assert res.status_code == 200
    assert b"Showing 1-5" in res.data
    assert b"Page 1 of" in res.data
    assert b"Previous" in res.data
    assert b"Next" in res.data
    assert b"q=malaria" in res.data
    assert b"language=ENG" in res.data
    assert b"subject=malaria" in res.data
    assert b"page=2" in res.data
    assert b"size=5" in res.data


def test_catalogue_search_result_links_preserve_result_context(client):
    """Test record links carry the current search context as a safe return URL."""
    res = client.get(
        url_for("nhrils_catalogue_shell.catalogue_search_view"),
        query_string={
            "q": "malaria",
            "availability": "online",
            "language": "ENG",
            "subject": "malaria",
            "page": "2",
            "size": "5",
        },
    )

    assert res.status_code == 200
    assert b"/nhrils/catalogue/records/" in res.data
    assert b"return_to=" in res.data
    assert b"/nhrils/catalogue/search%3Fq%3Dmalaria" in res.data
    assert b"availability%3Donline" in res.data
    assert b"language%3DENG" in res.data
    assert b"subject%3Dmalaria" in res.data
    assert b"page%3D2" in res.data
    assert b"size%3D5" in res.data


def test_catalogue_record_detail_shell_renders(client):
    """Test the NHRILS public review record detail shell."""
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_view",
            pid="nimr-doc-0001",
        )
    )

    assert res.status_code == 200
    assert b"Review record" in res.data
    assert b"Artemisinin-resistant malaria in Africa demands urgent action" in res.data
    assert b"Mehul Dhorda" in res.data
    assert b"Digital access available" in res.data
    assert b"Availability and access" in res.data
    assert b"View online" in res.data
    assert b"Record summary" in res.data
    assert b"Abstract" in res.data
    assert b"Subjects" in res.data
    assert b"Local PID" in res.data
    assert b"Language" in res.data
    assert b"rel=\"noopener noreferrer\"" in res.data
    assert b"Request item" in res.data
    assert b"Ask librarian" in res.data
    assert b"/nhrils/catalogue/records/nimr-doc-0001/request" in res.data
    assert b"No physical holding attached" in res.data
    assert b"Request workflow will be enabled" in res.data
    assert b"Bibliographic metadata" in res.data
    assert b"Before production import" in res.data
    assert b"Confirm metadata" in res.data
    assert b"NIMR source page" in res.data


def test_catalogue_record_detail_identifier_links_render(client):
    """Test DOI identifiers are rendered as safe external links."""
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_view",
            pid="nimr-doc-0002",
        )
    )

    assert res.status_code == 200
    assert b"DOI" in res.data
    assert b"10.1101/2023.11.07.23298207" in res.data
    assert b"https://doi.org/10.1101/2023.11.07.23298207" in res.data
    assert b"target=\"_blank\"" in res.data
    assert b"rel=\"noopener noreferrer\"" in res.data


def test_catalogue_record_detail_review_only_access_panel(client):
    """Test review-only records show disabled access actions honestly."""
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_view",
            pid="nimr-doc-0004",
        )
    )

    assert res.status_code == 200
    assert b"Metadata review required" in res.data
    assert b"No digital access link is attached" in res.data
    assert b"Not attached" in res.data
    assert b"nhrils-button-disabled" in res.data
    assert b"Request workflow will be enabled" in res.data
    assert b"Librarian contact workflow is pending" in res.data


def test_catalogue_record_detail_back_link_uses_safe_return_context(client):
    """Test record detail back link returns to the previous result state."""
    return_to = (
        "/nhrils/catalogue/search?q=malaria&availability=online"
        "&language=ENG&subject=malaria&page=2&size=5"
    )
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_view",
            pid="nimr-doc-0001",
        ),
        query_string={"return_to": return_to},
    )

    assert res.status_code == 200
    assert b"Back to results" in res.data
    assert b"/nhrils/catalogue/search?q=malaria&amp;availability=online" in res.data
    assert b"language=ENG" in res.data
    assert b"subject=malaria" in res.data
    assert b"page=2" in res.data
    assert b"size=5" in res.data


def test_catalogue_record_detail_rejects_external_return_context(client):
    """Test external return URLs are not rendered into record detail links."""
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_view",
            pid="nimr-doc-0001",
        ),
        query_string={"return_to": "https://example.test/phishing"},
    )

    assert res.status_code == 200
    assert b"https://example.test/phishing" not in res.data
    assert b'href="/nhrils/catalogue/search"' in res.data


def test_catalogue_record_detail_rejects_search_prefix_lookalike(client):
    """Test non-search catalogue paths cannot be used as return targets."""
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_view",
            pid="nimr-doc-0001",
        ),
        query_string={"return_to": "/nhrils/catalogue/searchbad"},
    )

    assert res.status_code == 200
    assert b"/nhrils/catalogue/searchbad" not in res.data
    assert b'href="/nhrils/catalogue/search"' in res.data


def test_catalogue_record_detail_unknown_pid_returns_404(client):
    """Test that unknown review seed PIDs return not found."""
    res = client.get("/nhrils/catalogue/records/not-a-seed-pid")

    assert res.status_code == 404


def test_catalogue_record_request_shell_renders(client):
    """Test the NHRILS request workflow shell renders without writes."""
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_request_view",
            pid="nimr-doc-0001",
        )
    )

    assert res.status_code == 200
    assert b"Catalogue request" in res.data
    assert b"Prepare a library request" in res.data
    assert b"Artemisinin-resistant malaria in Africa demands urgent action" in res.data
    assert b"Request record summary" in res.data
    assert b"Request details" in res.data
    assert b"Information the library will need" in res.data
    assert b"Request submission is intentionally disabled" in res.data
    assert b"Request workflow shell" in res.data
    assert b"Not submitting yet" in res.data
    assert b"Contact support" in res.data
    assert b"/nhrils/catalogue/contact" in res.data
    assert b"method=\"post\"" not in res.data


def test_catalogue_record_request_back_link_uses_safe_return_context(client):
    """Test request shell preserves only safe catalogue result return links."""
    return_to = "/nhrils/catalogue/search?q=malaria&availability=online"
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_request_view",
            pid="nimr-doc-0001",
        ),
        query_string={"return_to": return_to},
    )

    assert res.status_code == 200
    assert b"/nhrils/catalogue/search?q=malaria&amp;availability=online" in res.data
    assert b"Back to results" in res.data


def test_catalogue_record_request_rejects_external_return_context(client):
    """Test request shell does not render external return URLs."""
    res = client.get(
        url_for(
            "nhrils_catalogue_shell.catalogue_record_request_view",
            pid="nimr-doc-0001",
        ),
        query_string={"return_to": "https://example.test/phishing"},
    )

    assert res.status_code == 200
    assert b"https://example.test/phishing" not in res.data
    assert b'href="/nhrils/catalogue/search"' in res.data


def test_catalogue_record_request_unknown_pid_returns_404(client):
    """Test that unknown review seed PIDs return not found for request shell."""
    res = client.get("/nhrils/catalogue/records/not-a-seed-pid/request")

    assert res.status_code == 404


def test_catalogue_search_results_empty_state(client):
    """Test that the review search results shell has a useful empty state."""
    res = client.get(
        url_for("nhrils_catalogue_shell.catalogue_search_view"),
        query_string={"q": "nonexistent-catalogue-query"},
    )

    assert res.status_code == 200
    assert b"0 review records" in res.data
    assert b"No review records match this search" in res.data
    assert b"Reset search" in res.data


def test_seed_catalogue_search_backend_filters_and_paginates():
    """Test the read-only seed backend behind the catalogue search route."""
    response = SeedCatalogueSearchBackend().search(
        CatalogueSearchQuery(
            query="malaria",
            availability="online",
            page=1,
            size=5,
        )
    )

    assert response.backend == "seed-review"
    assert response.result_count >= 1
    assert 0 < len(response.results) <= 5
    assert response.query.selected_filters == {
        "availability": "online",
        "type": "",
        "year": "",
        "source": "",
        "language": "",
        "subject": "",
    }
    assert all(result["has_online_access"] for result in response.results)
    assert all(result["access"]["label"] == "Online access" for result in response.results)
    assert all(result["access"]["online_url"] for result in response.results)
    assert all(result["source"] for result in response.results)
    assert all(result["languages"] for result in response.results)
    assert any("malaria" in result["title"].lower() for result in response.results)
    assert {"availability", "type", "year", "source", "language", "subject"}.issubset(
        response.facets
    )
    assert response.pagination == {
        "page": 1,
        "requested_page": 1,
        "size": 5,
        "total_pages": response.pagination["total_pages"],
        "first_item": 1,
        "last_item": len(response.results),
        "has_previous": False,
        "has_next": response.pagination["total_pages"] > 1,
        "previous_page": None,
        "next_page": 2 if response.pagination["total_pages"] > 1 else None,
    }
    assert response.facets["availability"][0]["label"] == "Digital access"


def test_seed_catalogue_search_backend_shapes_review_only_result_access():
    """Test result card access state for records without digital e-items."""
    response = SeedCatalogueSearchBackend().search(
        CatalogueSearchQuery(
            query="schistosomiasis",
            availability="review",
            page=1,
            size=5,
        )
    )

    assert response.result_count >= 1
    assert all(not result["has_online_access"] for result in response.results)
    assert all(
        result["access"]["label"] == "Metadata review needed"
        for result in response.results
    )
    assert all(result["access"]["online_url"] is None for result in response.results)


def test_seed_catalogue_search_backend_clamps_requested_page():
    """Test out-of-range requested pages render the last available page."""
    response = SeedCatalogueSearchBackend().search(
        CatalogueSearchQuery(page=99, size=10)
    )

    assert response.result_count == 42
    assert response.pagination["requested_page"] == 99
    assert response.pagination["page"] == 5
    assert response.pagination["total_pages"] == 5
    assert response.pagination["first_item"] == 41
    assert response.pagination["last_item"] == 42
    assert response.pagination["has_previous"]
    assert not response.pagination["has_next"]
    assert len(response.results) == 2


def test_seed_catalogue_search_backend_filters_by_source_language_and_subject():
    """Test source, language, and subject filters for the review seed backend."""
    response = SeedCatalogueSearchBackend().search(
        CatalogueSearchQuery(
            source="NIMR 2025/2026 Peer Reviewed Papers",
            language="ENG",
            subject="malaria",
            page=1,
            size=20,
        )
    )

    assert response.result_count >= 1
    assert response.query.selected_filters["source"] == (
        "NIMR 2025/2026 Peer Reviewed Papers"
    )
    assert response.query.selected_filters["language"] == "ENG"
    assert response.query.selected_filters["subject"] == "malaria"
    assert all("malaria" in result["keywords"] for result in response.results)
    assert any(
        facet["value"] == "NIMR 2025/2026 Peer Reviewed Papers"
        for facet in response.facets["source"]
    )
    assert response.facets["language"] == [
        {"value": "ENG", "label": "ENG", "count": 42}
    ]
    assert any(facet["value"] == "malaria" for facet in response.facets["subject"])


def test_seed_catalogue_search_backend_builds_collection_search_context():
    """Test collection-filtered searches expose template-ready context."""
    response = SeedCatalogueSearchBackend().search(
        CatalogueSearchQuery(material_type="ARTICLE", page=1)
    )

    assert response.context["eyebrow"] == "Collection"
    assert response.context["title"] == "Peer-reviewed papers"
    assert response.context["collection"] == {
        "eyebrow": "Collection",
        "title": "Peer-reviewed papers",
        "lead": (
            "Published NIMR research articles and collaborative papers for "
            "scientific discovery."
        ),
        "back_label": "Back to Collections",
        "back_href": "/nhrils/catalogue/collections",
    }
    assert response.context["active_filters"] == [
        {
            "name": "type",
            "value": "ARTICLE",
            "label": "Articles",
            "href": "/nhrils/catalogue/search",
        }
    ]
    assert response.context["quick_filters"][0] == {
        "label": "Digital access",
        "name": "availability",
        "value": "online",
        "href": "/nhrils/catalogue/search?availability=online&type=ARTICLE",
        "selected": False,
    }
    assert response.context["quick_filters"][3]["selected"]
    assert response.context["empty_title"] == "No records found in this collection"


def test_seed_catalogue_search_backend_builds_seed_review_summary():
    """Test the read-only seed review summary behind the review page."""
    response = SeedCatalogueSearchBackend().seed_review()

    assert response.backend == "seed-review"
    assert response.summary["record_count"] == 42
    assert response.summary["digital_link_count"] == 21
    assert response.summary["physical_item_count"] == 0
    assert response.summary["records_needing_review"] == (
        response.summary["record_count"]
        - response.summary["records_with_digital_access"]
    )
    assert response.summary["identifier_record_count"] >= len(
        response.records_with_identifiers
    )
    assert response.summary["physical_holdings_missing_count"] == 42
    assert response.summary["subject_cleanup_count"] == len(response.subject_cleanup)
    assert response.summary["material_type_count"] >= 1
    assert response.review_actions == [
        {
            "label": "Missing digital access",
            "count": response.summary["records_needing_review"],
            "summary": (
                "Open records that need a public, licensed, or internal source decision."
            ),
            "href": "/nhrils/catalogue/search?availability=review",
            "status": "Needs review",
        },
        {
            "label": "Records with identifiers",
            "count": response.summary["identifier_record_count"],
            "summary": (
                "Check DOI, ISSN, ISBN, and local identifier coverage before import."
            ),
            "href": "#nhrils-identifiers",
            "status": "Review",
        },
        {
            "label": "Physical holdings missing",
            "count": response.summary["physical_holdings_missing_count"],
            "summary": (
                "Confirm whether each record has no shelf copy or needs holdings added."
            ),
            "href": "#nhrils-holdings",
            "status": "Confirm",
        },
        {
            "label": "All seed records",
            "count": response.summary["record_count"],
            "summary": "Browse the full provisional catalogue dataset.",
            "href": "/nhrils/catalogue/search",
            "status": "Browse",
        },
    ]
    assert response.readiness_checks == [
        {
            "label": "Digital access",
            "value": "21 of 42 linked",
            "status": "Needs review",
        },
        {
            "label": "Identifiers",
            "value": "19 records have identifiers",
            "status": "Review",
        },
        {
            "label": "Physical holdings",
            "value": "0 items attached",
            "status": "Confirm",
        },
        {
            "label": "Controlled subjects",
            "value": "{} low-frequency terms listed".format(
                response.summary["subject_cleanup_count"]
            ),
            "status": "Review",
        },
    ]
    assert response.quality_sections == [
        {
            "label": "Digital access cleanup",
            "count": response.summary["records_needing_review"],
            "status": "Needs review",
            "summary": (
                "Classify missing public, licensed, internal, or restricted access decisions."
            ),
            "href": "/nhrils/catalogue/search?availability=review",
            "action_label": "Open records",
        },
        {
            "label": "Identifier review",
            "count": response.summary["identifier_record_count"],
            "status": "Review",
            "summary": "Confirm DOI, ISSN, ISBN, and local identifier consistency.",
            "href": "#nhrils-identifiers",
            "action_label": "Review identifiers",
        },
        {
            "label": "Physical holdings",
            "count": response.summary["physical_holdings_missing_count"],
            "status": "Confirm",
            "summary": (
                "Decide whether a catalogue record needs a shelf copy, item, barcode, or no holding."
            ),
            "href": "#nhrils-holdings",
            "action_label": "Review holdings",
        },
        {
            "label": "Subject vocabulary",
            "count": response.summary["subject_cleanup_count"],
            "status": "Review",
            "summary": (
                "Normalize low-frequency terms before controlled vocabulary approval."
            ),
            "href": "#nhrils-subjects",
            "action_label": "Review subjects",
        },
    ]
    assert response.records_missing_digital_access
    assert all(
        not record["has_online_access"]
        for record in response.records_missing_digital_access
    )
    assert len(response.records_missing_digital_access) <= 10
    assert response.records_missing_physical_holdings
    assert len(response.records_missing_physical_holdings) <= 10
    assert len(response.records_with_identifiers) <= 10
    assert [group["label"] for group in response.distribution_groups] == [
        "Material type distribution",
        "Source distribution",
        "Language distribution",
    ]
    assert all(group["items"] for group in response.distribution_groups)
    assert response.source_distribution
    assert response.language_distribution == [
        {"value": "ENG", "label": "ENG", "count": 42}
    ]
    assert response.subject_cleanup
    assert all("review_note" in subject for subject in response.subject_cleanup)


def test_seed_catalogue_search_backend_builds_collections():
    """Test seed-backed catalogue collections and search filter handoffs."""
    response = SeedCatalogueSearchBackend().collections()

    assert response.backend == "seed-review"
    assert response.summary == {
        "collection_count": 5,
        "record_count": 42,
        "digital_link_count": 21,
    }
    assert [collection["title"] for collection in response.collections] == [
        "Peer-reviewed papers",
        "Reports",
        "Journals",
        "Guidelines and standards",
        "Proceedings",
    ]
    assert [collection["count"] for collection in response.collections] == [
        25,
        1,
        5,
        9,
        2,
    ]
    assert response.collections[0]["href"] == "/nhrils/catalogue/search?type=ARTICLE"
    assert response.collections[3]["href"] == "/nhrils/catalogue/search?type=STANDARD"
    assert all(collection["summary"] for collection in response.collections)


def test_catalogue_search_query_reads_extended_filter_args():
    """Test request argument parsing for facet-ready catalogue search."""
    query = CatalogueSearchQuery.from_mapping(
        {
            "q": " health ",
            "type": "ARTICLE",
            "year": "2026",
            "availability": "online",
            "source": "NIMR Publications",
            "language": "ENG",
            "subject": "malaria",
            "page": "2",
            "size": "500",
        }
    )

    assert query.query == "health"
    assert query.material_type == "ARTICLE"
    assert query.year == "2026"
    assert query.availability == "online"
    assert query.source == "NIMR Publications"
    assert query.language == "ENG"
    assert query.subject == "malaria"
    assert query.page == 2
    assert query.size == 100
    assert query.selected_filters == {
        "availability": "online",
        "type": "ARTICLE",
        "year": "2026",
        "source": "NIMR Publications",
        "language": "ENG",
        "subject": "malaria",
    }


def test_seed_catalogue_search_backend_record_detail():
    """Test record detail shaping through the search service boundary."""
    response = SeedCatalogueSearchBackend().get_record("nimr-doc-0001")

    assert response is not None
    assert response.backend == "seed-review"
    assert response.record["pid"] == "nimr-doc-0001"
    assert response.record["has_online_access"]
    assert response.record["access"]["status"]["label"] == "Digital access available"
    assert response.record["access"]["online_url"]
    assert not response.record["access"]["request"]["enabled"]
    assert not response.record["access"]["contact"]["enabled"]
    assert response.record["primary_link"] == {
        "label": "NIMR source page",
        "href": "https://nimr.or.tz/publications/",
    }
    assert response.record["link_items"] == [response.record["primary_link"]]
    assert response.record["language_label"] == "ENG"
    assert response.record["summary_items"] == [
        {"label": "Type", "value": "ARTICLE"},
        {"label": "Year", "value": "2026"},
        {"label": "Source", "value": "NIMR Publications"},
        {"label": "Language", "value": "ENG"},
        {"label": "Local PID", "value": "nimr-doc-0001"},
    ]
    assert response.record["all_authors"]
    assert response.record["urls"]


def test_seed_catalogue_search_backend_record_detail_identifier_items():
    """Test identifier shaping for catalogue detail records."""
    response = SeedCatalogueSearchBackend().get_record("nimr-doc-0002")

    assert response is not None
    assert response.record["identifier_items"] == [
        {
            "scheme": "DOI",
            "value": "10.1101/2023.11.07.23298207",
            "href": "https://doi.org/10.1101/2023.11.07.23298207",
        }
    ]


def test_seed_catalogue_search_backend_record_detail_without_eitem():
    """Test access shaping for records without attached digital e-items."""
    response = SeedCatalogueSearchBackend().get_record("nimr-doc-0004")

    assert response is not None
    assert not response.record["has_online_access"]
    assert response.record["access"]["status"]["label"] == "Metadata review required"
    assert response.record["access"]["online_url"] is None
    assert response.record["primary_link"] is None
    assert response.record["link_items"] == []
    assert response.record["access"]["physical_holding"]["label"] == (
        "No physical holding attached"
    )
    assert not response.record["urls"]


def test_native_catalogue_search_backend_is_explicitly_gated():
    """Test that the native backend placeholder cannot silently query indexes."""
    backend = InvenioCatalogueSearchBackend()

    with pytest.raises(NotImplementedError, match="OpenSearch"):
        backend.search(CatalogueSearchQuery(query="malaria"))

    with pytest.raises(NotImplementedError, match="OpenSearch"):
        backend.get_record("nimr-doc-0001")

    with pytest.raises(NotImplementedError, match="OpenSearch"):
        backend.collections()

    with pytest.raises(NotImplementedError, match="OpenSearch"):
        backend.seed_review()


def test_logged_out_page_uses_nhrils_return_path(client, users):
    """Test that the logout page no longer points to local development URLs."""
    res = client.get(url_for("logged_out.logged_out_view"))

    assert b"127.0.0.1" not in res.data
    assert b"/nhrils/catalogue" in res.data


def test_catalogue_shell_static_markup():
    """Test catalogue shell copy without requiring service-backed fixtures."""
    shell = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "templates"
        / "invenio_app_ils"
        / "catalogue_shell.html"
    ).read_text(encoding="utf-8")

    assert "Find health research resources held by NIMR" in shell
    assert "Search the catalogue" in shell
    assert "/nhrils/catalogue/search" in shell
    assert "/nhrils/catalogue/search-guide" in shell
    assert "/pages/search-guide" not in shell
    assert "seed records" in shell
    assert "Featured records" in shell
    assert "Representative NIMR catalogue records" in shell
    assert "What needs confirmation" in shell
    assert "Artemisinin-resistant malaria" in shell
    assert "Tanzania Journal of Health Research" in shell
    assert "Database and OpenSearch writes remain approval-gated" in shell
    assert "Seed data is ready for NIMR review" in shell


def test_catalogue_search_static_markup():
    """Test catalogue search shell copy without requiring service-backed fixtures."""
    shell = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "templates"
        / "invenio_app_ils"
        / "catalogue_search.html"
    ).read_text(encoding="utf-8")

    assert "search_context.title" in shell
    assert "nhrils-filter-context" in shell
    assert "Active filters" in shell
    assert "Quick filters" in shell
    assert "search_context.empty_title" in shell
    assert "Refine results" in shell
    assert "Source" in shell
    assert "Language" in shell
    assert "Subject" in shell
    assert "search_context.empty_lead" in shell
    assert "Back to Collections" in shell
    assert "search_context.lead" in shell
    assert "Search results pages" in shell
    assert "Showing {{ pagination.first_item }}-{{ pagination.last_item }}" in shell
    assert "return_to={{ search_return_url|urlencode }}" in shell
    assert "nhrils-result-meta" in shell
    assert "result.access.label" in shell
    assert "result.access.summary" in shell
    assert "result.access.online_url" in shell
    assert "View online" in shell
    assert "/nhrils/catalogue/search" in shell
    assert "/nhrils/catalogue/search-guide" in shell
    assert "/pages/search-guide" not in shell
    assert "result.detail_url" in shell


def test_catalogue_record_static_markup():
    """Test catalogue record shell copy without requiring service-backed fixtures."""
    shell = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "templates"
        / "invenio_app_ils"
        / "catalogue_record.html"
    ).read_text(encoding="utf-8")

    assert "Bibliographic metadata" in shell
    assert 'href="{{ return_to }}"' in shell
    assert "nhrils-record-fact-grid" in shell
    assert "record.summary_items" in shell
    assert "Record summary" in shell
    assert "Abstract" in shell
    assert "Subjects" in shell
    assert "Availability and access" in shell
    assert "record.access.status.label" in shell
    assert "View online" in shell
    assert "record.primary_link" in shell
    assert "record.identifier_items" in shell
    assert "record.link_items" in shell
    assert "noopener noreferrer" in shell
    assert "record.access.request.label" in shell
    assert "record.access.contact.label" in shell
    assert "record.access.physical_holding.label" in shell
    assert "record.access.contact.summary" in shell
    assert "/request" in shell
    assert "Before production import" in shell
    assert "Confirm metadata" in shell
    assert "Confirm access" in shell
    assert "Add holdings" in shell
    assert "_catalogue_topbar.html" in shell


def test_catalogue_record_request_static_markup():
    """Test catalogue request shell copy and non-mutating structure."""
    shell = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "templates"
        / "invenio_app_ils"
        / "catalogue_record_request.html"
    ).read_text(encoding="utf-8")

    assert "Prepare a library request" in shell
    assert "Back to record" in shell
    assert "Selected record" in shell
    assert "Request record summary" in shell
    assert "Information the library will need" in shell
    assert "Request submission is intentionally disabled" in shell
    assert "Request workflow shell" in shell
    assert "Not submitting yet" in shell
    assert "Contact support" in shell
    assert "/nhrils/catalogue/contact" in shell
    assert "record.pid" in shell
    assert "record.access.status.label" in shell
    assert "record.access.physical_holding.label" in shell
    assert "<form" not in shell
    assert "method=\"post\"" not in shell
    assert "_catalogue_topbar.html" in shell


def test_catalogue_info_static_markup():
    """Test catalogue help page copy and navigation."""
    shell = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "templates"
        / "invenio_app_ils"
        / "catalogue_info.html"
    ).read_text(encoding="utf-8")
    nav = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "templates"
        / "invenio_app_ils"
        / "_catalogue_topbar.html"
    ).read_text(encoding="utf-8")

    assert "nhrils-info-title" in shell
    assert "Search the catalogue" in shell
    assert "Open catalogue results" in shell
    assert "/nhrils/catalogue/search" in shell
    assert "/nhrils/catalogue/collections" in nav
    assert "/nhrils/catalogue/search-guide" in nav
    assert "/nhrils/catalogue/seed-review" in nav
    assert "/nhrils/catalogue/about" in nav
    assert "/nhrils/catalogue/contact" in nav
    assert "/nhrils/catalogue/terms" in nav
    assert "/nhrils/catalogue/privacy" in nav
    assert "/pages/search-guide" not in nav


def test_catalogue_terms_and_privacy_static_definitions():
    """Test terms and privacy page definitions stay visible and placeholder-safe."""
    views = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "views.py"
    ).read_text(encoding="utf-8")

    assert "\"terms\"" in views
    assert "\"privacy\"" in views
    assert "Catalogue use and access conditions" in views
    assert "Draft MVP copy for review, not final legal text." in views
    assert "Catalogue privacy and data handling" in views
    assert "MVP placeholder notice for review." in views
    assert "Future patron data handling" in views
    assert "def catalogue_terms_view" in views
    assert "def catalogue_privacy_view" in views


def test_catalogue_seed_review_static_markup():
    """Test seed review page copy and structure."""
    shell = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "templates"
        / "invenio_app_ils"
        / "catalogue_seed_review.html"
    ).read_text(encoding="utf-8")

    assert "Review the catalogue seed before import" in shell
    assert "Search seed records" in shell
    assert "Review workflow" in shell
    assert "Start with the records that need decisions" in shell
    assert "nhrils-review-action-grid" in shell
    assert "review.review_actions" in shell
    assert "Data quality workbench" in shell
    assert "review.quality_sections" in shell
    assert "review.readiness_checks" in shell
    assert "nhrils-readiness" in shell
    assert "nhrils-holdings" in shell
    assert "nhrils-identifiers" in shell
    assert "nhrils-subjects" in shell
    assert "Records missing digital access" in shell
    assert "View filtered records" in shell
    assert "records_missing_physical_holdings" in shell
    assert "Records with identifiers" in shell
    assert "Source, language, and type coverage" in shell
    assert "review.distribution_groups" in shell
    assert "Subjects needing vocabulary review" in shell
    assert "database import, indexing, or circulation setup is approved" in shell
    assert "/nhrils/catalogue/search?availability=review" in shell
    assert "_catalogue_topbar.html" in shell


def test_catalogue_collections_static_markup():
    """Test catalogue collections page copy and structure."""
    shell = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "templates"
        / "invenio_app_ils"
        / "catalogue_collections.html"
    ).read_text(encoding="utf-8")

    assert "Browse NIMR resources by collection" in shell
    assert "Search all collections" in shell
    assert "nhrils-collection-grid" in shell
    assert "collection.material_type" in shell
    assert "collection.action_label" in shell
    assert "Browse all records" in shell
    assert "/nhrils/catalogue/seed-review" in shell
    assert "_catalogue_topbar.html" in shell


def test_search_guide_uses_health_research_examples():
    """Test that the public search guide is NHRILS-domain oriented."""
    guide = (
        Path(__file__).resolve().parents[1]
        / "invenio_app_ils"
        / "static_pages"
        / "search_guide.html"
    ).read_text(encoding="utf-8")

    assert "NHRILS catalogue" in guide
    assert "malaria guidelines" in guide
    assert "maternal health" in guide
    assert "Tanzania Journal of Health Research" in guide
    assert "dark matter" not in guide
    assert "Albert Einstein" not in guide
    assert "affiliated to CERN" not in guide


def test_nimr_publications_seed_bundle_shape():
    """Test that the provisional seed bundle can support catalogue MVP review."""
    seed_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "seed-data"
        / "nimr-publications-seed.json"
    )
    seed = json.loads(seed_path.read_text(encoding="utf-8"))

    documents = seed["documents"]
    eitems = seed["eitems"]
    document_pids = {document["pid"] for document in documents}

    assert len(documents) >= 40
    assert len(document_pids) == len(documents)
    assert len({eitem["pid"] for eitem in eitems}) == len(eitems)
    assert seed["items"] == []

    required_document_fields = {
        "$schema",
        "pid",
        "title",
        "authors",
        "publication_year",
        "document_type",
        "created_by",
    }
    for document in documents:
        assert required_document_fields.issubset(document)
        assert document["authors"]
        assert document["document_type"] in {
            "ARTICLE",
            "BOOK",
            "PROCEEDINGS",
            "STANDARD",
            "SERIAL_ISSUE",
        }

    assert {eitem["document_pid"] for eitem in eitems}.issubset(document_pids)
    assert "https://nimr.or.tz/peer-reviewed-papers/" in seed["bundle"]["source_pages"]
    assert any(
        document["source"] == "NIMR 2025/2026 Peer Reviewed Papers"
        for document in documents
    )


def test_nimr_publications_seed_dry_run_validator_accepts_bundle():
    """Test that the seed bundle passes the dry-run import-readiness gate."""
    repo_root = Path(__file__).resolve().parents[1]
    validator_path = repo_root / "scripts" / "validate_seed_bundle.py"
    seed_path = repo_root / "docs" / "seed-data" / "nimr-publications-seed.json"

    spec = importlib.util.spec_from_file_location("validate_seed_bundle", validator_path)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)

    result = validator.validate_seed_bundle(seed_path)

    assert result["ok"], result["errors"]
    assert result["counts"] == {
        "documents": 42,
        "eitems": 21,
        "locations": 1,
        "internal_locations": 2,
        "items": 0,
    }


def test_nimr_publications_seed_duplicate_pid_detection(tmp_path):
    """Test that duplicate document PIDs fail before import planning."""
    repo_root = Path(__file__).resolve().parents[1]
    validator_path = repo_root / "scripts" / "validate_seed_bundle.py"
    seed_path = repo_root / "docs" / "seed-data" / "nimr-publications-seed.json"
    duplicate_seed_path = tmp_path / "duplicate-seed.json"

    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    seed["documents"][1]["pid"] = seed["documents"][0]["pid"]
    duplicate_seed_path.write_text(json.dumps(seed), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("validate_seed_bundle", validator_path)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)

    result = validator.validate_seed_bundle(duplicate_seed_path)

    assert not result["ok"]
    assert any("Duplicate document PID" in error for error in result["errors"])


def test_nimr_publications_seed_import_plan_is_dry_run():
    """Test that the guarded import planner remains read-only by default."""
    repo_root = Path(__file__).resolve().parents[1]
    importer_path = repo_root / "scripts" / "import_seed_bundle.py"
    seed_path = repo_root / "docs" / "seed-data" / "nimr-publications-seed.json"

    sys_path = str(importer_path.parent)
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)

    spec = importlib.util.spec_from_file_location("import_seed_bundle", importer_path)
    importer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(importer)

    plan = importer.build_import_plan(seed_path)

    assert plan["mode"] == "dry-run"
    assert plan["validation"]["ok"], plan["validation"]["errors"]
    assert [operation["section"] for operation in plan["operations"]] == [
        "locations",
        "internal_locations",
        "documents",
        "eitems",
        "items",
    ]
    assert plan["operations"][2]["entity"] == "Document"
    assert plan["operations"][2]["count"] == 42
    assert "database writes" in plan["blocked_operations"]


def test_nimr_seed_review_renderer_outputs_markdown_and_csv():
    """Test that the seed review report is deterministic and reviewer-friendly."""
    repo_root = Path(__file__).resolve().parents[1]
    renderer_path = repo_root / "scripts" / "render_seed_review.py"
    seed_path = repo_root / "docs" / "seed-data" / "nimr-publications-seed.json"

    sys_path = str(renderer_path.parent)
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)

    spec = importlib.util.spec_from_file_location("render_seed_review", renderer_path)
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)

    summary = renderer.build_review_summary(seed_path)
    markdown = renderer.render_markdown(summary)
    csv_output = renderer.render_csv(summary)

    assert summary["validation"]["ok"], summary["validation"]["errors"]
    assert summary["document_type_counts"]["ARTICLE"] >= 20
    assert "# NHRILS Seed Review" in markdown
    assert "Needs NIMR review" in markdown
    assert "Artemisinin-resistant malaria" in markdown
    assert "Mehul Dhorda; Akira Kaneko; Ryuichi Komatsu" in markdown
    assert "{'full_name'" not in markdown
    assert csv_output.startswith("pid,title,publication_year,document_type")
    assert "digital_links" in csv_output
