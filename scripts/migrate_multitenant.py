import asyncio
from backend.database.connection import AsyncSessionLocal
from backend.auth.security import hash_password
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        print("1. Creating users table if not exists...")
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL
            );
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
        """))

        print("2. Adding user_id column to transactions & chat_sessions if needed...")
        await session.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='transactions' AND column_name='user_id'
                ) THEN
                    ALTER TABLE transactions ADD COLUMN user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE;
                    CREATE INDEX ix_transactions_user_id ON transactions (user_id);
                END IF;
            END $$;
        """))

        await session.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='chat_sessions' AND column_name='user_id'
                ) THEN
                    ALTER TABLE chat_sessions ADD COLUMN user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE;
                    CREATE INDEX ix_chat_sessions_user_id ON chat_sessions (user_id);
                END IF;
            END $$;
        """))

        print("3. Seeding Lokender Singh demo user...")
        demo_id = "usr-lokender-2026"
        demo_email = "lokender@wealthcopilot.ai"
        hashed_pw = hash_password("Password#2026")
        
        await session.execute(text("""
            INSERT INTO users (id, email, hashed_password, full_name, created_at, is_active)
            VALUES (:id, :email, :pw, 'Lokender Singh', CURRENT_TIMESTAMP, TRUE)
            ON CONFLICT (email) DO NOTHING;
        """), {"id": demo_id, "email": demo_email, "pw": hashed_pw})

        print("4. Linking all existing transactions and chat sessions to Lokender Singh...")
        await session.execute(text("""
            UPDATE transactions SET user_id = :uid WHERE user_id IS NULL;
        """), {"uid": demo_id})
        
        await session.execute(text("""
            UPDATE chat_sessions SET user_id = :uid WHERE user_id IS NULL;
        """), {"uid": demo_id})

        await session.commit()
        print(f"Migration complete! Linked transactions and sessions to {demo_email}.")

if __name__ == "__main__":
    asyncio.run(main())
