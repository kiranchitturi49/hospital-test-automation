"""
Pytest fixtures for live API tests.
All tests hit the running app over HTTP — no direct DB access.
"""
import os
import pytest
import requests

BASE_URL = os.getenv("APP_BASE_URL", "http://65.0.98.124:8000")
ADMIN_USER = os.getenv("TEST_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("TEST_ADMIN_PASS", "admin123")
DOCTOR_USER = os.getenv("TEST_DOCTOR_USER", "dr_padmavathi")
DOCTOR_PASS = os.getenv("TEST_DOCTOR_PASS", "doctor123")


def get_token(username: str, password: str) -> str:
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": username, "password": password, "grant_type": "password"},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def admin_token():
    return get_token(ADMIN_USER, ADMIN_PASS)


@pytest.fixture(scope="session")
def doctor_token():
    return get_token(DOCTOR_USER, DOCTOR_PASS)


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def doctor_headers(doctor_token):
    return {"Authorization": f"Bearer {doctor_token}"}
