import re
import datetime
import io
import json
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from backend.database.connection import sync_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = 1.0
    unit_price: Optional[float] = None
    total_price: float


class ExtractedReceipt(BaseModel):
    vendor_name: str = Field(description="Merchant or vendor name")
    date: str = Field(description="Transaction date in YYYY-MM-DD format")
    total_amount: float = Field(description="Total monetary amount paid in INR (₹)")
    tax_amount: Optional[float] = Field(default=0.0, description="GST / VAT / Sales tax")
    payment_method: str = Field(default="UPI", description="Payment method: UPI, Credit Card, Debit Card, Net Banking, Cash")
    category: str = Field(default="groceries", description="Expense category e.g. dining, groceries, utilities, transportation, rent, healthcare, entertainment, subscriptions")
    invoice_number: Optional[str] = Field(default=None, description="Invoice or bill reference number")
    line_items: List[LineItem] = Field(default_factory=list, description="Itemized receipt line items")
    confidence_score: float = Field(default=0.95, description="Confidence score between 0 and 1")


def infer_category(vendor: str, text: str = "") -> str:
    """Infers appropriate household expense category based on vendor and context."""
    combined = (vendor + " " + text).lower()
    if any(k in combined for k in ["swiggy", "zomato", "mcdonald", "starbucks", "pizza", "burger", "cafe", "restaurant", "dining", "food", "tea", "chai", "coffee"]):
        return "dining"
    elif any(k in combined for k in ["blinkit", "zepto", "instamart", "bigbasket", "dmart", "kirana", "ration", "grocery", "groceries", "milk", "vegetable"]):
        return "groceries"
    elif any(k in combined for k in ["uber", "ola", "rapido", "petrol", "fuel", "diesel", "metro", "auto", "irctc", "flight", "indigo", "transport"]):
        return "transportation"
    elif any(k in combined for k in ["bescom", "electricity", "power", "water", "gas", "cylinder", "lpg", "png", "wifi", "broadband", "jio", "airtel", "bill"]):
        return "utilities"
    elif any(k in combined for k in ["rent", "maintenance", "society", "flat", "apartment", "maid", "cook"]):
        return "rent"
    elif any(k in combined for k in ["pharmacy", "apollo", "1mg", "hospital", "clinic", "doctor", "medicine", "health"]):
        return "healthcare"
    elif any(k in combined for k in ["netflix", "prime", "hotstar", "spotify", "youtube", "movie", "bookmyshow", "cinema", "entertainment"]):
        return "entertainment"
    elif any(k in combined for k in ["school", "college", "tuition", "course", "udemy", "coursera", "books"]):
        return "subscriptions"
    return "groceries"


