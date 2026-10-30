"""
Enterprise Synthetic Financial Data Seeder
Generates 8,000+ realistic, production-grade transactions across 3 calendar years (2024-01-01 to 2026-10-31)
with 100% balanced double-entry general ledger journal entries.
"""

import sys
import random
import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from decimal import Decimal
from typing import List, Dict, Tuple
from sqlalchemy import text
from backend.database.connection import sync_engine, SyncSessionLocal
from backend.database.models import Base, Account, Vendor, Transaction, JournalEntry

# Account mappings
ACCOUNT_DEFINITIONS = [
    ("1010", "Operating Cash & Bank", "asset", "Primary liquid operating checking and UPI bank account"),
    ("2010", "Credit Card Liabilities", "liability", "Revolving household credit card lines"),
    ("5010", "Subscriptions & Software", "expense", "Digital streaming, fitness, and recurring services"),
    ("5020", "Transportation & Fleet", "expense", "Fuel, metro, ride-hailing, and mobility"),
    ("5030", "Entertainment & Events", "expense", "Cinema, concerts, gaming, and leisure"),
    ("5040", "Healthcare & Medical", "expense", "Pharmacy, diagnostics, consultations, and dental"),
    ("5050", "Utilities & Telecom", "expense", "Electricity, water, gas, broadband, and telecom"),
    ("5060", "Rent & Facilities", "expense", "Apartment rent, maintenance, and domestic staff"),
    ("5070", "Groceries & Ration", "expense", "Daily provisions, fresh produce, and supermarket"),
    ("5080", "Dining & Catering", "expense", "Restaurants, quick bites, cafes, and food delivery"),
]

CAT_TO_CODE = {
    "subscriptions": "5010",
    "transportation": "5020",
    "entertainment": "5030",
    "healthcare": "5040",
    "utilities": "5050",
    "rent": "5060",
    "groceries": "5070",
    "dining": "5080",
}

