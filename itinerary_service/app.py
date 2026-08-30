"""
Itinerary Service - Port 5002
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app.itineraries import itineraries_bp
from app.models import DATA_DIR

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

os.makedirs(DATA_DIR, exist_ok=True)

app.register_blueprint(itineraries_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)