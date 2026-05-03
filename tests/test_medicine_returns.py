"""Functional tests — Medicine Returns (stock restoration, price recalc, fraud prevention)."""
import requests
import pytest


class TestMedicineReturns:
    """Return processing — inventory update, sales ledger recalc, anti-fraud."""

    @pytest.fixture(autouse=True)
    def _setup(self, base_url, admin_headers):
        self.base = base_url
        self.headers = admin_headers

    def _find_returnable_sale(self):
        """Find a sale with returnable quantity > 0."""
        r = requests.get(f"{self.base}/api/v1/medicines/sales", headers=self.headers, timeout=10)
        sales = r.json()
        for s in sales:
            returnable = s["quantity_sold"] - (s.get("quantity_returned") or 0)
            if returnable > 0 and s["payment_status"] not in ("full_return",):
                return s
        return None

    # ─── Inventory Stock Restoration ────────────────────────────────
    def test_return_restores_stock(self):
        """After return, medicine stock_quantity must increase."""
        sale = self._find_returnable_sale()
        if not sale:
            pytest.skip("No returnable sale found")

        # Get stock before
        meds = requests.get(f"{self.base}/api/v1/medicines/", headers=self.headers, timeout=10).json()
        med = next((m for m in meds if m["medicine_id"] == sale["medicine_id"]), None)
        if not med:
            pytest.skip("Medicine not found in inventory")
        stock_before = med["stock_quantity"]

        # Process return
        ret_qty = 1
        payload = {"sale_id": sale["sale_id"], "quantity_returned": ret_qty, "return_reason": "Test return"}
        r = requests.post(f"{self.base}/api/v1/medicine-returns/", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 201
        ret = r.json()
        assert ret["return_id"].startswith("RET-")
        assert ret["quantity_returned"] == ret_qty

        # Verify stock increased
        med_after = requests.get(f"{self.base}/api/v1/medicines/{med['id']}", headers=self.headers, timeout=10).json()
        assert med_after["stock_quantity"] == stock_before + ret_qty

    # ─── Sales Price Recalculation ──────────────────────────────────
    def test_return_recalculates_sale_total_price(self):
        """total_price on the sale should equal unit_price * (sold - returned)."""
        sale = self._find_returnable_sale()
        if not sale:
            pytest.skip("No returnable sale found")

        unit_price = sale["unit_price"] or 0
        original_qty_returned = sale.get("quantity_returned") or 0
        ret_qty = 1

        payload = {"sale_id": sale["sale_id"], "quantity_returned": ret_qty, "return_reason": "Price recalc test"}
        r = requests.post(f"{self.base}/api/v1/medicine-returns/", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 201

        # Fetch updated sale
        sales = requests.get(f"{self.base}/api/v1/medicines/sales", headers=self.headers, timeout=10).json()
        updated_sale = next((s for s in sales if s["sale_id"] == sale["sale_id"]), None)
        assert updated_sale is not None

        expected_net_qty = sale["quantity_sold"] - (original_qty_returned + ret_qty)
        expected_total = round(unit_price * expected_net_qty, 2)
        assert abs(updated_sale["total_price"] - expected_total) < 0.01

    # ─── Payment Status Transitions ────────────────────────────────
    def test_return_sets_partial_return_status(self):
        """Partial return should set payment_status to 'partial_return'."""
        sale = self._find_returnable_sale()
        if not sale:
            pytest.skip("No returnable sale found")
        returnable = sale["quantity_sold"] - (sale.get("quantity_returned") or 0)
        if returnable < 2:
            pytest.skip("Need sale with returnable >= 2 for partial test")

        payload = {"sale_id": sale["sale_id"], "quantity_returned": 1, "return_reason": "Partial status test"}
        r = requests.post(f"{self.base}/api/v1/medicine-returns/", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 201

        sales = requests.get(f"{self.base}/api/v1/medicines/sales", headers=self.headers, timeout=10).json()
        updated = next((s for s in sales if s["sale_id"] == sale["sale_id"]), None)
        assert updated["payment_status"] == "partial_return"

    # ─── Fraud Prevention — Duplicate / Over-Return ─────────────────
    def test_cannot_return_more_than_sold(self):
        """Returning more than sold - already_returned should fail."""
        sale = self._find_returnable_sale()
        if not sale:
            pytest.skip("No returnable sale found")
        returnable = sale["quantity_sold"] - (sale.get("quantity_returned") or 0)

        payload = {"sale_id": sale["sale_id"], "quantity_returned": returnable + 100}
        r = requests.post(f"{self.base}/api/v1/medicine-returns/", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 400
        assert "returnable" in r.json()["detail"].lower() or "cannot return" in r.json()["detail"].lower()

    def test_cannot_return_zero_quantity(self):
        """Return quantity = 0 should be rejected."""
        sale = self._find_returnable_sale()
        if not sale:
            pytest.skip("No returnable sale found")

        payload = {"sale_id": sale["sale_id"], "quantity_returned": 0}
        r = requests.post(f"{self.base}/api/v1/medicine-returns/", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 400

    def test_cannot_return_negative_quantity(self):
        """Return quantity < 0 should be rejected."""
        sale = self._find_returnable_sale()
        if not sale:
            pytest.skip("No returnable sale found")

        payload = {"sale_id": sale["sale_id"], "quantity_returned": -5}
        r = requests.post(f"{self.base}/api/v1/medicine-returns/", json=payload, headers=self.headers, timeout=10)
        assert r.status_code in (400, 422)

    def test_return_nonexistent_sale(self):
        """Returning against a non-existent sale ID should 404."""
        payload = {"sale_id": "SALE-99999", "quantity_returned": 1}
        r = requests.post(f"{self.base}/api/v1/medicine-returns/", json=payload, headers=self.headers, timeout=10)
        assert r.status_code == 404

    # ─── Returns Listing ────────────────────────────────────────────
    def test_list_returns(self):
        r = requests.get(f"{self.base}/api/v1/medicine-returns/", headers=self.headers, timeout=10)
        assert r.status_code == 200
        returns = r.json()
        assert isinstance(returns, list)
        if returns:
            ret = returns[0]
            assert "return_id" in ret
            assert "sale_id" in ret
            assert "quantity_returned" in ret
            assert "refund_amount" in ret
            assert "returned_by" in ret

    # ─── Due Tracking ───────────────────────────────────────────────
    def test_list_dues(self):
        r = requests.get(f"{self.base}/api/v1/medicine-returns/dues", headers=self.headers, timeout=10)
        assert r.status_code == 200
        dues = r.json()
        assert isinstance(dues, list)
        for d in dues:
            assert d["payment_status"] in ("due", "partial_return")
