import sys
import os
import asyncio

# On Windows, psycopg async requires WindowsSelectorEventLoopPolicy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.api.routes.analytics import router as analytics_router
from backend.api.routes.transactions import router as transactions_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.auth import router as auth_router

app = FastAPI(
    title="AI Expense & Accounting Platform API",
    description="Odoo-Grade Double-Entry Financial Engine with LangGraph ReAct Copilot",
    version="2.0.0"
)

# CORS Configuration for React Frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(auth_router, prefix="/api")
app.include_router(analytics_router)
app.include_router(transactions_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-expense-accounting-api",
        "database": "postgresql-17-pgvector",
        "version": "2.0.0"
    }


@app.get("/")
async def root():
    return {
        "platform": "AI Expense Accounting Platform",
        "docs_url": "/docs",
        "endpoints": {
            "kpis": "/api/analytics/kpis",
            "transactions": "/api/transactions",
            "accounts": "/api/accounts",
            "chat_stream": "/api/chat/stream",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)

