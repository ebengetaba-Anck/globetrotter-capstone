"""
app/activities.py

Activity search endpoint (things to do in Douala).

Routes
------
GET /activities?q=marche&tag=food&quartier=Akwa
    Returns activities that match any of the provided query parameters.
    All parameters are optional; omitting them returns the full catalogue.
"""
from flask import Blueprint, request, jsonify

from app.models import get_all_activities

activities_bp = Blueprint("activities", __name__)


@activities_bp.route("/activities", methods=["GET"])
def search_activities():
    """Search activities by name keyword, tag, and/or quartier.

    Query parameters (all optional):
        q         – free-text search against name, quartier, and description
        tag       – filter by a single interest tag (e.g. "culture")
        quartier  – filter by neighbourhood name (e.g. "Akwa")
        max_cost  – filter by maximum cost (integer)

    Returns a JSON list of matching activity objects.
    """
    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip().lower()
    quartier = request.args.get("quartier", "").strip().lower()
    max_cost_str = request.args.get("max_cost", "").strip()

    max_cost = None
    if max_cost_str:
        try:
            max_cost = int(max_cost_str)
        except ValueError:
            return jsonify({"error": "max_cost must be an integer"}), 400

    activities = get_all_activities()
    results = []

    for act in activities:
        if q:
            searchable = " ".join([
                act.get("name", ""),
                act.get("quartier", ""),
                act.get("description", ""),
            ]).lower()
            if q not in searchable:
                continue

        if tag and tag not in [t.lower() for t in act.get("tags", [])]:
            continue

        if quartier and quartier != act.get("quartier", "").lower():
            continue

        if max_cost is not None:
            cost = act.get("avg_cost")
            if cost is None or cost > max_cost:
                continue

        results.append(act)

    return jsonify(results), 200