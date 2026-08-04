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
        "/nhrils/catalogue/records/<pid>",
        view_func=catalogue_record_view,
    )
    return blueprint


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
