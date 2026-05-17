# tests/test_auth.py
import pytest


class TestAuth:

    def test_login_success(self, client, auth_headers):
        """Login with correct credentials returns tokens."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@admin.com",
            "password": "testpass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["admin_name"] == "Test Admin"

    def test_login_wrong_password(self, client):
        """Login with wrong password returns 401."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@admin.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_wrong_email(self, client):
        """Login with non-existent email returns 401."""
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@nowhere.com",
            "password": "anypassword",
        })
        assert response.status_code == 401

    def test_login_invalid_email_format(self, client):
        """Login with invalid email format returns 422."""
        response = client.post("/api/v1/auth/login", json={
            "email": "not-an-email",
            "password": "testpass123",
        })
        assert response.status_code == 422

    def test_get_me_authenticated(self, client, auth_headers):
        """GET /auth/me returns admin info when authenticated."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@admin.com"
        assert data["full_name"] == "Test Admin"
        assert data["is_active"] is True

    def test_get_me_no_token(self, client):
        """GET /auth/me without token returns 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """GET /auth/me with invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    def test_refresh_token(self, client):
        """Valid refresh token returns new access token."""
        # Login first to get refresh token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@admin.com",
            "password": "testpass123",
        })
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_with_access_token_fails(self, client, auth_headers):
        """Using access token as refresh token returns 401."""
        access_token = auth_headers["Authorization"].split(" ")[1]
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token,
        })
        assert response.status_code == 401
