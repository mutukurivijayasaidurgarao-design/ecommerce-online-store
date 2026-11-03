from fastapi.testclient import TestClient
from main import app
from uuid import uuid4


client = TestClient(app)


def test_register_customer():
    unique_id = uuid4().hex[:8]

    response = client.post(
        "/register",
        json={
            "username": f"test_customer_{unique_id}",
            "email": f"test_customer_{unique_id}@example.com",
            "password": "Test@123"
        }
    )

    assert response.status_code == 200


def test_duplicate_username():
    response = client.post(
        "/register",
        json={
            "username": "test_customer",
            "email": "another@example.com",
            "password": "Test@123"
        }
    )

    assert response.status_code == 400


def test_login_customer():
    response = client.post(
        "/login",
        json={
            "username": "test_customer",
            "password": "Test@123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_wrong_password():
    response = client.post(
        "/login",
        json={
            "username": "test_customer",
            "password": "WrongPassword"
        }
    )

    assert response.status_code == 401


def test_me_without_token():
    response = client.get("/me")

    assert response.status_code == 401