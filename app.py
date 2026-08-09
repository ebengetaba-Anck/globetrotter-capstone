from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import os

# === CONFIGURATION DES CHEMINS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'app', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

# Configuration des URLs des microservices
USER_SERVICE_URL = "http://127.0.0.1:5001"
ITINERARY_SERVICE_URL = "http://127.0.0.1:5002"
RECOMMENDATION_SERVICE_URL = "http://127.0.0.1:5003"


# ============================================================
# Routes statiques (HTML, CSS, Images)
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

@app.route("/destination")
def destination_details():
    return render_template("destination_details.html")

@app.route("/category/<any_category>")
def category_page(any_category):
    return render_template("category.html", category=any_category)

@app.route("/gallery/<dest_id>")
def gallery_page(dest_id):
    return render_template("media_gallery.html", destination={"id": dest_id})

@app.route("/my-itineraries")
def my_itineraries():
    return render_template("my_itineraries.html")

@app.route("/itinerary/<itinerary_id>")
def itinerary_detail(itinerary_id):
    return render_template("itinerary_detail.html", itinerary={"id": itinerary_id})

@app.route("/itinerary-builder")
def itinerary_builder():
    return render_template("itinerary_builder.html")

@app.route("/my-favorites")
def my_favorites():
    return render_template("my_favorites.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


# ============================================================
# API Gateway (Redirection vers les microservices)
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
    else:  # POST
        response = requests.post(f"{ITINERARY_SERVICE_URL}/itineraries", 
                                 headers=headers, 
                                 json=request.get_json())
    
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

# === AJOUT CRUCIAL : Redirection de /destinations vers le service de recommandations ===
@app.route("/destinations", methods=["GET"])
def proxy_destinations():
    # On redirige simplement vers l'API du service de recommandations
    response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/destinations")
    return jsonify(response.json()), response.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)