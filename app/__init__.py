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
        return render_template("home.html")


    @app.route("/category/<any_category>")
    def category_page(any_category):
        from app.models import get_all_destinations
        destinations = get_all_destinations()
        filtered = [d for d in destinations if d.get('type') == any_category]
        if not filtered:
            return redirect("/dashboard")
        return render_template("category.html", 
                               category=any_category, 
                               destinations=filtered,
                               category_name=any_category.capitalize())


    @app.route("/destination")
    def destination_details():
        from app.models import get_all_destinations, update_user_preferences
        from app.auth import get_current_user
        
        dest_id = request.args.get('id')
        if not dest_id:
            return redirect("/dashboard")
        
        destinations = get_all_destinations()
        destination = next((d for d in destinations if str(d.get('id')) == str(dest_id)), None)
        
        if not destination:
            return redirect("/dashboard")
        
        username = get_current_user(request)
        if username and destination.get('category'):
            update_user_preferences(username, destination.get('category'))
        
        return render_template("destination_details.html", destination=destination)


    @app.route("/gallery/<dest_id>")
    def gallery_page(dest_id):
        from app.models import get_all_destinations
        
        destinations = get_all_destinations()
        destination = next((d for d in destinations if str(d.get('id')) == str(dest_id)), None)
        
        if not destination:
            return redirect("/dashboard")
        
        return render_template("media_gallery.html", destination=destination)


    @app.route("/api/me")
    def api_get_current_user():
        from app.auth import get_current_user
        from app.models import get_user_by_username
        
        username = get_current_user(request)
        if not username:
            return jsonify({"error": "Non authentifié"}), 401
        
        user = get_user_by_username(username)
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404
        
        return jsonify({
            "username": user.get("username"),
            "gender": user.get("gender", "masculin"),
            "preferences": user.get("preferences", [])
        })


    @app.route("/api/recommendations")
    def api_recommendations():
        from app.models import get_user_by_username, get_all_destinations
        from app.auth import get_current_user
        
        username = get_current_user(request)
        if not username:
            return jsonify({"error": "Non authentifié"}), 401
        
        user = get_user_by_username(username)
        preferences = user.get("preferences", [])
        
        destinations = get_all_destinations()
        
        scored = []
        for d in destinations:
            score = 0
            if d.get('category') in preferences:
                score += 3
            if d.get('tags'):
                for tag in d.get('tags', []):
                    if tag in preferences:
                        score += 1
            scored.append((score, d))
        
        scored.sort(key=lambda x: -x[0])
        recommendations = [d for _, d in scored[:6]]
        
        return jsonify(recommendations)


    @app.route("/itinerary-builder")
    def itinerary_builder_page():
        return render_template("itinerary_builder.html")


    @app.route("/api/build-itinerary", methods=["POST"])
    def api_build_itinerary():
        try:
            from app.models import get_all_destinations
            
            data = request.get_json(silent=True) or {}
            mood = data.get("mood", "")
            time = data.get("time", "")
            budget = data.get("budget", "")
            
            destinations = get_all_destinations()
            
            results = []
            for d in destinations:
                if not d.get('tags'):
                    continue
                
                mood_match = any(mood in tag for tag in d['tags'])
                
                budget_match = True
                if budget == 'petit':
                    budget_match = d.get('avg_cost', 999999) <= 2000
                elif budget == 'moyen':
                    budget_match = d.get('avg_cost', 999999) <= 10000
                
                if mood_match and budget_match:
                    results.append(d)
            
            return jsonify(results[:6])
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/my-itineraries")
    def my_itineraries_page():
        return render_template("my_itineraries.html")


    @app.route("/itinerary/<itinerary_id>")
    def itinerary_details(itinerary_id):
        from app.models import get_itinerary_by_id, get_all_destinations
        
        itinerary = get_itinerary_by_id(itinerary_id)
        if not itinerary:
            return redirect("/my-itineraries")
        
        all_destinations = get_all_destinations()
        destination_details = []
        for dest_id in itinerary.get("destinations", []):
            dest = next((d for d in all_destinations if str(d.get("id")) == str(dest_id)), None)
            if dest:
                destination_details.append({
                    "id": dest.get("id"),
                    "name": dest.get("name"),
                    "quartier": dest.get("quartier"),
                    "lat": dest.get("lat"),
                    "lng": dest.get("lng")
                })
        
        return render_template("itinerary_detail.html", itinerary=itinerary, destination_details=destination_details)


    @app.route("/my-favorites")
    def my_favorites_page():
        return render_template("my_favorites.html")


    @app.route("/api/natural-search", methods=["POST"])
    def api_natural_search():
        from app.assistant import analyze_natural_language, get_recommendations_for_criteria
        from app.models import get_all_destinations
        
        data = request.get_json(silent=True) or {}
        query = data.get("query", "")
        
        criteria = analyze_natural_language(query)
        destinations = get_all_destinations()
        results = get_recommendations_for_criteria(criteria, destinations)
        
        return jsonify({
            "criteria": criteria,
            "results": results
        })


    @app.route("/api/reviews")
    def api_reviews():
        from app.models import get_reviews_for_destination
        
        dest_id = request.args.get('destination_id')
        if not dest_id:
            return jsonify([])
        
        reviews = get_reviews_for_destination(dest_id)
        return jsonify(reviews)


    @app.route("/api/reviews", methods=["POST"])
    def api_post_review():
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
        
        all_reviews = get_reviews_for_destination(destination_id)
        avg_rating = 0
        if all_reviews:
            avg_rating = sum(r["rating"] for r in all_reviews) / len(all_reviews)
        
        return jsonify({
            "message": "Avis publié avec succès !",
            "review": review,
            "average_rating": round(avg_rating, 1)
        }), 201


    @app.route("/api/favorites", methods=["GET"])
    def api_get_favorites():
        from app.models import get_favorites_for_user
        from app.auth import get_current_user
        
        username = get_current_user(request)
        if not username:
            return jsonify({"error": "Non authentifié"}), 401
        
        favorites = get_favorites_for_user(username)
        return jsonify(favorites)


    @app.route("/api/favorites", methods=["POST"])
    def api_add_favorite():
        from app.models import save_favorite
        from app.auth import get_current_user
        
        username = get_current_user(request)
        if not username:
            return jsonify({"error": "Non authentifié"}), 401
        
        data = request.get_json(silent=True) or {}
        destination_id = data.get("destination_id")
        
        if not destination_id:
            return jsonify({"error": "destination_id requis"}), 400
        
        favorite = {
            "id": str(uuid.uuid4()),
            "username": username,
            "destination_id": str(destination_id),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        save_favorite(favorite)
        return jsonify({"message": "Ajouté aux favoris !"}), 201


    @app.route("/api/favorites", methods=["DELETE"])
    def api_remove_favorite():
        from app.models import delete_favorite
        from app.auth import get_current_user
        
        username = get_current_user(request)
        if not username:
            return jsonify({"error": "Non authentifié"}), 401
        
        destination_id = request.args.get("destination_id")
        if not destination_id:
            return jsonify({"error": "destination_id requis"}), 400
        
        success = delete_favorite(username, destination_id)
        if success:
            return jsonify({"message": "Retiré des favoris"}), 200
        return jsonify({"error": "Favori introuvable"}), 404


    @app.route("/api/gallery/<dest_id>")
    def api_gallery_images(dest_id):
        # Chemin vers le dossier du lieu
        folder_path = os.path.join(app.static_folder, "images", dest_id)
        
        if not os.path.isdir(folder_path):
            return jsonify([])
        
        # Lister tous les fichiers images et vidéos
        valid_ext = (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".avi")
        files = sorted([
            f for f in os.listdir(folder_path) 
            if f.lower().endswith(valid_ext)
        ])
        
        # Retourner la liste des URLs vers ces fichiers
        urls = [f"/static/images/{dest_id}/{f}" for f in files]
        return jsonify(urls)


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