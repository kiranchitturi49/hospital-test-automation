"""Functional tests — Medicine Inventory (Medical Desk)."""
import requests
import pytest


class TestMedicineInventory:
    """CRUD and stock management for medicines."""

    def test_list_medicines(self, base_url, admin_headers):
        r = requests.get(f"{base_url}/api/v1/medicines/", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            m = data[0]
            assert "medicine_id" in m
            assert "name" in m
            assert "stock_quantity" in m
            assert "price" in m

    def test_create_medicine(self, base_url, admin_headers):
        payload = {
            "name": "Test Paracetamol 500mg",
            "category": "tablets",
            "manufacturer": "TestPharma",
            "batch_number": "BATCH-TEST-001",
            "unit": "tablets",
            "stock_quantity": 100,
            "low_stock_threshold": 10,
            "price": 5.50,
            "expiry_date": "2027-12-31",
            "notes": "Created by automated test",
        }
        r = requests.post(f"{base_url}/api/v1/medicines/", json=payload, headers=admin_headers, timeout=10)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Test Paracetamol 500mg"
        assert data["stock_quantity"] == 100
        assert data["medicine_id"].startswith("MED-")
        # Store for cleanup
        pytest.test_med_id = data["id"]
        pytest.test_med_str_id = data["medicine_id"]

    def test_get_single_medicine(self, base_url, admin_headers):
        mid = getattr(pytest, "test_med_id", None)
        if not mid:
            pytest.skip("No test medicine created")
        r = requests.get(f"{base_url}/api/v1/medicines/{mid}", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert r.json()["name"] == "Test Paracetamol 500mg"

    def test_update_medicine_stock(self, base_url, admin_headers):
        mid = getattr(pytest, "test_med_id", None)
        if not mid:
            pytest.skip("No test medicine created")
        r = requests.put(
            f"{base_url}/api/v1/medicines/{mid}",
            json={"stock_quantity": 200},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["stock_quantity"] == 200

    def test_low_stock_endpoint(self, base_url, admin_headers):
        r = requests.get(f"{base_url}/api/v1/medicines/low-stock", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for m in data:
            assert m["stock_quantity"] <= m["low_stock_threshold"]

    def test_expiring_medicines_endpoint(self, base_url, admin_headers):
        r = requests.get(f"{base_url}/api/v1/medicines/expiring?days=365", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_delete_medicine(self, base_url, admin_headers):
        mid = getattr(pytest, "test_med_id", None)
        if not mid:
            pytest.skip("No test medicine created")
        r = requests.delete(f"{base_url}/api/v1/medicines/{mid}", headers=admin_headers, timeout=10)
        assert r.status_code == 204
