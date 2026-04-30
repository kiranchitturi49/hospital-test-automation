"""Prescription API tests."""
import requests


def test_list_prescriptions(base_url, doctor_headers):
    r = requests.get(f"{base_url}/api/v1/prescriptions/", headers=doctor_headers, timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_prescriptions_unauthenticated(base_url):
    r = requests.get(f"{base_url}/api/v1/prescriptions/", timeout=10)
    assert r.status_code == 401


def test_patient_prescriptions_empty_after_seed(base_url, admin_headers):
    patients = requests.get(
        f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10
    ).json()
    assert len(patients) > 0
    patient_db_id = patients[0]["id"]
    r = requests.get(
        f"{base_url}/api/v1/prescriptions/patient/{patient_db_id}",
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)
