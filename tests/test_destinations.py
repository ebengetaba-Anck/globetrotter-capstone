"""
tests/test_destinations.py

Tests for the /destinations search endpoint.
"""


def test_get_all_destinations(client):
    response = client.get("/destinations")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_filter_by_quartier(client):
    response = client.get("/destinations?quartier=Akwa")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0
    for dest in data:
        assert dest["quartier"].lower() == "akwa"


def test_filter_by_tag(client):
    response = client.get("/destinations?tag=famille")
    assert response.status_code == 200
    data = response.get_json()
    for dest in data:
        assert "famille" in [t.lower() for t in dest["tags"]]


def test_filter_by_max_cost(client):
    response = client.get("/destinations?max_cost=1000")
    assert response.status_code == 200
    data = response.get_json()
    for dest in data:
        assert dest["avg_cost"] <= 1000


def test_invalid_max_cost_returns_400(client):
    response = client.get("/destinations?max_cost=abc")
    assert response.status_code == 400


def test_free_text_search(client):
    response = client.get("/destinations?q=marche")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0