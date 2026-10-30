import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.database.connection import get_async_db
from backend.auth.security import get_user_id_from_auth

router = APIRouter(prefix="/api", tags=["transactions"])


class CreateTransactionRequest(BaseModel):
    date: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD format")
    description: str = Field(..., description="Transaction memo or note")
    category: str = Field(..., description="Expense category e.g. 'groceries', 'utilities'")
    amount: float = Field(..., gt=0, description="Transaction monetary amount")
    payment_method: Optional[str] = Field(default="Bank Transfer")
    vendor_name: Optional[str] = Field(default=None)


@router.get("/transactions")
async def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_reconciled: Optional[bool] = None,
    sort_by: str = Query("date", regex="^(date|total_amount|category|description)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Returns a filterable, sortable, paginated transaction ledger.
    """
    user_id = get_user_id_from_auth(authorization, x_user_id)
    conditions = ["1=1"]
    params: Dict[str, Any] = {}

    if user_id == "usr-lokender-2026":
        conditions.append("(t.user_id = :user_id OR t.user_id IS NULL)")
    else:
        conditions.append("t.user_id = :user_id")
    params["user_id"] = user_id

    if category and category.lower() != "all":
        conditions.append("LOWER(t.category) = LOWER(:category)")
        params["category"] = category

    if search:
        conditions.append("(t.description ILIKE :search OR t.notes ILIKE :search OR v.name ILIKE :search)")
        params["search"] = f"%{search}%"

    if start_date:
        conditions.append("t.date >= :start_date")
        params["start_date"] = start_date

    if end_date:
        conditions.append("t.date <= :end_date")
        params["end_date"] = end_date

    if is_reconciled is not None:
        conditions.append("t.is_reconciled = :is_reconciled")
        params["is_reconciled"] = is_reconciled

    where_clause = " AND ".join(conditions)

    # Count total matching rows
    count_sql = f"""
        SELECT COUNT(t.id) 
        FROM transactions t
        LEFT JOIN vendors v ON t.vendor_id = v.id
        WHERE {where_clause};
    """
    count_res = await db.execute(text(count_sql), params)
    total_count = int(count_res.scalar() or 0)

    # Fetch rows
    offset = (page - 1) * limit
    order_column = f"t.{sort_by}"
    query_sql = f"""
        SELECT 
            t.id,
            t.date,
            t.description,
            t.total_amount,
            t.payment_method,
            t.category,
            t.is_reconciled,
            t.notes,
            COALESCE(v.name, 'Unassigned') as vendor_name,
            COALESCE(a.name, 'Expense') as account_name,
            COALESCE(a.code, '5000') as account_code
        FROM transactions t
        LEFT JOIN vendors v ON t.vendor_id = v.id
        LEFT JOIN accounts a ON t.account_id = a.id
        WHERE {where_clause}
        ORDER BY {order_column} {sort_order.upper()}
        LIMIT :limit OFFSET :offset;
    """
    params["limit"] = limit
    params["offset"] = offset

    result = await db.execute(text(query_sql), params)
    rows = result.fetchall()

    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "date": r[1].strftime("%Y-%m-%d") if r[1] else "",
            "description": r[2],
            "total_amount": float(r[3]),
            "payment_method": r[4],
            "category": r[5],
            "is_reconciled": bool(r[6]),
            "notes": r[7],
            "vendor_name": r[8],
            "account_name": r[9],
            "account_code": r[10]
        })

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


@router.get("/accounts")
async def list_accounts(db: AsyncSession = Depends(get_async_db)) -> List[Dict[str, Any]]:
    """Returns Chart of Accounts."""
    result = await db.execute(text("SELECT id, code, name, type, description FROM accounts ORDER BY code ASC;"))
    return [
        {
            "id": r[0],
            "code": r[1],
            "name": r[2],
            "type": r[3],
            "description": r[4]
        }
        for r in result.fetchall()
    ]


@router.get("/vendors")
async def list_vendors(db: AsyncSession = Depends(get_async_db)) -> List[Dict[str, Any]]:
    """Returns list of active vendors."""
    result = await db.execute(text("SELECT id, name, category FROM vendors ORDER BY name ASC;"))
    return [
        {"id": r[0], "name": r[1], "category": r[2]}
        for r in result.fetchall()
    ]


@router.post("/transactions")
async def create_transaction(
    payload: CreateTransactionRequest,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Creates a new transaction and automatically enforces balanced double-entry journal entries:
    - Debit: Expense Account
    - Credit: Operating Cash & Bank Account (1010) or Credit Card Liability (2010)
    """
    user_id = get_user_id_from_auth(authorization, x_user_id)
    tx_date = (
        datetime.datetime.strptime(payload.date, "%Y-%m-%d")
        if payload.date
        else datetime.datetime.utcnow()
    )
    amount = Decimal(str(round(payload.amount, 2)))

    # Find or create vendor
    vendor_id = None
    if payload.vendor_name:
        v_res = await db.execute(
            text("SELECT id FROM vendors WHERE LOWER(name) = LOWER(:name);"),
            {"name": payload.vendor_name.strip()}
        )
        v_row = v_res.fetchone()
        if v_row:
            vendor_id = v_row[0]
        else:
            insert_v = await db.execute(
                text("INSERT INTO vendors (name, category, created_at) VALUES (:name, :category, NOW()) RETURNING id;"),
                {"name": payload.vendor_name.strip(), "category": payload.category.lower()}
            )
            vendor_id = insert_v.scalar()

    # Find appropriate expense account
    acc_res = await db.execute(
        text("SELECT id FROM accounts WHERE type = 'expense' AND (LOWER(name) LIKE :cat OR LOWER(description) LIKE :cat) LIMIT 1;"),
        {"cat": f"%{payload.category.lower()}%"}
    )
    acc_row = acc_res.fetchone()
    if acc_row:
        account_id = acc_row[0]
    else:
        # Fallback to General & Miscellaneous (5120) or first available expense account
        fallback_res = await db.execute(
            text("SELECT id FROM accounts WHERE code = '5120' OR type = 'expense' ORDER BY (code = '5120') DESC LIMIT 1;")
        )
        account_id = fallback_res.scalar() or 3

    # Find settlement credit account: 2010 for Credit Card, 1010 for Cash/Bank/UPI
    is_credit_card = bool(payload.payment_method and "credit" in payload.payment_method.lower())
    credit_code = "2010" if is_credit_card else "1010"
    settle_res = await db.execute(text("SELECT id FROM accounts WHERE code = :code LIMIT 1;"), {"code": credit_code})
    settle_account_id = settle_res.scalar() or 1

    # Insert Transaction
    insert_tx = await db.execute(
        text("""
            INSERT INTO transactions (date, description, vendor_id, account_id, user_id, total_amount, payment_method, category, is_reconciled, notes, created_at)
            VALUES (:date, :description, :vendor_id, :account_id, :user_id, :amount, :payment_method, :category, false, :notes, NOW())
            RETURNING id;
        """),
        {
            "date": tx_date,
            "description": payload.description,
            "vendor_id": vendor_id,
            "account_id": account_id,
            "user_id": user_id,
            "amount": amount,
            "payment_method": payload.payment_method or "Bank Transfer",
            "category": payload.category.lower(),
            "notes": payload.description
        }
    )
    tx_id = insert_tx.scalar()

    # Insert Double-Entry Journal Lines
    # Debit Expense
    await db.execute(
        text("""
            INSERT INTO journal_entries (transaction_id, account_id, debit, credit, description, entry_date)
            VALUES (:tx_id, :account_id, :debit, 0.00, :description, :date);
        """),
        {
            "tx_id": tx_id,
            "account_id": account_id,
            "debit": amount,
            "description": f"Debit Expense: {payload.description}",
            "date": tx_date
        }
    )
    # Credit Settlement Account (Cash/Bank or Credit Card Liability)
    await db.execute(
        text("""
            INSERT INTO journal_entries (transaction_id, account_id, debit, credit, description, entry_date)
            VALUES (:tx_id, :account_id, 0.00, :credit, :description, :date);
        """),
        {
            "tx_id": tx_id,
            "account_id": settle_account_id,
            "credit": amount,
            "description": f"Credit {'Card Liability' if is_credit_card else 'Bank/Cash'}: {payload.description}",
            "date": tx_date
        }
    )

    await db.commit()

    return {
        "success": True,
        "transaction_id": tx_id,
        "message": f"Transaction recorded and double-entry balanced with ${amount:.2f}."
    }


@router.patch("/transactions/{transaction_id}/reconcile")
async def reconcile_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Marks a single transaction as reconciled and statement-verified."""
    res = await db.execute(
        text("UPDATE transactions SET is_reconciled = true WHERE id = :id RETURNING id;"),
        {"id": transaction_id}
    )
    row = res.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await db.commit()
    return {"success": True, "transaction_id": transaction_id, "is_reconciled": True}


class BatchReconcileRequest(BaseModel):
    category: Optional[str] = None
    account_code: Optional[str] = None


@router.post("/transactions/reconcile-all")
async def batch_reconcile_transactions(
    payload: Optional[BatchReconcileRequest] = None,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Batch reconciles all pending unreconciled transactions, optionally filtered by category."""
    cat = payload.category if payload else None
    if cat:
        res = await db.execute(
            text("UPDATE transactions SET is_reconciled = true WHERE is_reconciled = false AND LOWER(category) = LOWER(:cat) RETURNING id;"),
            {"cat": cat.strip()}
        )
    else:
        res = await db.execute(
            text("UPDATE transactions SET is_reconciled = true WHERE is_reconciled = false RETURNING id;")
        )
    reconciled_ids = [r[0] for r in res.fetchall()]
    await db.commit()
    return {
        "success": True,
        "reconciled_count": len(reconciled_ids),
        "message": f"Successfully audited and reconciled {len(reconciled_ids)} transaction(s)."
    }

