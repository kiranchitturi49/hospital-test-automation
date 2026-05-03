"""Patient API tests — hits live app over HTTP."""
import requests


def test_list_patients_authenticated(base_url, admin_headers):
    r = requests.get(f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_patients_unauthenticated(base_url):
    r = requests.get(f"{base_url}/api/v1/patients/", timeout=10)
    assert r.status_code == 401


def test_patients_are_present(base_url, admin_headers):
    r = requests.get(f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10)
    assert r.status_code == 200
    patients = r.json()
    assert len(patients) > 0, "Expected at least one patient — run seed first"


def test_patients_all_female(base_url, admin_headers):
    r = requests.get(f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10)
    assert r.status_code == 200
    patients = r.json()
    # Exclude test patients created by security tests
    seeded_patients = [p for p in patients if not p.get("first_name", "").startswith("<script>")]
    non_female = [p for p in seeded_patients if p.get("gender") != "female"]
    assert len(non_female) == 0, f"Found non-female patients: {non_female}"


def test_patient_id_format(base_url, admin_headers):
    r = requests.get(f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10)
    patients = r.json()
    for p in patients:
        pid = p.get("patient_id", "")
        # Format: OP-DDMMYYYY-NNN-N (12 chars) or similar
        assert len(pid) >= 12, f"Invalid patient ID format: {pid}"
        assert pid[:8].isdigit(), f"Date part not numeric: {pid}"


def test_get_single_patient(base_url, admin_headers):
    patients = requests.get(
        f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10
    ).json()
    assert len(patients) > 0
    pid = patients[0]["id"]
    r = requests.get(f"{base_url}/api/v1/patients/{pid}", headers=admin_headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["id"] == pid
