def test_login_returns_a_bearer_token(client, make_user):
    make_user(email="engineer@hom.local")
    resp = client.post("/api/auth/login", json={"email": "engineer@hom.local", "password": "changeme"})

    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert resp.json()["access_token"]


def test_login_with_wrong_password_is_rejected(client, make_user):
    make_user(email="engineer@hom.local")
    resp = client.post("/api/auth/login", json={"email": "engineer@hom.local", "password": "wrong"})

    assert resp.status_code == 401


def test_me_reflects_the_authenticated_user(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.json()["role"] == "ml_engineer"


def test_overview_on_an_empty_database_returns_zeroed_stats(client, auth_headers):
    resp = client.get("/api/overview", headers=auth_headers)

    assert resp.status_code == 200
    stats = resp.json()["stats"]
    assert stats["models_total"] == 0
    assert stats["active_training_jobs"] == 0
    assert resp.json()["recent_training_runs"] == []
