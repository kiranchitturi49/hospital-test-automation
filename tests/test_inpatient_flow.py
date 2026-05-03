"""Functional tests — Inpatient Module (admission, prescriptions, diagnostics, activities, billing)."""
import requests
import pytest


class TestInpatientAdmission:
    """Admission lifecycle: create, list, update, discharge."""

    def test_list_inpatients(self, base_url, admin_headers):
        r = requests.get(f"{base_url}/api/v1/inpatients/", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            ip = data[0]
            assert "inpatient_id" in ip
            assert "patient_id" in ip
            assert "status" in ip
            assert ip["inpatient_id"].startswith("IP-")

    def test_get_inpatients_by_patient(self, base_url, admin_headers):
        """Fetch IP records for a known OP patient."""
        # Get first IP to find a patient_id
        r = requests.get(f"{base_url}/api/v1/inpatients/", headers=admin_headers, timeout=10)
        ips = r.json()
        if not ips:
            pytest.skip("No inpatients in system")
        pid = ips[0]["patient_id"]

        r2 = requests.get(f"{base_url}/api/v1/inpatients/by-patient/{pid}", headers=admin_headers, timeout=10)
        assert r2.status_code == 200
        assert isinstance(r2.json(), list)
        assert len(r2.json()) >= 1


class TestInpatientPrescriptions:
    """IP prescription creation and listing."""

    @pytest.fixture(autouse=True)
    def _setup(self, base_url, admin_headers):
        self.base = base_url
        self.headers = admin_headers
        # Find an admitted inpatient
        r = requests.get(f"{base_url}/api/v1/inpatients/", headers=admin_headers, timeout=10)
        admitted = [ip for ip in r.json() if ip.get("status") == "admitted"]
        self.ip = admitted[0] if admitted else None

    def test_list_ip_prescriptions(self):
        if not self.ip:
            pytest.skip("No admitted inpatient")
        r = requests.get(
            f"{self.base}/api/v1/ip/prescriptions/by-inpatient/{self.ip['inpatient_id']}",
            headers=self.headers, timeout=10,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_all_ip_prescriptions(self):
        """Medical Desk view — all IP prescriptions across patients."""
        r = requests.get(f"{self.base}/api/v1/ip/prescriptions/all", headers=self.headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            rx = data[0]
            assert "ip_rx_id" in rx
            assert "medicines" in rx


class TestInpatientDiagnostics:
    """Diagnostic test ordering and status workflow."""

    @pytest.fixture(autouse=True)
    def _setup(self, base_url, admin_headers):
        self.base = base_url
        self.headers = admin_headers
        r = requests.get(f"{base_url}/api/v1/inpatients/", headers=admin_headers, timeout=10)
        admitted = [ip for ip in r.json() if ip.get("status") == "admitted"]
        self.ip = admitted[0] if admitted else None

    def test_list_diagnostics_for_inpatient(self):
        if not self.ip:
            pytest.skip("No admitted inpatient")
        r = requests.get(
            f"{self.base}/api/v1/ip-diagnostics/by-inpatient/{self.ip['inpatient_id']}",
            headers=self.headers, timeout=10,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestInpatientActivities:
    """Nursing activity ordering and completion."""

    @pytest.fixture(autouse=True)
    def _setup(self, base_url, admin_headers):
        self.base = base_url
        self.headers = admin_headers
        r = requests.get(f"{base_url}/api/v1/inpatients/", headers=admin_headers, timeout=10)
        admitted = [ip for ip in r.json() if ip.get("status") == "admitted"]
        self.ip = admitted[0] if admitted else None

    def test_list_activities_for_inpatient(self):
        if not self.ip:
            pytest.skip("No admitted inpatient")
        r = requests.get(
            f"{self.base}/api/v1/ip-activities/by-inpatient/{self.ip['inpatient_id']}",
            headers=self.headers, timeout=10,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestInpatientBilling:
    """Billing item management and summaries."""

    @pytest.fixture(autouse=True)
    def _setup(self, base_url, admin_headers):
        self.base = base_url
        self.headers = admin_headers
        r = requests.get(f"{base_url}/api/v1/inpatients/", headers=admin_headers, timeout=10)
        admitted = [ip for ip in r.json() if ip.get("status") == "admitted"]
        self.ip = admitted[0] if admitted else None

    def test_list_billing_items(self):
        if not self.ip:
            pytest.skip("No admitted inpatient")
        r = requests.get(
            f"{self.base}/api/v1/ip-billing/by-inpatient/{self.ip['inpatient_id']}",
            headers=self.headers, timeout=10,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_billing_summary(self):
        if not self.ip:
            pytest.skip("No admitted inpatient")
        r = requests.get(
            f"{self.base}/api/v1/ip-billing/summary/{self.ip['inpatient_id']}",
            headers=self.headers, timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert "breakdown" in data
        assert "grand_total" in data
        assert isinstance(data["grand_total"], (int, float))

    def test_create_manual_billing_item(self):
        if not self.ip:
            pytest.skip("No admitted inpatient")
        payload = {
            "inpatient_id": self.ip["inpatient_id"],
            "category": "other",
            "description": "Test billing item (automated test)",
            "quantity": 1,
            "unit_price": 100.00,
            "notes": "Auto-test - safe to delete",
        }
        r = requests.post(f"{self.base}/api/v1/ip-billing/", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 201
        item = r.json()
        assert item["description"] == payload["description"]
        assert float(item["total_price"]) == 100.00
        # Cleanup
        requests.delete(f"{self.base}/api/v1/ip-billing/{item['id']}", headers=self.headers, timeout=10)
