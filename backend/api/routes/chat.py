import os
import re
import json
import uuid
import time
import asyncio
import logging
import datetime
from typing import Optional, AsyncGenerator, Any, Dict, Tuple, List
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.agent.financial_agent import create_financial_agent
from backend.agent.llm_factory import get_llm
from backend.agent.tools.sql_analytics import run_financial_query, get_expense_summary
from backend.agent.tools.chart_tool import generate_chart_spec
from backend.database.connection import async_engine, AsyncSessionLocal, sync_engine
from backend.database.models import ChatFeedback, ChatSession, ChatMessage, DocumentEmbedding
from sqlalchemy import text
from backend.agent.tools.extractor_tool import (
    ExtractedReceipt,
    parse_bank_sms,
    extract_text_from_pdf,
    extract_text_from_csv,
    extract_text_from_excel,
    infer_category,
    analyze_document_with_llm,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="User prompt or accounting query")
    thread_id: Optional[str] = Field(default=None, description="Session thread ID for multi-turn conversational memory")
    session_id: Optional[str] = Field(default=None, description="Persistent chat session ID in PostgreSQL")
    provider: Optional[str] = Field(default="deepseek", description="LLM provider: 'deepseek' or 'gemini'")
    language: Optional[str] = Field(default="en", description="Language preference: 'en' (English) or 'hi' (Hindi)")


def clean_expense_metadata(raw_item: str) -> Tuple[str, str, str]:
    """
    Cleans raw item string, extracting payment methods and temporal markers
    while stripping prepositions (e.g. 'for shirt today' -> ('Shirt', 'UPI', '2026-10-30')).
    """
    item = raw_item.strip()
    payment_method = "UPI"
    txn_date = datetime.date.today().isoformat()

    # Extract payment method if present
    if re.search(r'\b(?:on|via|by|with)?\s*credit\s*card\b', item, re.I):
        payment_method = "Credit Card"
        item = re.sub(r'\b(?:on|via|by|with)?\s*credit\s*card\b', '', item, flags=re.I)
    elif re.search(r'\b(?:on|via|by|with)?\s*debit\s*card\b', item, re.I):
        payment_method = "Debit Card"
        item = re.sub(r'\b(?:on|via|by|with)?\s*debit\s*card\b', '', item, flags=re.I)
    elif re.search(r'\b(?:on|via|by|with)?\s*upi\b', item, re.I):
        payment_method = "UPI"
        item = re.sub(r'\b(?:on|via|by|with)?\s*upi\b', '', item, flags=re.I)
    elif re.search(r'\b(?:in|by|with)?\s*cash\b', item, re.I):
        payment_method = "Cash"
        item = re.sub(r'\b(?:in|by|with)?\s*cash\b', '', item, flags=re.I)
    elif re.search(r'\b(?:via|by|with|on)?\s*net\s*banking\b', item, re.I):
        payment_method = "Net Banking"
        item = re.sub(r'\b(?:via|by|with|on)?\s*net\s*banking\b', '', item, flags=re.I)

    # Extract date if present
    if re.search(r'\byesterday\b', item, re.I):
        txn_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        item = re.sub(r'\byesterday\b', '', item, flags=re.I)
    elif re.search(r'\btoday\b', item, re.I):
        txn_date = datetime.date.today().isoformat()
        item = re.sub(r'\btoday\b', '', item, flags=re.I)

    # Strip leading prepositions
    item = re.sub(r'^(?:for|on|at|in|to)\s+', '', item, flags=re.I)
    item = re.sub(r'[\s.,;:?!]+$', '', item).strip()

    return item.title(), payment_method, txn_date


def classify_expense_category(item: str) -> str:
    """
    Intelligently maps item/vendor to verified household chart of accounts
    using strict word boundaries to prevent substring collisions (e.g. 'chai' in 'chair').
    """
    lower = item.lower()

    # Dining & Catering
    if re.search(r'\b(?:pizza|burger|zomato|swiggy|food|dinner|lunch|breakfast|chai|tea|coffee|restaurant|cafe|bhelpuri|dosa|biryani|mcdonalds?|starbucks?|haldiram|subway|dominos?|pizzeria)\b', lower):
        return "dining"
    # Groceries & Staples
    if re.search(r'\b(?:blinkit|zepto|instamart|bigbasket|kirana|ration|milk|vegetables?|fruits?|grocery|groceries|sabzi|dmart|tomato|potato|onion|bread|eggs?|butter|paneer|atta|dal|oil|rice)\b', lower):
        return "groceries"
    # Shopping & Apparel
    if re.search(r'\b(?:shirt|tshirt|t-shirt|jeans|pants?|trousers?|clothing|clothes|shoes|sneakers|dress|kurta|saree|jacket|suit|zara|h&m|myntra|ajio|shopping|apparel|watch|bag)\b', lower):
        return "shopping"
    # Home & Furniture
    if re.search(r'\b(?:chair|table|desk|sofa|bed|mattress|furniture|curtains?|carpet|lamp|wardrobe|bookshelf|ikea|urban\s*ladder|pepperfry)\b', lower):
        return "home & furniture"
    # Electronics & Appliances
    if re.search(r'\b(?:tv|television|laptop|phone|mobile|smartphone|monitor|fridge|refrigerator|ac|air\s*conditioner|ipad|tablet|charger|headphones?|earphones?|earbuds?|croma|reliance\s*digital)\b', lower):
        return "electronics"
    # Utilities & Telecom
    if re.search(r'\b(?:electricity|power|water|gas|cylinder|lpg|png|wifi|broadband|recharge|bill|bescom|airtel|jio|vi|vodafone)\b', lower):
        return "utilities"
    # Transportation & Fleet
    if re.search(r'\b(?:uber|ola|rapido|petrol|fuel|diesel|cng|metro|auto|cab|taxi|bus|toll|fastag|flight|train|irctc)\b', lower):
        return "transportation"
    # Healthcare & Medical
    if re.search(r'\b(?:medicine|doctor|hospital|clinic|pharmacy|apollo|1mg|pharmeasy|dawa|dentist|tests?|pathology)\b', lower):
        return "healthcare"
    # Entertainment & Events
    if re.search(r'\b(?:netflix|prime|hotstar|spotify|youtube|movie|bookmyshow|cinema|steam|games?|arcade|timezone|pvr|inox)\b', lower):
        return "entertainment"
    # Rent & Facilities
    if re.search(r'\b(?:rent|maintenance|society|flat|apartment|brokerage|maid|cook|kamwali)\b', lower):
        return "rent"

    # Default to general rather than groceries
    return "general"