VENDOR_CATALOG: Dict[str, List[Tuple[str, str]]] = {
    "dining": [
        ("Swiggy Delivery", "UPI/SWIGGY-BLR/FoodOrder"),
        ("Zomato Online", "UPI/ZOMATO/DinnerDelivery"),
        ("Chai Point", "UPI/CHAIPOINT/EveningTea"),
        ("Starbucks Coffee", "POS STARBUCKS INDIRANAGAR"),
        ("Haldiram's Sweets", "HALDIRAM FOODS PVT LTD"),
        ("Bikanervala", "BIKANERVALA RESTAURANT"),
        ("Pizzeria Locale", "UPI/PIZZA-HUT/FamilyDinner"),
        ("McDonald's India", "HARDCASTLE RESTAURANTS/MCD"),
        ("Cafe Coffee Day", "CCD KORAMANGALA CAFE"),
        ("Blue Tokai Coffee", "BLUE TOKAI ROASTERS"),
    ],
    "groceries": [
        ("Blinkit Commerce", "UPI/BLINKIT/DailyEssentials"),
        ("Zepto Delivery", "ZEPTO 10MIN GROCERY"),
        ("Swiggy Instamart", "INSTAMART PROVISIONS"),
        ("BigBasket Supermarket", "BIGBASKET INNOVATIVE RETAIL"),
        ("D-Mart Supermarket", "AVENUE SUPERMARTS DMART"),
        ("Nature's Basket", "NATURES BASKET ORGANIC"),
        ("Local Kirana Store", "UPI/KIRANA/RiceAndDal"),
        ("MilkBasket Daily", "MILKBASKET DAIRY SUBSCRIPTION"),
        ("Reliance Smart Point", "RELIANCE RETAIL SMART"),
    ],
    "utilities": [
        ("BESCOM Electricity", "BESCOM ONLINE BILL PAYMENT"),
        ("Airtel Fiber Broadband", "AIRTEL BROADBAND TELECOM"),
        ("Indane LPG Gas", "IOCL INDANE GAS REFILL"),
        ("BWSSB Water Supply", "BWSSB WATER BILL BANGALORE"),
        ("Jio Postpaid Telecom", "RELIANCE JIO TELECOM BILL"),
        ("Tata Power Solar", "TATA POWER DISCOM RETAIL"),
    ],
    "transportation": [
        ("Uber India", "UBER TRIP HELP.UBER.COM"),
        ("Ola Cabs", "ANI TECHNOLOGIES OLA TRIP"),
        ("Rapido Bike Taxi", "RAPIDO ROAPPEN MOBILITY"),
        ("Shell Fuel Station", "SHELL MOBILITY FUEL PUMP"),
        ("HPCL Petrol Pump", "HINDUSTAN PETROLEUM DIESEL"),
        ("Namma Metro Transit", "BMRCL METRO SMART CARD RECHARGE"),
    ],
    "rent": [
        ("Apartment Maintenance", "PRESTIGE ENCLAVE RESIDENTS ASSOC"),
        ("Monthly Flat Rent", "NEFT/FLAT-RENT/OWNER-TRANSFER"),
        ("Urban Company Home Care", "URBAN COMPANY DEEP CLEAN"),
        ("Maid & Cook Salary", "UPI/DOMESTIC-HELP/MONTHLY-SALARY"),
        ("Society Security Fund", "RESIDENTIAL WELFARE CORP"),
    ],
    "subscriptions": [
        ("Netflix India", "NETFLIX ENTERTAINMENT SVOD"),
        ("Amazon Prime", "AMAZON PRIME ANNUAL MEMBERSHIP"),
        ("Spotify Premium", "SPOTIFY AB MUSIC SUBSCRIPTION"),
        ("YouTube Premium", "GOOGLE YOUTUBE MEMBERSHIP"),
        ("Cult.fit Fitness", "CULTFIT HEALTHCARE GYM PASS"),
        ("Disney+ Hotstar", "NOVI DIGITAL HOTSTAR VIP"),
        ("Google One Cloud", "GOOGLE CLOUD 2TB STORAGE"),
    ],
    "healthcare": [
        ("Apollo Pharmacy", "APOLLO HOSPITALS PHARMACY"),
        ("Tata 1mg Healthcare", "1MG TECHNOLOGIES MEDICINES"),
        ("Practo Telehealth", "PRACTO CONSULTATION CLINIC"),
        ("Dr. Lal PathLabs", "DR LAL PATHLABS DIAGNOSTICS"),
        ("Dental Clinic", "DENTAL CARE SMILE IMPLANTS"),
        ("Max Healthcare", "MAX SPECIALITY HOSPITALS"),
    ],
    "entertainment": [
        ("BookMyShow Cinema", "BIGTREE ENTERTAINMENT BMS"),
        ("PVR Inox Movies", "PVR INOX CINEMAS FORUM"),
        ("Timezone Arcade", "TIMEZONE ENTERTAINMENT ARCADE"),
        ("Steam Games", "VALVE STEAM DIGITAL PURCHASE"),
    ],
}


