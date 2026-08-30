from flask import Flask, jsonify, render_template, send_from_directory
import os
import json

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "templates"),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static"))

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/api/destinations")
def api_destinations():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "destinations.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    print("="*60)
    print("🚀 TEST COMPLET - Ô'MBOA")
    print("🌐 http://localhost:5000")
    print("📂 Routes:")
    print("   - /")
    print("   - /login")
    print("   - /register")
    print("   - /dashboard")
    print("   - /api/destinations")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=True)