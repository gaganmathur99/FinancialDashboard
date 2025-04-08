from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class BankAccountBase(BaseModel):
    """Base schema for bank account data."""
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    institution: Optional[str] = None
    account_number: Optional[str] = None
    sort_code: Optional[str] = None
    iban: Optional[str] = None
    currency: Optional[str] = None
    balance: Optional[float] = None
    available_balance: Optional[float] = None

class BankAccountCreate(BankAccountBase):
    """Schema for creating a bank account."""
    user_id: int
    account_id: str
    account_name: str
    institution: str
    currency: str
    balance: float
    encrypted_access_token: str
    encrypted_refresh_token: str

class BankAccountUpdate(BankAccountBase):
    """Schema for updating a bank account."""
    pass

class BankAccountResponse(BankAccountBase):
    """Schema for bank account response."""
    id: int
    user_id: int
    account_id: str
    last_synced: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    """Base schema for transaction data."""
    date: datetime
    description: str
    amount: float
    currency: str
    transaction_type: Optional[str] = None
    category: Optional[str] = None
    merchant: Optional[str] = None

class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    account_id: int
    transaction_id: str

class TransactionUpdate(TransactionBase):
    """Schema for updating a transaction."""
    pass

class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: int
    account_id: int
    transaction_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AuthCodeExchange(BaseModel):
    """Schema for exchanging an authorization code for a token."""
    code: str
    redirect_uri: Optional[str] = None

class TrueLayerToken(BaseModel):
    """Schema for TrueLayer access token."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int