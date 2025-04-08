from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.base import Base


class BankAccount(Base):
    """
    Bank account model for database.
    
    Attributes:
    -----------
    id: int
        Bank account ID
    user_id: int
        User ID (foreign key)
    account_id: str
        TrueLayer account ID
    account_name: str
        Account name
    institution: str
        Financial institution name
    account_type: str
        Account type (e.g., checking, savings)
    currency: str
        Account currency
    balance: float
        Current balance
    available_balance: float
        Available balance
    access_token: str
        Encrypted access token
    refresh_token: str
        Encrypted refresh token
    token_expires_at: datetime
        Token expiration timestamp
    last_synced: datetime
        Last synchronization timestamp
    is_active: bool
        Whether the account is active
    created_at: datetime
        Creation timestamp
    updated_at: datetime
        Last update timestamp
    """
    __tablename__ = "bank_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, index=True, nullable=False)
    account_name = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    account_type = Column(String, nullable=True)
    currency = Column(String, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    available_balance = Column(Float, nullable=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime, nullable=True)
    last_synced = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="bank_accounts")
    transactions = relationship("Transaction", back_populates="bank_account", cascade="all, delete-orphan")


class Transaction(Base):
    """
    Transaction model for database.
    
    Attributes:
    -----------
    id: int
        Transaction ID
    bank_account_id: int
        Bank account ID (foreign key)
    transaction_id: str
        TrueLayer transaction ID
    transaction_category: str
        Transaction category
    transaction_classification: str
        Transaction classification (JSON)
    timestamp: str
        Timestamp string from API
    date: datetime
        Transaction date
    description: str
        Transaction description
    amount: float
        Transaction amount
    currency: str
        Transaction currency
    merchant_name: str
        Merchant name
    meta: str
        Additional metadata (JSON)
    created_at: datetime
        Creation timestamp
    updated_at: datetime
        Last update timestamp
    """
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=False)
    transaction_id = Column(String, index=True, nullable=False)
    transaction_category = Column(String, nullable=True)
    transaction_classification = Column(Text, nullable=True)  # JSON string
    timestamp = Column(String, nullable=True)
    date = Column(DateTime, nullable=False, index=True)
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=True)
    merchant_name = Column(String, nullable=True)
    meta = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bank_account = relationship("BankAccount", back_populates="transactions")