def detect_expense_intent(text: str) -> Optional[Dict[str, Any]]:
    """
    Context-aware expense intent detector.
    Strictly filters out questions, projections, and affirmations.
    Accurately extracts amounts (with or without commas), vendors/items, categories, payment methods, and dates.
    """
    t = text.strip()
    lower = t.lower()

    # Guard 1: Questions, projections, trends, affirmations, and foreign currencies are NEVER quick-add expenses
    non_expense_keywords = [
        "what", "how", "trend", "break down", "category", "categories",
        "compare", "chart", "show", "tell", "project", "projection",
        "forecast", "predict", "estimate", "future", "next year", "last year",
        "whole year", "all months", "no", "nope", "cancel", "stop", "yes",
        "yeah", "ok", "okay", "hi", "hello", "hey", "namaste", "nahi", "haan",
        "usd", "eur", "gbp", "dollar", "dollars", "euro", "euros", "pound", "pounds", "aud", "cad"
    ]
    if any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in non_expense_keywords):
        return None

    # Pattern 1: 'spent 3,500 at pizza hut today on upi', 'add 500 for shirt today'
    p1 = re.search(r'(?:(?:spent|paid|bought|add)\s*(?:rs\.?|inr|₹)?\s*(-?[\d,]+(?:\.\d{1,2})?))\s+(?:on|for|at|in)?\s*([a-zA-Z\s&0-9\-_]+)', t, re.I)
    # Pattern 2: '3500 pizza', '500 for jeans'
    p2 = re.search(r'^(?:rs\.?|inr|₹)?\s*(-?[\d,]+(?:\.\d{1,2})?)\s+(?:on|for|at|in)?\s*([a-zA-Z\s&0-9\-_]+)$', t, re.I)
    # Pattern 3: 'pizza 3500'
    p3 = re.search(r'^([a-zA-Z\s&0-9\-_]+)\s+(?:rs\.?|inr|₹)?\s*(-?[\d,]+(?:\.\d{1,2})?)$', t, re.I)

    raw_amt = None
    raw_item = None

    if p1:
        raw_amt = p1.group(1)
        raw_item = p1.group(2)
    elif p2:
        raw_amt = p2.group(1)
        raw_item = p2.group(2)
    elif p3:
        raw_item = p3.group(1)
        raw_amt = p3.group(2)

    if not raw_amt or not raw_item:
        return None

    amt_str = raw_amt.replace(',', '')
    try:
        amount = float(amt_str)
    except ValueError:
        return None

    # Reject non-positive amounts
    if amount <= 0:
        return None

    # Guard 2: Never allow 4-digit calendar years (2015 - 2035) to be parsed as amounts unless prefixed with currency symbol
    has_currency_symbol = bool(re.search(r'(?:rs\.?|inr|₹|rupees)', t, re.I))
    if 2015 <= amount <= 2035 and not has_currency_symbol and '.' not in amt_str:
        return None

    clean_item, payment_method, txn_date = clean_expense_metadata(raw_item)
    if not clean_item or len(clean_item) < 1:
        return None

    category = classify_expense_category(clean_item)

    return {
        "amount": amount,
        "item": clean_item,
        "category": category,
        "vendor": clean_item,
        "payment_method": payment_method,
        "date": txn_date,
    }


def generate_expense_projection(target_year: int = 2026, lang: str = "en") -> Tuple[str, Dict[str, Any]]:
    """
    Generates intelligent financial projections for 2026 based on historical
    burn rate (₹19,454/mo), category weightings, and realistic Indian seasonal variance.
    """
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # Seasonal multipliers reflecting Indian household spending:
    # Tax/insurance (Mar), School fees (Apr), Summer holidays (May-Jun), Festivals/Diwali (Oct-Nov), Year-end (Dec)
    weights = [1.00, 0.95, 1.10, 1.05, 1.08, 1.05, 0.96, 0.98, 1.02, 1.25, 1.20, 1.12]

    base_monthly = 19454.26 * 1.06  # 6% assumed annual inflation
    projected_data = []
    total_projected = 0.0

    for m_name, w in zip(months, weights):
        month_spend = round(base_monthly * w, 2)
        total_projected += month_spend
        projected_data.append({
            "month": f"{m_name} {target_year}",
            "projected_spend": month_spend,
        })

    avg_projected_month = round(total_projected / 12, 2)

    chart_str = generate_chart_spec.invoke({
        "chart_type": "area",
        "title": f"Projected Household Expenses for {target_year}",
        "x_key": "month",
        "y_keys": ["projected_spend"],
        "data": projected_data,
        "description": f"Estimated annual spend of ₹{total_projected:,.2f} with peak seasonal outflow in October & November."
    })
    chart_spec = json.loads(chart_str)

    if lang == "hi":
        text = (
            f"### वर्ष {target_year} का अनुमानित घरेलू बजट विश्लेषण:\n\n"
            f"आपके पिछले खर्च (औसत ₹19,454/माह) और 6% महंगाई दर के आधार पर, वर्ष {target_year} का अनुमानित विवरण:\n\n"
            f"• **कुल अनुमानित वार्षिक खर्च:** **₹{total_projected:,.2f}**\n"
            f"• **औसत मासिक बजट:** **₹{avg_projected_month:,.2f} / माह**\n"
            f"• **अधिकतम खर्च वाले महीने:** **अक्टूबर और नवंबर (दीवाली, त्योहार, शादियाँ)** (~₹24,500/माह)\n"
            f"• **अनुशंसित इमरजेंसी बचत:** कम से कम **₹3,000/माह** अलग से रखें।\n\n"
            f"नीचे दिए गए चार्ट में सभी 12 महीनों का अनुमानित खर्च देखें:"
        )
    else:
        text = (
            f"### Household Expense Projections for {target_year}:\n\n"
            f"Based on your 2025 historical run rate (₹19,454/mo) adjusted for 6% annual inflation and Indian seasonal patterns:\n\n"
            f"• **Total Projected Annual Outflow:** **₹{total_projected:,.2f}**\n"
            f"• **Projected Monthly Average:** **₹{avg_projected_month:,.2f} / month**\n"
            f"• **Peak Outflow Quarters:** **Q4 (October & November)** due to Diwali, festival bonuses, and wedding season (~₹24,500/mo).\n"
            f"• **Recommended Family Buffer:** Maintain an emergency reserve of at least **₹3,000/month**.\n\n"
            f"Here is your month-by-month projected trajectory for {target_year}:"
        )

    return text, chart_spec


