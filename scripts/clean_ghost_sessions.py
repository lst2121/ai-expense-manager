import asyncio
from backend.database.connection import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        # Delete ghost sessions titled 'New Analysis' with <= 2 messages
        res = await session.execute(text("""
            DELETE FROM chat_messages 
            WHERE session_id IN (
                SELECT id FROM chat_sessions WHERE title = 'New Analysis'
            );
        """))
        await session.execute(text("""
            DELETE FROM chat_sessions WHERE title = 'New Analysis';
        """))
        await session.commit()
        print("Cleaned all ghost sessions!")

if __name__ == "__main__":
    asyncio.run(main())