def parse_bank_sms(sms_text: str) -> Optional[ExtractedReceipt]:
    """
    Parses Indian Bank / UPI transaction alerts (HDFC, SBI, ICICI, Axis, Paytm, PhonePe, GPay, Cred, Kotak, etc.).
    Example inputs:
    - 'HDFC Bank: Rs 450.00 debited from a/c **1234 at SWIGGY on 29-OCT-26 via UPI. Bal Rs 45,210.00'
    - 'Dear SBI User, your A/C ending with 5678 debited by INR 3,500.00 on 29-10-2026 transfer to Pizza Hut ref no 123456789'
    - 'Paid Rs.120.00 to Chai Point on 29 Oct via PhonePe UPI.'
    """
    t = sms_text.strip()

    # Must contain a debit or payment indicator
    if not re.search(r'\b(debited|paid|spent|sent|transferred|purchase|withdrawn|dr)\b', t, re.I):
        return None

    # Amount extraction: captures Rs, Rs., INR, ₹ followed by number
    amt_match = re.search(r'(?:rs\.?|inr|₹)\s*([\d,]+(?:\.\d{1,2})?)', t, re.I)
    if not amt_match:
        # Fallback: number followed by debited/paid
        amt_match = re.search(r'([\d,]+(?:\.\d{1,2})?)\s*(?:rs\.?|inr|₹)', t, re.I)

    if not amt_match:
        return None

    raw_amt = amt_match.group(1).replace(",", "")
    try:
        amount = float(raw_amt)
    except ValueError:
        return None

    if amount <= 0:
        return None

    # Vendor / Payee extraction: looks for 'at <Vendor>', 'to <Vendor>', 'vpa <Vendor>', 'info: <Vendor>'
    vendor = "Unknown Merchant"
    v_match = re.search(r'(?:at|to|info[:\s]|towards|vpa[:\s])\s+([a-zA-Z0-9\s&\'\.-]+?)(?=\s+(?:on|via|ref|bal|using|from|avbl|avl|\.|\,|$))', t, re.I)
    if v_match:
        cand = v_match.group(1).strip()
        # Clean common noise words
        cand = re.sub(r'^(a/c|vpa|the)\s+', '', cand, flags=re.I).strip()
        cand = re.sub(r'\s+(electricity bill|water bill|bill|upi|ref|no)$', '', cand, flags=re.I).strip()
        if len(cand) >= 2 and not cand.lower().startswith("a/c"):
            vendor = cand.title()
    else:
        # Look for merchant name before ref/upi
        alt_match = re.search(r'(?:transfer to|paid to)\s+([a-zA-Z0-9\s&]+)', t, re.I)
        if alt_match:
            cand = alt_match.group(1).strip()
            cand = re.sub(r'\s+(electricity bill|water bill|bill|upi|ref|no)$', '', cand, flags=re.I).strip()
            vendor = cand.title()

    # Payment Method extraction
    payment_method = "UPI"
    if re.search(r'\b(credit card|card ending|cc)\b', t, re.I):
        payment_method = "Credit Card"
    elif re.search(r'\b(debit card|dc)\b', t, re.I):
        payment_method = "Debit Card"
    elif re.search(r'\b(netbanking|neft|rtgs|imps)\b', t, re.I):
        payment_method = "Net Banking"
    elif re.search(r'\b(phonepe)\b', t, re.I):
        payment_method = "PhonePe"
    elif re.search(r'\b(paytm)\b', t, re.I):
        payment_method = "Paytm"
    elif re.search(r'\b(gpay|google pay)\b', t, re.I):
        payment_method = "GPay"
    elif re.search(r'\b(upi)\b', t, re.I):
        payment_method = "UPI"

    # Date extraction
    today_str = datetime.date.today().isoformat()
    date_str = today_str

    # Date patterns: DD-MM-YYYY, DD/MM/YYYY, DD-Mon-YY (e.g. 29-OCT-26)
    d1 = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b', t)
    d2 = re.search(r'\b(\d{1,2})[- ]([a-zA-Z]{3})[- ](\d{2,4})\b', t)

    if d1:
        day, month, year = int(d1.group(1)), int(d1.group(2)), int(d1.group(3))
        if year < 100:
            year += 2000
        try:
            date_str = datetime.date(year, month, day).isoformat()
        except Exception:
            date_str = today_str
    elif d2:
        day = int(d2.group(1))
        m_name = d2.group(2).title()
        year = int(d2.group(3))
        if year < 100:
            year += 2000
        try:
            d_obj = datetime.datetime.strptime(f"{day}-{m_name}-{year}", "%d-%b-%Y").date()
            date_str = d_obj.isoformat()
        except Exception:
            date_str = today_str

    # Category inference
    category = infer_category(vendor, t)

    return ExtractedReceipt(
        vendor_name=vendor,
        date=date_str,
        total_amount=round(amount, 2),
        payment_method=payment_method,
        category=category,
        confidence_score=0.96
    )


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text content from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        full_text = []
        for page in reader.pages[:10]:  # limit to top 10 pages for statement safety
            text = page.extract_text()
            if text:
                full_text.append(text)
        return "\n".join(full_text)
    except Exception as e:
        return f"PDF Extraction Error: {str(e)}"


def extract_text_from_csv(csv_bytes: bytes) -> str:
    """Extracts and formats tabular data from a CSV file using pandas."""
    try:
        import pandas as pd
        df = pd.read_csv(io.BytesIO(csv_bytes))
        rows, cols = df.shape
        col_names = ", ".join(df.columns.astype(str))
        sample_rows = df.head(20).to_string(index=False)
        return (
            f"CSV Document Summary: {rows} rows, {cols} columns.\n"
            f"Columns: {col_names}\n\n"
            f"Sample Data (First 20 Rows):\n{sample_rows}"
        )
    except Exception as e:
        return f"CSV Extraction Error: {str(e)}"


