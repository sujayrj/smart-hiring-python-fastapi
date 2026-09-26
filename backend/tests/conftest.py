import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-long-enough-32b")
os.environ.setdefault("INPUT_DATA_PATH", "../input-data.json")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import models.entities  # noqa: F401,E402  (register mappings)
from database import Base, engine  # noqa: E402
from main import app  # noqa: E402
from seed import load_seed  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    load_seed()
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str) -> str:
    resp = client.post("/api/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
