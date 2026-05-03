# Hospital Management System — User Guide

> **Version**: 1.0 | **Generated from**: Codebase analysis (May 2026)
> **Base URL**: `http://<host>:8000` | **API Docs**: `/api/docs`

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Login & Authentication](#2-login--authentication)
3. [Staff Dashboard — OP Patient Registration](#3-staff-dashboard--op-patient-registration)
4. [Doctor Dashboard — Consultations & Prescriptions](#4-doctor-dashboard--consultations--prescriptions)
5. [Doctor Dashboard — Inpatient Admission](#5-doctor-dashboard--inpatient-admission)
6. [Inpatient Management](#6-inpatient-management)
7. [Medical Desk — Pharmacy & Dispensing](#7-medical-desk--pharmacy--dispensing)
8. [Medical Desk — Returns & Due Tracking](#8-medical-desk--returns--due-tracking)
9. [Admin Dashboard — Finance & Audit](#9-admin-dashboard--finance--audit)
10. [Audit Trail & Compliance](#10-audit-trail--compliance)

---

## 1. System Overview

The Hospital Management System (HMS) is a web-based application built with **FastAPI** (backend) and vanilla **JavaScript** (frontend). It supports the following user roles:

| Role | Dashboard | Key Capabilities |
|------|-----------|-----------------|
| **admin** | Admin Dashboard | User management, financial audit, expense tracking, overall summary |
| **doctor** | Doctor Dashboard | Patient lookup, consultations, OP prescriptions, IP admission, IP management |
| **staff** | Staff Dashboard | OP patient registration, token generation, appointment booking |
| **medical_desk** | Medical Desk | Medicine inventory, sales, prescription dispensing, returns, due tracking |

### Application Architecture
- **Backend**: FastAPI + SQLAlchemy ORM + PostgreSQL
- **Frontend**: HTML/CSS/JS (Poppins font, FontAwesome icons)
- **Auth**: JWT Bearer tokens (OAuth2 password flow)
- **Deployment**: Docker container on AWS EC2, CI/CD via GitHub Actions

---

## 2. Login & Authentication

### Flow
1. Navigate to `http://<host>:8000/` → Login page loads.
2. Enter **Username** and **Password**.
3. Click **Login**.
4. System authenticates via `POST /api/v1/auth/login` (OAuth2 form-urlencoded).
5. On success: JWT token stored in `localStorage`, user redirected to role-specific dashboard.
6. On failure: Error message "Incorrect username or password".

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/auth/login` | Get JWT access token |
| GET | `/api/v1/auth/me` | Get current user info |

### Security Notes
- All API endpoints require `Authorization: Bearer <token>` header.
- Inactive users are blocked at login and middleware level.
- Tokens contain username in `sub` claim.

---

## 3. Staff Dashboard — OP Patient Registration

### Flow: Register New Outpatient
1. Staff logs in → **Staff Dashboard** loads.
2. Click **"Register Patient"** or **"+ New Patient"**.
3. Select **Form Type**: General, Maternity, or Other.
4. Fill in patient details:
   - **Required**: First name, last name, gender, phone number
   - **Optional**: DOB/Age, blood group, address, email, emergency contact, Aadhar ID, guardian
   - **Maternity-specific**: Due date, obstetric history, in-laws address
   - **Vitals**: Weight, height, BP, temperature, pulse, SpO2
   - **Payment**: Cash/UPI, amount
5. Click **Submit** → `POST /api/v1/patients/`
6. System generates **OP ID** in format `OP-DDmmmYY` (day + last 3 digits of phone + year).
   - Example: Phone 9876543745, registered on 03-May-2026 → `OP-0374526`
7. Patient record created, confirmation shown with OP ID.

### Flow: Search & Update Patient
1. Use search bar (by OP ID, name, or phone).
2. Click patient row → detail panel opens.
3. Edit any field → Click **Update** → `PUT /api/v1/patients/{id}`
4. System automatically saves a **full snapshot** in `patient_history` before updating (audit trail).
5. View edit history via **History** button → `GET /api/v1/patients/{id}/history`

### Flow: Generate Token / Appointment
1. Select patient → Click **"Generate Token"**.
2. System creates appointment with daily sequential token number.
3. Token displayed for patient.

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/patients/` | Register new patient |
| GET | `/api/v1/patients/` | List all patients |
| GET | `/api/v1/patients/{id}` | Get patient by DB ID |
| GET | `/api/v1/patients/search/{patient_number}` | Search by OP ID |
| PUT | `/api/v1/patients/{id}` | Update patient (creates history snapshot) |
| DELETE | `/api/v1/patients/{id}` | Delete patient (admin only) |
| GET | `/api/v1/patients/{id}/history` | Get edit history |

---

## 4. Doctor Dashboard — Consultations & Prescriptions

### Flow: View Today's Patients
1. Doctor logs in → **Doctor Dashboard** loads.
2. **Patients tab** shows all registered patients (searchable).
3. **Appointments tab** shows today's tokens/appointments.

### Flow: Create OP Prescription
1. Navigate to **Prescriptions** tab.
2. Click **"+ New Prescription"**.
3. Select patient (by OP ID or search).
4. Enter:
   - **Diagnosis** (free text)
   - **Medicines**: Select from inventory dropdown (shows stock level + price), add dosage, frequency, duration, instructions.
   - **Notes** / **Follow-up date**
5. Click **Save** → `POST /api/v1/prescriptions/`
6. Prescription ID generated: `RX-NNNN`.
7. Prescription reflects in **Medical Desk** for dispensing.
8. **Print** button generates A4 layout with patient details + vitals + medicines.

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/prescriptions/` | Create prescription |
| GET | `/api/v1/prescriptions/` | List all prescriptions |
| GET | `/api/v1/prescriptions/patient/{patient_id}` | Prescriptions for a patient |
| GET | `/api/v1/prescriptions/{rx_id}` | Get single prescription |
| PUT | `/api/v1/prescriptions/{rx_id}` | Update prescription |
| DELETE | `/api/v1/prescriptions/{rx_id}` | Delete prescription |

---

## 5. Doctor Dashboard — Inpatient Admission

### Flow: Admit Patient (OP → IP)
1. From Doctor Dashboard, navigate to **Inpatients** tab.
2. Click **"+ Admit Patient"**.
3. Select existing OP patient (by OP ID).
4. Fill admission details:
   - **Admission date**, **Ward** (General / Maternity / ICU / Private / Semi-Private)
   - **Room & bed number**, **Attending doctor**
   - **Admission diagnosis**, **Observations**
   - **Surgery details** (if applicable): procedure, date, anaesthesia type
5. Click **Admit** → `POST /api/v1/inpatients/`
6. System derives **IP ID** from OP ID: `OP-0374526` → `IP-0374526`.
7. IP record created, patient now appears in inpatient list.
8. Click **Manage** to open **Inpatient Management** page.

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/inpatients/` | Create admission |
| GET | `/api/v1/inpatients/` | List all inpatients |
| GET | `/api/v1/inpatients/by-patient/{patient_id}` | IP records for OP patient |
| GET | `/api/v1/inpatients/{id}` | Get single IP record |
| PUT | `/api/v1/inpatients/{id}` | Update IP record (discharge, transfer) |
| DELETE | `/api/v1/inpatients/{id}` | Delete IP record |

---

## 6. Inpatient Management

The Inpatient Management page (`/inpatient-management?ip=IP-XXX&pid=OP-XXX`) has **4 tabs**:

### 6.1 Medicine Tab — IP Prescriptions
1. Click **"+ Add Prescription"**.
2. Select medicines from **inventory-backed dropdown** (shows stock + price).
3. Add dosage, frequency, duration, instructions per medicine.
4. Enter diagnosis and notes.
5. Click **Save** → `POST /api/v1/ip/prescriptions/`
6. Prescription appears in list with `IP-RX-NNNN` ID.
7. This prescription is also visible in **Medical Desk** for dispensing.

### 6.2 Diagnostics Tab
1. Click **"+ Order Diagnostic"**.
2. Select test type (Lab / Scan / X-Ray / Blood / ECG / Other).
3. Enter test name and notes.
4. Click **Save** → `POST /api/v1/ip-diagnostics/`
5. Status lifecycle: **Pending** → **In Progress** → **Completed** (auto-sets completed_by and completed_at).
6. Results and report text can be updated.

### 6.3 Activities Tab
1. Click **"+ Order Activity"**.
2. Select type (BP Check / Sugar Check / Injection / Physiotherapy / Nursing Care / Dressing / Walking / Diet / Other).
3. Enter activity name, schedule time, instructions.
4. Click **Save** → `POST /api/v1/ip-activities/`
5. Nurses mark as **Completed** or **Skipped** with completion notes.

### 6.4 Billing Tab
1. Displays all billing line-items for this inpatient.
2. **Categories**: Room Charge, Doctor Visit, Medicine, Surgery, Lab, Nursing, Other.
3. Medicine billing items are **auto-created** when Medical Desk dispenses IP prescriptions.
4. Manual billing items can be added via **"+ Add Item"**.
5. **Summary** shows per-category totals and grand total.
6. Billing items from medicine returns are automatically adjusted.

### API Endpoints (Inpatient Management)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/ip/prescriptions/` | Create IP prescription |
| GET | `/api/v1/ip/prescriptions/by-inpatient/{ip_id}` | List prescriptions for IP |
| GET | `/api/v1/ip/prescriptions/all` | All IP prescriptions (Medical Desk view) |
| POST | `/api/v1/ip/medicine-issues/` | Record medicine issue/dispensing |
| POST | `/api/v1/ip-diagnostics/` | Order diagnostic test |
| GET | `/api/v1/ip-diagnostics/by-inpatient/{ip_id}` | List diagnostics for IP |
| POST | `/api/v1/ip-activities/` | Create nursing activity |
| GET | `/api/v1/ip-activities/by-inpatient/{ip_id}` | List activities for IP |
| POST | `/api/v1/ip-billing/` | Add billing item |
| GET | `/api/v1/ip-billing/by-inpatient/{ip_id}` | List billing items |
| GET | `/api/v1/ip-billing/summary/{ip_id}` | Billing summary |

---

## 7. Medical Desk — Pharmacy & Dispensing

### 7.1 Medicine Inventory Management
1. Medical Desk user logs in → **Medical Desk Dashboard** loads.
2. **Medicines** tab shows full inventory with stock levels, expiry, prices.
3. **Add Medicine**: Name, category, manufacturer, batch, unit, stock qty, price, expiry, low-stock threshold.
4. **Edit/Delete** existing medicines.
5. **Alerts**: Low-stock (amber) and out-of-stock (red) badges.
6. **Expiry tracking**: `GET /api/v1/medicines/expiring?days=30`

### 7.2 Direct Medicine Sale (Walk-in)
1. Navigate to **Sales** tab → Click **"+ Sell Medicine"**.
2. Search patient by OP ID.
3. Add medicines to cart (select from inventory, enter quantity).
4. System auto-calculates unit price × quantity.
5. Select payment mode (Cash / UPI).
6. Click **Confirm Sale** → `POST /api/v1/medicines/sell`
7. Stock deducted, sale recorded with `SALE-NNNN` ID, payment_status = `"paid"`.

### 7.3 Dispense from OP Prescription
1. Navigate to **OP Prescriptions** tab.
2. View all doctor-created prescriptions (RX-NNNN).
3. Click **"Dispense"** on a prescription.
4. Modal shows prescribed medicines matched against inventory (auto-lookup by name).
5. Adjust quantities, select payment mode.
6. Click **Confirm** → creates sale records for each medicine.
7. Stock deducted, sales recorded.

### 7.4 Dispense from IP Prescription
1. Navigate to **IP Prescriptions** tab.
2. View all inpatient prescriptions (IP-RX-NNNN) with patient info.
3. Click **"Dispense"** on a prescription.
4. Modal shows medicines matched to inventory.
5. Adjust quantities → Click **Confirm**.
6. **Key difference from OP**: `inpatient_id` is passed to sell API:
   - `payment_status` = `"due"` (not paid upfront)
   - `due_amount` = total price
   - **Auto-creates billing item** in `inpatient_billing_items` with `sale_ref_id` linkage
7. Sale appears in Sales tab with **DUE** badge.

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/medicines/` | Add medicine to inventory |
| GET | `/api/v1/medicines/` | List all medicines |
| GET | `/api/v1/medicines/expiring` | Expiring medicines |
| GET | `/api/v1/medicines/low-stock` | Low-stock medicines |
| PUT | `/api/v1/medicines/{id}` | Update medicine |
| DELETE | `/api/v1/medicines/{id}` | Delete medicine |
| POST | `/api/v1/medicines/sell` | Sell/dispense medicine |
| GET | `/api/v1/medicines/sales` | List all sales |

---

## 8. Medical Desk — Returns & Due Tracking

### 8.1 Medicine Return Flow
1. Navigate to **Sales** tab.
2. Find the sale row → Click **"Return"** button (visible if returnable qty > 0).
3. **Return Modal** opens showing:
   - Original sale details (medicine, qty sold, qty already returned)
   - Maximum returnable quantity
4. Enter **quantity to return** and optional **reason**.
5. Click **Submit Return** → `POST /api/v1/medicine-returns/`
6. System performs **atomic transaction**:
   - Creates `MedicineReturn` record (RET-NNNN)
   - **Restores stock** in medicine inventory
   - **Recalculates sale total_price** = unit_price × (sold − returned)
   - Updates **payment_status** → `"partial_return"` or `"full_return"`
   - For IP sales: adjusts `InpatientBillingItem` (qty and total_price)
   - Writes **AuditLog** entry with old/new values
7. Sale row updates with return badge and recalculated price.

### 8.2 Anti-Fraud Validation
- Cannot return more than `quantity_sold - quantity_already_returned`
- Return quantity must be > 0
- Original sale must exist
- Medicine record must exist
- Full rollback on any failure

### 8.3 Due Tracking (Inpatient)
1. Navigate to **Dues** tab.
2. Shows all sales with `payment_status = "due"` or `"partial_return"`.
3. Click **"Clear Due"** → `POST /api/v1/medicine-returns/dues/clear/{sale_id}`
4. Status changes to `"cleared"`, `cleared_at` timestamp set, `due_amount` → 0.

### 8.4 Returns History
1. Navigate to **Returns** tab.
2. Shows all processed returns with details:
   - Return ID, sale ID, patient, medicine, qty, refund amount, reason, who returned, when.

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/medicine-returns/` | Process return |
| GET | `/api/v1/medicine-returns/` | List all returns |
| GET | `/api/v1/medicine-returns/dues` | List outstanding dues |
| POST | `/api/v1/medicine-returns/dues/clear/{sale_id}` | Clear a due |

---

## 9. Admin Dashboard — Finance & Audit

### 9.1 Expense Management
1. Admin logs in → **Admin Dashboard** / **Audit Dashboard**.
2. Navigate to **Expenses** section.
3. Add expense: category (Salary / Utilities / Rent / Supplies / Maintenance / Equipment / Insurance / Other), description, amount, paid_to, payment mode, date.
4. Filter by date range and category.

### 9.2 Financial Summaries
| Endpoint | Report |
|----------|--------|
| `GET /api/v1/finance/summary/hospital` | Patient income vs expenses, by payment mode, by expense category |
| `GET /api/v1/finance/summary/medical-desk` | Medicine sales revenue, top-selling medicines, by payment mode |
| `GET /api/v1/finance/summary/overall` | Combined: patient income + medicine income - expenses = net profit |

All summaries support **date range filtering** via `start_date` and `end_date` query parameters.

### 9.3 Audit Logs
- `GET /api/v1/audit/` — Full audit trail of all system actions.
- Each entry records: who, what action, which table, record ID, old values, new values, timestamp.

---

## 10. Audit Trail & Compliance

### Audit Mechanisms in the System

| Mechanism | Where | Purpose |
|-----------|-------|---------|
| **Patient History** | `patient_history` table | Full snapshot on every patient edit |
| **AuditLog** | `audit_logs` table | All RETURN transactions with old/new JSON values |
| **Sale Tracking** | `medicine_sales` | `sold_by`, `payment_status` lifecycle, `quantity_returned` |
| **Return Records** | `medicine_returns` | `returned_by`, `return_reason`, `created_at` |
| **Billing Linkage** | `inpatient_billing_items.sale_ref_id` | Traces billing items back to SALE-NNNN |
| **Timestamps** | All tables | `created_at`, `updated_at` on every record |

### Compliance Checklist
- [x] Patient data edit history (immutable snapshots)
- [x] Medicine return audit trail (who, when, how many, reason)
- [x] Anti-fraud: over-return prevention, atomic transactions, rollback on failure
- [x] Billing traceability: sale → billing item → return adjustment
- [x] Financial audit: income vs expense reports with date filtering
- [x] Role-based access: admin-only for expenses, delete operations
- [x] JWT authentication on all API endpoints