def seed_enterprise_data(target_transactions: int = 8500):
    print(f"Beginning Enterprise Financial Data Seeding ({target_transactions} target transactions)...")
    session = SyncSessionLocal()

    try:
        # Clear existing transactions and journal entries to eliminate the 16-month gap
        print("Clearing existing transaction records and journal entries...")
        session.execute(text("DELETE FROM journal_entries;"))
        session.execute(text("DELETE FROM transactions;"))
        session.execute(text("DELETE FROM vendors;"))
        session.commit()

        # Ensure Chart of Accounts exist
        existing_accounts = {a.code: a for a in session.query(Account).all()}
        for code, name, acc_type, desc in ACCOUNT_DEFINITIONS:
            if code not in existing_accounts:
                acc = Account(code=code, name=name, type=acc_type, description=desc)
                session.add(acc)
        session.commit()

        accounts_by_code = {a.code: a for a in session.query(Account).all()}
        cash_account = accounts_by_code["1010"]
        credit_account = accounts_by_code["2010"]

        # Pre-seed vendors
        print("Seeding Indian household vendor directory...")
        vendor_entities = {}
        for cat, v_list in VENDOR_CATALOG.items():
            for v_name, _ in v_list:
                if v_name not in vendor_entities:
                    v = Vendor(name=v_name, category=cat)
                    session.add(v)
                    vendor_entities[v_name] = v
        session.commit()

        # Reload vendors with IDs
        vendors_db = {v.name: v for v in session.query(Vendor).all()}
        print(f"Verified {len(vendors_db)} unique merchant vendors.")

        # Date parameters: 2024-01-01 to 2026-10-31 (approx 1,035 days)
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2026, 10, 31)
        total_days = (end_date - start_date).days

        random.seed(42)  # Deterministic repeatability

        tx_list = []
        current_date = start_date

        # Iterate day by day to model domestic cash flow cycles
        while current_date <= end_date:
            day_num = current_date.day
            month_num = current_date.month
            weekday = current_date.weekday()  # 5=Sat, 6=Sun
            is_weekend = weekday in (5, 6)
            is_diwali_season = (month_num in (10, 11))
            is_summer_vacation = (month_num in (5, 6))

            # Fixed Monthly Debits on 1st, 5th, and 10th of each month
            if day_num == 1:
                # Flat Rent
                tx_list.append({
                    "date": datetime.datetime.combine(current_date, datetime.time(9, 30)),
                    "description": "Monthly Flat Rent - Prestige Enclave",
                    "vendor_name": "Monthly Flat Rent",
                    "category": "rent",
                    "amount": round(Decimal(random.uniform(22000, 26000)), 2),
                    "payment_method": "Net Banking",
                    "is_reconciled": True,
                })
                # Apartment Maintenance
                tx_list.append({
                    "date": datetime.datetime.combine(current_date, datetime.time(11, 0)),
                    "description": "Apartment Society Maintenance & Water charges",
                    "vendor_name": "Apartment Maintenance",
                    "category": "rent",
                    "amount": round(Decimal(random.uniform(4200, 5200)), 2),
                    "payment_method": "UPI",
                    "is_reconciled": True,
                })
            elif day_num == 5:
                # Electricity bill
                tx_list.append({
                    "date": datetime.datetime.combine(current_date, datetime.time(14, 15)),
                    "description": "BESCOM Electricity Utility Bill",
                    "vendor_name": "BESCOM Electricity",
                    "category": "utilities",
                    "amount": round(Decimal(random.uniform(1800, 3400)), 2),
                    "payment_method": "UPI",
                    "is_reconciled": True,
                })
                # Domestic Staff Salary
                tx_list.append({
                    "date": datetime.datetime.combine(current_date, datetime.time(18, 0)),
                    "description": "Maid & Cook Monthly Salary",
                    "vendor_name": "Maid & Cook Salary",
                    "category": "rent",
                    "amount": Decimal("6500.00"),
                    "payment_method": "UPI",
                    "is_reconciled": True,
                })
            elif day_num == 10:
                # Broadband Fiber
                tx_list.append({
                    "date": datetime.datetime.combine(current_date, datetime.time(10, 45)),
                    "description": "Airtel Xstream Fiber 200Mbps Monthly Bill",
                    "vendor_name": "Airtel Fiber Broadband",
                    "category": "utilities",
                    "amount": Decimal("1179.00"),
                    "payment_method": "UPI",
                    "is_reconciled": True,
                })

            # Daily Micro-Transactions & Living Expenses (4 to 9 per day)
            daily_tx_count = random.randint(5, 10) if is_weekend else random.randint(3, 7)
            if is_diwali_season:
                daily_tx_count += random.randint(1, 3)

            for _ in range(daily_tx_count):
                roll = random.random()

                # Tier A: Micro-UPI spends (₹20 to ₹350) - 50%
                if roll < 0.50:
                    cat = random.choice(["dining", "groceries", "transportation"])
                    v_name, memo_template = random.choice(VENDOR_CATALOG[cat])
                    if cat == "dining":
                        amt = Decimal(str(random.randint(20, 250)))
                    elif cat == "transportation":
                        amt = Decimal(str(random.randint(40, 180)))
                    else:
                        amt = Decimal(str(random.randint(50, 350)))
                    pay_method = "UPI"

                # Tier B: Variable Weekly Outflows (₹350 to ₹3,000) - 30%
                elif roll < 0.80:
                    cat = random.choice(["groceries", "dining", "transportation", "entertainment"])
                    v_name, memo_template = random.choice(VENDOR_CATALOG[cat])
                    amt = Decimal(str(random.randint(400, 2800)))
                    pay_method = random.choice(["UPI", "UPI", "Credit Card", "Debit Card"])

                # Tier C / Subscriptions & Healthcare - 12%
                elif roll < 0.92:
                    cat = random.choice(["subscriptions", "healthcare", "utilities"])
                    v_name, memo_template = random.choice(VENDOR_CATALOG[cat])
                    if cat == "subscriptions":
                        amt = Decimal(str(random.choice([199, 499, 649, 999, 1499])))
                        pay_method = random.choice(["Credit Card", "UPI"])
                    elif cat == "healthcare":
                        amt = Decimal(str(random.randint(300, 3200)))
                        pay_method = random.choice(["UPI", "Credit Card"])
                    else:
                        amt = Decimal(str(random.randint(400, 1500)))
                        pay_method = "UPI"

                # Tier D: Festive Spikes & Gadgets / Shopping - 6%
                elif roll < 0.98:
                    cat = "entertainment" if not is_diwali_season else "dining"
                    v_name, memo_template = random.choice(VENDOR_CATALOG[cat])
                    multiplier = 2.0 if is_diwali_season else 1.0
                    amt = round(Decimal(random.randint(3500, 15000)) * Decimal(str(multiplier)), 2)
                    pay_method = "Credit Card"

                # Tier E: Rare Outliers / Big-Ticket (₹40,000 - ₹1,20,000) - 2%
                else:
                    cat = random.choice(["healthcare", "entertainment"])
                    v_name, memo_template = random.choice(VENDOR_CATALOG[cat])
                    amt = Decimal(str(random.randint(38000, 85000)))
                    pay_method = "Credit Card"

                # Time distribution throughout the day
                hour = random.randint(7, 23)
                minute = random.randint(0, 59)
                tx_time = datetime.datetime.combine(current_date, datetime.time(hour, minute))

                # Unreconciled backlog: recent months (Aug - Oct 2026) have ~15% unreconciled
                is_recent = (current_date >= datetime.date(2026, 8, 1))
                reconciled_prob = 0.85 if is_recent else 0.97
                is_reconciled = (random.random() < reconciled_prob)

                tx_list.append({
                    "date": tx_time,
                    "description": memo_template,
                    "vendor_name": v_name,
                    "category": cat,
                    "amount": amt,
                    "payment_method": pay_method,
                    "is_reconciled": is_reconciled,
                })

            current_date += datetime.timedelta(days=1)

        print(f"Generated {len(tx_list)} simulated transactions in memory. Committing in batches...")

        # Batch insert transactions and balanced journal entries
        batch_size = 1000
        total_created = 0

        for i in range(0, len(tx_list), batch_size):
            batch = tx_list[i : i + batch_size]
            for item in batch:
                v = vendors_db.get(item["vendor_name"])
                exp_acc = accounts_by_code[CAT_TO_CODE[item["category"]]]

                tx = Transaction(
                    date=item["date"],
                    description=item["description"],
                    vendor_id=v.id if v else None,
                    account_id=exp_acc.id,
                    total_amount=item["amount"],
                    payment_method=item["payment_method"],
                    category=item["category"],
                    is_reconciled=item["is_reconciled"],
                )
                session.add(tx)
                session.flush()  # Generates tx.id

                # Credit account: Credit Card account if CC, else Operating Cash
                credit_acc = credit_account if item["payment_method"] == "Credit Card" else cash_account

                # 1. Debit Entry: Expense Account
                debit_entry = JournalEntry(
                    transaction_id=tx.id,
                    account_id=exp_acc.id,
                    debit=item["amount"],
                    credit=Decimal("0.00"),
                    description=f"Debit: {item['category'].title()} Outflow",
                    entry_date=item["date"],
                )
                # 2. Credit Entry: Asset / Liability Account
                credit_entry = JournalEntry(
                    transaction_id=tx.id,
                    account_id=credit_acc.id,
                    debit=Decimal("0.00"),
                    credit=item["amount"],
                    description=f"Credit: {credit_acc.name}",
                    entry_date=item["date"],
                )
                session.add_all([debit_entry, credit_entry])

            session.commit()
            total_created += len(batch)
            print(f"  -> Committed {total_created} / {len(tx_list)} transactions with double-entry ledgers...")

        # Verify double entry balance
        res = session.execute(text("SELECT SUM(debit) AS total_dr, SUM(credit) AS total_cr FROM journal_entries;")).fetchone()
        diff = res.total_dr - res.total_cr
        print(f"\nSeeding complete!")
        print(f"Total Transactions: {total_created}")
        print(f"Total Journal Lines: {total_created * 2}")
        print(f"Total Ledger Debit: ₹{res.total_dr:,.2f} | Total Ledger Credit: ₹{res.total_cr:,.2f}")
        print(f"Double-Entry Discrepancy: ₹{diff:,.2f} (Must be exactly 0.00)")
        assert diff == 0, "Double-entry accounting equation violated!"

    finally:
        session.close()


if __name__ == "__main__":
    seed_enterprise_data(target_transactions=8500)
