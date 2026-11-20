from converter import create_app


def test_home_page():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"conversion service is not implemented yet" in response.data


def test_health_endpoint_checks_database():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}
