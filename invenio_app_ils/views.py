# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio App ILS views."""

from flask import Blueprint, abort, g, jsonify, render_template, request
from invenio_accounts.views.rest import UserInfoView, default_user_payload
from invenio_userprofiles import UserProfile

from invenio_app_ils.catalogue.search_service import (
    CatalogueSearchQuery,
    get_catalogue_search_backend,
)


class UserInfoResource(UserInfoView):
    """Retrieve current user's information."""

    def get_user_roles(self):
        """Get all user roles."""
        return [need.value for need in g.identity.provides if need.method == "role"]

    def success_response(self, user):
        """Return response with current user's information."""
        from invenio_app_ils.proxies import current_app_ils

        user_payload = default_user_payload(user)
        user_payload["roles"] = self.get_user_roles()
        # fetch user profile for extra info
        user_profile = UserProfile.get_by_userid(user.id)

        loc_pid_value, _ = current_app_ils.get_default_location_pid
        user_payload.update(
            dict(
                username=user_profile.username,
                full_name=user_profile.full_name,
                location_pid=loc_pid_value,
            )
        )
        return jsonify(user_payload), 200


def create_catalogue_shell_blueprint(app):
    """Create NHRILS catalogue shell blueprint."""
    blueprint = Blueprint("nhrils_catalogue_shell", __name__)
    blueprint.add_url_rule(
        "/nhrils/catalogue",
        view_func=catalogue_shell_view,
    )
    blueprint.add_url_rule(
        "/nhrils/catalogue/search",
        view_func=catalogue_search_view,
    )
    blueprint.add_url_rule(
        "/nhrils/catalogue/collections",
        view_func=catalogue_collections_view,
    )
    blueprint.add_url_rule(
        "/nhrils/catalogue/records/<pid>",
        view_func=catalogue_record_view,
    )
    blueprint.add_url_rule(
        "/nhrils/catalogue/about",
        view_func=catalogue_about_view,
    )
    blueprint.add_url_rule(
        "/nhrils/catalogue/search-guide",
        view_func=catalogue_search_guide_view,
    )
    blueprint.add_url_rule(
        "/nhrils/catalogue/contact",
        view_func=catalogue_contact_view,
    )
    blueprint.add_url_rule(
        "/nhrils/catalogue/seed-review",
        view_func=catalogue_seed_review_view,
    )
    return blueprint


CATALOGUE_HELP_PAGES = {
    "about": {
        "active_page": "about",
        "eyebrow": "About NHRILS",
        "title": "National health research discovery service",
        "lead": (
            "NHRILS is the National Health Research Integrated Library System "
            "for discovering NIMR library materials, publications, reports, "
            "journals, guidelines, and selected digital research resources."
        ),
        "sections": [
            {
                "title": "What the catalogue supports",
                "items": [
                    "Search across representative health research records.",
                    "Filter by material type, access, year, source, language, and subject.",
                    "Open records to review identifiers, abstracts, source links, and availability notes.",
                    "Prepare records for later InvenioILS database import and indexed discovery.",
                ],
            },
            {
                "title": "Current MVP boundary",
                "items": [
                    "The public catalogue shell is review-ready and seed-backed.",
                    "Circulation, patron requests, and production imports remain approval-gated.",
                    "Physical holdings will be attached after locations, shelves, and barcodes are confirmed.",
                ],
            },
        ],
        "aside_title": "Catalogue scope",
        "aside_items": [
            ("Primary users", "Researchers, students, librarians, and NIMR staff."),
            ("Record types", "Articles, reports, journals, guidelines, standards, and proceedings."),
            ("Access model", "Public metadata first, with digital links shown when approved."),
        ],
    },
    "search-guide": {
        "active_page": "search-guide",
        "eyebrow": "Search Guide",
        "title": "Search NIMR resources with practical health research terms",
        "lead": (
            "Use the catalogue search to find resources by title, author, "
            "subject, identifier, source, or publication year."
        ),
        "sections": [
            {
                "title": "Recommended search patterns",
                "items": [
                    "Start broad with a topic such as malaria, maternal health, tuberculosis, or climate health.",
                    "Use quoted phrases for exact titles or programme names.",
                    "Search identifiers such as DOI, ISSN, ISBN, report number, or local accession number when available.",
                    "Use filters after searching to narrow by type, source, language, year, or access.",
                ],
            },
            {
                "title": "Examples",
                "items": [
                    "malaria guidelines",
                    "\"Tanzania Journal of Health Research\"",
                    "maternal health 2026",
                    "schistosomiasis online",
                ],
            },
        ],
        "aside_title": "Search workflow",
        "aside_items": [
            ("Search", "Enter a topic, title, author, source, identifier, or year."),
            ("Filter", "Narrow results by the facets shown on the left side."),
            ("Open", "Review the record, identifiers, source, availability, and access notes."),
        ],
    },
    "contact": {
        "active_page": "contact",
        "eyebrow": "Contact And Requests",
        "title": "Request catalogue support from the NIMR library team",
        "lead": (
            "Use this page as the first support route while request workflows, "
            "patron accounts, and circulation operations are being configured."
        ),
        "sections": [
            {
                "title": "When to contact the library",
                "items": [
                    "A record needs metadata correction or a missing identifier.",
                    "A digital link is missing, restricted, or points to the wrong source.",
                    "A physical holding, shelf location, or barcode needs confirmation.",
                    "You need help finding NIMR publications, reports, journals, or guidelines.",
                ],
            },
            {
                "title": "Information to include",
                "items": [
                    "Record title or local PID.",
                    "Your name, institution, and reason for request.",
                    "Whether you need online access, a physical item, or metadata correction.",
                ],
            },
        ],
        "aside_title": "Support status",
        "aside_items": [
            ("Current channel", "Library support details are pending NIMR confirmation."),
            ("Future workflow", "Authenticated request and circulation workflows are planned after MVP validation."),
            ("Catalogue action", "Open a record first, then include the PID in any support request."),
        ],
    },
}


