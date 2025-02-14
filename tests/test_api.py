def test_read_comics(client):
    response = client.get("/comics/")
    assert response.status_code in [200, 404]


def test_read_posts(client):
    response = client.get("/posts/")
    assert response.status_code in [200, 404]
