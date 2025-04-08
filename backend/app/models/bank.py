from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.base import Base

class BankAccount(Base):
    """Bank account model for storing connected accounts and their details."""
    __tablename__ = "bank_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, index=True, unique=True, nullable=False)  # TrueLayer account ID
    account_name = Column(String, nullable=False)
    account_type = Column(String, nullable=True)
    institution = Column(String, nullable=False)
    account_number = Column(String, nullable=True)
    sort_code = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    currency = Column(String, nullable=False, default="GBP")
    balance = Column(Float, nullable=False, default=0.0)
    available_balance = Column(Float, nullable=True)
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, nullable=False)
    token_expiry = Column(DateTime, nullable=True)
    last_synced = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Transaction(Base):
    """Transaction model for storing bank transactions."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=False)
    transaction_id = Column(String, index=True, unique=True, nullable=False)  # TrueLayer transaction ID
    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="GBP")
    transaction_type = Column(String, nullable=True)  # debit, credit
    category = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("BankAccount", backref="transactions")