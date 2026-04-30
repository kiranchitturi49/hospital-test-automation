"""Appointment API tests."""
import requests
from datetime import date


def test_list_appointments(base_url, admin_headers):
    r = requests.get(f"{base_url}/api/v1/appointments/", headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_today_appointments_exist(base_url, admin_headers):
    today = date.today().isoformat()
    r = requests.get(
        f"{base_url}/api/v1/appointments/",
        headers=admin_headers,
        params={"date": today},
        timeout=10,
    )
    assert r.status_code == 200
    appts = r.json()
    assert len(appts) > 0, f"Expected today's appointments ({today}) — run seed first"


def test_appointments_have_required_fields(base_url, admin_headers):
    r = requests.get(f"{base_url}/api/v1/appointments/", headers=admin_headers, timeout=10)
    appts = r.json()
    for appt in appts:
        assert "id" in appt
        assert "appointment_date" in appt
        assert "status" in appt


def test_appointment_statuses_valid(base_url, admin_headers):
    valid_statuses = {"scheduled", "confirmed", "in_progress", "completed", "cancelled", "no_show"}
    r = requests.get(f"{base_url}/api/v1/appointments/", headers=admin_headers, timeout=10)
    for appt in r.json():
        assert appt["status"] in valid_statuses, f"Invalid status: {appt['status']}"
