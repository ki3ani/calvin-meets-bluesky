from unittest import mock


def test_read_comics(client):
    with mock.patch(
        "app.services.bluesky_service.BlueskyService"
    ) as MockBlueskyService:  # noqa
        response = client.get("/comics/")
        assert response.status_code in [200, 404]


def test_read_posts(client):
    with mock.patch(
        "app.services.bluesky_service.BlueskyService"
    ) as MockBlueskyService:  # noqa
        response = client.get("/posts/")
        assert response.status_code in [200, 404]
