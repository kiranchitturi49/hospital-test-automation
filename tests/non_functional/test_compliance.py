"""Non-functional tests — Compliance (audit trails, billing traceability, data integrity)."""
import requests
import pytest


class TestAuditTrailCompliance:
    """Verify audit mechanisms exist and function."""

    def test_patient_edit_creates_history(self, base_url, admin_headers):
        """Updating a patient should create a history snapshot."""
        # Get a patient
        r = requests.get(f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10)
        patients = r.json()
        if not patients:
            pytest.skip("No patients")
        p = patients[0]

        # Check history before
        r1 = requests.get(
            f"{base_url}/api/v1/patients/{p['id']}/history",
            headers=admin_headers, timeout=10,
        )
        assert r1.status_code == 200
        history_before = len(r1.json())

        # Update patient (trivial change)
        requests.put(
            f"{base_url}/api/v1/patients/{p['id']}",
            json={"allergies": f"Test allergy (compliance check)"},
            headers=admin_headers, timeout=10,
        )

        # Check history after
        r2 = requests.get(
            f"{base_url}/api/v1/patients/{p['id']}/history",
            headers=admin_headers, timeout=10,
        )
        history_after = len(r2.json())
        assert history_after > history_before, "Patient edit did not create history snapshot"

        # Restore
        requests.put(
            f"{base_url}/api/v1/patients/{p['id']}",
            json={"allergies": p.get("allergies") or ""},
            headers=admin_headers, timeout=10,
        )

    def test_history_contains_changed_by(self, base_url, admin_headers):
        """History records must contain who made the change."""
        r = requests.get(f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=10)
        patients = r.json()
        if not patients:
            pytest.skip("No patients")

        r2 = requests.get(
            f"{base_url}/api/v1/patients/{patients[0]['id']}/history",
            headers=admin_headers, timeout=10,
        )
        history = r2.json()
        if not history:
            pytest.skip("No history records")
        assert "changed_by" in history[0]
        assert history[0]["changed_by"] is not None


class TestBillingTraceability:
    """Billing items must be traceable to source transactions."""

    def test_medicine_billing_has_sale_ref(self, base_url, admin_headers):
        """Medicine billing items created from dispense should have sale_ref_id."""
        r = requests.get(f"{base_url}/api/v1/inpatients/", headers=admin_headers, timeout=10)
        ips = r.json()
        if not ips:
            pytest.skip("No inpatients")

        for ip in ips[:5]:
            r2 = requests.get(
                f"{base_url}/api/v1/ip-billing/by-inpatient/{ip['inpatient_id']}",
                headers=admin_headers, timeout=10,
            )
            items = r2.json()
            med_items = [i for i in items if i.get("category") == "medicine"]
            for item in med_items:
                assert "sale_ref_id" in item, f"Medicine billing item {item['id']} missing sale_ref_id"

    def test_billing_totals_are_positive(self, base_url, admin_headers):
        """Billing totals should never be negative."""
        r = requests.get(f"{base_url}/api/v1/inpatients/", headers=admin_headers, timeout=10)
        ips = r.json()
        for ip in ips[:5]:
            r2 = requests.get(
                f"{base_url}/api/v1/ip-billing/summary/{ip['inpatient_id']}",
                headers=admin_headers, timeout=10,
            )
            summary = r2.json()
            assert summary["grand_total"] >= 0


class TestReturnAuditCompliance:
    """Return records must maintain full audit trail."""

    def test_returns_have_audit_fields(self, base_url, admin_headers):
        """Every return record must have returned_by and created_at."""
        r = requests.get(f"{base_url}/api/v1/medicine-returns/", headers=admin_headers, timeout=10)
        returns = r.json()
        for ret in returns[:10]:
            assert ret.get("returned_by"), f"Return {ret['return_id']} missing returned_by"
            assert ret.get("created_at"), f"Return {ret['return_id']} missing created_at"

    def test_returns_reference_valid_sale(self, base_url, admin_headers):
        """Every return must reference an existing sale."""
        r = requests.get(f"{base_url}/api/v1/medicine-returns/", headers=admin_headers, timeout=10)
        returns = r.json()
        if not returns:
            pytest.skip("No returns to verify")

        sales_r = requests.get(f"{base_url}/api/v1/medicines/sales", headers=admin_headers, timeout=10)
        sale_ids = {s["sale_id"] for s in sales_r.json()}

        for ret in returns[:10]:
            assert ret["sale_id"] in sale_ids, f"Return {ret['return_id']} references missing sale {ret['sale_id']}"


class TestDataIntegrity:
    """Cross-entity data consistency checks."""

    def test_sale_quantity_returned_never_exceeds_sold(self, base_url, admin_headers):
        """quantity_returned should never exceed quantity_sold."""
        r = requests.get(f"{base_url}/api/v1/medicines/sales", headers=admin_headers, timeout=10)
        sales = r.json()
        for s in sales:
            returned = s.get("quantity_returned") or 0
            assert returned <= s["quantity_sold"], (
                f"Sale {s['sale_id']}: returned {returned} > sold {s['quantity_sold']}"
            )

    def test_sale_total_price_consistent_with_net_qty(self, base_url, admin_headers):
        """total_price should equal unit_price * (sold - returned) after returns."""
        r = requests.get(f"{base_url}/api/v1/medicines/sales", headers=admin_headers, timeout=10)
        sales = r.json()
        for s in sales:
            if s.get("unit_price") is None or s.get("total_price") is None:
                continue
            returned = s.get("quantity_returned") or 0
            net_qty = s["quantity_sold"] - returned
            expected = round(s["unit_price"] * net_qty, 2)
            actual = round(s["total_price"], 2)
            assert abs(actual - expected) < 0.02, (
                f"Sale {s['sale_id']}: total_price {actual} != expected {expected} "
                f"(unit={s['unit_price']}, sold={s['quantity_sold']}, ret={returned})"
            )

    def test_full_return_has_zero_total(self, base_url, admin_headers):
        """Sales with full_return status should have total_price = 0."""
        r = requests.get(f"{base_url}/api/v1/medicines/sales", headers=admin_headers, timeout=10)
        sales = r.json()
        for s in sales:
            if s.get("payment_status") == "full_return":
                assert s["total_price"] == 0 or s["total_price"] is None, (
                    f"Sale {s['sale_id']} is full_return but total_price = {s['total_price']}"
                )
