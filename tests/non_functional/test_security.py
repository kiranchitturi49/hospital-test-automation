"""Non-functional tests — Security (authentication, authorization, injection)."""
import requests
import pytest


class TestAuthenticationSecurity:
    """JWT / OAuth2 security checks."""

    def test_no_token_returns_401(self, base_url):
        """All protected endpoints must reject unauthenticated requests."""
        endpoints = [
            "/api/v1/patients/",
            "/api/v1/medicines/",
            "/api/v1/medicines/sales",
            "/api/v1/prescriptions/",
            "/api/v1/inpatients/",
            "/api/v1/medicine-returns/",
            "/api/v1/finance/expenses",
        ]
        for ep in endpoints:
            r = requests.get(f"{base_url}{ep}", timeout=10)
            assert r.status_code == 401, f"{ep} should return 401 without token"

    def test_expired_or_invalid_token(self, base_url):
        """Malformed tokens must be rejected."""
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJoYWNrZXIifQ.invalid"}
        r = requests.get(f"{base_url}/api/v1/patients/", headers=headers, timeout=10)
        assert r.status_code == 401

    def test_bearer_scheme_required(self, base_url, admin_token):
        """Token without 'Bearer' prefix should fail."""
        headers = {"Authorization": admin_token}  # Missing "Bearer "
        r = requests.get(f"{base_url}/api/v1/patients/", headers=headers, timeout=10)
        assert r.status_code in (401, 403)


class TestAuthorizationSecurity:
    """Role-based access control checks."""

    def test_doctor_cannot_delete_patient(self, base_url, doctor_headers):
        """Only admin can delete patients."""
        r = requests.delete(f"{base_url}/api/v1/patients/1", headers=doctor_headers, timeout=10)
        assert r.status_code in (403, 404)  # 403 if role check runs first, 404 if not found

    def test_doctor_cannot_access_expenses(self, base_url, doctor_headers):
        r = requests.get(f"{base_url}/api/v1/finance/expenses", headers=doctor_headers, timeout=10)
        assert r.status_code == 403

    def test_doctor_cannot_create_expense(self, base_url, doctor_headers):
        payload = {"category": "supplies", "description": "hack", "amount": 1, "expense_date": "2026-01-01"}
        r = requests.post(f"{base_url}/api/v1/finance/expenses", json=payload, headers=doctor_headers, timeout=10)
        assert r.status_code == 403


class TestInputValidation:
    """SQL injection and input sanitisation."""

    def test_sql_injection_in_patient_search(self, base_url, admin_headers):
        """Searching with SQL injection payload should not crash or leak data."""
        evil = "' OR '1'='1"
        r = requests.get(f"{base_url}/api/v1/patients/search/{evil}", headers=admin_headers, timeout=10)
        assert r.status_code in (404, 422)  # Not found or validation error, not 500

    def test_xss_in_patient_name(self, base_url, admin_headers):
        """XSS payload in name should be stored as-is (no execution) or rejected."""
        payload = {
            "first_name": "<script>alert('xss')</script>",
            "last_name": "TestXSS",
            "gender": "male",
            "phone": "9999900001",
            "patient_form_type": "general",
        }
        r = requests.post(f"{base_url}/api/v1/patients/", json=payload, headers=admin_headers, timeout=10)
        # Should succeed (stored as text) or be rejected — must NOT crash
        assert r.status_code in (201, 400, 422)

    def test_oversized_payload_rejected(self, base_url, admin_headers):
        """Extremely large payload should be rejected or handled gracefully."""
        payload = {"sale_id": "SALE-0001", "quantity_returned": 1, "return_reason": "A" * 1_000_000}
        r = requests.post(f"{base_url}/api/v1/medicine-returns/", json=payload, headers=admin_headers, timeout=10)
        assert r.status_code in (201, 400, 404, 413, 422)  # Must not crash with 500
