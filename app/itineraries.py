"""
app/itineraries.py

Create, list, update, and delete itineraries for the authenticated user.

Routes
------
POST   /itineraries       – create a new itinerary
GET    /itineraries       – list all itineraries for the logged-in user
PUT    /itineraries/<id>  – update an itinerary owned by the logged-in user
DELETE /itineraries/<id>  – delete an itinerary owned by the logged-in user

All routes require a valid JWT in the Authorization header.
"""
import uuid
import datetime

from flask import Blueprint, request, jsonify

from app.auth import get_current_user
from app.models import (
    get_itineraries_for_user,
    get_itinerary_by_id,
    save_itinerary,
    update_itinerary,
    delete_itinerary,
)

itineraries_bp = Blueprint("itineraries", __name__)


def _validate_dates(start_date: str, end_date: str) -> str | None:
    """Return an error message if the date range is invalid, else None."""
    if not start_date or not end_date:
        return None
    try:
        start = datetime.date.fromisoformat(start_date)
        end = datetime.date.fromisoformat(end_date)
    except ValueError:
        return "start_date and end_date must be valid dates in YYYY-MM-DD format"
    if end < start:
        return "end_date cannot be before start_date"
    return None


@itineraries_bp.route("/itineraries", methods=["POST"])
def create_itinerary():
    """Create a new itinerary for the authenticated user.

    Expected JSON body:
        {
          "title": "Summer in Douala",
          "destinations": ["Marche Central"],
          "start_date": "2026-08-01",
          "end_date": "2026-08-15",
          "notes": "Optional free-text notes"
        }

    Returns 201 with the created itinerary on success.
    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    destinations = data.get("destinations", [])
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")

    if not title:
        return jsonify({"error": "title is required"}), 400
    if not isinstance(destinations, list):
        return jsonify({"error": "destinations must be a list"}), 400

    date_error = _validate_dates(start_date, end_date)
    if date_error:
        return jsonify({"error": date_error}), 400

    itinerary = {
        "id": str(uuid.uuid4()),
        "username": username,
        "title": title,
        "destinations": destinations,
        "start_date": start_date,
        "end_date": end_date,
        "notes": data.get("notes", ""),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    save_itinerary(itinerary)
    return jsonify(itinerary), 201


@itineraries_bp.route("/itineraries", methods=["GET"])
def list_itineraries():
    """List all itineraries for the authenticated user.

    Returns 200 with a JSON array of itinerary objects.
    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    itineraries = get_itineraries_for_user(username)
    return jsonify(itineraries), 200


@itineraries_bp.route("/itineraries/<itinerary_id>", methods=["PUT"])
def edit_itinerary(itinerary_id):
    """Update an itinerary owned by the authenticated user.

    Accepts the same fields as creation; only provided fields are updated.
    Returns 200 with the updated itinerary, 404 if not found, 403 if the
    itinerary belongs to another user.
    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    itinerary = get_itinerary_by_id(itinerary_id)
    if not itinerary:
        return jsonify({"error": "itinerary not found"}), 404
    if itinerary.get("username") != username:
        return jsonify({"error": "you do not own this itinerary"}), 403

    data = request.get_json(silent=True) or {}
    updates = {}

    if "title" in data:
        title = data["title"].strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        updates["title"] = title

    if "destinations" in data:
        if not isinstance(data["destinations"], list):
            return jsonify({"error": "destinations must be a list"}), 400
        updates["destinations"] = data["destinations"]

    if "notes" in data:
        updates["notes"] = data["notes"]

    new_start = data.get("start_date", itinerary.get("start_date", ""))
    new_end = data.get("end_date", itinerary.get("end_date", ""))
    date_error = _validate_dates(new_start, new_end)
    if date_error:
        return jsonify({"error": date_error}), 400
    if "start_date" in data:
        updates["start_date"] = data["start_date"]
    if "end_date" in data:
        updates["end_date"] = data["end_date"]

    updated = update_itinerary(itinerary_id, updates)
    return jsonify(updated), 200


@itineraries_bp.route("/itineraries/<itinerary_id>", methods=["DELETE"])
def remove_itinerary(itinerary_id):
    """Delete an itinerary owned by the authenticated user.

    Returns 200 on success, 404 if not found, 403 if owned by another user.
    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    itinerary = get_itinerary_by_id(itinerary_id)
    if not itinerary:
        return jsonify({"error": "itinerary not found"}), 404
    if itinerary.get("username") != username:
        return jsonify({"error": "you do not own this itinerary"}), 403

    delete_itinerary(itinerary_id)
    return jsonify({"message": "itinerary deleted"}), 200