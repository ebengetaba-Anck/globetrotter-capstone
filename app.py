from flask import Flask, request, jsonify, render_template, send_from_directory, redirect
import requests
import os
import json
import jwt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'app', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

USER_SERVICE_URL = "http://127.0.0.1:5001"
ITINERARY_SERVICE_URL = "http://127.0.0.1:5002"
RECOMMENDATION_SERVICE_URL = "http://127.0.0.1:5003"
FAVORITES_SERVICE_URL = "http://127.0.0.1:5004"


# ============================================================
# Routes statiques
# ============================================================
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("home.html")

@app.route("/signup")
def signup():
    return render_template("register.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/category/<any_category>")
def category_page(any_category):
    try:
        response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/destinations")
        if response.status_code != 200:
            return render_template("category.html", category=any_category, destinations=[], category_name=any_category.capitalize())
        all_destinations = response.json()
        filtered = [d for d in all_destinations if d.get('type') == any_category]
        return render_template("category.html", category=any_category, destinations=filtered, category_name=any_category.capitalize())
    except:
        return render_template("category.html", category=any_category, destinations=[], category_name=any_category.capitalize())

@app.route("/gallery/<dest_id>")
def gallery_page(dest_id):
    return render_template("media_gallery.html", destination={"id": dest_id})

@app.route("/itinerary/<itinerary_id>")
def itinerary_detail(itinerary_id):
    return render_template("itinerary_detail.html", itinerary={"id": itinerary_id})

@app.route("/itinerary-builder")
def itinerary_builder():
    return render_template("itinerary_builder.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


# ============================================================
# API Gateway
# ============================================================

@app.route("/register", methods=["POST"])
def proxy_register():
    response = requests.post(f"{USER_SERVICE_URL}/register", json=request.get_json())
    return jsonify(response.json()), response.status_code

@app.route("/login", methods=["POST"])
def proxy_login():
    response = requests.post(f"{USER_SERVICE_URL}/login", json=request.get_json())
    return jsonify(response.json()), response.status_code

@app.route("/api/me", methods=["GET"])
def proxy_me():
    headers = {"Authorization": request.headers.get("Authorization", "")}
    response = requests.get(f"{USER_SERVICE_URL}/me", headers=headers)
    return jsonify(response.json()), response.status_code

@app.route("/itineraries", methods=["GET", "POST"])
def proxy_itineraries():
    headers = {"Authorization": request.headers.get("Authorization", "")}
    if request.method == "GET":
        response = requests.get(f"{ITINERARY_SERVICE_URL}/itineraries", headers=headers)
    else:
        response = requests.post(f"{ITINERARY_SERVICE_URL}/itineraries", headers=headers, json=request.get_json())
    return jsonify(response.json()), response.status_code

@app.route("/itineraries/<itinerary_id>", methods=["DELETE"])
def proxy_delete_itinerary(itinerary_id):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    response = requests.delete(f"{ITINERARY_SERVICE_URL}/itineraries/{itinerary_id}", headers=headers)
    return jsonify(response.json()), response.status_code

@app.route("/api/recommendations", methods=["GET"])
def proxy_recommendations():
    headers = {"Authorization": request.headers.get("Authorization", "")}
    response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/recommendations", headers=headers)
    return jsonify(response.json()), response.status_code

@app.route("/destinations", methods=["GET"])
def proxy_destinations():
    response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/destinations")
    return jsonify(response.json()), response.status_code

@app.route("/destination")
def destination_details():
    dest_id = request.args.get('id')
    if not dest_id:
        return redirect("/dashboard")
    try:
        response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/destinations")
        if response.status_code != 200:
            return render_template("destination_details.html", destination=None)
        destinations = response.json()
        destination = next((d for d in destinations if str(d.get('id')) == str(dest_id)), None)
        if not destination:
            return redirect("/dashboard")
        return render_template("destination_details.html", destination=destination)
    except:
        return redirect("/dashboard")

@app.route("/api/gallery/<dest_id>")
def proxy_gallery(dest_id):
    response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/api/gallery/{dest_id}")
    return jsonify(response.json()), response.status_code

@app.route("/api/favorites", methods=["GET", "POST", "DELETE"])
def proxy_favorites():
    headers = {"Authorization": request.headers.get("Authorization", "")}
    if request.method == "GET":
        response = requests.get(f"{FAVORITES_SERVICE_URL}/favorites", headers=headers)
    elif request.method == "POST":
        response = requests.post(f"{FAVORITES_SERVICE_URL}/favorites", headers=headers, json=request.get_json())
    else:
        response = requests.delete(f"{FAVORITES_SERVICE_URL}/favorites", headers=headers, params=request.args)
    return jsonify(response.json()), response.status_code


# ============================================================
# ROUTE DES FAVORIS (Version POST + Formulaire caché)
# ============================================================
@app.route("/my-favorites", methods=["POST"])
def my_favorites_post():
    # On lit le token depuis le champ caché du formulaire
    token = request.form.get('token')
    username = None
    
    if token:
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            username = payload.get("sub")
        except:
            pass

    if not username:
        return redirect("/login")

    favorites_file = os.path.join(BASE_DIR, "data", "favorites.json")
    all_favorites = []
    if os.path.exists(favorites_file):
        with open(favorites_file, "r", encoding="utf-8") as f:
            all_favorites = json.load(f)

    user_favorites = [f for f in all_favorites if f.get("username") == username]

    response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/destinations")
    all_destinations = response.json() if response.status_code == 200 else []

    enriched_favorites = []
    for fav in user_favorites:
        dest = next((d for d in all_destinations if str(d.get("id")) == str(fav.get("destination_id"))), None)
        if dest:
            enriched_favorites.append({
                "id": fav.get("id"),
                "destination": dest
            })

    return render_template("my_favorites.html", favorites=enriched_favorites)

@app.route("/my-favorites", methods=["GET"])
def my_favorites_redirect():
    # Cette route redirige vers la page de redirection qui lit le token depuis localStorage
    return render_template("favorites_redirect.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)