"""
app/favorites.py

Favorites service for Ô'MBOA.

Routes
------
GET    /favorites  – list user favorites
POST   /favorites  – add a favorite
DELETE /favorites  – remove a favorite
"""
import uuid
from flask import Blueprint, request, jsonify

from app.auth import get_current_user
from app.models import (
    get_all_favorites,
    get_favorites_for_user,
    save_favorite,
    delete_favorite,
)

favorites_bp = Blueprint("favorites", __name__)


@favorites_bp.route("/favorites", methods=["GET"])
def list_favorites():
    """List all favorites for the authenticated user."""
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

    favorites = get_favorites_for_user(username)
    return jsonify(favorites), 200


@favorites_bp.route("/favorites", methods=["POST"])
def add_favorite():
    """Add a destination to favorites."""
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

    data = request.get_json(silent=True) or {}
    destination_id = data.get("destination_id")
    if not destination_id:
        return jsonify({"error": "destination_id requis"}), 400

    # Vérifier si déjà en favori
    favorites = get_all_favorites()
    for f in favorites:
        if f.get("username") == username and str(f.get("destination_id")) == str(destination_id):
            return jsonify({"message": "Déjà en favori"}), 200

    favorite = {
        "id": str(uuid.uuid4()),
        "username": username,
        "destination_id": destination_id,
        "created_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    }
    save_favorite(favorite)
    return jsonify({"message": "Ajouté aux favoris"}), 201


@favorites_bp.route("/favorites", methods=["DELETE"])
def remove_favorite():
    """Remove a destination from favorites."""
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

    destination_id = request.args.get("destination_id")
    if not destination_id:
        return jsonify({"error": "destination_id requis"}), 400

    if delete_favorite(username, destination_id):
        return jsonify({"message": "Retiré des favoris"}), 200
    return jsonify({"error": "Favori non trouvé"}), 404