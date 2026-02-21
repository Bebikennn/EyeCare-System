import math


def test_assessments_list(authenticated_client):
    resp = authenticated_client.get("/api/assessments/?page=1&per_page=5")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert "assessments" in data or "results" in data or "data" in data


def test_assessments_stats_growth(authenticated_client):
    resp = authenticated_client.get("/api/assessments/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert "high_risk" in data
    assert "high_risk_growth" in data

    hr = data["high_risk_growth"]
    assert isinstance(hr, (int, float))
    assert not math.isnan(float(hr))
