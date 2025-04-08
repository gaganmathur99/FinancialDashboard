from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel


class BankAccountBase(BaseModel):
    """Base bank account schema"""
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    institution: Optional[str] = None
    account_type: Optional[str] = None
    currency: Optional[str] = None
    balance: Optional[float] = None
    available_balance: Optional[float] = None
    is_active: Optional[bool] = True


class BankAccountCreate(BankAccountBase):
    """Bank account creation schema"""
    account_id: str
    account_name: str
    institution: str
    currency: str
    balance: float
    access_token: str
    refresh_token: str
    token_expires_at: Optional[datetime] = None


class BankAccountUpdate(BankAccountBase):
    """Bank account update schema"""
    balance: Optional[float] = None
    available_balance: Optional[float] = None
    last_synced: Optional[datetime] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class BankAccountInDBBase(BankAccountBase):
    """Bank account in DB schema"""
    id: Optional[int] = None
    user_id: int
    last_synced: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankAccount(BankAccountInDBBase):
    """Bank account schema (returned to client)"""
    pass


class BankAccountInDB(BankAccountInDBBase):
    """Bank account in DB schema (with sensitive fields)"""
    access_token: str
    refresh_token: str
    token_expires_at: Optional[datetime] = None


class TransactionBase(BaseModel):
    """Base transaction schema"""
    transaction_id: Optional[str] = None
    transaction_category: Optional[str] = None
    transaction_classification: Optional[str] = None
    timestamp: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    merchant_name: Optional[str] = None
    meta: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Transaction creation schema"""
    transaction_id: str
    transaction_category: str
    date: datetime
    amount: float
    bank_account_id: int


class TransactionUpdate(TransactionBase):
    """Transaction update schema"""
    pass


class TransactionInDBBase(TransactionBase):
    """Transaction in DB schema"""
    id: Optional[int] = None
    bank_account_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Transaction(TransactionInDBBase):
    """Transaction schema (returned to client)"""
    pass


class TransactionInDB(TransactionInDBBase):
    """Transaction in DB schema (with sensitive fields)"""
    pass