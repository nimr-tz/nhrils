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


def test_catalogue_shell_renders(client):
    """Test the NHRILS public catalogue shell route."""
    res = client.get(url_for("nhrils_catalogue_shell.catalogue_shell_view"))

    assert res.status_code == 200
    assert b"NHRILS" in res.data
    assert b"National Health Research Integrated Library System" in res.data
    assert b"Search the catalogue" in res.data
    assert b"/search" in res.data
    assert b"nimr.svg" in res.data


def test_logged_out_page_uses_nhrils_return_path(client, users):
    """Test that the logout page no longer points to local development URLs."""
    res = client.get(url_for("logged_out.logged_out_view"))

    assert res.status_code == 200
    assert b"127.0.0.1" not in res.data
    assert b"/nhrils/catalogue" in res.data


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