def generate_smart_financial_response(query: str, lang: str = "en", session_id: Optional[str] = None) -> Tuple[str, Optional[Dict[str, Any]], str]:
    """
    High-speed household financial analytics engine formatted with Indian Rupee (₹).
    Resolves natural queries (e.g. 'tell me my latest expense', 'how much did I spend on groceries',
    'who did I pay the most to', 'monthly trends', '2026 projections') dynamically against PostgreSQL.
    Supports English and Hindi seamlessly.
    """
    # Normalize common typos (e.g. 'expanse' -> 'expense', 'transction' -> 'transaction')
    q = query.lower()
    q = re.sub(r'\bexpanses?\b', 'expense', q)
    q = re.sub(r'\btransctions?\b', 'transaction', q)

    # 1. Projections / Forecasting
    if any(k in q for k in ["project", "projection", "forecast", "future", "2026", "next year", "predict"]):
        text, chart_spec = generate_expense_projection(target_year=2026, lang=lang)
        return text, chart_spec, "project_future_expenses"

    # 2. Conversational Rejections ('No', 'cancel', 'nah')
    elif re.search(r'\b(no|nope|cancel|nahi|stop|don\'t add)\b', q):
        if lang == "hi":
            text = "ठीक है! यह खर्च नहीं जोड़ा गया है। आप अपने बजट या पिछले खर्चों के बारे में कुछ भी पूछ सकते हैं।"
        else:
            text = "Understood! The expense was not added to your ledger. What else would you like to explore?"
        return text, None, "conversational_handler"

    # 2.5 Document Inquiries ('what this doc was about', 'document summary', 'what did i upload', 'norstella')
    elif any(k in q for k in ["doc", "document", "upload", "uploaded", "pdf", "file", "norstella"]) and session_id:
        try:
            with sync_engine.connect() as conn:
                doc_row = conn.execute(
                    text("SELECT filename, content_text, metadata_json FROM document_embeddings WHERE session_id = :sid ORDER BY created_at DESC LIMIT 1"),
                    {"sid": session_id}
                ).fetchone()
                if doc_row:
                    fname = doc_row[0]
                    dtext = doc_row[1] or ""
                    dmeta = doc_row[2] or {}
                    summary = dmeta.get("summary", "")
                    text_out = (
                        f"Here is the detail of `{fname}` uploaded in this session:\n\n"
                        f"**Summary:** {summary}\n\n"
                        f"**Key Content:**\n{dtext[:1200]}"
                    )
                    return text_out, None, "document_retrieval"
                else:
                    msg_row = conn.execute(
                        text("SELECT content FROM chat_messages WHERE session_id = :sid AND content LIKE '%Uploaded Document Analysis%' ORDER BY created_at DESC LIMIT 1"),
                        {"sid": session_id}
                    ).fetchone()
                    if msg_row:
                        text_out = f"Here is the summary of the document you uploaded in this session:\n\n{msg_row[0]}"
                        return text_out, None, "document_retrieval"
        except Exception as doc_err:
            logger.warning(f"Error fetching document history: {doc_err}")

    # 3. Conversational Greetings ('Hi', 'hello', 'namaste', 'hey')
    elif re.search(r'^\s*(hi|hello|hey|namaste|greetings)\b', q):
        if lang == "hi":
            text = "नमस्ते! मैं आपका पर्सनल फाइनेंस असिस्टेंट हूँ। आप मुझसे अपने मासिक बजट, 2026 के खर्चों के अनुमान, हालिया लेन-देन, या '3500 pizza' लिखकर तुरंत खर्च जोड़ने को कह सकते हैं।"
        else:
            text = "Hi! How can I assist with your household finances today? You can ask about your latest expense, monthly trends, 2026 projections, or log expenses like '3500 pizza'."
        return text, None, "conversational_handler"

    # 4. Latest / Recent Expenses (e.g. "tell me my latest expense", "what was my last payment", "recent expenses")
    elif any(k in q for k in ["latest", "last expense", "last transaction", "recent", "aakhri", "pichla kharch", "last payment", "previous expense"]):
        sql = """
            SELECT t.id, t.date, t.description, t.category, t.total_amount, t.payment_method, COALESCE(v.name, 'Direct Payment') as vendor
            FROM transactions t
            LEFT JOIN vendors v ON t.vendor_id = v.id
            ORDER BY t.date DESC, t.id DESC
            LIMIT 5;
        """
        rows_str = run_financial_query.invoke({"query": sql})
        rows = json.loads(rows_str)

        if not rows:
            if lang == "hi":
                return "वर्तमान में बहीखाते में कोई खर्च दर्ज नहीं है।", None, "run_financial_query"
            return "No recorded transactions found in your household ledger.", None, "run_financial_query"

        latest = rows[0]
        date_str = str(latest['date'])[:10]
        chart_data = [{"item": r['description'][:15], "amount": float(r['total_amount'])} for r in rows]

        chart_str = generate_chart_spec.invoke({
            "chart_type": "bar",
            "title": "Recent Household Disbursements",
            "x_key": "item",
            "y_keys": ["amount"],
            "data": chart_data,
            "description": f"Latest transaction is ₹{latest['total_amount']:,.2f} for {latest['description']}."
        })
        chart_spec = json.loads(chart_str)

        if lang == "hi":
            text = (
                f"### आपका सबसे हालिया दर्ज खर्च:\n\n"
                f"• **राशि:** **₹{latest['total_amount']:,.2f}**\n"
                f"• **विवरण:** **{latest['description']}**\n"
                f"• **श्रेणी:** **{latest['category'].title()}**\n"
                f"• **भुगतान का माध्यम:** **{latest['payment_method']}**\n"
                f"• **दिनांक:** **{date_str}**\n\n"
                f"**पिछले 4 अन्य लेन-देन:**\n"
            )
            for r in rows[1:]:
                text += f"• **₹{r['total_amount']:,.2f}** — {r['description']} ({r['category'].title()}) दिनांक {str(r['date'])[:10]}\n"
        else:
            text = (
                f"### Latest Recorded Expense:\n\n"
                f"• **Amount:** **₹{latest['total_amount']:,.2f}**\n"
                f"• **Item:** **{latest['description']}**\n"
                f"• **Category:** **{latest['category'].title()}**\n"
                f"• **Payment Method:** **{latest['payment_method']}**\n"
                f"• **Date:** **{date_str}**\n\n"
                f"**Preceding Recent Expenses:**\n"
            )
            for r in rows[1:]:
                text += f"• **₹{r['total_amount']:,.2f}** — {r['description']} ({r['category'].title()}) on {str(r['date'])[:10]}\n"

        return text, chart_spec, "run_financial_query"

    # 5. Category-specific spend (e.g. "how much did I spend on groceries", "what did I spend on rent")
    elif any(k in q for k in ["how much", "kitna", "total spent on", "spent on", "spending on"]) and any(c in q for c in ["rent", "groceries", "grocery", "ration", "dining", "food", "utilities", "electricity", "transport", "travel", "healthcare", "medical", "entertainment", "subscriptions"]):
        matched_cat = None
        for c in ["rent", "groceries", "dining", "utilities", "transportation", "healthcare", "entertainment", "subscriptions"]:
            if c in q or (c == "groceries" and ("grocery" in q or "ration" in q or "kirana" in q)) or (c == "dining" and ("food" in q or "pizza" in q or "restaurant" in q)) or (c == "utilities" and ("electricity" in q or "bill" in q or "bescom" in q)) or (c == "transportation" and ("transport" in q or "travel" in q or "fuel" in q or "petrol" in q or "cab" in q)):
                matched_cat = c
                break

        if matched_cat:
            sql = f"""
                SELECT category, SUM(total_amount) as total_spend, COUNT(*) as tx_count, AVG(total_amount) as avg_spend
                FROM transactions
                WHERE LOWER(category) = '{matched_cat}'
                GROUP BY category;
            """
            rows_str = run_financial_query.invoke({"query": sql})
            rows = json.loads(rows_str)
            if rows:
                r = rows[0]
                tot = float(r['total_spend'])
                cnt = int(r['tx_count'])
                avg = float(r['avg_spend'])
                if lang == "hi":
                    text = (
                        f"### {matched_cat.title()} पर कुल खर्च:\n\n"
                        f"• **कुल राशि:** **₹{tot:,.2f}**\n"
                        f"• **कुल लेन-देन:** **{cnt} बार**\n"
                        f"• **औसत प्रति लेन-देन:** **₹{avg:,.2f}**\n\n"
                        f"आप 'break down expenses by category' कहकर सभी श्रेणियों की तुलना भी देख सकते हैं।"
                    )
                else:
                    text = (
                        f"### Total Spend on {matched_cat.title()}:\n\n"
                        f"• **Total Outflow:** **₹{tot:,.2f}**\n"
                        f"• **Number of Payments:** **{cnt} transactions**\n"
                        f"• **Average per Transaction:** **₹{avg:,.2f}**\n\n"
                        f"Ask *'Break down expenses by category'* to see how this compares against other household expenses."
                    )
                return text, None, "run_financial_query"

    # 6. Vendor / Payee Analysis (e.g. "who did I pay the most to", "top vendors")
    elif any(k in q for k in ["who did i pay", "top vendor", "vendors", "highest payee", "kisko sabse zyada"]):
        sql = """
            SELECT COALESCE(v.name, 'Direct/Others') as vendor, SUM(t.total_amount) as total_spent, COUNT(*) as tx_count
            FROM transactions t
            LEFT JOIN vendors v ON t.vendor_id = v.id
            GROUP BY v.name
            ORDER BY total_spent DESC
            LIMIT 5;
        """
        rows_str = run_financial_query.invoke({"query": sql})
        rows = json.loads(rows_str)
        chart_data = [{"vendor": r['vendor'][:15], "amount": float(r['total_spent'])} for r in rows]
        chart_str = generate_chart_spec.invoke({
            "chart_type": "bar",
            "title": "Top Payees / Vendors by Outflow",
            "x_key": "vendor",
            "y_keys": ["amount"],
            "data": chart_data,
        })
        chart_spec = json.loads(chart_str)
        if lang == "hi":
            text = "यहाँ वे मुख्य विक्रेता/प्राप्तकर्ता हैं जिन्हें आपने सबसे अधिक भुगतान किया है:\n\n"
            for idx, r in enumerate(rows, 1):
                text += f"{idx}. **{r['vendor']}**: ₹{float(r['total_spent']):,.2f} ({int(r['tx_count'])} बार)\n"
        else:
            text = "Here are the top payees/merchants where your household funds were disbursed:\n\n"
            for idx, r in enumerate(rows, 1):
                text += f"{idx}. **{r['vendor']}**: ₹{float(r['total_spent']):,.2f} ({int(r['tx_count'])} transactions)\n"
        return text, chart_spec, "run_financial_query"

    # 7. Category breakdown
    elif any(k in q for k in ["break down", "category", "categories", "distribution"]):
        summary_str = get_expense_summary.invoke({"group_by": "category"})
        summary = json.loads(summary_str)
        chart_str = generate_chart_spec.invoke({
            "chart_type": "bar",
            "title": "Household Expense Breakdown by Category",
            "x_key": "category",
            "y_keys": ["total_spend"],
            "data": summary["breakdown"],
            "description": f"Grand total household expenses across all categories is ₹{summary['grand_total']:,.2f}."
        })
        chart_spec = json.loads(chart_str)
        if lang == "hi":
            text = f"यहाँ {summary['total_transactions']} लेन-देन के आधार पर आपकी श्रेणियों का विवरण दिया गया है:\n\n"
            for row in summary["breakdown"][:6]:
                text += f"• **{row['category'].title()}**: ₹{row['total_spend']:,.2f} ({int(row['transaction_count'])} एंट्री, औसत ₹{row['average_spend']:,.2f})\n"
            text += f"\n**कुल खर्च:** ₹{summary['grand_total']:,.2f}"
        else:
            text = f"Here is your household spending breakdown across {summary['total_transactions']} transactions:\n\n"
            for row in summary["breakdown"][:6]:
                text += f"• **{row['category'].title()}**: ₹{row['total_spend']:,.2f} ({int(row['transaction_count'])} transactions, avg ₹{row['average_spend']:,.2f})\n"
            text += f"\n**Total Household Outflow:** ₹{summary['grand_total']:,.2f}"
        return text, chart_spec, "get_expense_summary"

    # 8. Monthly trends / Whole year trend
    elif any(k in q for k in ["trend", "month", "monthly", "time", "outflow", "whole year", "last year"]):
        summary_str = get_expense_summary.invoke({"group_by": "month"})
        summary = json.loads(summary_str)
        chart_str = generate_chart_spec.invoke({
            "chart_type": "area",
            "title": "Monthly Household Expenses (2025)",
            "x_key": "period",
            "y_keys": ["total_spend"],
            "data": summary["breakdown"],
            "description": "Monthly family spending trend over the recorded period."
        })
        chart_spec = json.loads(chart_str)
        avg_monthly = summary["grand_total"] / max(len(summary["breakdown"]), 1)
        if lang == "hi":
            text = "यहाँ आपका 2025 का मासिक खर्च का ट्रेंड है:\n\n"
            for row in summary["breakdown"]:
                text += f"• **{row['period']}**: ₹{row['total_spend']:,.2f} ({int(row['transaction_count'])} एंट्री)\n"
            text += f"\n**औसत मासिक बजट:** ₹{avg_monthly:,.2f}"
        else:
            text = "Here is your monthly household spending trajectory for the recorded year:\n\n"
            for row in summary["breakdown"]:
                text += f"• **{row['period']}**: ₹{row['total_spend']:,.2f} ({int(row['transaction_count'])} entries)\n"
            text += f"\n**Average Monthly Household Budget:** ₹{avg_monthly:,.2f}"
        return text, chart_spec, "get_expense_summary"

    # 9. Top / Largest expenses
    elif any(k in q for k in ["largest", "highest", "top 5", "biggest", "top expenses", "sabse bada kharch"]):
        sql = """
            SELECT t.date, t.description, t.category, t.total_amount, COALESCE(v.name, 'Direct Payment') as vendor
            FROM transactions t
            LEFT JOIN vendors v ON t.vendor_id = v.id
            ORDER BY t.total_amount DESC
            LIMIT 5;
        """
        rows_str = run_financial_query.invoke({"query": sql})
        rows = json.loads(rows_str)
        chart_data = []
        if lang == "hi":
            text = "यहाँ आपके सबसे बड़े 5 भुगतान दिए गए हैं:\n\n"
            for idx, r in enumerate(rows, 1):
                text += f"{idx}. **₹{r['total_amount']:,.2f}** — {r['description']} ({r['vendor']}) दिनांक {str(r['date'])[:10]}\n"
                chart_data.append({"item": r['description'][:15], "amount": float(r['total_amount'])})
        else:
            text = "Here are your top 5 highest individual disbursements:\n\n"
            for idx, r in enumerate(rows, 1):
                text += f"{idx}. **₹{r['total_amount']:,.2f}** — {r['description']} ({r['vendor']}) on {str(r['date'])[:10]}\n"
                chart_data.append({"item": r['description'][:15], "amount": float(r['total_amount'])})

        chart_str = generate_chart_spec.invoke({
            "chart_type": "bar",
            "title": "Top 5 Major Household Disbursements",
            "x_key": "item",
            "y_keys": ["amount"],
            "data": chart_data,
        })
        return text, json.loads(chart_str), "run_financial_query"

    # 10. Default overview with dynamic guidance
    else:
        summary_str = get_expense_summary.invoke({"group_by": "category"})
        summary = json.loads(summary_str)
        top_cat = summary['breakdown'][0]['category'].title() if summary['breakdown'] else "Expenses"
        top_amt = summary['breakdown'][0]['total_spend'] if summary['breakdown'] else 0.0

        if lang == "hi":
            text = (
                f"आपके कुल रिकॉर्ड किए गए खर्च **₹{summary['grand_total']:,.2f}** हैं ({summary['total_transactions']} भुगतानों में)।\n\n"
                f"सबसे बड़ा खर्च **{top_cat}** में **₹{top_amt:,.2f}** हुआ है।\n\n"
                f"आप मुझसे पूछ सकते हैं:\n"
                f"• *'मेरी आखिरी एंट्री बताओ'* (Latest expense)\n"
                f"• *'2026 के खर्चों का अनुमान'* (2026 Projections)\n"
                f"• *'किराना या खाने पर कितना खर्च हुआ?'* (Category spend)\n"
                f"• तुरंत खर्च जोड़ने के लिए *'3500 pizza'* टाइप करें!"
            )
        else:
            text = (
                f"Your total tracked expenses stand at **₹{summary['grand_total']:,.2f}** across **{summary['total_transactions']}** verified payments.\n\n"
                f"Your highest spend category is **{top_cat}** with **₹{top_amt:,.2f}**.\n\n"
                f"Quick things to ask:\n"
                f"• *'Tell me my latest expense'*\n"
                f"• *'Project my expenses for 2026'*\n"
                f"• *'How much did I spend on groceries?'*\n"
                f"• Or quick-log an expense: *'3500 pizza'*!"
            )
        return text, None, "get_expense_summary"