def catalogue_shell_view():
    """Render the first NHRILS catalogue shell."""
    return render_template("invenio_app_ils/catalogue_shell.html")


def catalogue_search_view():
    """Render the NHRILS catalogue search results shell from review seed data."""
    search_query = CatalogueSearchQuery.from_mapping(request.args)
    response = get_catalogue_search_backend().search(search_query)
    search_return_url = request.full_path.rstrip("?")

    return render_template(
        "invenio_app_ils/catalogue_search.html",
        query=response.query.query,
        selected_filters=response.query.selected_filters,
        result_count=response.result_count,
        results=response.results,
        facets=response.facets,
        pagination=response.pagination,
        search_return_url=search_return_url,
        search_backend=response.backend,
    )


def catalogue_collections_view():
    """Render public NHRILS catalogue collection cards from seed data."""
    response = get_catalogue_search_backend().collections()
    return render_template(
        "invenio_app_ils/catalogue_collections.html",
        collections=response.collections,
        summary=response.summary,
        search_backend=response.backend,
    )


def catalogue_record_view(pid):
    """Render a NHRILS review record detail shell from seed data."""
    response = get_catalogue_search_backend().get_record(pid)
    if response is None:
        abort(404)

    return render_template(
        "invenio_app_ils/catalogue_record.html",
        record=response.record,
        return_to=_safe_catalogue_return_url(request.args.get("return_to")),
        search_backend=response.backend,
    )


def catalogue_about_view():
    """Render the NHRILS catalogue about page."""
    return _render_catalogue_help_page("about")


def catalogue_search_guide_view():
    """Render the NHRILS catalogue search guide page."""
    return _render_catalogue_help_page("search-guide")


def catalogue_contact_view():
    """Render the NHRILS catalogue contact page."""
    return _render_catalogue_help_page("contact")


def catalogue_seed_review_view():
    """Render a read-only NHRILS seed dataset review page."""
    response = get_catalogue_search_backend().seed_review()
    return render_template(
        "invenio_app_ils/catalogue_seed_review.html",
        review=response,
    )


def _render_catalogue_help_page(page):
    """Render a static NHRILS catalogue help page."""
    return render_template(
        "invenio_app_ils/catalogue_info.html",
        page=CATALOGUE_HELP_PAGES[page],
    )


def _safe_catalogue_return_url(value):
    """Return a safe catalogue search back link."""
    if value and (
        value == "/nhrils/catalogue/search"
        or value.startswith("/nhrils/catalogue/search?")
    ):
        return value
    return "/nhrils/catalogue/search"


def create_logged_out_blueprint(app):
    """Create logged_out blueprint."""
    blueprint = Blueprint("logged_out", __name__)
    if app.config["DEBUG"]:
        blueprint.add_url_rule(
            "/logged-out",
            view_func=logged_out_view,
        )
    return blueprint


def logged_out_view():
    """Render logged_out view."""
    return render_template("logged_out.html")
