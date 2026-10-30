from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from backend.database.connection import get_async_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_async_db)) -> Dict[str, Any]:
    """
    Returns executive KPI metrics:
    - Total spend
    - Monthly variance
    - Burn rate
    - Top spending category
    - Active account count
    - Category distribution
    - Monthly spend trend
    """
    # 1. Total Spend and Count
    total_query = await db.execute(
        text("SELECT COALESCE(SUM(total_amount), 0) as total, COUNT(id) as count FROM transactions;")
    )
    total_row = total_query.fetchone()
    total_spend = float(total_row[0]) if total_row else 0.0
    total_transactions = int(total_row[1]) if total_row else 0

    # 2. Monthly Trend
    monthly_query = await db.execute(text("""
        SELECT 
            TO_CHAR(date, 'YYYY-MM') as month,
            ROUND(SUM(total_amount)::numeric, 2) as spend,
            COUNT(id) as count
        FROM transactions
        GROUP BY TO_CHAR(date, 'YYYY-MM')
        ORDER BY month ASC;
    """))
    monthly_trend = [
        {"month": row[0], "spend": float(row[1]), "count": int(row[2])}
        for row in monthly_query.fetchall()
    ]

    # Calculate Monthly Variance and Burn Rate
    monthly_variance = 0.0
    burn_rate = 0.0
    if len(monthly_trend) >= 2:
        last_month = monthly_trend[-1]["spend"]
        prev_month = monthly_trend[-2]["spend"]
        if prev_month > 0:
            monthly_variance = round(((last_month - prev_month) / prev_month) * 100, 2)
        burn_rate = round(sum(m["spend"] for m in monthly_trend) / len(monthly_trend), 2)
    elif monthly_trend:
        burn_rate = monthly_trend[0]["spend"]

    # 3. Category Distribution
    cat_query = await db.execute(text("""
        SELECT 
            category,
            ROUND(SUM(total_amount)::numeric, 2) as total,
            COUNT(id) as count
        FROM transactions
        GROUP BY category
        ORDER BY total DESC;
    """))
    cat_rows = cat_query.fetchall()
    category_distribution = []
    top_category = "N/A"
    if cat_rows:
        top_category = cat_rows[0][0].title()

    for row in cat_rows:
        cat_amount = float(row[1])
        pct = round((cat_amount / total_spend * 100), 1) if total_spend > 0 else 0.0
        category_distribution.append({
            "category": row[0].title(),
            "amount": cat_amount,
            "count": int(row[2]),
            "percentage": pct
        })

    # 4. Active Accounts & Vendors count
    acc_query = await db.execute(text("SELECT COUNT(id) FROM accounts;"))
    accounts_count = int(acc_query.scalar() or 0)

    avg_transaction = round(total_spend / total_transactions, 2) if total_transactions > 0 else 0.0

    return {
        "total_spend": round(total_spend, 2),
        "monthly_variance": monthly_variance,
        "burn_rate": burn_rate,
        "top_category": top_category,
        "active_accounts": accounts_count,
        "total_transactions": total_transactions,
        "average_transaction": avg_transaction,
        "monthly_trend": monthly_trend,
        "category_distribution": category_distribution,
    }

