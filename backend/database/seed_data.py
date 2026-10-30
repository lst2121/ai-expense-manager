import csv
import datetime
from decimal import Decimal
from pathlib import Path

from backend.database.connection import sync_engine, SyncSessionLocal
from backend.database.models import Base, Account, Vendor, Transaction, JournalEntry

ACCOUNT_MAPPING = {
    "subscriptions": ("5010", "Subscriptions & Software", "expense"),
    "transportation": ("5020", "Transportation & Fleet", "expense"),
    "entertainment": ("5030", "Entertainment & Events", "expense"),
    "healthcare": ("5040", "Healthcare & Medical", "expense"),
    "utilities": ("5050", "Utilities & Telecom", "expense"),
    "rent": ("5060", "Rent & Facilities", "expense"),
    "groceries": ("5070", "Groceries & Office Supplies", "expense"),
    "dining": ("5080", "Dining & Catering", "expense"),
}

VENDOR_MAPPING = {
    "Spotify": ("Spotify AB", "subscriptions"),
    "Adobe": ("Adobe Systems Inc.", "subscriptions"),
    "Medium": ("A Medium Corporation", "subscriptions"),
    "YouTube": ("Google YouTube Premium", "subscriptions"),
    "Netflix": ("Netflix Inc.", "subscriptions"),
    "VPN": ("Nord Security", "subscriptions"),
    "Costco": ("Costco Wholesale", "groceries"),
    "Walmart": ("Walmart Stores", "groceries"),
    "Trader Joes": ("Trader Joe's", "groceries"),
    "Trader Joe's": ("Trader Joe's", "groceries"),
    "Local Market": ("City Local Market", "groceries"),
    "Uber": ("Uber Technologies", "transportation"),
    "Fuel": ("Shell Mobility / Fuel", "transportation"),
    "Metro pass": ("Metropolitan Transit Authority", "transportation"),
    "Bus pass": ("City Transit Authority", "transportation"),
    "Electricity bill": ("Consolidated Edison Power", "utilities"),
    "Water bill": ("Municipal Water Dept", "utilities"),
    "Gas bill": ("National Gas Corp", "utilities"),
    "Internet": ("Apex Fiber Broadband", "utilities"),
    "Advance rent": ("Prime Commercial Realty", "rent"),
    "Partial rent": ("Prime Commercial Realty", "rent"),
    "Monthly rent": ("Prime Commercial Realty", "rent"),
    "Blood test": ("Quest Diagnostics Labs", "healthcare"),
    "Dental checkup": ("Gentle Dental Care", "healthcare"),
    "Eye test": ("Vision World Optometry", "healthcare"),
    "Pharmacy": ("CVS Health Pharmacy", "healthcare"),
    "Concert": ("LiveNation Concerts", "entertainment"),
    "Movie night": ("AMC Theatres", "entertainment"),
    "Board game": ("Hasbro Gaming Store", "entertainment"),
    "Arcade": ("Dave & Buster's", "entertainment"),
    "Lunch out": ("Bistro Downtown", "dining"),
    "Coffee": ("Blue Bottle Coffee", "dining"),
    "Dinner with friends": ("Artisan Trattoria", "dining"),
    "Fast food": ("Chipotle Mexican Grill", "dining"),
    "Pizza": ("Pizzeria Locale", "dining"),
}

PAYMENT_METHODS = ["Corporate Credit Card", "ACH Direct Debit", "Wire Transfer", "Virtual Card"]


