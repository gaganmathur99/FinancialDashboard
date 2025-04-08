from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_expiry: Optional[datetime] = None

class BankConnectionBase(BaseModel):
    provider: str

class BankConnectionCreate(BankConnectionBase):
    user_id: str
    access_token: str
    refresh_token: str
    token_expiry: Optional[datetime] = None

class BankConnection(BankConnectionBase):
    id: str
    user_id: str
    last_sync: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class BankAccountBase(BaseModel):
    name: str
    type: str
    provider: str
    currency: str
    balance: float

class BankAccountCreate(BankAccountBase):
    id: str
    user_id: str
    connection_id: str
    account_data: str

class BankAccount(BankAccountBase):
    id: str
    user_id: str
    connection_id: str
    last_updated: datetime
    created_at: datetime
    
    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    date: datetime
    description: str
    amount: float
    currency: str
    type: str
    category: Optional[str] = None

class TransactionCreate(TransactionBase):
    id: str
    user_id: str
    account_id: str
    transaction_data: str

class Transaction(TransactionBase):
    id: str
    user_id: str
    account_id: str
    created_at: datetime
    
    class Config:
        orm_mode = True

class BudgetBase(BaseModel):
    category: str
    amount: float
    period: str

class BudgetCreate(BudgetBase):
    user_id: str

class Budget(BudgetBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True