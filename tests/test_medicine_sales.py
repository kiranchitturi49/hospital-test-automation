"""Functional tests — Medicine Sales (sell, stock deduction, IP auto-billing)."""
import requests
import pytest


class TestMedicineSales:
    """Sale transactions — both OP (paid) and IP (due)."""

    @pytest.fixture(autouse=True)
    def _setup(self, base_url, admin_headers):
        """Ensure at least one patient and one medicine exist for sale tests."""
        self.base = base_url
        self.headers = admin_headers

        # Fetch first available patient
        r = requests.get(f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10)
        patients = r.json()
        if not patients:
            pytest.skip("No patients in system")
        self.patient_id = patients[0]["patient_id"]

        # Fetch first medicine with stock > 0
        r = requests.get(f"{base_url}/api/v1/medicines/", headers=admin_headers, timeout=10)
        meds = [m for m in r.json() if m["stock_quantity"] > 2]
        if not meds:
            pytest.skip("No medicines with stock")
        self.med = meds[0]

    def test_sell_medicine_op(self):
        """Sell medicine to OP patient — should deduct stock and status = paid."""
        stock_before = self.med["stock_quantity"]
        qty = 1
        payload = {
            "patient_id": self.patient_id,
            "medicine_db_id": self.med["id"],
            "quantity_sold": qty,
            "payment_mode": "cash",
        }
        r = requests.post(f"{self.base}/api/v1/medicines/sell", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 201
        sale = r.json()
        assert sale["sale_id"].startswith("SALE-")
        assert sale["quantity_sold"] == qty
        assert sale["payment_status"] == "paid"
        assert sale["is_inpatient"] is False

        # Verify stock deducted
        r2 = requests.get(f"{self.base}/api/v1/medicines/{self.med['id']}", headers=self.headers, timeout=10)
        assert r2.json()["stock_quantity"] == stock_before - qty

        # Store for return tests
        pytest.last_sale_id = sale["sale_id"]
        pytest.last_sale_unit_price = sale["unit_price"]
        pytest.last_sale_qty = qty

    def test_sell_insufficient_stock(self):
        """Selling more than available should fail with 400."""
        payload = {
            "patient_id": self.patient_id,
            "medicine_db_id": self.med["id"],
            "quantity_sold": 999999,
            "payment_mode": "cash",
        }
        r = requests.post(f"{self.base}/api/v1/medicines/sell", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 400
        assert "Insufficient stock" in r.json()["detail"]

    def test_sell_zero_quantity(self):
        """Quantity 0 should be rejected."""
        payload = {
            "patient_id": self.patient_id,
            "medicine_db_id": self.med["id"],
            "quantity_sold": 0,
            "payment_mode": "cash",
        }
        r = requests.post(f"{self.base}/api/v1/medicines/sell", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 400

    def test_sell_invalid_patient(self):
        """Non-existent patient should get 404."""
        payload = {
            "patient_id": "OP-DOESNOTEXIST",
            "medicine_db_id": self.med["id"],
            "quantity_sold": 1,
            "payment_mode": "cash",
        }
        r = requests.post(f"{self.base}/api/v1/medicines/sell", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 404

    def test_list_sales(self):
        r = requests.get(f"{self.base}/api/v1/medicines/sales", headers=self.headers, timeout=10)
        assert r.status_code == 200
        sales = r.json()
        assert isinstance(sales, list)
        if sales:
            s = sales[0]
            assert "sale_id" in s
            assert "total_price" in s
            assert "payment_status" in s
            assert "quantity_returned" in s
