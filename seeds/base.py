"""
Shared helpers for seed scripts.
These run INSIDE the hospital_api container via docker exec,
so they can import from app.* freely.
"""
import random
from datetime import date, timedelta, datetime, timezone

TODAY    = date.today()
TOMORROW = TODAY + timedelta(days=1)
NOW      = datetime.now(timezone.utc)

FEMALE_FIRST = [
    "Lakshmi", "Saraswathi", "Padmavathi", "Annapurna", "Vijayalakshmi",
    "Radhika", "Sivagami", "Santha Kumari", "Naga Laxmi", "Bhavani",
    "Kamala", "Pushpa", "Sailaja", "Triveni", "Vasantha",
    "Kavitha", "Hymavathi", "Sridevi", "Nirmala", "Mangamma",
]
MALE_FIRST = [
    "Venkata Sai", "Srinivasa", "Ramakrishna", "Narasimha", "Balakrishna",
    "Venkateswara", "Surya Prakash", "Ravi Shankar", "Kondaiah", "Govinda",
]
LAST_NAMES = ["Reddy", "Naidu", "Rao", "Chowdary", "Varma", "Sharma", "Goud", "Raju", "Pillai", "Kumar"]
CITIES     = ["Vijayawada", "Guntur", "Nellore", "Tirupati", "Kurnool", "Rajahmundry", "Eluru"]
REASONS    = ["BP Check", "Diabetes Follow-up", "Fever & Cold", "General Checkup",
              "Knee Pain", "Skin Allergy", "Cough & Cold", "Stomach Pain",
              "Back Pain", "Headache", "Thyroid Check", "Anaemia"]

def rand_phone() -> str:
    prefix = random.choice(["94", "95", "96", "98", "99"])
    return prefix + str(random.randint(10000000, 99999999))

def rand_dob(min_age: int = 20, max_age: int = 60) -> date:
    return TODAY - timedelta(days=random.randint(min_age * 365, max_age * 365))

def rand_address() -> str:
    return f"{random.randint(1, 99)}-{random.randint(1, 9)}, {random.choice(CITIES)}"

def generate_patient_id(db, phone: str) -> str:
    """Matches current app logic: OP-DDmmmYY with optional -N suffix on collision."""
    from app.models.patient import Patient
    from datetime import date as date_module
    today = date_module.today()
    day_part = today.strftime("%d")
    phone_last3 = phone[-3:] if phone and len(phone) >= 3 else "000"
    year_part = today.strftime("%y")
    base_id = f"OP-{day_part}{phone_last3}{year_part}"
    existing = db.query(Patient).filter(Patient.patient_id.like(f"{base_id}%")).count()
    return f"{base_id}-{existing + 1}" if existing > 0 else base_id
