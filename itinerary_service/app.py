from flask import Flask, request, jsonify
import uuid
import datetime
import json
import os
import jwt

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

# Base de données simulée (fichier JSON partagé)
ITINERARIES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "itineraries.json")

def read_itineraries():
    if not os.path.exists(ITINERARIES_FILE):
        return []
    with open(ITINERARIES_FILE, "r") as f:
        return json.load(f)

def write_itineraries(itineraries):
    with open(ITINERARIES_FILE, "w") as f:
        json.dump(itineraries, f, indent=2)

# Helper : Extraire l'utilisateur depuis le token JWT
def get_current_user_from_token(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

# Route : Créer un itinéraire
@app.route("/itineraries", methods=["POST"])
def create_itinerary():
    auth_header = request.headers.get("Authorization", "")
    username = get_current_user_from_token(auth_header)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    destinations = data.get("destinations", [])
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    notes = data.get("notes", "")

    if not title:
        title = f"Itinéraire du {datetime.datetime.now().strftime('%d/%m/%Y')}"

    if not isinstance(destinations, list):
        return jsonify({"error": "destinations must be a list"}), 400

    itinerary = {
        "id": str(uuid.uuid4()),
        "username": username,
        "title": title,
        "destinations": destinations,
        "start_date": start_date,
        "end_date": end_date,
        "notes": notes,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    itineraries = read_itineraries()
    itineraries.append(itinerary)
    write_itineraries(itineraries)

    return jsonify({"message": "Itinéraire créé avec succès !", "itinerary": itinerary}), 201

# Route : Lister les itinéraires de l'utilisateur
@app.route("/itineraries", methods=["GET"])
def list_itineraries():
    auth_header = request.headers.get("Authorization", "")
    username = get_current_user_from_token(auth_header)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

    itineraries = read_itineraries()
    user_itineraries = [it for it in itineraries if it.get("username") == username]
    return jsonify(user_itineraries), 200

# Route : Supprimer un itinéraire
@app.route("/itineraries/<itinerary_id>", methods=["DELETE"])
def delete_itinerary(itinerary_id):
    auth_header = request.headers.get("Authorization", "")
    username = get_current_user_from_token(auth_header)
    if not username:
        return jsonify({"error": "Authentification requise"}), 401

    itineraries = read_itineraries()
    filtered = [it for it in itineraries if not (it.get("id") == itinerary_id and it.get("username") == username)]

    if len(filtered) == len(itineraries):
        return jsonify({"error": "Itinéraire introuvable ou non autorisé"}), 404

    write_itineraries(filtered)
    return jsonify({"message": "Itinéraire supprimé avec succès"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)