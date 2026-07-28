"""
app/destinations.py

Destination search endpoint.

Routes
------
GET /destinations?q=akwa&tag=food&quartier=Bonanjo&max_cost=5000
    Returns destinations that match any of the provided query parameters.
    All parameters are optional; omitting them returns the full catalogue.
"""
from flask import Blueprint, request, jsonify

from app.models import get_all_destinations

destinations_bp = Blueprint("destinations", __name__)


@destinations_bp.route("/destinations", methods=["GET"])
def search_destinations():
    """Search destinations by name keyword, tag, and/or quartier.

    Query parameters (all optional):
        q         – free-text search against name, quartier, and description
        tag       – filter by a single interest tag (e.g. "beach")
        quartier  – filter by neighbourhood name (e.g. "Bonanjo")
        max_cost  – filter by maximum average cost (integer)

    Returns a JSON list of matching destination objects.
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

    destinations = get_all_destinations()
    results = []

    for dest in destinations:
        # Free-text filter
        if q:
            searchable = " ".join([
                dest.get("name", ""),
                dest.get("quartier", ""),
                dest.get("description", ""),
            ]).lower()
            if q not in searchable:
                continue

        # Tag filter
        if tag and tag not in [t.lower() for t in dest.get("tags", [])]:
            continue

        # Quartier filter
        if quartier and quartier != dest.get("quartier", "").lower():
            continue

        # Cost filter – skip destinations that have no cost information or exceed the limit
        if max_cost is not None:
            cost = dest.get("avg_cost")
            if cost is None or cost > max_cost:
                continue

        results.append(dest)

    return jsonify(results), 200