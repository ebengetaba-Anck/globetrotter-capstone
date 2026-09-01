"""
app/recommendations.py

Personalised recommendations for Ô'MBOA using the rich destination data.
"""
from flask import Blueprint, request, jsonify
import random

from app.auth import get_current_user
from app.models import (
    get_all_destinations,
    get_all_activities,
    get_all_transport,
    get_user_by_username,
)

recommendations_bp = Blueprint("recommendations", __name__)


def _score_items(items: list, preferences: list, limit: int) -> list:
    """Score items against user preferences."""
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
    """Return personalised recommendations for the logged-in user."""
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


@recommendations_bp.route("/api/build-itinerary", methods=["POST"])
def build_itinerary():
    """
    Build a custom itinerary based on user criteria.
    Uses the rich destination data with mood, search, budget_level, etc.
    """
    data = request.get_json(silent=True) or {}
    mood = data.get("mood", "relax")
    search = data.get("search", "")
    time = data.get("time", "journee")
    budget = data.get("budget", "moyen")
    surprise = data.get("surprise", "oui")

    # Récupérer toutes les destinations
    destinations = get_all_destinations()

    # Filtrer par budget
    budget_map = {
        "petit": "economique",
        "moyen": "moyen",
        "premium": "premium"
    }
    budget_level = budget_map.get(budget, "moyen")

    filtered = []
    for d in destinations:
        # Filtrer par budget_level
        if d.get("budget_level", "moyen") != budget_level:
            continue

        # Filtrer par mood (utiliser le champ "mood" du fichier)
        if "mood" in d:
            if mood not in d.get("mood", []):
                continue

        # Filtrer par search
        if search and "search" in d:
            if search not in d.get("search", []):
                continue

        filtered.append(d)

    # Mélanger et limiter
    random.shuffle(filtered)
    
    # Déterminer le nombre de résultats
    time_count = {
        "2h": 2,
        "demi": 3,
        "journee": 5,
        "weekend": 8
    }
    count = time_count.get(time, 4)
    plan = filtered[:count]

    # Si "surprise" est oui, ajouter un élément aléatoire
    if surprise == "oui" and len(plan) > 0:
        if "tags" not in plan[0]:
            plan[0]["tags"] = []
        plan[0]["tags"].append("surprise")

    # Déterminer le type de plan
    plan_type = "classic"
    if mood == "romantique":
        plan_type = "romantic_plan"

    return jsonify({
        "plan": plan,
        "type": plan_type,
        "time": time,
        "mood": mood
    }), 200


@recommendations_bp.route("/api/replace-suggestion", methods=["POST"])
def replace_suggestion():
    """
    Replace a destination suggestion with an alternative.
    """
    data = request.get_json(silent=True) or {}
    current_id = data.get("current_id")
    mood = data.get("mood", "relax")
    search = data.get("search", "")
    budget = data.get("budget", "moyen")

    if not current_id:
        return jsonify({"error": "current_id is required"}), 400

    destinations = get_all_destinations()

    # Filtrer par budget
    budget_map = {
        "petit": "economique",
        "moyen": "moyen",
        "premium": "premium"
    }
    budget_level = budget_map.get(budget, "moyen")

    filtered = []
    for d in destinations:
        if str(d.get("id")) == str(current_id):
            continue

        if d.get("budget_level", "moyen") != budget_level:
            continue

        if "mood" in d and mood not in d.get("mood", []):
            continue

        filtered.append(d)

    if not filtered:
        return jsonify({"error": "No alternative found"}), 404

    random.shuffle(filtered)
    return jsonify(filtered[0]), 200


@recommendations_bp.route("/destinations", methods=["GET"])
def get_destinations():
    """Return all destinations with enriched data."""
    destinations = get_all_destinations()
    return jsonify(destinations), 200


@recommendations_bp.route("/api/gallery/<dest_id>", methods=["GET"])
def get_gallery(dest_id):
    """Return gallery images for a destination."""
    import os
    images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static", "images", str(dest_id))
    
    urls = []
    if os.path.exists(images_dir):
        for filename in sorted(os.listdir(images_dir)):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov')):
                urls.append(f"/static/images/{dest_id}/{filename}")
    
    # Si pas d'images, retourner des images par défaut
    if not urls:
        default_images = [
            "https://images.unsplash.com/photo-1562677944-9c18d55125a6?w=500&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=500&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=500&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=500&auto=format&fit=crop"
        ]
        urls = default_images
    
    return jsonify(urls), 200


# Ajouter l'endpoint pour les avis
@recommendations_bp.route("/reviews", methods=["GET", "POST"])
def handle_reviews():
    """Handle reviews - GET for listing, POST for creating."""
    from app.reviews import list_reviews, add_review
    if request.method == "GET":
        return list_reviews()
    else:
        return add_review()