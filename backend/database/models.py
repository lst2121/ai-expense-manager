import datetime
import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} ({self.full_name})>"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # e.g., '1010', '5010'
    name = Column(String(100), nullable=False)                          # e.g., 'Operating Cash', 'Software'
    type = Column(String(50), nullable=False, index=True)              # 'asset', 'liability', 'equity', 'income', 'expense'
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    journal_entries = relationship("JournalEntry", back_populates="account")

    def __repr__(self):
        return f"<Account {self.code}: {self.name} ({self.type})>"


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    transactions = relationship("Transaction", back_populates="vendor")

    def __repr__(self):
        return f"<Vendor {self.id}: {self.name}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    description = Column(String(255), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), default="Bank Transfer")  # 'Credit Card', 'Bank Transfer', 'UPI', 'Cash'
    category = Column(String(50), nullable=True, index=True)
    is_reconciled = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="transactions")
    vendor = relationship("Vendor", back_populates="transactions")
    account = relationship("Account")
    journal_entries = relationship("JournalEntry", back_populates="transaction", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transaction {self.id}: {self.date.strftime('%Y-%m-%d')} | {self.description} | ${self.total_amount}>"


class JournalEntry(Base):
    """
    Odoo-style double-entry ledger lines.
    Enforces double-entry principle:
    For every transaction, SUM(debit) must equal SUM(credit).
    """
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    debit = Column(Numeric(12, 2), default=0.0, nullable=False)
    credit = Column(Numeric(12, 2), default=0.0, nullable=False)
    description = Column(String(255), nullable=True)
    entry_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    transaction = relationship("Transaction", back_populates="journal_entries")
    account = relationship("Account", back_populates="journal_entries")

    def __repr__(self):
        return f"<JournalEntry #{self.id} Tx:{self.transaction_id} Acc:{self.account_id} Debit:{self.debit} Credit:{self.credit}>"


class DocumentEmbedding(Base):
    """
    Dual-track RAG storage for unstructured invoices, receipts, and bank statements
    indexed via pgvector.
    """
    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), index=True, nullable=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(255), nullable=True)
    content_text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    transaction = relationship("Transaction")

    def __repr__(self):
        return f"<DocumentEmbedding #{self.id} File:{self.filename}>"


class ChatFeedback(Base):
    """
    User satisfaction and response quality feedback monitoring.
    """
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(100), nullable=False, index=True)
    thread_id = Column(String(100), nullable=True, index=True)
    rating = Column(String(20), nullable=False)  # 'thumbs_up', 'thumbs_down'
    category = Column(String(50), nullable=True)  # 'inaccurate_math', 'too_wordy', 'misunderstood', 'broken_chart'
    comment = Column(Text, nullable=True)
    user_query = Column(Text, nullable=True)
    assistant_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ChatFeedback #{self.id} Msg:{self.message_id} Rating:{self.rating}>"


class ChatSession(Base):
    """
    Persistent conversational session / thread for ChatGPT-style left sidebar.
    """
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    is_pinned = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession {self.id}: {self.title}>"


class ChatMessage(Base):
    """
    Individual turn within a persistent chat session.
    Stores user queries and assistant responses along with Generative UI specs (Recharts & tool calls).
    """
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    chart_spec = Column(JSON, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage #{self.id} Session:{self.session_id} Role:{self.role}>"



