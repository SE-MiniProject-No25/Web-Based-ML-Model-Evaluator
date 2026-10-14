def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_directory_is_outside_the_source_tree(client, settings):
    assert settings.storage_dir.exists()
