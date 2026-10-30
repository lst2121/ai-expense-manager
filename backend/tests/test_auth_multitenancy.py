import pytest
import uuid
import httpx
from backend.database.connection import AsyncSessionLocal
from sqlalchemy import text


@pytest.mark.asyncio
async def test_auth_and_multitenancy_isolation():
    base_url = "http://localhost:8000"
    random_suffix = uuid.uuid4().hex[:6]
    test_email = f"user_{random_suffix}@example.com"
    test_password = "Password#999"
    test_name = "Test Freelancer"

    async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
        # 1. Demo login
        demo_resp = await client.post("/api/auth/demo-login")
        assert demo_resp.status_code == 200
        demo_data = demo_resp.json()
        assert demo_data["status"] == "success"
        assert demo_data["user"]["email"] == "lokender@wealthcopilot.ai"
        demo_token = demo_data["token"]

        # 2. Verify /api/auth/me with Bearer token
        me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {demo_token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["authenticated"] is True
        assert me_resp.json()["user"]["email"] == "lokender@wealthcopilot.ai"

        # 3. Register new isolated tenant
        reg_resp = await client.post(
            "/api/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": test_name,
            }
        )
        assert reg_resp.status_code == 200
        reg_data = reg_resp.json()
        assert reg_data["status"] == "success"
        new_token = reg_data["token"]
        new_uid = reg_data["user"]["id"]

        # 4. Multi-tenancy isolation check in DB:
        async with AsyncSessionLocal() as session:
            # Lokender has 6,455 transactions
            lokender_tx = await session.execute(
                text("SELECT count(*) FROM transactions WHERE user_id = 'usr-lokender-2026'")
            )
            assert lokender_tx.scalar() == 6455

            # New tenant has exactly 0 transactions (clean isolated ledger!)
            new_tx = await session.execute(
                text("SELECT count(*) FROM transactions WHERE user_id = :uid"),
                {"uid": new_uid}
            )
            assert new_tx.scalar() == 0

            # Cleanup test user
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": new_uid})
            await session.commit()