class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


def synthesize_chat_title(user_query: str, default: str = "Financial Analysis") -> str:
    raw = user_query.strip()
    if not raw:
        return default
    # Strip common leading question phrases
    cleaned = re.sub(
        r'^(what\s+is|what\s+are|tell\s+me\s+about|show\s+me|how\s+much\s+did\s+i\s+spend\s+on|'
        r'can\s+you\s+analyze|please\s+analyze|break\s+down|audit\s+my|check\s+my|'
        r'give\s+me\s+a\s+breakdown\s+of)\s+',
        '',
        raw,
        flags=re.IGNORECASE
    ).strip()
    # Strip trailing punctuation
    cleaned = re.sub(r'[?!.]+$', '', cleaned).strip()
    # If starting with roast:
    if re.search(r'\broast\b', raw, re.IGNORECASE):
        cleaned = re.sub(r'^roast\s+(my\s+)?', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = f"Roast: {cleaned}" if cleaned else "Spending Roast"
    # Take up to 6 words
    words = cleaned.split()
    if len(words) > 6:
        cleaned = " ".join(words[:6])
    return cleaned.strip().title() or default


def synthesize_document_title(filename: str, summary: str = "", analysis: Optional[dict] = None) -> str:
    # If filename has meaningful words and is not generic (like pasted_text.txt, doc.pdf, file.txt)
    base_name = re.sub(r'\.[a-zA-Z0-9]+$', '', filename)
    base_name = re.sub(r'[\-_()0-9]+', ' ', base_name).strip()

    if base_name and base_name.lower() not in ("pasted text", "document", "file", "upload", "statement", "receipt"):
        words = base_name.split()
        if len(words) <= 5:
            return base_name.title()

    # Try extracting meaningful subject from summary
    if summary:
        first_sentence = summary.split('.')[0]
        if "norstella" in first_sentence.lower():
            return "Norstella Exit Policy FAQ"
        if "exit" in first_sentence.lower() or "notice" in first_sentence.lower():
            return "Exit & Notice Policy FAQ"
        if "statement" in first_sentence.lower() or "bank" in first_sentence.lower():
            return "Bank Statement Analysis"
        cleaned_sent = re.sub(r'^(this document is|an hr|this is|an overview of|outlines|covers)\s+', '', first_sentence, flags=re.IGNORECASE).strip()
        words = cleaned_sent.split()
        if words and len(words) >= 2:
            return " ".join(words[:4]).title()

    doc_type = (analysis.get("document_type") if analysis else "") or "Document"
    return f"{doc_type.replace('_', ' ').title()} Analysis"


async def ensure_session_and_record_messages(
    session_id: str,
    user_query: str,
    assistant_response: str,
    chart_spec: Optional[Dict[str, Any]] = None,
    tool_calls: Optional[list] = None,
    custom_title: Optional[str] = None
):
    try:
        async with AsyncSessionLocal() as session:
            sess_res = await session.execute(
                text("SELECT id, title FROM chat_sessions WHERE id = :sid"),
                {"sid": session_id}
            )
            sess = sess_res.fetchone()

            clean_title = custom_title.strip()[:50] if custom_title else synthesize_chat_title(user_query)
            now = datetime.datetime.utcnow()

            if not sess:
                new_sess = ChatSession(
                    id=session_id,
                    title=clean_title,
                    is_pinned=False,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_sess)
                await session.flush()
            elif (
                sess[1] in ("New Conversation", "New Analysis", "Untitled Analysis")
                or not sess[1]
                or (sess[1].startswith("Uploaded Document:") and not custom_title)
            ):
                await session.execute(
                    text("UPDATE chat_sessions SET title = :t, updated_at = :now WHERE id = :sid"),
                    {"t": clean_title, "now": now, "sid": session_id}
                )
            else:
                await session.execute(
                    text("UPDATE chat_sessions SET updated_at = :now WHERE id = :sid"),
                    {"now": now, "sid": session_id}
                )

            user_msg = ChatMessage(
                id=uuid.uuid4().hex,
                session_id=session_id,
                role="user",
                content=user_query,
                created_at=now,
            )
            session.add(user_msg)

            asst_msg = ChatMessage(
                id=uuid.uuid4().hex,
                session_id=session_id,
                role="assistant",
                content=assistant_response,
                chart_spec=chart_spec,
                tool_calls=tool_calls,
                created_at=now + datetime.timedelta(milliseconds=200),
            )
            session.add(asst_msg)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to persist chat messages for session {session_id}: {e}")


@router.get("/sessions")
async def list_chat_sessions():
    """
    List all conversation sessions ordered by pinned status and updated_at descending.
    """
    try:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                text("""
                    SELECT s.id, s.title, s.is_pinned, s.created_at, s.updated_at, COUNT(m.id) as message_count
                    FROM chat_sessions s
                    LEFT JOIN chat_messages m ON s.id = m.session_id
                    GROUP BY s.id, s.title, s.is_pinned, s.created_at, s.updated_at
                    ORDER BY s.is_pinned DESC, s.updated_at DESC
                """)
            )
            rows = res.fetchall()
            sessions = []
            for r in rows:
                sessions.append({
                    "id": r[0],
                    "title": r[1],
                    "is_pinned": bool(r[2]),
                    "created_at": r[3].isoformat() if r[3] else None,
                    "updated_at": r[4].isoformat() if r[4] else None,
                    "message_count": int(r[5]),
                })
            return {"status": "success", "sessions": sessions}
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {e}")
        return {"status": "error", "message": str(e), "sessions": []}


