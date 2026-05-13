# login user tests
def test_login_success(client):

    client.post(
        "/api/v1/users/",
        json={
            "name": "loginuser",
            "email": "login@test.com",
            "password": "12345678",
            "role": "user",
            "specialty": "backend",
            "is_active": True
        }
    )

    response = client.post(
        "/api/v1/login",
        data={
            "username": "login@test.com",
            "password": "12345678"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_email(client):

    response = client.post(
        "/api/v1/login",
        data={
            "username": "wrong@test.com",
            "password": "12345678"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid credentials"


def test_login_invalid_password(client):

    client.post(
        "/api/v1/users/",
        json={
            "name": "testuser",
            "email": "test@test.com",
            "password": "12345678",
            "role": "user",
            "specialty": "backend",
            "is_active": True
        }
    )

    response = client.post(
        "/api/v1/login",
        data={
            "username": "test@test.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid credentials"

