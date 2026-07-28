"""
app/recommendations.py

Personalised recommendations across destinations, activities, and transport.

Routes
------
GET /recommendations
    Returns destinations, activities, and transport options that best match
    the authenticated user's preferences.
    Requires a valid JWT in the Authorization header.
"""
from flask import Blueprint, request, jsonify

from app.auth import get_current_user
from app.models import (
    get_all_destinations,
    get_all_activities,
    get_all_transport,
    get_user_by_username,
)

recommendations_bp = Blueprint("recommendations", __name__)


def _score_items(items: list, preferences: list, limit: int) -> list:
    """Score *items* against *preferences* by matching the "tags" field.

    Each item gets +1 for every preference tag it shares. Items are sorted
    by descending score, then by name for stable ordering. The returned
    list is capped at *limit* entries and each entry includes a
    "match_score" field for transparency.
    """
    scored = []
    for item in items:
        item_tags = [t.lower() for t in item.get("tags", [])]
        score = sum(1 for pref in preferences if pref in item_tags)
        scored.append((score, item))

    scored.sort(key=lambda x: (-x[0], x[1].get("name", "")))

    results = []
    for score, item in scored[:limit]:
        entry = dict(item)
        entry["match_score"] = score
        results.append(entry)
    return results


@recommendations_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    """Return personalised recommendations for the logged-in user.

    Recommendations are derived by scoring destinations, activities, and
    transport options against the user's preference tags. Each category is
    returned in descending score order. An optional *limit* query parameter
    caps the number of results per category (default 5).

    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "user not found"}), 404

    preferences = [p.lower() for p in user.get("preferences", [])]

    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    destinations = _score_items(get_all_destinations(), preferences, limit)
    activities = _score_items(get_all_activities(), preferences, limit)
    transport = _score_items(get_all_transport(), preferences, limit)

    return jsonify({
        "destinations": destinations,
        "activities": activities,
        "transport": transport,
    }), 200