import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.main import JOB_PREFIX, QUEUE_KEY, app, get_redis


@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def client(fake_redis):
    app.dependency_overrides[get_redis] = lambda: fake_redis
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_check_queues_job(client, fake_redis):
    response = client.post("/checks", json={"url": "https://example.com"})

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert fake_redis.lrange(QUEUE_KEY, 0, -1) == [body["id"]]
    stored = fake_redis.hgetall(f"{JOB_PREFIX}{body['id']}")
    assert stored["url"] == "https://example.com/"
    assert stored["status"] == "pending"


def test_create_check_rejects_invalid_url(client):
    response = client.post("/checks", json={"url": "not-a-url"})

    assert response.status_code == 422


def test_get_check_not_found(client):
    response = client.get("/checks/does-not-exist")

    assert response.status_code == 404


def test_get_check_returns_stored_result(client, fake_redis):
    fake_redis.hset(
        f"{JOB_PREFIX}abc123",
        mapping={"url": "https://example.com/", "status": "done", "result": "up"},
    )

    response = client.get("/checks/abc123")

    assert response.status_code == 200
    assert response.json()["result"] == "up"
