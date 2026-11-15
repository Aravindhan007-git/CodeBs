def test_landing_page_is_served_as_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "CodeBs" in response.text


def test_landing_page_is_not_listed_in_the_api_schema(client):
    schema = client.get("/openapi.json").json()

    assert "/" not in schema["paths"]