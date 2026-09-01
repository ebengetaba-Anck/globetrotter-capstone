"""
app/reviews.py

Reviews service for Ô'MBOA.

Routes
------
GET    /reviews  – list reviews for a destination
POST   /reviews  – add a review
"""
import uuid
import datetime
from flask import Blueprint, request, jsonify

from app.auth import get_current_user
from app.models import (
    get_reviews_for_destination,
    get_all_reviews,
    save_review,
    get_user_by_username,
)

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("/reviews", methods=["GET"])
def list_reviews():
    """List reviews for a destination."""
    destination_id = request.args.get("destination_id")
    if not destination_id:
        return jsonify({"error": "destination_id is required"}), 400

    reviews = get_reviews_for_destination(destination_id)
    
    # Enrichir avec les noms d'utilisateurs
    enriched = []
    for r in reviews:
        user = get_user_by_username(r.get("username", ""))
        enriched.append({
            "id": r.get("id"),
            "destination_id": r.get("destination_id"),
            "author": user.get("full_name", user.get("username", "Anonyme")) if user else "Anonyme",
            "username": r.get("username"),
            "rating": r.get("rating", 5),
            "comment": r.get("comment", ""),
            "date": r.get("created_at", "")[:10]
        })
    
    return jsonify(enriched), 200


@reviews_bp.route("/reviews", methods=["POST"])
def add_review():
    """Add a review for a destination."""
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

    data = request.get_json(silent=True) or {}
    destination_id = data.get("destination_id")
    rating = data.get("rating", 5)
    comment = data.get("comment", "")

    if not destination_id:
        return jsonify({"error": "destination_id is required"}), 400

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "rating must be between 1 and 5"}), 400

    review = {
        "id": str(uuid.uuid4()),
        "username": username,
        "destination_id": str(destination_id),
        "rating": rating,
        "comment": comment,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    save_review(review)
    return jsonify({"message": "Avis publié avec succès !"}), 201