"""
app/transport.py

Transport (taxi / moto-taxi / VTC / van familial) search and reservation.

Routes
------
GET  /transport                 – search available transport options (no auth)
POST /transport/reserve         – reserve a transport option (requires JWT)
GET  /transport/reservations    – list the logged-in user's reservations (requires JWT)
"""
import uuid
import datetime

from flask import Blueprint, request, jsonify

from app.auth import get_current_user
from app.models import (
    get_all_transport,
    get_transport_by_id,
    get_reservations_for_user,
    get_reservation_by_id,
    save_reservation,
    delete_reservation,
)
transport_bp = Blueprint("transport", __name__)


@transport_bp.route("/transport", methods=["GET"])
def search_transport():
    """Search transport options by type, quartier, tag, and/or availability.

    Query parameters (all optional):
        type         – e.g. "taxi_classique", "moto_taxi", "vtc_confort", "van_familial"
        quartier     – base neighbourhood of the driver
        tag          – filter by a single tag (e.g. "famille")
        disponible   – "true" to only show currently available vehicles

    Returns a JSON list of matching transport objects.
    """
    t_type = request.args.get("type", "").strip().lower()
    quartier = request.args.get("quartier", "").strip().lower()
    tag = request.args.get("tag", "").strip().lower()
    disponible_str = request.args.get("disponible", "").strip().lower()

    transport = get_all_transport()
    results = []

    for t in transport:
        if t_type and t_type != t.get("type", "").lower():
            continue

        if quartier and quartier != t.get("quartier_base", "").lower():
            continue

        if tag and tag not in [tg.lower() for tg in t.get("tags", [])]:
            continue

        if disponible_str == "true" and not t.get("disponible", False):
            continue

        results.append(t)

    return jsonify(results), 200


@transport_bp.route("/transport/reserve", methods=["POST"])
def reserve_transport():
    """Reserve a transport option for the authenticated user.

    Expected JSON body:
        {
          "transport_id": "taxi-005",
          "depart": "Bonanjo",
          "destination": "Aeroport de Douala"
        }

    Returns 201 with the created reservation on success.
    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    transport_id = data.get("transport_id", "").strip()

    if not transport_id:
        return jsonify({"error": "transport_id is required"}), 400

    transport = get_transport_by_id(transport_id)
    if not transport:
        return jsonify({"error": "transport option not found"}), 404

    if not transport.get("disponible", False):
        return jsonify({"error": "this transport option is not currently available"}), 409

    reservation = {
        "id": str(uuid.uuid4()),
        "username": username,
        "transport_id": transport_id,
        "depart": data.get("depart", ""),
        "destination": data.get("destination", ""),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    save_reservation(reservation)
    return jsonify(reservation), 201


@transport_bp.route("/transport/reservations", methods=["GET"])
def list_reservations():
    """List all transport reservations for the authenticated user.

    Returns 200 with a JSON array of reservation objects.
    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    reservations = get_reservations_for_user(username)
    return jsonify(reservations), 200
@transport_bp.route("/transport/reservations/<reservation_id>", methods=["DELETE"])
def cancel_reservation(reservation_id):
    """Cancel a transport reservation owned by the authenticated user.

    Returns 200 on success, 404 if not found, 403 if owned by another user.
    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    reservation = get_reservation_by_id(reservation_id)
    if not reservation:
        return jsonify({"error": "reservation not found"}), 404
    if reservation.get("username") != username:
        return jsonify({"error": "you do not own this reservation"}), 403

    delete_reservation(reservation_id)
    return jsonify({"message": "reservation cancelled"}), 200