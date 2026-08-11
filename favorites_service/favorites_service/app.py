from flask import Flask, request, jsonify
import json
import os
import uuid
import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

FAVORITES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "favorites.json")

def read_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return []
    with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_favorites(data):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_username_from_token(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        import jwt
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

# ============================================================
# LA CORRECTION ICI : Ajout de methods=["GET", "POST", "DELETE"]
# ============================================================
@app.route("/favorites", methods=["GET", "POST", "DELETE"])
def handle_favorites():
    auth_header = request.headers.get("Authorization", "")
    username = get_username_from_token(auth_header)
    if not username:
        return jsonify({"error": "Non authentifié"}), 401

    # GET : Récupérer les favoris
    if request.method == "GET":
        favorites = read_favorites()
        user_favs = [f for f in favorites if f.get("username") == username]
        return jsonify(user_favs), 200

    # POST : Ajouter un favori
    elif request.method == "POST":
        data = request.get_json(silent=True) or {}
        destination_id = data.get("destination_id")
        if not destination_id:
            return jsonify({"error": "destination_id requis"}), 400

        favorites = read_favorites()
        for f in favorites:
            if f.get("username") == username and str(f.get("destination_id")) == str(destination_id):
                return jsonify({"message": "Déjà dans les favoris"}), 200

        favorite = {
            "id": str(uuid.uuid4()),
            "username": username,
            "destination_id": str(destination_id),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        favorites.append(favorite)
        write_favorites(favorites)
        return jsonify({"message": "Ajouté aux favoris !"}), 201

    # DELETE : Supprimer un favori
    elif request.method == "DELETE":
        destination_id = request.args.get("destination_id")
        if not destination_id:
            return jsonify({"error": "destination_id requis"}), 400

        favorites = read_favorites()
        filtered = [f for f in favorites if not (f.get("username") == username and str(f.get("destination_id")) == str(destination_id))]

        if len(filtered) == len(favorites):
            return jsonify({"error": "Favori introuvable"}), 404

        write_favorites(filtered)
        return jsonify({"message": "Retiré des favoris"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)