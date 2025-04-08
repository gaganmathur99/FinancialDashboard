from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.app.models.bank import BankAccount
from backend.app.api.schemas.bank import BankAccountCreate, BankAccountUpdate

def get(db: Session, bank_account_id: int) -> Optional[BankAccount]:
    """
    Get a bank account by ID
    
    Args:
        db: Database session
        bank_account_id: Bank account ID
        
    Returns:
        BankAccount: Bank account object if found, None otherwise
    """
    return db.query(BankAccount).filter(BankAccount.id == bank_account_id).first()

def get_by_account_id(db: Session, account_id: str) -> Optional[BankAccount]:
    """
    Get a bank account by TrueLayer account ID
    
    Args:
        db: Database session
        account_id: TrueLayer account ID
        
    Returns:
        BankAccount: Bank account object if found, None otherwise
    """
    return db.query(BankAccount).filter(BankAccount.account_id == account_id).first()

def get_by_user_id(db: Session, user_id: int) -> List[BankAccount]:
    """
    Get all bank accounts for a user
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List[BankAccount]: List of bank accounts
    """
    return db.query(BankAccount).filter(BankAccount.user_id == user_id).all()

def create(db: Session, obj_in: BankAccountCreate) -> BankAccount:
    """
    Create a new bank account
    
    Args:
        db: Database session
        obj_in: Bank account data
        
    Returns:
        BankAccount: Created bank account
    """
    db_obj = BankAccount(
        user_id=obj_in.user_id,
        account_id=obj_in.account_id,
        account_name=obj_in.account_name,
        account_type=obj_in.account_type,
        institution=obj_in.institution,
        account_number=obj_in.account_number,
        currency=obj_in.currency,
        balance=obj_in.balance,
        encrypted_access_token=obj_in.encrypted_access_token,
        encrypted_refresh_token=obj_in.encrypted_refresh_token,
        last_synced=datetime.utcnow()
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update(db: Session, db_obj: BankAccount, obj_in: BankAccountUpdate) -> BankAccount:
    """
    Update a bank account
    
    Args:
        db: Database session
        db_obj: Bank account object to update
        obj_in: Bank account data
        
    Returns:
        BankAccount: Updated bank account
    """
    update_data = obj_in.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete(db: Session, bank_account_id: int) -> bool:
    """
    Delete a bank account
    
    Args:
        db: Database session
        bank_account_id: Bank account ID
        
    Returns:
        bool: True if deleted, False otherwise
    """
    bank_account = db.query(BankAccount).filter(BankAccount.id == bank_account_id).first()
    if not bank_account:
        return False
    
    db.delete(bank_account)
    db.commit()
    return True

def update_balance(db: Session, bank_account_id: int, balance: float, available_balance: Optional[float] = None) -> BankAccount:
    """
    Update bank account balance
    
    Args:
        db: Database session
        bank_account_id: Bank account ID
        balance: Current balance
        available_balance: Available balance
        
    Returns:
        BankAccount: Updated bank account
    """
    bank_account = db.query(BankAccount).filter(BankAccount.id == bank_account_id).first()
    if not bank_account:
        return None
    
    bank_account.balance = balance
    if available_balance is not None:
        bank_account.available_balance = available_balance
    bank_account.last_synced = datetime.utcnow()
    
    db.add(bank_account)
    db.commit()
    db.refresh(bank_account)
    return bank_account

def update_token(db: Session, bank_account_id: int, access_token: str, refresh_token: str, expires_in: int) -> BankAccount:
    """
    Update bank account tokens
    
    Args:
        db: Database session
        bank_account_id: Bank account ID
        access_token: Encrypted access token
        refresh_token: Encrypted refresh token
        expires_in: Token expiry in seconds
        
    Returns:
        BankAccount: Updated bank account
    """
    bank_account = db.query(BankAccount).filter(BankAccount.id == bank_account_id).first()
    if not bank_account:
        return None
    
    bank_account.encrypted_access_token = access_token
    bank_account.encrypted_refresh_token = refresh_token
    bank_account.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
    
    db.add(bank_account)
    db.commit()
    db.refresh(bank_account)
    return bank_account