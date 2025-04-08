from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.core.security import encrypt, decrypt
from backend.app.models.bank import BankAccount, Transaction
from backend.app.schemas.bank import BankAccountCreate, BankAccountUpdate, TransactionCreate, TransactionUpdate


def get_bank_account(db: Session, bank_account_id: int) -> Optional[BankAccount]:
    """
    Get a bank account by ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    bank_account_id: int
        Bank account ID
        
    Returns:
    --------
    Optional[BankAccount]
        Bank account object if found, None otherwise
    """
    return db.query(BankAccount).filter(BankAccount.id == bank_account_id).first()


def get_bank_account_by_account_id(db: Session, account_id: str) -> Optional[BankAccount]:
    """
    Get a bank account by account ID (from the provider).
    
    Parameters:
    -----------
    db: Session
        Database session
    account_id: str
        Account ID from the provider
        
    Returns:
    --------
    Optional[BankAccount]
        Bank account object if found, None otherwise
    """
    return db.query(BankAccount).filter(BankAccount.account_id == account_id).first()


def get_user_bank_accounts(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[BankAccount]:
    """
    Get bank accounts for a user with pagination.
    
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
    return db.query(BankAccount).filter(BankAccount.user_id == user_id).offset(skip).limit(limit).all()


def create_bank_account(db: Session, bank_account_in: BankAccountCreate) -> BankAccount:
    """
    Create a new bank account.
    
    Parameters:
    -----------
    db: Session
        Database session
    bank_account_in: BankAccountCreate
        Bank account creation data
        
    Returns:
    --------
    BankAccount
        Created bank account
    """
    # Encrypt sensitive data
    access_token_encrypted = encrypt(bank_account_in.access_token)
    refresh_token_encrypted = encrypt(bank_account_in.refresh_token)
    
    # Create the bank account object
    db_bank_account = BankAccount(
        user_id=bank_account_in.user_id,
        account_id=bank_account_in.account_id,
        provider_id=bank_account_in.provider_id,
        account_type=bank_account_in.account_type,
        account_name=bank_account_in.account_name,
        account_number=bank_account_in.account_number,
        sort_code=bank_account_in.sort_code,
        iban=bank_account_in.iban,
        institution=bank_account_in.institution,
        currency=bank_account_in.currency,
        country=bank_account_in.country,
        access_token=access_token_encrypted,
        refresh_token=refresh_token_encrypted,
        token_expiry=bank_account_in.token_expiry,
        balance=bank_account_in.balance,
        available_balance=bank_account_in.available_balance,
        is_active=bank_account_in.is_active,
        is_connected=bank_account_in.is_connected
    )
    
    # Add to the database and commit
    db.add(db_bank_account)
    db.commit()
    db.refresh(db_bank_account)
    
    return db_bank_account


def update_bank_account(db: Session, db_bank_account: BankAccount, bank_account_in: Union[BankAccountUpdate, Dict[str, Any]]) -> BankAccount:
    """
    Update a bank account.
    
    Parameters:
    -----------
    db: Session
        Database session
    db_bank_account: BankAccount
        Existing bank account object
    bank_account_in: Union[BankAccountUpdate, Dict[str, Any]]
        Bank account update data
        
    Returns:
    --------
    BankAccount
        Updated bank account
    """
    # Convert to dict if not already
    update_data = bank_account_in if isinstance(bank_account_in, dict) else bank_account_in.dict(exclude_unset=True)
    
    # Encrypt sensitive data if present
    if "access_token" in update_data and update_data["access_token"]:
        update_data["access_token"] = encrypt(update_data["access_token"])
    
    if "refresh_token" in update_data and update_data["refresh_token"]:
        update_data["refresh_token"] = encrypt(update_data["refresh_token"])
    
    # Update the bank account object
    for field, value in update_data.items():
        setattr(db_bank_account, field, value)
    
    # Commit the changes
    db.add(db_bank_account)
    db.commit()
    db.refresh(db_bank_account)
    
    return db_bank_account


def update_bank_account_sync_time(db: Session, db_bank_account: BankAccount) -> BankAccount:
    """
    Update the last sync time for a bank account.
    
    Parameters:
    -----------
    db: Session
        Database session
    db_bank_account: BankAccount
        Existing bank account object
        
    Returns:
    --------
    BankAccount
        Updated bank account
    """
    # Update the last sync time
    db_bank_account.last_sync = datetime.utcnow()
    
    # Commit the changes
    db.add(db_bank_account)
    db.commit()
    db.refresh(db_bank_account)
    
    return db_bank_account


def delete_bank_account(db: Session, bank_account_id: int) -> Optional[BankAccount]:
    """
    Delete a bank account (mark as inactive).
    
    Parameters:
    -----------
    db: Session
        Database session
    bank_account_id: int
        Bank account ID
        
    Returns:
    --------
    Optional[BankAccount]
        Deleted bank account if found, None otherwise
    """
    # Get the bank account
    db_bank_account = get_bank_account(db, bank_account_id=bank_account_id)
    if not db_bank_account:
        return None
    
    # Mark as inactive
    db_bank_account.is_active = False
    db_bank_account.is_connected = False
    
    # Commit the changes
    db.add(db_bank_account)
    db.commit()
    db.refresh(db_bank_account)
    
    return db_bank_account


def get_bank_account_tokens(db: Session, bank_account_id: int) -> Dict[str, str]:
    """
    Get the access and refresh tokens for a bank account.
    
    Parameters:
    -----------
    db: Session
        Database session
    bank_account_id: int
        Bank account ID
        
    Returns:
    --------
    Dict[str, str]
        Dictionary with access_token and refresh_token
    """
    # Get the bank account
    db_bank_account = get_bank_account(db, bank_account_id=bank_account_id)
    if not db_bank_account:
        return {"access_token": "", "refresh_token": ""}
    
    # Decrypt the tokens
    access_token = decrypt(db_bank_account.access_token)
    refresh_token = decrypt(db_bank_account.refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


def update_bank_account_tokens(db: Session, bank_account_id: int, access_token: str, refresh_token: str, token_expiry: Optional[datetime] = None) -> Optional[BankAccount]:
    """
    Update the access and refresh tokens for a bank account.
    
    Parameters:
    -----------
    db: Session
        Database session
    bank_account_id: int
        Bank account ID
    access_token: str
        Access token
    refresh_token: str
        Refresh token
    token_expiry: Optional[datetime]
        Token expiry time
        
    Returns:
    --------
    Optional[BankAccount]
        Updated bank account if found, None otherwise
    """
    # Get the bank account
    db_bank_account = get_bank_account(db, bank_account_id=bank_account_id)
    if not db_bank_account:
        return None
    
    # Encrypt the tokens
    db_bank_account.access_token = encrypt(access_token)
    db_bank_account.refresh_token = encrypt(refresh_token)
    
    # Update the token expiry
    if token_expiry:
        db_bank_account.token_expiry = token_expiry
    
    # Commit the changes
    db.add(db_bank_account)
    db.commit()
    db.refresh(db_bank_account)
    
    return db_bank_account


# Transaction CRUD operations

def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    """
    Get a transaction by ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    transaction_id: int
        Transaction ID
        
    Returns:
    --------
    Optional[Transaction]
        Transaction object if found, None otherwise
    """
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_transaction_by_transaction_id(db: Session, transaction_id: str) -> Optional[Transaction]:
    """
    Get a transaction by transaction ID (from the provider).
    
    Parameters:
    -----------
    db: Session
        Database session
    transaction_id: str
        Transaction ID from the provider
        
    Returns:
    --------
    Optional[Transaction]
        Transaction object if found, None otherwise
    """
    return db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()


def get_account_transactions(db: Session, account_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """
    Get transactions for a bank account with pagination.
    
    Parameters:
    -----------
    db: Session
        Database session
    account_id: int
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
    return db.query(Transaction).filter(Transaction.account_id == account_id).order_by(Transaction.date.desc()).offset(skip).limit(limit).all()


def create_transaction(db: Session, transaction_in: TransactionCreate) -> Transaction:
    """
    Create a new transaction.
    
    Parameters:
    -----------
    db: Session
        Database session
    transaction_in: TransactionCreate
        Transaction creation data
        
    Returns:
    --------
    Transaction
        Created transaction
    """
    # Check if the transaction already exists
    existing_transaction = get_transaction_by_transaction_id(db, transaction_id=transaction_in.transaction_id)
    if existing_transaction:
        return existing_transaction
    
    # Create the transaction object
    db_transaction = Transaction(
        account_id=transaction_in.account_id,
        transaction_id=transaction_in.transaction_id,
        transaction_category=transaction_in.transaction_category,
        date=transaction_in.date,
        description=transaction_in.description,
        merchant=transaction_in.merchant,
        amount=transaction_in.amount,
        currency=transaction_in.currency,
        category=transaction_in.category,
        reference=transaction_in.reference,
        metadata=transaction_in.metadata
    )
    
    # Add to the database and commit
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction


def update_transaction(db: Session, db_transaction: Transaction, transaction_in: Union[TransactionUpdate, Dict[str, Any]]) -> Transaction:
    """
    Update a transaction.
    
    Parameters:
    -----------
    db: Session
        Database session
    db_transaction: Transaction
        Existing transaction object
    transaction_in: Union[TransactionUpdate, Dict[str, Any]]
        Transaction update data
        
    Returns:
    --------
    Transaction
        Updated transaction
    """
    # Convert to dict if not already
    update_data = transaction_in if isinstance(transaction_in, dict) else transaction_in.dict(exclude_unset=True)
    
    # Update the transaction object
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    # Commit the changes
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction


def create_or_update_transactions(db: Session, account_id: int, transactions: List[Dict[str, Any]]) -> List[Transaction]:
    """
    Create or update multiple transactions.
    
    Parameters:
    -----------
    db: Session
        Database session
    account_id: int
        Bank account ID
    transactions: List[Dict[str, Any]]
        List of transaction data
        
    Returns:
    --------
    List[Transaction]
        List of created or updated transactions
    """
    result = []
    
    for transaction_data in transactions:
        # Add the account ID to the transaction data
        transaction_data["account_id"] = account_id
        
        # Create the transaction schema
        transaction_in = TransactionCreate(**transaction_data)
        
        # Check if the transaction already exists
        existing_transaction = get_transaction_by_transaction_id(db, transaction_id=transaction_in.transaction_id)
        
        if existing_transaction:
            # Update the existing transaction
            result.append(update_transaction(db, existing_transaction, transaction_in))
        else:
            # Create a new transaction
            result.append(create_transaction(db, transaction_in))
    
    return result