def extract_text_from_excel(excel_bytes: bytes) -> str:
    """Extracts and formats sheets from an Excel (.xlsx/.xls) workbook."""
    try:
        import pandas as pd
        excel_file = pd.ExcelFile(io.BytesIO(excel_bytes))
        sheet_summaries = []
        for sheet in excel_file.sheet_names[:5]:
            df = excel_file.parse(sheet)
            rows, cols = df.shape
            sample_rows = df.head(15).to_string(index=False)
            sheet_summaries.append(
                f"### Sheet: '{sheet}' ({rows} rows, {cols} columns)\n"
                f"Columns: {', '.join(df.columns.astype(str))}\n\n"
                f"{sample_rows}"
            )
        return "\n\n---\n\n".join(sheet_summaries)
    except Exception as e:
        return f"Excel Extraction Error: {str(e)}"


async def analyze_document_with_llm(
    text_content: str,
    filename: str,
    provider: str = "deepseek"
) -> Dict[str, Any]:
    """
    Genuine LLM document classifier and transaction extractor.
    Classifies documents accurately into:
    - bank_statement
    - receipt
    - invoice
    - non_financial_document

    If non-financial (e.g. FAQs for India Leavers, HR policy, article):
    Returns is_financial=False, transactions=[], and an accurate executive summary.
    Never fabricates dummy amounts or vendors.
    """
    from backend.agent.llm_factory import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    # If document has almost no text
    if not text_content or len(text_content.strip()) < 10:
        return {
            "is_financial": False,
            "document_type": "non_financial_document",
            "summary": f"Uploaded file '{filename}' contains no readable or extractable text.",
            "transactions": []
        }

    # First check deterministic bank SMS / UPI text
    sms_parsed = parse_bank_sms(text_content)
    if sms_parsed and len(text_content.strip()) < 500:
        return {
            "is_financial": True,
            "document_type": "receipt",
            "summary": f"Parsed transaction SMS alert for ₹{sms_parsed.total_amount:,.2f} at {sms_parsed.vendor_name}.",
            "transactions": [sms_parsed.dict()]
        }

    truncated_text = text_content[:4000]

    system_prompt = (
        "You are an expert financial auditor and document classifier. "
        "Analyze the provided document text and determine whether it is a financial document "
        "(such as a bank statement, tax invoice, purchase receipt, or bill) OR a non-financial informational document "
        "(such as HR guidelines, immigration/visa FAQs, company policies, or articles).\n\n"
        "STRICT EXTRACTION RULES:\n"
        "1. If the document is NOT a financial record (e.g. FAQs, guidelines, contracts without bills), "
        "set 'is_financial': false, 'document_type': 'non_financial_document', 'transactions': [], and provide a clear 2-sentence summary of what the document explains.\n"
        "2. NEVER invent or fabricate transactions for non-financial documents.\n"
        "3. If it IS a receipt or invoice, extract the vendor, date (YYYY-MM-DD), total_amount (float in INR), category, and payment_method.\n"
        "4. If it IS a bank statement with multiple debit/credit rows, extract up to 10 prominent rows into 'transactions'.\n"
        "Respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        '  "is_financial": boolean,\n'
        '  "document_type": "bank_statement" | "receipt" | "invoice" | "non_financial_document",\n'
        '  "summary": "Concise summary of the document",\n'
        '  "transactions": [\n'
        '    {\n'
        '      "vendor_name": "Merchant or Beneficiary",\n'
        '      "date": "YYYY-MM-DD",\n'
        '      "total_amount": 0.0,\n'
        '      "payment_method": "UPI" | "Credit Card" | "Debit Card" | "Net Banking" | "Bank Statement",\n'
        '      "category": "dining" | "groceries" | "utilities" | "transportation" | "rent" | "healthcare" | "entertainment" | "subscriptions" | "other"\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    try:
        llm = get_llm(provider=provider, temperature=0.0, with_fallback=True)
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document Filename: {filename}\n\nDocument Text:\n{truncated_text}")
        ])
        raw_text = response.content if hasattr(response, "content") else str(response)

        # Clean markdown code fence if LLM wrapped in ```json ... ```
        cleaned_json = re.sub(r'^```(?:json)?\s*', '', raw_text.strip(), flags=re.MULTILINE)
        cleaned_json = re.sub(r'\s*```$', '', cleaned_json.strip(), flags=re.MULTILINE)
        data = json.loads(cleaned_json)
        return data
    except Exception as e:
        logger.warning(f"LLM document analysis error: {e}. Falling back to safe deterministic classifier.")
        # Safe fallback: Check for keywords
        lower = text_content.lower()
        has_financial_keywords = any(k in lower for k in [
            "statement period", "account statement", "total amount due", "invoice no",
            "tax invoice", "taxable value", "debit amount"
        ])
        if not has_financial_keywords:
            return {
                "is_financial": False,
                "document_type": "non_financial_document",
                "summary": f"Uploaded informational document '{filename}'. No financial transactions or payable bills were detected in this document.",
                "transactions": []
            }
        else:
            return {
                "is_financial": True,
                "document_type": "receipt",
                "summary": f"Detected financial document '{filename}'.",
                "transactions": []
            }