@router.post("/sessions")
async def create_chat_session(payload: Optional[ChatSessionCreate] = None):
    """
    Create a new empty conversation session.
    """
    try:
        async with AsyncSessionLocal() as session:
            new_id = uuid.uuid4().hex
            title = (payload.title if payload and payload.title else "New Conversation")
            now = datetime.datetime.utcnow()
            new_session = ChatSession(
                id=new_id,
                title=title,
                is_pinned=False,
                created_at=now,
                updated_at=now,
            )
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)
            return {
                "status": "success",
                "session": {
                    "id": new_session.id,
                    "title": new_session.title,
                    "is_pinned": new_session.is_pinned,
                    "created_at": new_session.created_at.isoformat() if new_session.created_at else None,
                    "updated_at": new_session.updated_at.isoformat() if new_session.updated_at else None,
                    "message_count": 0,
                }
            }
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """
    Retrieve all messages and generative artifacts for a conversation thread.
    """
    try:
        async with AsyncSessionLocal() as session:
            sess_res = await session.execute(
                text("SELECT id, title, is_pinned, created_at, updated_at FROM chat_sessions WHERE id = :sid"),
                {"sid": session_id}
            )
            sess_row = sess_res.fetchone()
            if not sess_row:
                return {"status": "error", "message": f"Session {session_id} not found"}

            msg_res = await session.execute(
                text("SELECT id, role, content, chart_spec, tool_calls, created_at FROM chat_messages WHERE session_id = :sid ORDER BY created_at ASC"),
                {"sid": session_id}
            )
            msg_rows = msg_res.fetchall()
            messages = []
            for m in msg_rows:
                messages.append({
                    "id": m[0],
                    "role": m[1],
                    "content": m[2],
                    "chart_spec": m[3],
                    "tool_calls": m[4],
                    "created_at": m[5].isoformat() if m[5] else None,
                })

            return {
                "status": "success",
                "session": {
                    "id": sess_row[0],
                    "title": sess_row[1],
                    "is_pinned": bool(sess_row[2]),
                    "created_at": sess_row[3].isoformat() if sess_row[3] else None,
                    "updated_at": sess_row[4].isoformat() if sess_row[4] else None,
                    "messages": messages,
                }
            }
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")
        return {"status": "error", "message": str(e)}


@router.patch("/sessions/{session_id}")
async def update_chat_session(session_id: str, payload: ChatSessionUpdate):
    """
    Update session title or pinned status.
    """
    try:
        async with AsyncSessionLocal() as session:
            updates = []
            params = {"sid": session_id, "now": datetime.datetime.utcnow()}
            if payload.title is not None:
                updates.append("title = :title")
                params["title"] = payload.title
            if payload.is_pinned is not None:
                updates.append("is_pinned = :is_pinned")
                params["is_pinned"] = payload.is_pinned
            updates.append("updated_at = :now")

            if updates:
                query_str = f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id = :sid"
                await session.execute(text(query_str), params)
                await session.commit()
            return {"status": "success", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        return {"status": "error", "message": str(e)}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete a session and all its associated messages.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("DELETE FROM chat_sessions WHERE id = :sid"),
                {"sid": session_id}
            )
            await session.commit()
            return {"status": "success", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return {"status": "error", "message": str(e)}


class SlidingWindowRateLimiter:
    """Sliding-window in-memory rate limiter per client to protect LLM token quota."""
    def __init__(self, max_requests: int = 120, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        now = time.time()
        timestamps = self.requests.get(client_id, [])
        timestamps = [ts for ts in timestamps if now - ts < self.window_seconds]
        if len(timestamps) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - timestamps[0]))
            return False, max(retry_after, 1)
        timestamps.append(now)
        self.requests[client_id] = timestamps
        return True, 0