def create_schema_and_seed(csv_path: str = "data/sample_expense.csv"):
    print("Creating all tables in PostgreSQL...")
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
    print("Tables created successfully.")

    session = SyncSessionLocal()
    try:
        # 1. Create Core Default Accounts
        bank_account = Account(
            code="1010",
            name="Operating Cash & Bank",
            type="asset",
            description="Primary liquid operating checking and bank account"
        )
        cc_account = Account(
            code="2010",
            name="Corporate Credit Card Liabilities",
            type="liability",
            description="Corporate revolving expense lines"
        )
        session.add_all([bank_account, cc_account])

        # Create Category Accounts
        expense_accounts = {}
        for cat_key, (code, name, acc_type) in ACCOUNT_MAPPING.items():
            acc = Account(
                code=code,
                name=name,
                type=acc_type,
                description=f"Ledger account for {name}"
            )
            session.add(acc)
            expense_accounts[cat_key] = acc

        session.commit()
        print(f"Created {len(expense_accounts) + 2} Chart of Accounts entries.")

        # 2. Pre-create Vendors
        vendors = {}
        for raw_note, (v_name, v_cat) in VENDOR_MAPPING.items():
            if v_name not in vendors:
                v = Vendor(name=v_name, category=v_cat)
                session.add(v)
                vendors[v_name] = v

        session.commit()
        print(f"Created {len(vendors)} vendor records.")

        # 3. Read CSV and insert Transactions + Journal Entries
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found at {csv_path}")

        transactions_added = 0
        journal_entries_added = 0
        total_seeded_volume = Decimal("0.00")

        with open(csv_file, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                raw_date = row.get("Date", "").strip()
                raw_category = row.get("Category", "").strip().lower()
                raw_amount = row.get("Amount", "0").strip()
                raw_note = row.get("Notes", "").strip()

                try:
                    tx_date = datetime.datetime.strptime(raw_date, "%Y-%m-%d")
                except ValueError:
                    tx_date = datetime.datetime.utcnow()

                amount = Decimal(raw_amount)
                total_seeded_volume += amount

                # Vendor resolution
                vendor_info = VENDOR_MAPPING.get(raw_note)
                if vendor_info:
                    vendor_obj = vendors.get(vendor_info[0])
                else:
                    v_name = raw_note if raw_note else f"Vendor-{raw_category.title()}"
                    if v_name not in vendors:
                        vendor_obj = Vendor(name=v_name, category=raw_category)
                        session.add(vendor_obj)
                        session.flush()
                        vendors[v_name] = vendor_obj
                    else:
                        vendor_obj = vendors[v_name]

                # Account resolution
                expense_account = expense_accounts.get(raw_category)
                if not expense_account:
                    # Fallback general expense account
                    expense_account = expense_accounts["subscriptions"]

                # Payment method & status
                payment_method = PAYMENT_METHODS[idx % len(PAYMENT_METHODS)]
                is_reconciled = (idx % 3 != 0)  # ~67% reconciled

                tx = Transaction(
                    date=tx_date,
                    description=f"{raw_note} - {expense_account.name}",
                    vendor_id=vendor_obj.id if vendor_obj else None,
                    account_id=expense_account.id,
                    total_amount=amount,
                    payment_method=payment_method,
                    category=raw_category,
                    is_reconciled=is_reconciled,
                    notes=raw_note,
                )
                session.add(tx)
                session.flush()

                # Double-entry lines:
                # 1. Debit Expense Account
                debit_line = JournalEntry(
                    transaction_id=tx.id,
                    account_id=expense_account.id,
                    debit=amount,
                    credit=Decimal("0.00"),
                    description=f"Debit: {tx.description}",
                    entry_date=tx_date,
                )
                # 2. Credit Bank / Cash Account
                credit_line = JournalEntry(
                    transaction_id=tx.id,
                    account_id=bank_account.id,
                    debit=Decimal("0.00"),
                    credit=amount,
                    description=f"Credit Cash/Bank: {tx.description}",
                    entry_date=tx_date,
                )

                session.add_all([debit_line, credit_line])
                transactions_added += 1
                journal_entries_added += 2

        session.commit()
        print(f"Successfully seeded {transactions_added} transactions and {journal_entries_added} journal entries.")
        print(f"Total expense volume seeded: ${total_seeded_volume:,.2f}")

        # Verification check
        with sync_engine.connect() as conn:
            from sqlalchemy import text
            balance_check = conn.execute(text(
                "SELECT SUM(debit) as total_debit, SUM(credit) as total_credit FROM journal_entries;"
            )).fetchone()
            print(f"Ledger Balance Verification -> Total Debits: ${balance_check[0]:,.2f} | Total Credits: ${balance_check[1]:,.2f}")
            assert balance_check[0] == balance_check[1], "CRITICAL ERROR: Debits and Credits do not balance!"
            print("Ledger integrity confirmed: Double-entry balanced perfectly!")

    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    create_schema_and_seed()

