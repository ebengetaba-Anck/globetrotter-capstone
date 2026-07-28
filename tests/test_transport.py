"""
tests/test_transport.py

Tests for /transport search, reservation, and reservation listing.
"""


def test_get_all_transport(client):
    response = client.get("/transport")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_filter_transport_by_type(client):
    response = client.get("/transport?type=van_familial")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0
    for t in data:
        assert t["type"] == "van_familial"


def test_filter_transport_by_availability(client):
    response = client.get("/transport?disponible=true")
    assert response.status_code == 200
    data = response.get_json()
    for t in data:
        assert t["disponible"] is True


def test_reserve_requires_authentication(client):
    response = client.post("/transport/reserve", json={"transport_id": "taxi-001"})
    assert response.status_code == 401


def test_reserve_success(client, auth_headers):
    response = client.post(
        "/transport/reserve",
        json={"transport_id": "taxi-001", "depart": "Bonanjo", "destination": "Akwa"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["transport_id"] == "taxi-001"


def test_reserve_unknown_transport_fails(client, auth_headers):
    response = client.post(
        "/transport/reserve",
        json={"transport_id": "does-not-exist"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_list_reservations_requires_authentication(client):
    response = client.get("/transport/reservations")
    assert response.status_code == 401


def test_list_reservations_after_booking(client, auth_headers):
    client.post(
        "/transport/reserve",
        json={"transport_id": "taxi-001", "depart": "Bonanjo", "destination": "Akwa"},
        headers=auth_headers,
    )
    response = client.get("/transport/reservations", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1