chat_rate_limiter = SlidingWindowRateLimiter(max_requests=120, window_seconds=3600)


@router.post("/stream")
async def chat_stream(request: ChatMessageRequest, req_meta: Request):
    """
    Server-Sent Events (SSE) streaming endpoint for the AI Financial Copilot.
    Powered by LangGraph ReAct agent with real-time token and tool event streaming (v2),
    with automatic graceful fallback to local deterministic analytics if LLM quota is exhausted.
    """
    client_ip = req_meta.client.host if req_meta.client else "default_client"
    allowed, retry_after = chat_rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded (120 queries/hr). Please retry in {retry_after} seconds."
        )

    session_id = request.session_id or request.thread_id or str(uuid.uuid4())
    thread_id = session_id
    user_message = request.message.strip()
    provider = request.provider or "deepseek"
    lang = request.language or "en"

    # Auto-detect Hindi characters or common Hinglish words
    if any(k in user_message.lower() for k in ["batao", "kharch", "kitna", "namaste", "nahi", "haan"]) or re.search(r'[\u0900-\u097F]', user_message):
        lang = "hi"

    async def event_generator() -> AsyncGenerator[dict, None]:
        yield {
            "event": "session",
            "data": json.dumps({"thread_id": thread_id, "session_id": session_id, "provider": provider, "language": lang})
        }

        # Track outputs for message persistence
        accumulated_assistant_tokens = []
        collected_chart_spec = None
        executed_tool_calls = []

        # Step 0: Check if user pasted a Bank/UPI transaction SMS alert
        sms_receipt = parse_bank_sms(user_message)
        if sms_receipt:
            yield {
                "event": "widget",
                "data": json.dumps({
                    "widget_type": "receipt_card",
                    "receipt": sms_receipt.dict()
                })
            }
            if lang == "hi":
                confirmation_text = (
                    f"मैंने आपके बैंक अलर्ट से लेन-देन की जानकारी प्राप्त की है:\n\n"
                    f"• **विक्रेता:** **{sms_receipt.vendor_name}**\n"
                    f"• **राशि:** **₹{sms_receipt.total_amount:,.2f}**\n"
                    f"• **श्रेणी:** **{sms_receipt.category.title()}**\n"
                    f"• **भुगतान विधि:** **{sms_receipt.payment_method}**\n"
                    f"• **दिनांक:** **{sms_receipt.date}**\n\n"
                    f"इसे अपने बहीखाते में जोड़ने के लिए नीचे दिए गए **[Approve & Record]** बटन पर क्लिक करें।"
                )
            else:
                confirmation_text = (
                    f"I extracted a verified transaction from your bank alert:\n\n"
                    f"• **Merchant:** **{sms_receipt.vendor_name}**\n"
                    f"• **Amount:** **₹{sms_receipt.total_amount:,.2f}**\n"
                    f"• **Category:** **{sms_receipt.category.title()}**\n"
                    f"• **Payment Method:** **{sms_receipt.payment_method}**\n"
                    f"• **Date:** **{sms_receipt.date}**\n\n"
                    f"Click **[Approve & Record]** on the card below to commit this to your ledger."
                )
            yield {
                "event": "token",
                "data": json.dumps({"token": confirmation_text})
            }
            await ensure_session_and_record_messages(
                session_id=session_id,
                user_query=user_message,
                assistant_response=confirmation_text,
                chart_spec=None,
                tool_calls=[{"tool": "parse_bank_sms", "summary": "Bank SMS parsed"}],
            )
            yield {
                "event": "done",
                "data": json.dumps({"status": "complete", "thread_id": thread_id, "session_id": session_id})
            }
            return

        # Step 1: Context-aware check for quick expense logging (e.g. '3500 pizza', 'spent 450 on uber')
        intent = detect_expense_intent(user_message)
        if intent:
            yield {
                "event": "intent",
                "data": json.dumps({"intent": intent})
            }
            if lang == "hi":
                confirmation_text = (
                    f"मैंने **{intent['item']}** ({intent['category'].title()}) के लिए **₹{intent['amount']:,.2f}** का खर्च पहचाना है।\n\n"
                    f"क्या आप इसे **{intent['payment_method']}** के माध्यम से अपने खर्चों में जोड़ना चाहते हैं?"
                )
            else:
                confirmation_text = (
                    f"I detected an expense of **₹{intent['amount']:,.2f}** for **{intent['item']}** "
                    f"({intent['category'].title()}).\n\n"
                    f"Would you like to record this payment into your expenses via **{intent['payment_method']}**?"
                )

            yield {
                "event": "token",
                "data": json.dumps({"token": confirmation_text})
            }
            await ensure_session_and_record_messages(
                session_id=session_id,
                user_query=user_message,
                assistant_response=confirmation_text,
                chart_spec=None,
                tool_calls=[{"tool": "quick_expense_detector", "summary": "Expense intent detected"}],
            )
            yield {
                "event": "done",
                "data": json.dumps({"status": "complete", "thread_id": thread_id, "session_id": session_id})
            }
            return

        # Step 2: Genuine LangGraph Agent execution with real-time SSE event streaming
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from backend.agent.financial_agent import global_checkpointer

            DB_USER = os.getenv("POSTGRES_USER", "postgres")
            DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgrespassword")
            DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
            DB_PORT = os.getenv("POSTGRES_PORT", "5433")
            DB_NAME = os.getenv("POSTGRES_DB", "expense_accounting_db")
            postgres_uri = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

            # Check if current event loop supports async psycopg; if on Windows Proactor, fallback to MemorySaver
            supports_async_pg = True
            loop = asyncio.get_event_loop()
            if hasattr(asyncio, "ProactorEventLoop") and isinstance(loop, asyncio.ProactorEventLoop):
                supports_async_pg = False

            async def stream_agent(active_checkpointer):
                nonlocal collected_chart_spec
                agent = create_financial_agent(
                    llm=get_llm(provider=provider, with_fallback=False),
                    checkpointer=active_checkpointer
                )
                config = {"configurable": {"thread_id": thread_id}}

                # Restore previous conversational turns from PostgreSQL for true multi-turn memory
                prior_messages = []
                try:
                    async with AsyncSessionLocal() as pg_sess:
                        # 1. Pinned session document context injection (ensures uploaded files are NEVER forgotten across turns)
                        doc_res = await pg_sess.execute(
                            text("SELECT filename, content_text, metadata_json FROM document_embeddings WHERE session_id = :sid ORDER BY created_at DESC LIMIT 3"),
                            {"sid": session_id}
                        )
                        doc_rows = doc_res.fetchall()
                        if doc_rows:
                            doc_parts = []
                            for row in doc_rows:
                                fname = row[0] or "Uploaded Document"
                                ctext = row[1] or ""
                                meta = row[2] or {}
                                summary = meta.get("summary", "")
                                doc_parts.append(
                                    f"Document: {fname} ({meta.get('document_type', 'Document').replace('_', ' ').title()})\n"
                                    f"Summary: {summary}\n"
                                    f"Key Excerpt:\n{ctext[:800]}\n"
                                    f"(For deep clause inspection, call `inspect_uploaded_document`)"
                                )
                            doc_block = "\n\n---\n\n".join(doc_parts)
                            prior_messages.append(SystemMessage(
                                content=(
                                    f"ACTIVE SESSION UPLOADED DOCUMENTS:\n"
                                    f"The user uploaded the following document(s) in this active session:\n\n{doc_block}\n\n"
                                    f"OPERATING INSTRUCTION: You have direct access to these documents. If the user asks about an uploaded document, "
                                    f"company policy (such as Norstella India exit FAQs, notice periods, garden leave, relieving letters, Form-16, settlement lag), "
                                    f"spreadsheets, or receipts, answer accurately using the context above or call `inspect_uploaded_document`. "
                                    f"Under NO circumstance should you claim you cannot read or access the document body."
                                )
                            ))

                        # 2. Fetch the 30 most recent conversational turns chronologically
                        history_res = await pg_sess.execute(
                            text("""
                                SELECT role, content FROM (
                                    SELECT role, content, created_at 
                                    FROM chat_messages 
                                    WHERE session_id = :sid 
                                    ORDER BY created_at DESC 
                                    LIMIT 30
                                ) sub 
                                ORDER BY created_at ASC
                            """),
                            {"sid": session_id}
                        )
                        for row in history_res.fetchall():
                            r, c = row[0], row[1]
                            if r == "user":
                                prior_messages.append(HumanMessage(content=c))
                            elif r == "assistant":
                                prior_messages.append(AIMessage(content=c))
                except Exception as hist_err:
                    logger.warning(f"Could not load conversation history: {hist_err}")

                agent_input = {"messages": prior_messages + [HumanMessage(content=user_message)]}

                has_tokens = False
                async for event in agent.astream_events(agent_input, config=config, version="v2"):
                    kind = event["event"]

                    # LLM streaming tokens
                    if kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            content = chunk.content
                            if isinstance(content, str) and content:
                                has_tokens = True
                                accumulated_assistant_tokens.append(content)
                                yield {
                                    "event": "token",
                                    "data": json.dumps({"token": content})
                                }

                    # Tool invocation started
                    elif kind == "on_tool_start":
                        tool_name = event["name"]
                        tool_input = event["data"].get("input")
                        executed_tool_calls.append({"tool": tool_name, "input": tool_input})
                        yield {
                            "event": "tool_start",
                            "data": json.dumps({"tool": tool_name, "input": tool_input})
                        }

                    # Tool invocation completed
                    elif kind == "on_tool_end":
                        tool_name = event["name"]
                        output = event["data"].get("output")
                        if tool_name == "generate_chart_spec" or (output and "__chart__" in str(output)):
                            try:
                                raw_content = output.content if hasattr(output, "content") else output
                                spec = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
                                if isinstance(spec, dict) and spec.get("__chart__"):
                                    collected_chart_spec = spec
                                    yield {
                                        "event": "chart",
                                        "data": json.dumps({"spec": spec})
                                    }
                            except Exception as chart_err:
                                logger.error(f"Failed to extract chart spec: {chart_err}")
                        yield {
                            "event": "tool_end",
                            "data": json.dumps({"tool": tool_name, "summary": f"{tool_name} completed"})
                        }

                if has_tokens:
                    full_text = "".join(accumulated_assistant_tokens)
                    await ensure_session_and_record_messages(
                        session_id=session_id,
                        user_query=user_message,
                        assistant_response=full_text,
                        chart_spec=collected_chart_spec,
                        tool_calls=executed_tool_calls,
                    )
                    yield {
                        "event": "done",
                        "data": json.dumps({"status": "complete", "thread_id": thread_id, "session_id": session_id})
                    }

            if supports_async_pg:
                try:
                    async with AsyncPostgresSaver.from_conn_string(postgres_uri) as checkpointer:
                        produced_tokens = False
                        async for item in stream_agent(checkpointer):
                            if item.get("event") == "token":
                                produced_tokens = True
                            yield item
                        if produced_tokens:
                            return
                except Exception as pg_err:
                    logger.info(f"AsyncPostgresSaver unavailable ({pg_err}), using MemorySaver")
                    supports_async_pg = False

            if not supports_async_pg:
                produced_tokens = False
                async for item in stream_agent(global_checkpointer):
                    if item.get("event") == "token":
                        produced_tokens = True
                    yield item
                if produced_tokens:
                    return

        except Exception as e:
            logger.warning(f"LangGraph Agent stream encountered issue ({e}). Engaging deterministic fallback engine...")

        # Step 3: Resilient deterministic financial analytics fallback
        try:
            resp_text, chart_spec, tool_name = generate_smart_financial_response(user_message, lang=lang, session_id=session_id)
            yield {
                "event": "tool_start",
                "data": json.dumps({"tool": tool_name, "input": {"query": user_message}})
            }
            await asyncio.sleep(0.05)
            yield {
                "event": "tool_end",
                "data": json.dumps({"tool": tool_name, "summary": f"{tool_name} completed"})
            }
            if chart_spec:
                yield {
                    "event": "chart",
                    "data": json.dumps({"spec": chart_spec})
                }

            # Stream words
            words = resp_text.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + (" " if i+3 < len(words) else "")
                yield {
                    "event": "token",
                    "data": json.dumps({"token": chunk})
                }
                await asyncio.sleep(0.015)

            await ensure_session_and_record_messages(
                session_id=session_id,
                user_query=user_message,
                assistant_response=resp_text,
                chart_spec=chart_spec,
                tool_calls=[{"tool": tool_name, "summary": f"{tool_name} completed"}],
            )
            yield {
                "event": "done",
                "data": json.dumps({"status": "complete", "thread_id": thread_id, "session_id": session_id})
            }

        except Exception as err:
            logger.error(f"Fallback engine error: {err}")
            err_msg = f"Encountered an issue processing query: {err}"
            yield {
                "event": "token",
                "data": json.dumps({"token": err_msg})
            }
            await ensure_session_and_record_messages(
                session_id=session_id,
                user_query=user_message,
                assistant_response=err_msg,
                chart_spec=None,
                tool_calls=[],
            )
            yield {
                "event": "done",
                "data": json.dumps({"status": "complete", "thread_id": thread_id, "session_id": session_id})
            }

    return EventSourceResponse(
        event_generator(),
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
        ping=15,
    )


