from converter import create_app


def test_home_page():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b'<label for="media-url">YouTube URL</label>' in response.data
    assert b'id="media-url"' in response.data
    assert b'type="url"' in response.data
    assert b'<button type="submit">Submit URL</button>' in response.data
    assert b'id="video-preview"' in response.data
    assert b'youtube-player' in response.data


def test_health_endpoint_checks_database():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}
