# Hospital Test Automation & Documentation

Comprehensive test suite, documentation, and compliance verification for the Hospital Management System.

## Structure

```
docs/
  er-diagram.md              # Complete ER diagram (Mermaid) + textual description
  user-guide.md              # Step-by-step user guide for all discovered flows
  slideshow.html             # Interactive HTML slideshow (12 slides, keyboard nav)
seeds/
  base.py                    # Shared helpers (names, ID generation)
  seed_fresh.py              # Wipe DB + insert sample patients
  fixtures/
    patients.json            # Patient data fixture reference
tests/
  conftest.py                # Session-scoped fixtures (auth tokens, base URL)
  test_auth.py               # Login, token, protected route tests
  test_patients.py           # Patient CRUD, search, history tests
  test_appointments.py       # Appointment list and date tests
  test_prescriptions.py      # Prescription CRUD tests
  test_medicine_inventory.py # Medicine CRUD, stock, expiry, low-stock
  test_medicine_sales.py     # Sales (OP/IP), stock deduction, validation
  test_medicine_returns.py   # Returns: stock restore, price recalc, fraud prevention
  test_inpatient_flow.py     # IP admission, prescriptions, diagnostics, activities, billing
  test_finance_audit.py      # Expenses, financial summaries, role access
  non_functional/
    test_security.py         # Auth bypass, RBAC, SQL injection, XSS
    test_performance.py      # Response time, concurrency, pagination
    test_compliance.py       # Audit trails, billing traceability, data integrity
```

## How to run locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in values
pytest tests/ -v
```

## GitHub Actions — Secrets needed

Add in repo → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `EC2_HOST` | `65.0.100.26` |
| `EC2_SSH_KEY` | Contents of `.pem` key file |
| `TEST_ADMIN_USER` | `admin` |
| `TEST_ADMIN_PASS` | `admin123` |
| `TEST_DOCTOR_USER` | `dr_padmavathi` |
| `TEST_DOCTOR_PASS` | `doctor123` |

## Workflows

### Seed Data (manual)
Actions → Seed Data → Run workflow → choose `seed_fresh`
- Wipes existing clinical data
- Inserts 10 female patients (5 today, 3 tomorrow, 2 past)
- Patient IDs follow app format: `DDMMYYYYpppYY`

### API Tests (daily + manual)
Actions → API Tests → Run workflow
- Hits live app over HTTP — no direct DB access
- Runs daily at 6:00 AM IST
- Opens a GitHub Issue automatically on failure
