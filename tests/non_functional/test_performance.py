"""Non-functional tests — Performance (response time, concurrent load)."""
import requests
import pytest
import time
import concurrent.futures


RESPONSE_TIME_LIMIT_MS = 3000  # 3 seconds max for any single request


class TestResponseTime:
    """Individual endpoint response times should be within acceptable limits."""

    @pytest.mark.parametrize("endpoint", [
        "/health",
        "/api/v1/patients/",
        "/api/v1/medicines/",
        "/api/v1/medicines/sales",
        "/api/v1/prescriptions/",
        "/api/v1/inpatients/",
        "/api/v1/medicine-returns/",
        "/api/v1/medicine-returns/dues",
    ])
    def test_endpoint_response_time(self, base_url, admin_headers, endpoint):
        start = time.time()
        r = requests.get(f"{base_url}{endpoint}", headers=admin_headers, timeout=10)
        elapsed_ms = (time.time() - start) * 1000
        assert r.status_code in (200, 401), f"Unexpected status {r.status_code} for {endpoint}"
        assert elapsed_ms < RESPONSE_TIME_LIMIT_MS, (
            f"{endpoint} took {elapsed_ms:.0f}ms (limit: {RESPONSE_TIME_LIMIT_MS}ms)"
        )


class TestConcurrentAccess:
    """Simulate concurrent API calls."""

    def test_concurrent_patient_list(self, base_url, admin_headers):
        """10 concurrent requests to /patients/ should all succeed."""
        def fetch():
            return requests.get(f"{base_url}/api/v1/patients/", headers=admin_headers, timeout=15)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(fetch) for _ in range(10)]
            results = [f.result() for f in futures]

        for r in results:
            assert r.status_code == 200

    def test_concurrent_medicine_list(self, base_url, admin_headers):
        """10 concurrent requests to /medicines/ should all succeed."""
        def fetch():
            return requests.get(f"{base_url}/api/v1/medicines/", headers=admin_headers, timeout=15)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(fetch) for _ in range(10)]
            results = [f.result() for f in futures]

        for r in results:
            assert r.status_code == 200


class TestPagination:
    """Large dataset handling."""

    def test_patients_pagination(self, base_url, admin_headers):
        r = requests.get(
            f"{base_url}/api/v1/patients/", params={"skip": 0, "limit": 5},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) <= 5

    def test_medicines_pagination(self, base_url, admin_headers):
        r = requests.get(
            f"{base_url}/api/v1/medicines/", params={"skip": 0, "limit": 5},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) <= 5

    def test_sales_pagination(self, base_url, admin_headers):
        r = requests.get(
            f"{base_url}/api/v1/medicines/sales", params={"skip": 0, "limit": 5},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) <= 5
