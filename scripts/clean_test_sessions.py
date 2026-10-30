import asyncio
from backend.database.connection import AsyncSessionLocal
from sqlalchemy import text

async def clean_test_sessions():
    async with AsyncSessionLocal() as session:
        # Find test session IDs
        res = await session.execute(text("""
            SELECT id, title FROM chat_sessions 
            WHERE id LIKE 'test-%' OR id LIKE 'eval-%'
        """))
        test_sessions = res.fetchall()
        print(f"Found {len(test_sessions)} test sessions to clean:")
        for sid, title in test_sessions:
            print(f"  {sid}: {title}")

        if test_sessions:
            # Delete messages first
            await session.execute(text("""
                DELETE FROM chat_messages 
                WHERE session_id IN (
                    SELECT id FROM chat_sessions 
                    WHERE id LIKE 'test-%' OR id LIKE 'eval-%'
                )
            """))
            # Delete document_embeddings for these sessions
            await session.execute(text("""
                DELETE FROM document_embeddings 
                WHERE session_id IN (
                    SELECT id FROM chat_sessions 
                    WHERE id LIKE 'test-%' OR id LIKE 'eval-%'
                )
            """))
            # Delete sessions
            await session.execute(text("""
                DELETE FROM chat_sessions 
                WHERE id LIKE 'test-%' OR id LIKE 'eval-%'
            """))
            await session.commit()
            print("Successfully purged all test session artifacts!")
        else:
            print("No test sessions found.")

if __name__ == "__main__":
    asyncio.run(clean_test_sessions())

