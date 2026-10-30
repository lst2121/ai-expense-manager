import pytest
from decimal import Decimal
import datetime
from sqlalchemy import text
from backend.database.connection import sync_engine, SyncSessionLocal
from backend.database.models import Base, Account, Vendor, Transaction, JournalEntry


def test_database_connection():
    """Verify PostgreSQL 17 database is reachable."""
    with sync_engine.connect() as conn:
        res = conn.execute(text("SELECT 1;")).scalar()
        assert res == 1


def test_chart_of_accounts_exists():
    """Verify Chart of Accounts was seeded with asset, liability, and expense accounts."""
    session = SyncSessionLocal()
    try:
        accounts = session.query(Account).all()
        assert len(accounts) >= 8, f"Expected at least 8 accounts, found {len(accounts)}"

        account_types = {a.type for a in accounts}
        assert "asset" in account_types
        assert "expense" in account_types

        # Check Bank Account 1010
        bank = session.query(Account).filter_by(code="1010").first()
        assert bank is not None
        assert bank.name == "Operating Cash & Bank"
    finally:
        session.close()


def test_double_entry_balance_integrity():
    """
    CRITICAL ACCOUNTING INVARIANT:
    Total Debits across the entire general ledger must exactly equal Total Credits.
    """
    session = SyncSessionLocal()
    try:
        with sync_engine.connect() as conn:
            row = conn.execute(
                text("SELECT SUM(debit) as total_debit, SUM(credit) as total_credit FROM journal_entries;")
            ).fetchone()
            total_debit = Decimal(str(row[0]))
            total_credit = Decimal(str(row[1]))

            assert total_debit > Decimal("0.00"), "Ledger has no debit entries"
            assert total_debit == total_credit, f"Ledger imbalanced! Debits: {total_debit} != Credits: {total_credit}"
    finally:
        session.close()


def test_transaction_creation_with_balanced_journal():
    """Test manual transaction creation with double-entry lines."""
    session = SyncSessionLocal()
    try:
        bank = session.query(Account).filter_by(code="1010").first()
        sub_acc = session.query(Account).filter_by(code="5010").first()

        amount = Decimal("250.00")
        tx = Transaction(
            date=datetime.datetime.utcnow(),
            description="Test Accounting Software",
            account_id=sub_acc.id,
            total_amount=amount,
            payment_method="Corporate Credit Card",
            category="subscriptions",
            is_reconciled=False,
            notes="Pytest unit test"
        )
        session.add(tx)
        session.flush()

        debit_entry = JournalEntry(
            transaction_id=tx.id,
            account_id=sub_acc.id,
            debit=amount,
            credit=Decimal("0.00"),
            description="Debit Test Software",
            entry_date=tx.date
        )
        credit_entry = JournalEntry(
            transaction_id=tx.id,
            account_id=bank.id,
            debit=Decimal("0.00"),
            credit=amount,
            description="Credit Cash/Bank",
            entry_date=tx.date
        )
        session.add_all([debit_entry, credit_entry])
        session.commit()

        # Query back
        stored_tx = session.query(Transaction).filter_by(id=tx.id).first()
        assert stored_tx is not None
        assert stored_tx.total_amount == amount
        assert len(stored_tx.journal_entries) == 2

        tx_debits = sum(e.debit for e in stored_tx.journal_entries)
        tx_credits = sum(e.credit for e in stored_tx.journal_entries)
        assert tx_debits == tx_credits == amount

        # Clean up
        session.delete(stored_tx)
        session.commit()
    finally:
        session.close()

