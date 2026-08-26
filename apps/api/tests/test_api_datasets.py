import json

from hom_core.enums import UserRole


def _upload(client, headers, filename="samples.jsonl", content=None):
    if content is None:
        content = "\n".join(
            json.dumps({"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]})
            for _ in range(3)
        ).encode("utf-8")
    return client.post(
        "/api/datasets",
        headers=headers,
        data={"name": "Test Dataset", "description": "demo", "type": "conversation"},
        files={"file": (filename, content, "application/jsonl")},
    )


def test_upload_dataset_returns_computed_stats(client, auth_headers):
    resp = _upload(client, auth_headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "ready"
    assert body["sample_count"] == 3
    assert body["stats"]["invalid_count"] == 0


def test_list_datasets_requires_authentication(client):
    resp = client.get("/api/datasets")
    assert resp.status_code == 401


def test_viewer_cannot_upload_datasets(client, make_user):
    _, token = make_user(email="viewer@hom.local", role=UserRole.VIEWER)
    resp = _upload(client, {"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_unsupported_extension_is_rejected(client, auth_headers):
    resp = _upload(client, auth_headers, filename="samples.txt", content=b"not a dataset")
    assert resp.status_code == 400


def test_get_and_delete_dataset_roundtrip(client, auth_headers):
    created = _upload(client, auth_headers).json()

    fetched = client.get(f"/api/datasets/{created['id']}", headers=auth_headers)
    assert fetched.status_code == 200

    deleted = client.delete(f"/api/datasets/{created['id']}", headers=auth_headers)
    assert deleted.status_code == 204

    missing = client.get(f"/api/datasets/{created['id']}", headers=auth_headers)
    assert missing.status_code == 404
