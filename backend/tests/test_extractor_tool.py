import pytest
from backend.agent.tools.extractor_tool import parse_bank_sms, ExtractedReceipt


def test_parse_bank_sms_hdfc():
    sms = "HDFC Bank: Rs 450.00 debited from a/c **1234 at SWIGGY on 29-OCT-26 via UPI"
    receipt = parse_bank_sms(sms)
    assert receipt.vendor_name == "Swiggy"
    assert receipt.total_amount == 450.0
    assert receipt.category == "dining"
    assert receipt.payment_method == "UPI"


def test_parse_bank_sms_sbi():
    sms = "Dear SBI User, your A/C 9876 debited by INR 1,299.00 on 28-10-26 transfer to AMAZON UPI Ref 429381."
    receipt = parse_bank_sms(sms)
    assert receipt.vendor_name == "Amazon"
    assert receipt.total_amount == 1299.0
    assert receipt.category == "groceries"


def test_parse_bank_sms_phonepe():
    sms = "Paid Rs. 150 to Uber India via PhonePe UPI. Ref: 8291038"
    receipt = parse_bank_sms(sms)
    assert receipt.vendor_name == "Uber India"
    assert receipt.total_amount == 150.0
    assert receipt.category == "transportation"
    assert receipt.payment_method == "PhonePe"


def test_parse_bank_sms_bescom_utilities():
    sms = "Rs. 2,450.00 debited towards BESCOM Electricity bill via UPI on 25-10-2026."
    receipt = parse_bank_sms(sms)
    assert receipt.vendor_name == "Bescom"
    assert receipt.total_amount == 2450.0
    assert receipt.category == "utilities"
