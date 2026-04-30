"""Auth endpoint tests."""
import requests
import pytest


def test_health(base_url):
    r = requests.get(f"{base_url}/health", timeout=10)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_login_admin_success(base_url):
    r = requests.post(
        f"{base_url}/api/v1/auth/login",
        data={"username": "admin", "password": "admin123", "grant_type": "password"},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(base_url):
    r = requests.post(
        f"{base_url}/api/v1/auth/login",
        data={"username": "admin", "password": "wrongpass", "grant_type": "password"},
        timeout=10,
    )
    assert r.status_code in (400, 401)


def test_login_unknown_user(base_url):
    r = requests.post(
        f"{base_url}/api/v1/auth/login",
        data={"username": "ghost_user", "password": "pass123", "grant_type": "password"},
        timeout=10,
    )
    assert r.status_code in (400, 401)


def test_protected_route_no_token(base_url):
    r = requests.get(f"{base_url}/api/v1/patients/", timeout=10)
    assert r.status_code == 401


def test_protected_route_bad_token(base_url):
    r = requests.get(
        f"{base_url}/api/v1/patients/",
        headers={"Authorization": "Bearer invalid.token.value"},
        timeout=10,
    )
    assert r.status_code == 401
