"""
User Service - Port 5001
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app.auth import auth_bp
from app.models import _write_json, USERS_FILE

app = Flask(__name__)
app.config["SECRET_KEY"] = "microservices-secret-key-change-in-prod"

# Créer le dossier data
os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

# Enregistrer le blueprint
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)