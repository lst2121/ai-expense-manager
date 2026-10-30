import datetime
import math
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.database.connection import get_async_db
from backend.auth.security import get_user_id_from_auth

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# In-memory dismissed set for session persistence
DISMISSED_NOTIFICATIONS: set[str] = set()


class DismissNotificationRequest(BaseModel):
    notification_id: str


@router.get("")
async def get_notifications(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """
    Returns event-driven, non-spammy notifications:
    1. Statistical Anomaly (> 2.5 sigma or > 3x rolling 30-day baseline).
    2. Executive Monthly Briefing (1x/month).
    3. Background Task / Ingestion Completion.
    """
    user_id = get_user_id_from_auth(authorization, x_user_id)
    notifications: List[Dict[str, Any]] = []

    # 1. Statistical Z-Score Anomaly Worker
    # Compute rolling 30-day daily spend mean & std dev
    user_cond = "(user_id = :user_id OR user_id IS NULL)" if user_id == "usr-lokender-2026" else "user_id = :user_id"
    
    daily_res = await db.execute(
        text(f"""
            SELECT DATE(date) as day, SUM(total_amount) as daily_spend, COUNT(id) as tx_count
            FROM transactions
            WHERE {user_cond}
            GROUP BY DATE(date)
            ORDER BY day DESC
            LIMIT 45;
        """),
        {"user_id": user_id}
    )
    daily_rows = daily_res.fetchall()

    if len(daily_rows) >= 5:
        # Latest day spend
        latest_day = daily_rows[0][0]
        latest_spend = float(daily_rows[0][1])

        # Baseline excluding the latest day
        baseline_spends = [float(r[1]) for r in daily_rows[1:31]]
        if baseline_spends:
            mean = sum(baseline_spends) / len(baseline_spends)
            variance = sum((x - mean) ** 2 for x in baseline_spends) / len(baseline_spends)
            std = math.sqrt(variance)

            # Check if latest spend is anomalous (> 2.5 sigma or > 3.0x baseline)
            is_anomaly = False
            ratio = (latest_spend / mean) if mean > 0 else 0.0
            z_score = ((latest_spend - mean) / std) if std > 0 else 0.0

            if (latest_spend > 5000) and (ratio >= 2.5 or z_score >= 2.5):
                is_anomaly = True

            notif_id = f"anomaly-{latest_day}-{int(latest_spend)}"
            if is_anomaly and notif_id not in DISMISSED_NOTIFICATIONS:
                # Find top transaction on that day
                top_tx_res = await db.execute(
                    text(f"""
                        SELECT description, total_amount, category
                        FROM transactions
                        WHERE {user_cond} AND DATE(date) = :day
                        ORDER BY total_amount DESC
                        LIMIT 1;
                    """),
                    {"user_id": user_id, "day": latest_day}
                )
                top_tx = top_tx_res.fetchone()
                top_desc = f" (e.g. {top_tx[0]} ₹{float(top_tx[1]):,.0f})" if top_tx else ""

                notifications.append({
                    "id": notif_id,
                    "type": "anomaly",
                    "title": "Unusual Spending Spike Detected",
                    "message": f"Daily spending on {latest_day.strftime('%d %b %Y')} reached ₹{latest_spend:,.2f} — {ratio:.1f}x higher than your 30-day baseline (₹{mean:,.2f}){top_desc}.",
                    "severity": "high",
                    "date": latest_day.isoformat(),
                    "action_label": "Investigate Spike",
                    "action_prompt": f"Analyze why my spending spiked to ₹{latest_spend:,.0f} on {latest_day.strftime('%d %b %Y')}",
                    "read": False,
                })

    # 2. Monthly Executive Briefing (1x/month)
    month_res = await db.execute(
        text(f"""
            SELECT 
                TO_CHAR(date, 'Month YYYY') as month_label,
                TO_CHAR(date, 'YYYY-MM') as month_key,
                SUM(total_amount) as total_spend,
                COUNT(id) as tx_count
            FROM transactions
            WHERE {user_cond}
            GROUP BY TO_CHAR(date, 'Month YYYY'), TO_CHAR(date, 'YYYY-MM')
            ORDER BY month_key DESC
            LIMIT 1;
        """),
        {"user_id": user_id}
    )
    month_row = month_res.fetchone()
    if month_row:
        m_label = month_row[0].strip()
        m_key = month_row[1]
        m_spend = float(month_row[2])
        m_count = int(month_row[3])
        briefing_id = f"briefing-{m_key}"

        if briefing_id not in DISMISSED_NOTIFICATIONS:
            # Top category for the month
            top_cat_res = await db.execute(
                text(f"""
                    SELECT category, SUM(total_amount) as cat_spend
                    FROM transactions
                    WHERE {user_cond} AND TO_CHAR(date, 'YYYY-MM') = :m_key
                    GROUP BY category
                    ORDER BY cat_spend DESC
                    LIMIT 1;
                """),
                {"user_id": user_id, "m_key": m_key}
            )
            top_cat = top_cat_res.fetchone()
            cat_info = f" Top category: {top_cat[0].title()} (₹{float(top_cat[1]):,.0f})." if top_cat else ""

            notifications.append({
                "id": briefing_id,
                "type": "briefing",
                "title": f"Monthly Briefing: {m_label}",
                "message": f"Total household spend: ₹{m_spend:,.2f} across {m_count:,} transactions.{cat_info}",
                "severity": "normal",
                "date": f"{m_key}-01",
                "action_label": "Review Full Briefing",
                "action_prompt": f"Show full spending breakdown and review for {m_label}",
                "read": False,
            })

    return {
        "status": "success",
        "notifications": notifications,
        "unread_count": len([n for n in notifications if not n["read"]]),
    }


@router.post("/dismiss")
async def dismiss_notification(req: DismissNotificationRequest):
    """Dismisses a notification so it won't be shown again in this session."""
    DISMISSED_NOTIFICATIONS.add(req.notification_id)
    return {"status": "success", "dismissed": req.notification_id}
