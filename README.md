# Hospital Test Automation

Separate test and seed automation repo — completely decoupled from the app.

## Structure

```
.github/workflows/
  api-tests.yml     # Run API tests against live environment (daily + on-demand)
  seed-data.yml     # Seed data into EC2 via docker exec (on-demand)
seeds/
  base.py           # Shared helpers (names, ID generation)
  seed_fresh.py     # Wipe DB + insert 10 female patients
  fixtures/
    patients.json   # Patient data fixture reference
tests/
  conftest.py       # Session-scoped fixtures (auth tokens, base URL)
  test_auth.py      # Login, token, protected route tests
  test_patients.py  # Patient list, gender, ID format tests
  test_appointments.py  # Appointment list and date tests
  test_prescriptions.py # Prescription access tests
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