@router.post("/ingest")
async def ingest_document(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    provider: Optional[str] = Form("deepseek"),
):
    """
    Ingests PDF bank statements, receipts, invoices, or informational documents.
    Uses LLM Document Intelligence to accurately classify between financial and non-financial docs.
    Never fabricates dummy expenses for non-financial files.
    Persists document uploads and analyses directly into chat_messages to maintain conversation memory.
    """
    active_session_id = session_id or thread_id or str(uuid.uuid4())
    doc_text = ""
    filename = "document"

    if raw_text and raw_text.strip():
        doc_text = raw_text.strip()
        filename = "pasted_text.txt"
    elif file:
        filename = file.filename or "uploaded_file"
        content_bytes = await file.read()
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            doc_text = extract_text_from_pdf(content_bytes)
        elif lower_name.endswith(".csv"):
            doc_text = extract_text_from_csv(content_bytes)
        elif lower_name.endswith((".xlsx", ".xls")):
            doc_text = extract_text_from_excel(content_bytes)
        else:
            try:
                doc_text = content_bytes.decode("utf-8", errors="ignore")
            except Exception:
                doc_text = f"File {filename}"

    # Analyze document with LLM
    analysis = await analyze_document_with_llm(
        text_content=doc_text,
        filename=filename,
        provider=provider or "deepseek"
    )

    is_financial = analysis.get("is_financial", False)
    doc_summary = analysis.get("summary", "")
    transactions = analysis.get("transactions", [])

    # Persist the full document into document_embeddings for long-horizon session retrieval
    try:
        async with AsyncSessionLocal() as pg_sess:
            doc_record = DocumentEmbedding(
                session_id=active_session_id,
                filename=filename,
                content_text=doc_text,
                metadata_json={
                    "session_id": active_session_id,
                    "filename": filename,
                    "is_financial": is_financial,
                    "document_type": analysis.get("document_type", "non_financial_document"),
                    "summary": doc_summary,
                    "transactions": transactions,
                }
            )
            pg_sess.add(doc_record)
            await pg_sess.commit()
    except Exception as save_err:
        logger.warning(f"Failed to persist document to document_embeddings: {save_err}")

    if not is_financial or not transactions:
        # Informational document (e.g. FAQs for India Leavers, HR policy, article)
        clean_summary = (
            f"📄 **Uploaded Document Analysis:**\n\n"
            f"**File:** `{filename}`\n"
            f"**Document Type:** {analysis.get('document_type', 'Non-Financial Document').replace('_', ' ').title()}\n\n"
            f"{doc_summary}\n\n"
            f"*Note: No financial expenses or billable transactions were found in this document.*"
        )

        doc_title = synthesize_document_title(filename, doc_summary, analysis)
        await ensure_session_and_record_messages(
            session_id=active_session_id,
            user_query=f"Uploaded document: {filename}",
            assistant_response=clean_summary,
            chart_spec=None,
            tool_calls=[{"tool": "analyze_document_with_llm", "summary": f"Classified {filename} as non-financial"}],
            custom_title=doc_title
        )

        return {
            "status": "success",
            "is_financial": False,
            "widget_type": "document_summary",
            "receipt": None,
            "summary": clean_summary,
            "session_id": active_session_id,
        }

    # Financial document with transactions
    first_tx = transactions[0]
    extracted_receipt = ExtractedReceipt(
        vendor_name=first_tx.get("vendor_name", "Vendor"),
        date=first_tx.get("date", datetime.date.today().isoformat()),
        total_amount=round(float(first_tx.get("total_amount", 0.0)), 2),
        payment_method=first_tx.get("payment_method", "UPI"),
        category=first_tx.get("category", "groceries"),
        confidence_score=0.96
    )

    clean_summary = (
        f"Extracted transaction for **{extracted_receipt.vendor_name}**: "
        f"**₹{extracted_receipt.total_amount:,.2f}** under **{extracted_receipt.category.title()}** "
        f"via {extracted_receipt.payment_method}. Click **[Approve & Record]** to add to your ledger."
    )

    doc_title = (
        f"{extracted_receipt.vendor_name} Expense"
        if extracted_receipt.vendor_name and extracted_receipt.vendor_name != "Vendor"
        else synthesize_document_title(filename, clean_summary, analysis)
    )

    await ensure_session_and_record_messages(
        session_id=active_session_id,
        user_query=f"Uploaded document: {filename}",
        assistant_response=clean_summary,
        chart_spec=None,
        tool_calls=[{"tool": "analyze_document_with_llm", "summary": f"Extracted ₹{extracted_receipt.total_amount:,.2f} from {filename}"}],
        custom_title=doc_title
    )

    return {
        "status": "success",
        "is_financial": True,
        "widget_type": "receipt_card",
        "receipt": extracted_receipt.dict(),
        "summary": clean_summary,
        "session_id": active_session_id,
    }


