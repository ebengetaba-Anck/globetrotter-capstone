"""
Recommendation Service - Port 5003
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app.recommendations import recommendations_bp
from app.reviews import reviews_bp
from app.destinations import destinations_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"), exist_ok=True)

app.register_blueprint(recommendations_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(destinations_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)