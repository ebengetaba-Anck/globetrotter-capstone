"""
tests/test_auth.py

Tests for user registration and login (JWT authentication).
"""


def test_register_new_user(client):
    response = client.post("/register", json={
        "username": "alice",
        "password": "s3cr3t",
        "preferences": ["culture", "food"],
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["username"] == "alice"


def test_register_duplicate_username_fails(client):
    client.post("/register", json={"username": "bob", "password": "pass123"})
    response = client.post("/register", json={"username": "bob", "password": "otherpass"})
    assert response.status_code == 409


def test_register_missing_fields_fails(client):
    response = client.post("/register", json={"username": "onlyusername"})
    assert response.status_code == 400


def test_login_success_returns_token(client):
    client.post("/register", json={"username": "carla", "password": "mypassword"})
    response = client.post("/login", json={"username": "carla", "password": "mypassword"})
    assert response.status_code == 200
    assert "token" in response.get_json()


def test_login_wrong_password_fails(client):
    client.post("/register", json={"username": "dave", "password": "correctpass"})
    response = client.post("/login", json={"username": "dave", "password": "wrongpass"})
    assert response.status_code == 401


def test_login_unknown_user_fails(client):
    response = client.post("/login", json={"username": "ghost", "password": "whatever"})
    assert response.status_code == 401