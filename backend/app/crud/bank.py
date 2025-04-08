from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.models.bank import BankAccount, Transaction
from backend.app.schemas.bank import BankAccountCreate, BankAccountUpdate, TransactionCreate, TransactionUpdate
from backend.app.core.security import encrypt, decrypt


def get_bank_account(db: Session, id: int) -> Optional[BankAccount]:
    """
    Get bank account by ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    id: int
        Bank account ID
        
    Returns:
    --------
    Optional[BankAccount]
        Bank account if found, None otherwise
    """
    return db.query(BankAccount).filter(BankAccount.id == id).first()


def get_bank_account_by_account_id(db: Session, account_id: str) -> Optional[BankAccount]:
    """
    Get bank account by TrueLayer account ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    account_id: str
        TrueLayer account ID
        
    Returns:
    --------
    Optional[BankAccount]
        Bank account if found, None otherwise
    """
    return db.query(BankAccount).filter(BankAccount.account_id == account_id).first()


def get_bank_accounts_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[BankAccount]:
    """
    Get bank accounts by user ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    user_id: int
        User ID
    skip: int
        Number of records to skip
    limit: int
        Maximum number of records to return
        
    Returns:
    --------
    List[BankAccount]
        List of bank accounts
    """
    return (
        db.query(BankAccount)
        .filter(BankAccount.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_active_bank_accounts_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[BankAccount]:
    """
    Get active bank accounts by user ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    user_id: int
        User ID
    skip: int
        Number of records to skip
    limit: int
        Maximum number of records to return
        
    Returns:
    --------
    List[BankAccount]
        List of active bank accounts
    """
    return (
        db.query(BankAccount)
        .filter(BankAccount.user_id == user_id)
        .filter(BankAccount.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_bank_account(
    db: Session, *, obj_in: BankAccountCreate, user_id: int
) -> BankAccount:
    """
    Create new bank account.
    
    Parameters:
    -----------
    db: Session
        Database session
    obj_in: BankAccountCreate
        Bank account creation data
    user_id: int
        User ID
        
    Returns:
    --------
    BankAccount
        Created bank account
    """
    encrypted_access_token = encrypt(obj_in.access_token)
    encrypted_refresh_token = encrypt(obj_in.refresh_token)
    
    db_obj = BankAccount(
        user_id=user_id,
        account_id=obj_in.account_id,
        account_name=obj_in.account_name,
        institution=obj_in.institution,
        account_type=obj_in.account_type,
        currency=obj_in.currency,
        balance=obj_in.balance,
        available_balance=obj_in.available_balance,
        access_token=encrypted_access_token,
        refresh_token=encrypted_refresh_token,
        token_expires_at=obj_in.token_expires_at,
        last_synced=datetime.utcnow(),
        is_active=True,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_bank_account(
    db: Session,
    *,
    db_obj: BankAccount,
    obj_in: Union[BankAccountUpdate, Dict[str, Any]]
) -> BankAccount:
    """
    Update bank account.
    
    Parameters:
    -----------
    db: Session
        Database session
    db_obj: BankAccount
        Bank account to update
    obj_in: Union[BankAccountUpdate, Dict[str, Any]]
        Bank account update data
        
    Returns:
    --------
    BankAccount
        Updated bank account
    """
    obj_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
    
    # Encrypt access token and refresh token if provided
    if "access_token" in obj_data and obj_data["access_token"]:
        obj_data["access_token"] = encrypt(obj_data["access_token"])
    if "refresh_token" in obj_data and obj_data["refresh_token"]:
        obj_data["refresh_token"] = encrypt(obj_data["refresh_token"])
    
    for field in obj_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, obj_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_bank_account_tokens(
    db: Session,
    *,
    db_obj: BankAccount,
    access_token: str,
    refresh_token: str,
    expires_in: int
) -> BankAccount:
    """
    Update bank account tokens.
    
    Parameters:
    -----------
    db: Session
        Database session
    db_obj: BankAccount
        Bank account to update
    access_token: str
        New access token
    refresh_token: str
        New refresh token
    expires_in: int
        Expiration time in seconds
        
    Returns:
    --------
    BankAccount
        Updated bank account
    """
    encrypted_access_token = encrypt(access_token)
    encrypted_refresh_token = encrypt(refresh_token)
    token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    db_obj.access_token = encrypted_access_token
    db_obj.refresh_token = encrypted_refresh_token
    db_obj.token_expires_at = token_expires_at
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_transaction(db: Session, id: int) -> Optional[Transaction]:
    """
    Get transaction by ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    id: int
        Transaction ID
        
    Returns:
    --------
    Optional[Transaction]
        Transaction if found, None otherwise
    """
    return db.query(Transaction).filter(Transaction.id == id).first()


def get_transaction_by_transaction_id(
    db: Session, transaction_id: str
) -> Optional[Transaction]:
    """
    Get transaction by TrueLayer transaction ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    transaction_id: str
        TrueLayer transaction ID
        
    Returns:
    --------
    Optional[Transaction]
        Transaction if found, None otherwise
    """
    return db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()


def get_transactions_by_bank_account(
    db: Session, bank_account_id: int, skip: int = 0, limit: int = 100
) -> List[Transaction]:
    """
    Get transactions by bank account ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    bank_account_id: int
        Bank account ID
    skip: int
        Number of records to skip
    limit: int
        Maximum number of records to return
        
    Returns:
    --------
    List[Transaction]
        List of transactions
    """
    return (
        db.query(Transaction)
        .filter(Transaction.bank_account_id == bank_account_id)
        .order_by(Transaction.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_transactions_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[Transaction]:
    """
    Get all transactions for a user across all bank accounts.
    
    Parameters:
    -----------
    db: Session
        Database session
    user_id: int
        User ID
    skip: int
        Number of records to skip
    limit: int
        Maximum number of records to return
        
    Returns:
    --------
    List[Transaction]
        List of transactions
    """
    return (
        db.query(Transaction)
        .join(BankAccount, Transaction.bank_account_id == BankAccount.id)
        .filter(BankAccount.user_id == user_id)
        .order_by(Transaction.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_transaction(
    db: Session, *, obj_in: TransactionCreate
) -> Transaction:
    """
    Create new transaction.
    
    Parameters:
    -----------
    db: Session
        Database session
    obj_in: TransactionCreate
        Transaction creation data
        
    Returns:
    --------
    Transaction
        Created transaction
    """
    db_obj = Transaction(
        bank_account_id=obj_in.bank_account_id,
        transaction_id=obj_in.transaction_id,
        transaction_category=obj_in.transaction_category,
        transaction_classification=obj_in.transaction_classification,
        timestamp=obj_in.timestamp,
        date=obj_in.date,
        description=obj_in.description,
        amount=obj_in.amount,
        currency=obj_in.currency,
        merchant_name=obj_in.merchant_name,
        meta=obj_in.meta,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_transaction(
    db: Session,
    *,
    db_obj: Transaction,
    obj_in: Union[TransactionUpdate, Dict[str, Any]]
) -> Transaction:
    """
    Update transaction.
    
    Parameters:
    -----------
    db: Session
        Database session
    db_obj: Transaction
        Transaction to update
    obj_in: Union[TransactionUpdate, Dict[str, Any]]
        Transaction update data
        
    Returns:
    --------
    Transaction
        Updated transaction
    """
    obj_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
    
    for field in obj_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, obj_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_access_token(bank_account: BankAccount) -> str:
    """
    Get decrypted access token.
    
    Parameters:
    -----------
    bank_account: BankAccount
        Bank account
        
    Returns:
    --------
    str
        Decrypted access token
    """
    return decrypt(bank_account.access_token)


def get_refresh_token(bank_account: BankAccount) -> str:
    """
    Get decrypted refresh token.
    
    Parameters:
    -----------
    bank_account: BankAccount
        Bank account
        
    Returns:
    --------
    str
        Decrypted refresh token
    """
    return decrypt(bank_account.refresh_token)