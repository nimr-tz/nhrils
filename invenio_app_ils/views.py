# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio App ILS views."""

import json
from pathlib import Path

from flask import Blueprint, abort, g, jsonify, render_template, request
from invenio_accounts.views.rest import UserInfoView, default_user_payload
from invenio_userprofiles import UserProfile


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
        "/nhrils/catalogue/records/<pid>",
        view_func=catalogue_record_view,
    )
    return blueprint


def catalogue_shell_view():
    """Render the first NHRILS catalogue shell."""
    return render_template("invenio_app_ils/catalogue_shell.html")


def catalogue_search_view():
    """Render the NHRILS catalogue search results shell from review seed data."""
    seed = _load_nhrils_seed_bundle()
    documents = seed["documents"]
    eitem_document_pids = {eitem["document_pid"] for eitem in seed.get("eitems", [])}
    query = request.args.get("q", "").strip()
    material_type = request.args.get("type", "").strip()
    year = request.args.get("year", "").strip()
    availability = request.args.get("availability", "").strip()

    filtered_documents = _filter_seed_documents(
        documents,
        query=query,
        material_type=material_type,
        year=year,
        availability=availability,
        eitem_document_pids=eitem_document_pids,
    )

    return render_template(
        "invenio_app_ils/catalogue_search.html",
        query=query,
        selected_filters={
            "availability": availability,
            "type": material_type,
            "year": year,
        },
        result_count=len(filtered_documents),
        results=[
            _present_seed_document(document, eitem_document_pids)
            for document in filtered_documents[:25]
        ],
        facets={
            "availability": _build_availability_facets(documents, eitem_document_pids),
            "type": _build_count_facets(documents, "document_type"),
            "year": _build_count_facets(documents, "publication_year"),
        },
    )


def catalogue_record_view(pid):
    """Render a NHRILS review record detail shell from seed data."""
    seed = _load_nhrils_seed_bundle()
    document = next(
        (document for document in seed["documents"] if document["pid"] == pid),
        None,
    )
    if document is None:
        abort(404)

    eitems = [
        eitem for eitem in seed.get("eitems", []) if eitem.get("document_pid") == pid
    ]
    return render_template(
        "invenio_app_ils/catalogue_record.html",
        record=_present_seed_document_detail(document, eitems),
    )


def _load_nhrils_seed_bundle():
    """Load the review seed bundle without mutating database or search state."""
    seed_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "seed-data"
        / "nimr-publications-seed.json"
    )
    return json.loads(seed_path.read_text(encoding="utf-8"))


def _filter_seed_documents(
    documents,
    *,
    query,
    material_type,
    year,
    availability,
    eitem_document_pids,
):
    """Apply lightweight read-only search filters to seed documents."""
    normalized_query = query.lower()
    filtered = []
    for document in documents:
        if material_type and document.get("document_type") != material_type:
            continue
        if year and str(document.get("publication_year", "")) != year:
            continue
        has_online_access = document["pid"] in eitem_document_pids
        if availability == "online" and not has_online_access:
            continue
        if availability == "review" and has_online_access:
            continue
        if normalized_query and normalized_query not in _seed_document_text(document):
            continue
        filtered.append(document)
    return filtered


def _seed_document_text(document):
    """Return searchable text for a review seed document."""
    values = [
        document.get("pid", ""),
        document.get("title", ""),
        document.get("abstract", ""),
        document.get("document_type", ""),
        str(document.get("publication_year", "")),
        document.get("source", ""),
    ]
    values.extend(author.get("full_name", "") for author in document.get("authors", []))
    values.extend(keyword.get("value", "") for keyword in document.get("keywords", []))
    values.extend(
        identifier.get("value", "") for identifier in document.get("identifiers", [])
    )
    return " ".join(values).lower()


def _present_seed_document(document, eitem_document_pids):
    """Shape a seed document for the catalogue results template."""
    authors = [author.get("full_name", "") for author in document.get("authors", [])]
    keywords = [keyword.get("value", "") for keyword in document.get("keywords", [])]
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


def _present_seed_document_detail(document, eitems):
    """Shape a seed document for the catalogue detail template."""
    presented = _present_seed_document(
        document,
        {eitem["document_pid"] for eitem in eitems},
    )
    presented.update(
        {
            "all_authors": [
                author.get("full_name", "") for author in document.get("authors", [])
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


def _build_count_facets(documents, field):
    """Build count facets for a seed document field."""
    counts = {}
    for document in documents:
        value = str(document.get(field, "")).strip()
        if value:
            counts[value] = counts.get(value, 0) + 1
    return [
        {"value": value, "label": value.replace("_", " ").title(), "count": count}
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ][:8]


def _build_availability_facets(documents, eitem_document_pids):
    """Build simple access facets for the seed search shell."""
    online_count = sum(1 for document in documents if document["pid"] in eitem_document_pids)
    review_count = len(documents) - online_count
    return [
        {"value": "online", "label": "Digital access", "count": online_count},
        {"value": "review", "label": "Review record", "count": review_count},
    ]


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
