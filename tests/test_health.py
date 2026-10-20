from codebs.config import Settings, get_settings


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app_version" in body


def test_health_reports_exactly_the_configured_settings(app, client):
    def fake_settings() -> Settings:
        return Settings(app_version="9.9.9", environment="test")

    app.dependency_overrides[get_settings] = fake_settings

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_version": "9.9.9",
        "environment": "test",
    }
    
    
def test_unknown_route_returns_404(client):
    response = client.get("/does-not-exist")
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    