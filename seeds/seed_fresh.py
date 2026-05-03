"""
Fresh seed: wipe all clinical data, insert 50 patients.
  - 20 with appointments TODAY
  - 15 with appointments TOMORROW
  - 15 historical (past)
Patient IDs follow app logic: OP-DDmmmYY

Run inside container:
  docker cp seeds/seed_fresh.py hospital_api:/app/seed_fresh.py
  docker exec hospital_api python seed_fresh.py
"""
import random
from datetime import timedelta, datetime

from app.core.database import SessionLocal
from app.models.patient import Patient, Gender, BloodGroup, PatientFormType, PaymentMode
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription
from app.models.medicine_sale import MedicineSale
from app.models.medicine_return import MedicineReturn
from app.models.inpatient import Inpatient
from app.models.inpatient_activity import InpatientActivity
from app.models.inpatient_billing import InpatientBilling
from app.models.inpatient_diagnostic import InpatientDiagnostic
from app.models.inpatient_prescription import InpatientPrescription
from app.models.patient_history import PatientHistory
from app.models.user import User
from app.core.security import get_password_hash
from base import (TODAY, TOMORROW, NOW, FEMALE_FIRST, MALE_FIRST, LAST_NAMES,
                  rand_phone, rand_dob, rand_address, generate_patient_id, REASONS)

def generate_seed_patients(count: int):
    patients = []
    for idx in range(count):
        gender = random.choice([Gender.FEMALE, Gender.MALE])
        first = random.choice(FEMALE_FIRST if gender == Gender.FEMALE else MALE_FIRST)
        last = random.choice(LAST_NAMES)
        if idx < 20:
            appt = TODAY
        elif idx < 35:
            appt = TOMORROW
        else:
            appt = TODAY - timedelta(days=random.randint(3, 15))

        patients.append({
            "first": first,
            "last": last,
            "appt": appt,
            "reason": random.choice(REASONS),
            "form": random.choice(list(PatientFormType)),
            "gender": gender,
        })
    return patients

PATIENTS = generate_seed_patients(50)

db = SessionLocal()
try:
    # ── Wipe (FK-safe order) ──────────────────────────────────────────────────
    print("Clearing existing data...")
    d_inp_act = db.query(InpatientActivity).delete()
    d_inp_diag = db.query(InpatientDiagnostic).delete()
    d_inp_rx = db.query(InpatientPrescription).delete()
    d_inp_bill = db.query(InpatientBilling).delete()
    d_returns = db.query(MedicineReturn).delete()
    d_ms = db.query(MedicineSale).delete()
    d_rx = db.query(Prescription).delete()
    d_ap = db.query(Appointment).delete()
    d_history = db.query(PatientHistory).delete()
    d_ip = db.query(Inpatient).delete()
    d_pt = db.query(Patient).delete()
    db.commit()
    print(
        f"  Removed: {d_ms} sales | {d_rx} prescriptions | {d_ap} appointments | "
        f"{d_history} histories | {d_ip} inpatients | {d_pt} patients"
    )

    # ── Ensure nurse1 user ────────────────────────────────────────────────────
    if not db.query(User).filter(User.username == "nurse1").first():
        db.add(User(username="nurse1", email="nurse1@hospital.local",
                    hashed_password=get_password_hash("nurse123"),
                    full_name="Nurse Kavitha", role="staff",
                    phone_number="9848011111", is_active=True,
                    created_at=NOW, updated_at=NOW))
        db.commit()
        print("  ✅ nurse1 created")
    else:
        print("  ℹ️  nurse1 exists — skipped")

    # ── Insert patients ───────────────────────────────────────────────────────
    print(f"\nToday: {TODAY}  |  Tomorrow: {TOMORROW}\n")
    token_today = 0

    for idx, p in enumerate(PATIENTS, start=1):
        phone  = rand_phone()
        pid    = generate_patient_id(db, phone)
        hour   = 9 + (idx % 8)
        appt_dt = datetime.combine(p["appt"], datetime.min.time().replace(hour=hour, minute=0))

        due_date = (TODAY + timedelta(days=random.randint(20, 45))
                    if p["form"] == PatientFormType.MATERNITY else None)

        if p["appt"] == TODAY:
            token_today += 1
            token_num = token_today
            status = AppointmentStatus.CONFIRMED
        elif p["appt"] > TODAY:
            token_num = idx
            status = AppointmentStatus.SCHEDULED
        else:
            token_num = idx
            status = AppointmentStatus.COMPLETED

        patient = Patient(
            patient_id=pid,
            first_name=p["first"], last_name=p["last"],
            date_of_birth=rand_dob(),
            gender=p["gender"],
            blood_group=random.choice(list(BloodGroup)),
            phone=phone, address=rand_address(),
            patient_form_type=p["form"],
            appointment_date=p["appt"],
            due_date=due_date,
            next_visit_date=(p["appt"] + timedelta(days=7) if p["appt"] >= TODAY else None),
            payment_mode=random.choice([PaymentMode.CASH, PaymentMode.UPI]),
            amount=random.choice([200, 300, 500, 800]),
            medical_history=random.choice([None, "Hypertension", "Diabetes", "Thyroid"]),
            allergies=random.choice([None, None, "Penicillin"]),
            created_at=NOW, updated_at=NOW,
        )
        db.add(patient)
        db.flush()

        db.add(Appointment(
            appointment_number=f"APT-{idx:04d}",
            token_number=token_num, token_date=appt_dt,
            patient_id=patient.id, patient_str_id=pid,
            doctor_id=None, appointment_date=appt_dt,
            duration_minutes=30, status=status,
            reason=p["reason"], is_new_patient=1,
            created_at=NOW, updated_at=NOW,
        ))

        tag = "TODAY   " if p["appt"] == TODAY else ("TOMORROW" if p["appt"] == TOMORROW else "PAST    ")
        print(f"  [{tag}] {pid}  {p['first']:18s} {p['last']:10s}  {p['reason']}")

    db.commit()

    total   = db.query(Patient).count()
    today_c = db.query(Appointment).filter(
        Appointment.appointment_date >= datetime.combine(TODAY, datetime.min.time()),
        Appointment.appointment_date <  datetime.combine(TOMORROW, datetime.min.time()),
    ).count()
    tom_c = db.query(Appointment).filter(
        Appointment.appointment_date >= datetime.combine(TOMORROW, datetime.min.time()),
        Appointment.appointment_date <  datetime.combine(TOMORROW + timedelta(days=1), datetime.min.time()),
    ).count()
    print(f"\n✅ Done — {total} patients | {today_c} today | {tom_c} tomorrow")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    raise
finally:
    db.close()
