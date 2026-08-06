"""
Flask application factory.
"""

import os
import json
import datetime
import uuid
from flask import Flask, jsonify, send_from_directory, render_template, request, redirect


def create_app():

    app = Flask(__name__)


    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "globetrotter-secret-change-in-prod"
    )


    # Register blueprints

    from app.auth import auth_bp
    from app.destinations import destinations_bp
    from app.recommendations import recommendations_bp
    from app.itineraries import itineraries_bp
    from app.activities import activities_bp
    from app.transport import transport_bp


    app.register_blueprint(auth_bp)
    app.register_blueprint(destinations_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(itineraries_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(transport_bp)


    @app.route("/")
    def index():
        return send_from_directory(
            app.static_folder,
            "index.html"
        )


    @app.route("/signup")
    def signup_page():
       return render_template("register.html")


    @app.route("/dashboard")
    def dashboard():
         return render_template("dashboard.html")
         

    @app.route("/destination")
    def destination_details():
        from app.models import get_all_destinations
        
        dest_id = request.args.get('id')
        if not dest_id:
            return redirect("/dashboard")
        
        destinations = get_all_destinations()
        destination = next((d for d in destinations if str(d.get('id')) == str(dest_id)), None)
        
        if not destination:
            return redirect("/dashboard")
            
        return render_template("destination_details.html", destination=destination)


    @app.route("/my-itineraries")
    def my_itineraries_page():
        return render_template("my_itineraries.html")


    @app.route("/my-favorites")
    def my_favorites_page():
        return render_template("my_favorites.html")


    # =========================================================================
    # ROUTES DES FAVORIS
    # =========================================================================

    def safe_read_favorites():
        fav_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "favorites.json")
        if not os.path.exists(fav_file):
            return []
        try:
            with open(fav_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return []

    def safe_write_favorites(data):
        fav_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "favorites.json")
        os.makedirs(os.path.dirname(fav_file), exist_ok=True)
        with open(fav_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @app.route("/api/favorites", methods=["GET"])
    def api_get_favorites():
        try:
            from app.auth import get_current_user
            
            username = get_current_user(request)
            if not username:
                return jsonify({"error": "Non authentifié"}), 401
            
            favorites = safe_read_favorites()
            user_favs = [f for f in favorites if f.get("username") == username]
            return jsonify(user_favs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/favorites", methods=["POST"])
    def api_add_favorite():
        try:
            from app.auth import get_current_user
            
            username = get_current_user(request)
            if not username:
                return jsonify({"error": "Non authentifié"}), 401
            
            data = request.get_json(silent=True) or {}
            destination_id = data.get("destination_id")
            
            if not destination_id:
                return jsonify({"error": "destination_id requis"}), 400
            
            favorites = safe_read_favorites()
            
            existing = [f for f in favorites if f.get("username") == username and str(f.get("destination_id")) == str(destination_id)]
            if existing:
                return jsonify({"message": "Déjà dans les favoris"}), 200
            
            favorite = {
                "id": str(uuid.uuid4()),
                "username": username,
                "destination_id": str(destination_id),
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            favorites.append(favorite)
            safe_write_favorites(favorites)
            
            return jsonify({"message": "Ajouté aux favoris !"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/favorites", methods=["DELETE"])
    def api_remove_favorite():
        try:
            from app.auth import get_current_user
            
            username = get_current_user(request)
            if not username:
                return jsonify({"error": "Non authentifié"}), 401
            
            destination_id = request.args.get("destination_id")
            if not destination_id:
                return jsonify({"error": "destination_id requis"}), 400
            
            favorites = safe_read_favorites()
            filtered = [f for f in favorites if not (f.get("username") == username and str(f.get("destination_id")) == str(destination_id))]
            
            if len(filtered) == len(favorites):
                return jsonify({"error": "Favori introuvable"}), 404
            
            safe_write_favorites(filtered)
            
            return jsonify({"message": "Retiré des favoris"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    # =========================================================================
    # ROUTES DES AVIS (REVIEWS) - AJOUTÉES ICI
    # =========================================================================

    @app.route("/api/reviews", methods=["GET"])
    def api_get_reviews():
        try:
            from app.models import get_reviews_for_destination
            
            dest_id = request.args.get('destination_id')
            if not dest_id:
                return jsonify([])
            
            reviews = get_reviews_for_destination(dest_id)
            return jsonify(reviews)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/reviews", methods=["POST"])
    def api_post_review():
        try:
            from app.auth import get_current_user
            from app.models import save_review, get_reviews_for_destination
            
            username = get_current_user(request)
            if not username:
                return jsonify({"error": "Non authentifié"}), 401
            
            data = request.get_json(silent=True) or {}
            destination_id = data.get("destination_id")
            rating = data.get("rating")
            comment = data.get("comment", "").strip()
            
            if not destination_id or not rating:
                return jsonify({"error": "destination_id et rating requis"}), 400
            
            if rating < 1 or rating > 5:
                return jsonify({"error": "La note doit être comprise entre 1 et 5"}), 400
            
            review = {
                "id": str(uuid.uuid4()),
                "destination_id": str(destination_id),
                "author": username,
                "rating": int(rating),
                "comment": comment,
                "date": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            save_review(review)
            
            # Recalculer la moyenne (renvoyée au frontend pour affichage)
            all_reviews = get_reviews_for_destination(destination_id)
            avg_rating = 0
            if all_reviews:
                avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews)
            
            return jsonify({
                "message": "Avis publié avec succès !",
                "review": review,
                "average_rating": round(avg_rating, 1)
            }), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/api/hero-images")
    def hero_images():

        images_dir = os.path.join(
            app.static_folder,
            "images"
        )


        if not os.path.isdir(images_dir):
            return jsonify([])


        valid_ext = (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        )


        files = sorted(
            f for f in os.listdir(images_dir)
            if f.lower().endswith(valid_ext)
        )


        return jsonify(files)


    print(app.url_map)

    return app