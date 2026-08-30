from flask import Flask, jsonify
import json
import os

app = Flask(__name__)

@app.route("/api/destinations")
def get_destinations():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "destinations.json")
    print(f"📂 Lecture: {filepath}")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ {len(data)} destinations chargées")
        return jsonify(data), 200
    print("❌ Fichier non trouvé")
    return jsonify([]), 404

@app.route("/")
def home():
    return "<h1 style='color:green;'>✅ Le serveur fonctionne !</h1><p>Testez /api/destinations</p>"

if __name__ == "__main__":
    print("="*50)
    print("🚀 TEST API")
    print("🌐 http://localhost:5001/api/destinations")
    print("="*50)
    app.run(host="0.0.0.0", port=5001, debug=True)