@tool
def inspect_uploaded_document(query: str, session_id: Optional[str] = None) -> str:
    """
    Search and retrieve text sections, policies, terms, or clauses from documents
    (PDFs, Excel sheets, CSV statements, employee exit guidelines, contracts, invoices)
    uploaded by the user in this conversation session.
    Use this tool whenever the user asks about an uploaded document (e.g. Norstella exit FAQs, notice period,
    garden leave, last working day, relieving letters, Form-16, severance, receipt details, or invoices).
    """
    try:
        with sync_engine.connect() as conn:
            # Query documents scoped strictly to session_id when available (prevent cross-user leak)
            if session_id:
                doc_rows = conn.execute(
                    text("SELECT filename, content_text, metadata_json FROM document_embeddings WHERE session_id = :sid ORDER BY created_at DESC LIMIT 3"),
                    {"sid": session_id}
                ).fetchall()
            else:
                doc_rows = conn.execute(
                    text("SELECT filename, content_text, metadata_json FROM document_embeddings ORDER BY created_at DESC LIMIT 3")
                ).fetchall()

            if not doc_rows:
                # Fallback to chat_messages if document_embeddings is empty
                if session_id:
                    msg_rows = conn.execute(
                        text("SELECT content FROM chat_messages WHERE session_id = :sid AND content LIKE '%Uploaded Document Analysis%' ORDER BY created_at DESC LIMIT 3"),
                        {"sid": session_id}
                    ).fetchall()
                else:
                    msg_rows = conn.execute(
                        text("SELECT content FROM chat_messages WHERE content LIKE '%Uploaded Document Analysis%' ORDER BY created_at DESC LIMIT 3")
                    ).fetchall()

                if msg_rows:
                    return f"Found document analysis in session chat history:\n\n{msg_rows[0][0]}"
                return "No uploaded documents found in the current conversation."

            results = []
            q_lower = query.lower()
            for row in doc_rows:
                fname = row[0] or "Uploaded File"
                content = row[1] or ""
                meta = row[2] or {}
                summary = meta.get("summary", "")

                # If query keywords match parts of the document, extract relevant window
                lines = content.split("\n")
                matched_paragraphs = []
                for idx, line in enumerate(lines):
                    if any(w in line.lower() for w in q_lower.split() if len(w) > 3):
                        start_idx = max(0, idx - 2)
                        end_idx = min(len(lines), idx + 3)
                        matched_paragraphs.append("\n".join(lines[start_idx:end_idx]))
                        if len(matched_paragraphs) >= 3:
                            break

                if matched_paragraphs:
                    relevant_text = "\n---\n".join(matched_paragraphs)
                    results.append(
                        f"Document: {fname}\nSummary: {summary}\nRelevant Excerpts:\n{relevant_text}"
                    )
                else:
                    # Provide overview and first 1500 chars of body
                    results.append(
                        f"Document: {fname}\nSummary: {summary}\nDocument Excerpt:\n{content[:1500]}"
                    )

            return "\n\n====================\n\n".join(results)
    except Exception as e:
        logger.warning(f"Error inspecting uploaded document: {e}")
        return f"Error retrieving document content: {str(e)}"


