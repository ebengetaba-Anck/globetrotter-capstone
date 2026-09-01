from flask import Blueprint, render_template, request, jsonify, send_from_directory, redirect
import os
import json
import jwt
from functools import wraps

main_bp = Blueprint('main', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')
DATA_DIR = os.path.join(BASE_DIR, 'data')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return redirect('/login')
        try:
            jwt.decode(token, "microservices-secret-key-change-in-prod", algorithms=['HS256'])
            return f(*args, **kwargs)
        except:
            return redirect('/login')
    return decorated_function


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/login")
def login_page():
    return render_template("login.html")


@main_bp.route("/register")
def register_page():
    return render_template("register.html")


@main_bp.route("/destinations")
def destinations_page():
    return render_template("destinations.html")


@main_bp.route("/transport")
def transport_page():
    return render_template("transport.html")


@main_bp.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/my-favorites")
@login_required
def favorites_page():
    return render_template("my_favorites.html")


@main_bp.route("/my-itineraries")
@login_required
def itineraries_page():
    return render_template("my_itineraries.html")


@main_bp.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html")


@main_bp.route("/itinerary-builder")
@login_required
def itinerary_builder():
    return render_template("itinerary_builder.html")


@main_bp.route("/destination")
def destination_detail():
    dest_id = request.args.get('id')
    filepath = os.path.join(DATA_DIR, "destinations.json")
    destinations = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            destinations = json.load(f)
    destination = next((d for d in destinations if str(d.get('id')) == str(dest_id)), None)
    if not destination:
        return redirect("/destinations")
    return render_template("destination_details.html", destination=destination)


# ============================================================
# API - ROUTE DESTINATIONS
# ============================================================

@main_bp.route("/api/destinations", methods=["GET"])
def api_destinations():
    """Retourne toutes les destinations en JSON"""
    filepath = os.path.join(DATA_DIR, "destinations.json")
    print(f"📂 Lecture: {filepath}")  # Pour debug
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ {len(data)} destinations chargées")
        return jsonify(data), 200
    print("❌ Fichier non trouvé")
    return jsonify([]), 404


@main_bp.route("/api/me", methods=["GET"])
def api_me():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"error": "Non authentifié"}), 401
    try:
        payload = jwt.decode(token, "microservices-secret-key-change-in-prod", algorithms=["HS256"])
        username = payload.get("sub")
        users_file = os.path.join(DATA_DIR, "users.json")
        if os.path.exists(users_file):
            with open(users_file, "r", encoding="utf-8") as f:
                users = json.load(f)
            for user in users:
                if user.get("username") == username:
                    safe = {k: v for k, v in user.items() if k != "password_hash"}
                    return jsonify(safe), 200
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    except:
        return jsonify({"error": "Token invalide"}), 401


@main_bp.route("/api/logout", methods=["POST"])
def api_logout():
    return jsonify({"message": "Déconnexion réussie"}), 200