"""
tests/test_activities.py

Tests for the /activities search endpoint.
"""


def test_get_all_activities(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_filter_activities_by_tag(client):
    response = client.get("/activities?tag=culture")
    assert response.status_code == 200
    data = response.get_json()
    for act in data:
        assert "culture" in [t.lower() for t in act["tags"]]


def test_filter_activities_by_quartier(client):
    response = client.get("/activities?quartier=Bonanjo")
    assert response.status_code == 200
    data = response.get_json()
    for act in data:
        assert act["quartier"].lower() == "bonanjo"