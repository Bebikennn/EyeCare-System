import math


def test_users_list(authenticated_client):
    resp = authenticated_client.get("/api/users/?page=1&per_page=5")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert "users" in data
    assert "pagination" in data


def test_users_stats_growth(authenticated_client):
    resp = authenticated_client.get("/api/users/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert "total_users" in data
    assert "growth_percentage" in data

    gp = data["growth_percentage"]
    assert isinstance(gp, (int, float))
    assert not math.isnan(float(gp))
