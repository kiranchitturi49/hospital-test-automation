"""Functional tests — Finance, Expenses, and Audit summaries."""
import requests
import pytest


class TestExpenses:
    """Expense CRUD (admin only)."""

    def test_list_expenses(self, base_url, admin_headers):
        r = requests.get(f"{base_url}/api/v1/finance/expenses", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_expense(self, base_url, admin_headers):
        payload = {
            "category": "supplies",
            "description": "Test cotton rolls (automated test)",
            "amount": 250.00,
            "paid_to": "Test Vendor",
            "payment_mode": "cash",
            "expense_date": "2026-05-03",
        }
        r = requests.post(f"{base_url}/api/v1/finance/expenses", json=payload, headers=admin_headers, timeout=10)
        assert r.status_code == 201
        data = r.json()
        assert data["expense_id"].startswith("EXP-")
        assert float(data["amount"]) == 250.00
        # Cleanup
        requests.delete(
            f"{base_url}/api/v1/finance/expenses/{data['expense_id']}",
            headers=admin_headers, timeout=10,
        )

    def test_non_admin_cannot_create_expense(self, base_url, doctor_headers):
        payload = {
            "category": "supplies",
            "description": "Should fail",
            "amount": 100.00,
            "expense_date": "2026-05-03",
        }
        r = requests.post(f"{base_url}/api/v1/finance/expenses", json=payload, headers=doctor_headers, timeout=10)
        assert r.status_code == 403

    def test_filter_expenses_by_date(self, base_url, admin_headers):
        r = requests.get(
            f"{base_url}/api/v1/finance/expenses",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200


class TestFinancialSummaries:
    """Hospital, Medical Desk, and Overall summaries."""

    def test_hospital_summary(self, base_url, admin_headers):
        r = requests.get(f"{base_url}/api/v1/finance/summary/hospital", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "income" in data
        assert "expenses" in data
        assert "net" in data
        assert "total" in data["income"]
        assert "by_payment_mode" in data["income"]

    def test_medical_desk_summary(self, base_url, admin_headers):
        r = requests.get(f"{base_url}/api/v1/finance/summary/medical-desk", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "total_revenue" in data
        assert "total_sales" in data
        assert "top_medicines" in data

    def test_overall_summary(self, base_url, admin_headers):
        r = requests.get(f"{base_url}/api/v1/finance/summary/overall", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "patient_income" in data
        assert "medicine_income" in data
        assert "total_expenses" in data
        assert "net_profit" in data

    def test_non_admin_blocked_from_summaries(self, base_url, doctor_headers):
        for endpoint in ["hospital", "medical-desk", "overall"]:
            r = requests.get(
                f"{base_url}/api/v1/finance/summary/{endpoint}",
                headers=doctor_headers, timeout=10,
            )
            assert r.status_code == 403, f"Doctor should not access /summary/{endpoint}"

    def test_summary_with_date_range(self, base_url, admin_headers):
        r = requests.get(
            f"{base_url}/api/v1/finance/summary/overall",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["net_profit"], (int, float))
