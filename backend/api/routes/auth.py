import uuid
import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from backend.database.connection import AsyncSessionLocal
from backend.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_optional,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(req: RegisterRequest):
    """
    Registers a new user and provisions an isolated ledger.
    """
    email_clean = req.email.strip().lower()
    full_name_clean = req.full_name.strip()
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email_clean}
        )
        if existing.fetchone():
            raise HTTPException(status_code=400, detail="An account with this email already exists.")

        user_id = f"usr-{uuid.uuid4().hex[:12]}"
        hashed_pw = hash_password(req.password)
        now = datetime.datetime.utcnow()

        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, created_at, is_active)
                VALUES (:id, :email, :pw, :name, :now, TRUE)
            """),
            {"id": user_id, "email": email_clean, "pw": hashed_pw, "name": full_name_clean, "now": now}
        )
        await session.commit()

        token = create_access_token({
            "sub": user_id,
            "email": email_clean,
            "name": full_name_clean,
        })

        return {
            "status": "success",
            "token": token,
            "user": {
                "id": user_id,
                "email": email_clean,
                "full_name": full_name_clean,
            }
        }


@router.post("/login")
async def login(req: LoginRequest):
    """
    Authenticates a user via email and password, returning a JWT token.
    """
    email_clean = req.email.strip().lower()
    async with AsyncSessionLocal() as session:
        # Support both current branded lokender@nivo.ai and legacy lokender@wealthcopilot.ai
        if email_clean in ("lokender@nivo.ai", "lokender@wealthcopilot.ai"):
            res = await session.execute(
                text("SELECT id, email, hashed_password, full_name, is_active FROM users WHERE id = 'usr-lokender-2026' OR email = :email LIMIT 1"),
                {"email": email_clean}
            )
        else:
            res = await session.execute(
                text("SELECT id, email, hashed_password, full_name, is_active FROM users WHERE email = :email"),
                {"email": email_clean}
            )
        user = res.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        pw_valid = verify_password(req.password, user[2])
        # Allow both standard TestPassword123! and Password#2026 for Lokender's demo account
        if not pw_valid and user[0] == "usr-lokender-2026" and req.password in ("TestPassword123!", "Password#2026"):
            pw_valid = True

        if not pw_valid:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        if not user[4]:
            raise HTTPException(status_code=403, detail="Account is disabled.")

        token = create_access_token({
            "sub": user[0],
            "email": user[1],
            "name": user[3],
        })

        return {
            "status": "success",
            "token": token,
            "user": {
                "id": user[0],
                "email": user[1],
                "full_name": user[3],
            }
        }


@router.post("/demo-login")
async def demo_login():
    """
    Instant 1-Click Demo Login as Lokender Singh (with 6,455 transactions).
    """
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            text("SELECT id, email, full_name FROM users WHERE id = 'usr-lokender-2026' OR email IN ('lokender@nivo.ai', 'lokender@wealthcopilot.ai') LIMIT 1")
        )
        user = res.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Demo user not found.")

        token = create_access_token({
            "sub": user[0],
            "email": user[1],
            "name": user[2],
        })

        return {
            "status": "success",
            "token": token,
            "user": {
                "id": user[0],
                "email": user[1],
                "full_name": user[2],
            }
        }


@router.get("/me")
async def get_me(user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Returns current authenticated user profile.
    """
    if not user:
        return {
            "authenticated": False,
            "user": None
        }

    return {
        "authenticated": True,
        "user": {
            "id": user.get("sub"),
            "email": user.get("email"),
            "full_name": user.get("name"),
        }
    }
