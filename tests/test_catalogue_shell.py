# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 NIMR.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""NHRILS catalogue shell tests."""

from flask import url_for
from pathlib import Path


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
