"""
tests/conftest.py

Shared pytest fixtures for the GlobeTrotter test suite.

Each test gets a fresh Flask test client. To keep tests isolated from real
data, we point the app's data files at a temporary directory for the
duration of each test, then restore the originals afterwards.
"""
import json
import os
import shutil
import tempfile

import pytest

from app import create_app
from app import models


@pytest.fixture
def client():
    """Yield a Flask test client backed by a temporary, isolated data directory."""
    # Create a temporary directory to hold test data files
    temp_dir = tempfile.mkdtemp()

    # Copy the real seed catalogues (destinations/activities/transport) so
    # tests can exercise real search/filter logic, but keep users/itineraries/
    # reservations empty so tests don't interfere with each other.
    real_data_dir = models.DATA_DIR
    for filename in ("destinations.json", "activities.json", "transport.json"):
        src = os.path.join(real_data_dir, filename)
        dst = os.path.join(temp_dir, filename)
        if os.path.exists(src):
            shutil.copyfile(src, dst)
        else:
            with open(dst, "w", encoding="utf-8") as fh:
                json.dump([], fh)

    for filename in ("users.json", "itineraries.json", "reservations.json"):
        with open(os.path.join(temp_dir, filename), "w", encoding="utf-8") as fh:
            json.dump([], fh)

    # Point the models module at the temporary directory
    original_paths = {
        "DATA_DIR": models.DATA_DIR,
        "USERS_FILE": models.USERS_FILE,
        "ITINERARIES_FILE": models.ITINERARIES_FILE,
        "DESTINATIONS_FILE": models.DESTINATIONS_FILE,
        "ACTIVITIES_FILE": models.ACTIVITIES_FILE,
        "TRANSPORT_FILE": models.TRANSPORT_FILE,
        "RESERVATIONS_FILE": models.RESERVATIONS_FILE,
    }

    models.DATA_DIR = temp_dir
    models.USERS_FILE = os.path.join(temp_dir, "users.json")
    models.ITINERARIES_FILE = os.path.join(temp_dir, "itineraries.json")
    models.DESTINATIONS_FILE = os.path.join(temp_dir, "destinations.json")
    models.ACTIVITIES_FILE = os.path.join(temp_dir, "activities.json")
    models.TRANSPORT_FILE = os.path.join(temp_dir, "transport.json")
    models.RESERVATIONS_FILE = os.path.join(temp_dir, "reservations.json")

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

    # Restore original paths and clean up
    for attr, value in original_paths.items():
        setattr(models, attr, value)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def auth_headers(client):
    """Register and log in a test user, returning ready-to-use auth headers."""
    client.post(
        "/register",
        json={"username": "testuser", "password": "testpass123", "preferences": ["culture", "famille"]},
    )
    response = client.post(
        "/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}