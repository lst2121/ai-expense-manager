import os
import time
import json
import hmac
import hashlib
import base64
import secrets
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "wealthcopilot-super-secure-production-jwt-key-2026")


def hash_password(password: str) -> str:
    """NIST-compliant PBKDF2-HMAC-SHA256 password hasher."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time verification of PBKDF2 hashed password."""
    try:
        salt, key_hex = hashed_password.split(":")
        test_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(key_hex, test_key.hex())
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta_seconds: int = 86400 * 30) -> str:
    """RFC 7519 standard JWT generator with HS256 signature."""
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_delta_seconds
    header = {"alg": "HS256", "typ": "JWT"}

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Validates signature and expiration of JWT."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()

        pad = len(sig_b64) % 4
        if pad:
            sig_b64 += "=" * (4 - pad)
        provided_sig = base64.urlsafe_b64decode(sig_b64.encode())
        if not hmac.compare_digest(expected_sig, provided_sig):
            return None

        pad_p = len(payload_b64) % 4
        if pad_p:
            payload_b64 += "=" * (4 - pad_p)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """FastAPI dependency: Returns decoded user if Bearer token present, else None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    return decode_access_token(token)

