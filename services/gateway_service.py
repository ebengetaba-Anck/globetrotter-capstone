from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import requests

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "templates"),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static"))

app.config['SECRET_KEY'] = 'microservices-secret-key-change-in-prod'

USER_SERVICE = "http://localhost:5001"
ITINERARY_SERVICE = "http://localhost:5002"
RECOMMENDATION_SERVICE = "http://localhost:5003"


def route_request(url, method='GET', data=None, headers=None, params=None):
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        else:
            return jsonify({'error': 'Méthode non supportée'}), 405
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Service non disponible'}), 503


# ============================================================
# ROUTES PAGES
# ============================================================

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/destinations')
def destinations_page():
    return render_template('destinations.html')


@app.route('/transport')
def transport_page():
    return render_template('transport.html')


@app.route('/my-favorites')
def favorites_page():
    return render_template('my_favorites.html')


@app.route('/my-itineraries')
def my_itineraries_page():
    return render_template('my_itineraries.html')


@app.route('/recommendations')
def recommendations_page():
    return render_template('recommendations.html')


@app.route('/destination')
def destination_detail():
    dest_id = request.args.get('id')
    return render_template('destination_details.html', destination={'id': dest_id})


@app.route('/gallery/<dest_id>')
def gallery_page(dest_id):
    return render_template('gallery.html', destination={'id': dest_id})


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ============================================================
# ROUTES API
# ============================================================

@app.route('/api/register', methods=['POST'])
def api_register():
    return route_request(f"{USER_SERVICE}/register", 'POST', request.get_json())


@app.route('/api/login', methods=['POST'])
def api_login():
    return route_request(f"{USER_SERVICE}/login", 'POST', request.get_json())


@app.route('/api/me', methods=['GET'])
def api_me():
    return route_request(f"{USER_SERVICE}/me", 'GET', headers=request.headers)


@app.route('/api/destinations', methods=['GET'])
def api_destinations():
    return route_request(f"{RECOMMENDATION_SERVICE}/destinations", 'GET')


@app.route('/api/recommendations', methods=['GET'])
def api_recommendations():
    return route_request(f"{RECOMMENDATION_SERVICE}/recommendations", 'GET', headers=request.headers)


@app.route('/api/recommendations/personalized', methods=['GET'])
def api_recommendations_personalized():
    return route_request(f"{RECOMMENDATION_SERVICE}/recommendations/personalized", 'GET', headers=request.headers)


@app.route('/api/itineraries', methods=['GET', 'POST'])
def api_itineraries():
    if request.method == 'GET':
        return route_request(f"{ITINERARY_SERVICE}/itineraries", 'GET', headers=request.headers)
    else:
        return route_request(f"{ITINERARY_SERVICE}/itineraries", 'POST', request.get_json(), request.headers)


@app.route('/api/itineraries/<itinerary_id>', methods=['DELETE', 'PUT'])
def api_itinerary_detail(itinerary_id):
    if request.method == 'DELETE':
        return route_request(f"{ITINERARY_SERVICE}/itineraries/{itinerary_id}", 'DELETE', headers=request.headers)
    else:
        return route_request(f"{ITINERARY_SERVICE}/itineraries/{itinerary_id}", 'PUT', request.get_json(), request.headers)


@app.route('/api/reviews', methods=['GET', 'POST'])
def api_reviews():
    if request.method == 'GET':
        return route_request(f"{RECOMMENDATION_SERVICE}/reviews", 'GET', params=request.args)
    else:
        return route_request(f"{RECOMMENDATION_SERVICE}/reviews", 'POST', request.get_json(), request.headers)


@app.route('/api/build-itinerary', methods=['POST'])
def api_build_itinerary():
    return route_request(f"{RECOMMENDATION_SERVICE}/build-itinerary", 'POST', request.get_json(), request.headers)


if __name__ == '__main__':
    print("="*60)
    print("🚀 API GATEWAY - Port 5000")
    print("🌐 http://localhost:5000")
    print("📋 Services: User(5001), Itinerary(5002), Recommendation(5003)")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True)