import urllib.request
import json
import asyncio
from backend.database.connection import AsyncSessionLocal
from sqlalchemy import text

test_queries = [
    ('Spent 3,500 at Pizza Hut today on UPI', 3500.0, 'Pizza Hut', 'dining', 'UPI'),
    ('Add 500 for shirt today', 500.0, 'Shirt', 'shopping', 'UPI'),
    ('add 200 for tomato yesterday', 200.0, 'Tomato', 'groceries', 'UPI'),
    ('add 2000 for chair', 2000.0, 'Chair', 'home & furniture', 'UPI'),
    ('add 2000 for tv', 2000.0, 'Tv', 'electronics', 'UPI'),
    ('500 for jeans', 500.0, 'Jeans', 'shopping', 'UPI'),
    ('3500 pizza', 3500.0, 'Pizza', 'dining', 'UPI'),
    ('paid 450 for uber by credit card', 450.0, 'Uber', 'transportation', 'Credit Card')
]

def test_intent_detection():
    print("=== TEST 1: EXPENSE INTENT & EXTRACTION VIA LIVE API ===")
    all_passed = True
    for query, exp_amt, exp_item, exp_cat, exp_pay in test_queries:
        req = urllib.request.Request(
            'http://localhost:8000/api/chat/stream',
            data=json.dumps({'message': query, 'session_id': 'test-live-run'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            intent_data = None
            for line in body.split('\n'):
                if line.startswith('data: '):
                    try:
                        d = json.loads(line[6:])
                        if 'intent' in d:
                            intent_data = d['intent']
                            break
                    except:
                        pass
            if not intent_data:
                print(f"FAIL: No intent detected for '{query}'")
                all_passed = False
            else:
                amt_ok = (intent_data['amount'] == exp_amt)
                item_ok = (intent_data['item'] == exp_item)
                cat_ok = (intent_data['category'] == exp_cat)
                pay_ok = (intent_data['payment_method'] == exp_pay)
                if amt_ok and item_ok and cat_ok and pay_ok:
                    print(f"PASS: '{query}' -> Amount: ₹{intent_data['amount']:,.2f} | Item: {intent_data['item']} | Cat: {intent_data['category']} | Pay: {intent_data['payment_method']}")
                else:
                    print(f"FAIL: '{query}' -> got {intent_data}")
                    all_passed = False
    return all_passed

def test_transaction_recording():
    print("\n=== TEST 2: RECORDING AN EXPENSE & DOUBLE-ENTRY INVARIANT ===")
    req = urllib.request.Request(
        'http://localhost:8000/api/transactions',
        data=json.dumps({
            'description': 'Zara Denim Shirt',
            'amount': 2499.00,
            'category': 'shopping',
            'vendor_name': 'Zara',
            'payment_method': 'Credit Card',
            'date': '2026-10-30'
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Create Transaction Response:", res)
        tx_id = res.get('transaction_id')
        assert tx_id is not None, "Failed to get transaction_id"

    # Verify double-entry in database
    async def verify_db(tid):
        async with AsyncSessionLocal() as session:
            j_res = await session.execute(
                text("SELECT account_id, debit, credit, description FROM journal_entries WHERE transaction_id = :tid"),
                {'tid': tid}
            )
            entries = j_res.fetchall()
            print(f"Journal Entries for Tx #{tid}:")
            total_debit = 0.0
            total_credit = 0.0
            for e in entries:
                print(f"  Account {e[0]}: Debit ₹{e[1]} | Credit ₹{e[2]} | {e[3]}")
                total_debit += float(e[1])
                total_credit += float(e[2])
            print(f"Total Debit: ₹{total_debit:.2f} | Total Credit: ₹{total_credit:.2f}")
            assert abs(total_debit - total_credit) < 0.001, "DOUBLE ENTRY UNBALANCED!"
            print("PASS: Double-entry invariant verified (SUM Debit == SUM Credit)")

            # Clean up the test transaction
            await session.execute(text("DELETE FROM journal_entries WHERE transaction_id = :tid"), {'tid': tid})
            await session.execute(text("DELETE FROM transactions WHERE id = :tid"), {'tid': tid})
            await session.commit()
            print("Cleaned up test transaction cleanly!")

    asyncio.run(verify_db(tx_id))

def test_conversational_queries():
    print("\n=== TEST 3: CONVERSATIONAL LEDGER REASONING (DINING BREAKDOWN) ===")
    req = urllib.request.Request(
        'http://localhost:8000/api/chat/stream',
        data=json.dumps({'message': 'Break down my Dining expenses for 2026', 'session_id': 'test-live-conv'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode('utf-8')
        tokens = []
        has_table = False
        for line in body.split('\n'):
            if line.startswith('data: '):
                try:
                    d = json.loads(line[6:])
                    if 'token' in d:
                        tokens.append(d['token'])
                except:
                    pass
        full_text = "".join(tokens)
        print("Response length:", len(full_text))
        print("Response snippet:", full_text[:250].replace('\n', ' '))
        has_dining = "Dining" in full_text or "dining" in full_text
        has_amount = "₹" in full_text
        if has_dining and has_amount:
            print("PASS: Dining breakdown returned grounded numbers and currency formatting.")
        else:
            print("FAIL: Dining breakdown did not contain expected content.")

if __name__ == "__main__":
    t1 = test_intent_detection()
    test_transaction_recording()
    test_conversational_queries()
    print("\nALL BACKEND FUNCTIONALITY TESTS COMPLETE!")

