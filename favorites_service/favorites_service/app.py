"""
Favorites Service - Port 5004
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app.favorites import favorites_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"), exist_ok=True)

app.register_blueprint(favorites_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)