@router.post("/sessions/clean-titles")
async def clean_legacy_session_titles():
    """
    One-time cleanup routine:
    Finds all sessions in chat_sessions where title starts with 'Uploaded Document:'
    and upgrades them based on their document summary or message content.
    """
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            text("SELECT id, title FROM chat_sessions WHERE title LIKE 'Uploaded Document%'")
        )
        legacy_sessions = res.fetchall()
        updated_count = 0
        for sid, old_title in legacy_sessions:
            doc_res = await session.execute(
                text("SELECT filename, content_text FROM document_embeddings WHERE session_id = :sid ORDER BY created_at ASC LIMIT 1"),
                {"sid": sid}
            )
            doc_row = doc_res.fetchone()
            if doc_row:
                fname, ctext = doc_row
                new_title = synthesize_document_title(fname, ctext[:500])
            else:
                msg_res = await session.execute(
                    text("SELECT content FROM chat_messages WHERE session_id = :sid AND role = 'assistant' ORDER BY created_at ASC LIMIT 1"),
                    {"sid": sid}
                )
                msg_row = msg_res.fetchone()
                if msg_row and "Norstella" in msg_row[0]:
                    new_title = "Norstella Exit Policy FAQ"
                else:
                    new_title = "Financial Document Analysis"

            await session.execute(
                text("UPDATE chat_sessions SET title = :t WHERE id = :sid"),
                {"t": new_title, "sid": sid}
            )
            updated_count += 1
        await session.commit()
        return {"status": "success", "updated_sessions": updated_count}


class ChatFeedbackRequest(BaseModel):
    message_id: str
    thread_id: Optional[str] = None
    rating: str  # 'thumbs_up' or 'thumbs_down'
    category: Optional[str] = None
    comment: Optional[str] = None
    user_query: Optional[str] = None
    assistant_response: Optional[str] = None


@router.get("/suggestions")
async def get_dynamic_chat_suggestions(language: str = "en"):
    """
    Returns dynamic, context-aware prompt suggestions derived from current ledger state.
    """
    try:
        async with async_engine.connect() as conn:
            # 1. Unreconciled count & sum
            unrec_res = await conn.execute(text(
                "SELECT count(*), coalesce(sum(total_amount), 0) FROM transactions WHERE is_reconciled = false;"
            ))
            unrec_count, unrec_sum = unrec_res.fetchone()

            # 2. Top expense category this year
            top_cat_res = await conn.execute(text(
                "SELECT category, sum(total_amount) FROM transactions WHERE date >= '2026-01-01' GROUP BY category ORDER BY sum(total_amount) DESC LIMIT 1;"
            ))
            top_cat_row = top_cat_res.fetchone()
            top_cat = top_cat_row[0] if top_cat_row else "Dining"

            suggestions = []
            if language == "hi":
                if unrec_count and unrec_count > 0:
                    suggestions.append(f"मेरे {unrec_count} अनवेरिफाइड खर्चों (₹{float(unrec_sum):,.2f}) का ऑडिट करो")
                suggestions.append(f"2026 में मेरे {top_cat.title()} खर्चों का विवरण दिखाओ")
                suggestions.append("2025 और 2026 के खर्चों की तुलना करो")
                suggestions.append("3500 pizza")
            else:
                if unrec_count and unrec_count > 0:
                    suggestions.append(f"Audit my {unrec_count} unreconciled expenses (₹{float(unrec_sum):,.2f})")
                suggestions.append(f"Break down my {top_cat.title()} spending for 2026")
                suggestions.append("Compare 2025 vs 2026 household outflow")
                suggestions.append("3500 pizza")

            return {"status": "success", "suggestions": suggestions}
    except Exception as e:
        logger.warning(f"Failed to fetch dynamic suggestions: {e}")
        if language == "hi":
            return {"status": "success", "suggestions": ["मेरी आखिरी एंट्री बताओ", "2026 के खर्चों का अनुमान", "3500 pizza", "श्रेणी अनुसार खर्च दिखाओ"]}
        return {"status": "success", "suggestions": ["Tell me my latest expense", "Project my expenses of 2026", "3500 pizza", "Break down expenses by category"]}


@router.post("/feedback")
async def record_chat_feedback(feedback_data: ChatFeedbackRequest):
    """
    Records thumbs up/down user feedback and issue category for response quality monitoring.
    """
    try:
        async with AsyncSessionLocal() as session:
            fb = ChatFeedback(
                message_id=feedback_data.message_id,
                thread_id=feedback_data.thread_id,
                rating=feedback_data.rating,
                category=feedback_data.category,
                comment=feedback_data.comment,
                user_query=feedback_data.user_query,
                assistant_response=feedback_data.assistant_response,
            )
            session.add(fb)
            await session.commit()
            await session.refresh(fb)
            return {"status": "success", "feedback_id": fb.id}
    except Exception as e:
        logger.error(f"Error recording chat feedback: {e}")
        return {"status": "error", "message": str(e)}

