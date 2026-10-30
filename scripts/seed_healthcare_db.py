import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import datetime
import random

def create_and_seed_healthcare_db():
    print("Connecting to PostgreSQL on port 5432...")
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        dbname="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'optum_healthcare_db'")
    if cursor.fetchone():
        cursor.execute("DROP DATABASE optum_healthcare_db")
        print("Existing optum_healthcare_db dropped.")

    cursor.execute("CREATE DATABASE optum_healthcare_db")
    print("Database 'optum_healthcare_db' created successfully.")
    cursor.close()
    conn.close()

    # Connect to optum_healthcare_db
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        dbname="optum_healthcare_db"
    )
    cur = conn.cursor()

    # DDL
    ddl = """
    CREATE TABLE patients (
        patient_id VARCHAR(20) PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        dob DATE NOT NULL,
        gender VARCHAR(10) NOT NULL,
        insurance_policy_number VARCHAR(30) UNIQUE,
        state VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE providers (
        provider_id VARCHAR(20) PRIMARY KEY,
        provider_name VARCHAR(100) NOT NULL,
        specialty VARCHAR(50) NOT NULL,
        facility_name VARCHAR(100) NOT NULL,
        npi_number VARCHAR(20) UNIQUE NOT NULL,
        hourly_rate NUMERIC(10, 2) NOT NULL
    );

    CREATE TABLE appointments (
        appointment_id VARCHAR(20) PRIMARY KEY,
        patient_id VARCHAR(20) REFERENCES patients(patient_id) ON DELETE CASCADE,
        provider_id VARCHAR(20) REFERENCES providers(provider_id) ON DELETE CASCADE,
        appointment_date TIMESTAMP NOT NULL,
        status VARCHAR(20) NOT NULL, -- COMPLETED, CANCELLED, SCHEDULED, NO_SHOW
        copay_amount NUMERIC(8, 2) DEFAULT 25.00
    );

    CREATE TABLE claims (
        claim_id VARCHAR(20) PRIMARY KEY,
        patient_id VARCHAR(20) REFERENCES patients(patient_id) ON DELETE SET NULL,
        provider_id VARCHAR(20) REFERENCES providers(provider_id) ON DELETE SET NULL,
        diagnosis_code VARCHAR(20) NOT NULL, -- ICD-10
        procedure_code VARCHAR(20) NOT NULL, -- CPT
        billed_amount NUMERIC(12, 2) NOT NULL,
        approved_amount NUMERIC(12, 2) DEFAULT 0.00,
        claim_status VARCHAR(20) NOT NULL, -- PAID, DENIED, IN_REVIEW, PENDING
        submission_date DATE NOT NULL,
        adjudication_date DATE
    );

    CREATE TABLE prescriptions (
        prescription_id VARCHAR(20) PRIMARY KEY,
        patient_id VARCHAR(20) REFERENCES patients(patient_id),
        provider_id VARCHAR(20) REFERENCES providers(provider_id),
        medication_name VARCHAR(100) NOT NULL,
        dosage VARCHAR(50) NOT NULL,
        refills_remaining INT DEFAULT 0,
        prescribed_date DATE NOT NULL
    );

    CREATE TABLE claim_audit_logs (
        log_id SERIAL PRIMARY KEY,
        claim_id VARCHAR(20) REFERENCES claims(claim_id) ON DELETE CASCADE,
        action VARCHAR(50) NOT NULL,
        changed_by VARCHAR(50) NOT NULL,
        old_status VARCHAR(20),
        new_status VARCHAR(20),
        action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cur.execute(ddl)
    print("Tables created: patients, providers, appointments, claims, prescriptions, claim_audit_logs.")

    # Seed Providers
    providers = [
        ("PRV-001", "Dr. Rajesh Sharma", "Cardiology", "Optum Heart & Vascular", "NPI10928374", 280.00),
        ("PRV-002", "Dr. Priya Patel", "Oncology", "Apollo Specialty Center", "NPI28374619", 350.00),
        ("PRV-003", "Dr. Michael Chen", "Orthopedics", "Metro Bone & Joint", "NPI39485721", 240.00),
        ("PRV-004", "Dr. Sarah Jenkins", "Pediatrics", "Childrens Wellness Clinic", "NPI48572019", 190.00),
        ("PRV-005", "Dr. Amit Verma", "Family Medicine", "Optum Community Health", "NPI59683021", 160.00),
        ("PRV-006", "Dr. Emily Davis", "Neurology", "Advanced Neuro Institute", "NPI60719284", 320.00),
        ("PRV-007", "Dr. Vikram Malhotra", "Radiology", "Insight Diagnostic Imaging", "NPI71829304", 260.00),
        ("PRV-008", "Dr. Lisa Wong", "Dermatology", "Clear Skin Dermatology", "NPI82930415", 210.00),
        ("PRV-009", "Dr. Sunita Rao", "Endocrinology", "Metabolic Health Associates", "NPI93041526", 230.00),
        ("PRV-010", "Dr. David Miller", "General Surgery", "Surgical Specialists", "NPI04152637", 380.00),
    ]
    cur.executemany("INSERT INTO providers VALUES (%s, %s, %s, %s, %s, %s)", providers)

    # Seed Patients (30 patients)
    first_names = ["Aarav", "Ananya", "Rohan", "Sneha", "Karan", "Pooja", "Vikram", "Neha", "Rahul", "Deepika", 
                   "John", "Mary", "Robert", "Jennifer", "David", "Jessica", "James", "Sarah", "William", "Elizabeth"]
    last_names = ["Kumar", "Sharma", "Singh", "Patel", "Gupta", "Verma", "Reddy", "Mehta", "Smith", "Johnson", "Williams", "Brown", "Jones"]
    states = ["NY", "CA", "TX", "FL", "IL", "NJ", "PA", "OH", "GA", "NC"]
    
    patients = []
    for i in range(1, 36):
        pid = f"PAT-{i:03d}"
        fn = first_names[(i - 1) % len(first_names)]
        ln = last_names[(i * 3) % len(last_names)]
        year = random.randint(1955, 2010)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        dob = datetime.date(year, month, day)
        gender = "M" if i % 2 == 0 else "F"
        policy = f"POL-{100000 + i * 432}"
        state = states[i % len(states)]
        patients.append((pid, fn, ln, dob, gender, policy, state))
    cur.executemany("INSERT INTO patients (patient_id, first_name, last_name, dob, gender, insurance_policy_number, state) VALUES (%s, %s, %s, %s, %s, %s, %s)", patients)

    # Seed Appointments (60)
    statuses = ["COMPLETED", "COMPLETED", "COMPLETED", "CANCELLED", "SCHEDULED", "NO_SHOW"]
    appointments = []
    base_date = datetime.date(2026, 1, 1)
    for i in range(1, 61):
        aid = f"APT-{i:03d}"
        pid = f"PAT-{(i % 35) + 1:03d}"
        prv_id = providers[i % len(providers)][0]
        days_offset = random.randint(0, 300)
        app_date = datetime.datetime(2026, 1, 1, 9, 0) + datetime.timedelta(days=days_offset, hours=random.randint(0, 7))
        status = statuses[i % len(statuses)]
        copay = 25.00 if status != "CANCELLED" else 0.00
        appointments.append((aid, pid, prv_id, app_date, status, copay))
    cur.executemany("INSERT INTO appointments VALUES (%s, %s, %s, %s, %s, %s)", appointments)

    # Seed Claims (80 claims)
    diagnoses = ["E11.9", "I10", "M54.5", "J06.9", "Z00.00", "C50.9", "K21.9", "F41.1"]
    procedures = ["99213", "99214", "99215", "71045", "80053", "93000", "99395", "45378"]
    claim_statuses = ["PAID", "PAID", "PAID", "DENIED", "IN_REVIEW", "PENDING"]

    claims = []
    for i in range(1, 81):
        cid = f"CLM-{i:03d}"
        pid = f"PAT-{(i % 35) + 1:03d}"
        prv_id = providers[(i * 3) % len(providers)][0]
        diag = diagnoses[i % len(diagnoses)]
        proc = procedures[(i * 2) % len(procedures)]
        
        billed = round(random.uniform(150.0, 8500.0), 2)
        status = claim_statuses[i % len(claim_statuses)]
        
        sub_date = base_date + datetime.timedelta(days=random.randint(5, 280))
        if status == "PAID":
            approved = round(billed * random.uniform(0.70, 0.95), 2)
            adj_date = sub_date + datetime.timedelta(days=random.randint(7, 21))
        elif status == "DENIED":
            approved = 0.00
            adj_date = sub_date + datetime.timedelta(days=random.randint(5, 14))
        else: # PENDING or IN_REVIEW
            approved = 0.00
            adj_date = None
            
        claims.append((cid, pid, prv_id, diag, proc, billed, approved, status, sub_date, adj_date))

    # Add duplicate claim pattern for testing SQL duplicate checks
    claims.append(("CLM-081-DUP", "PAT-005", "PRV-001", "E11.9", "99214", 450.00, 0.00, "DENIED", base_date + datetime.timedelta(days=20), base_date + datetime.timedelta(days=25)))
    claims.append(("CLM-082-DUP", "PAT-005", "PRV-001", "E11.9", "99214", 450.00, 0.00, "DENIED", base_date + datetime.timedelta(days=20), base_date + datetime.timedelta(days=26)))

    cur.executemany("INSERT INTO claims VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", claims)

    # Seed Prescriptions (40)
    medications = [
        ("Metformin", "500mg"), ("Lisinopril", "10mg"), ("Atorvastatin", "20mg"),
        ("Levothyroxine", "50mcg"), ("Amlodipine", "5mg"), ("Metoprolol", "25mg"),
        ("Omeprazole", "40mg"), ("Losartan", "50mg"), ("Albuterol", "90mcg")
    ]
    prescriptions = []
    for i in range(1, 41):
        prid = f"RX-{i:03d}"
        pid = f"PAT-{(i % 35) + 1:03d}"
        prvid = providers[i % len(providers)][0]
        med, dose = medications[i % len(medications)]
        refills = random.randint(0, 5)
        pdate = base_date + datetime.timedelta(days=random.randint(10, 260))
        prescriptions.append((prid, pid, prvid, med, dose, refills, pdate))
    cur.executemany("INSERT INTO prescriptions VALUES (%s, %s, %s, %s, %s, %s, %s)", prescriptions)

    # Seed Audit Logs (50)
    audit_logs = []
    actions = ["STATUS_CHANGE", "ADJUDICATION", "PAYMENT_PROCESSED", "CLAIM_DENIAL"]
    for i in range(1, 51):
        cid = f"CLM-{(i % 80) + 1:03d}"
        act = actions[i % len(actions)]
        user = f"adjudicator_{i % 5 + 1}@optum.com"
        old_s = "PENDING" if i % 2 == 0 else "IN_REVIEW"
        new_s = "PAID" if i % 3 == 0 else "DENIED"
        ts = datetime.datetime(2026, 2, 1, 10, 0) + datetime.timedelta(days=i * 5)
        audit_logs.append((cid, act, user, old_s, new_s, ts))
    cur.executemany("INSERT INTO claim_audit_logs (claim_id, action, changed_by, old_status, new_status, action_timestamp) VALUES (%s, %s, %s, %s, %s, %s)", audit_logs)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ optum_healthcare_db created and seeded with realistic Optum healthcare data!")

if __name__ == "__main__":
    create_and_seed_healthcare_db()

