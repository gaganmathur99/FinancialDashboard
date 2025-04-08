from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime, date, timedelta
import uuid

from backend.app.api.dependencies import get_db, get_current_active_user
from backend.app.core import truelayer
from backend.app.core.security import encrypt, decrypt
from backend.app.api.crud import crud_bank
from backend.app.api.schemas.bank import BankAccountResponse, TransactionResponse
from backend.app.models.user import User
from backend.app.models.bank import BankAccount

router = APIRouter()

@router.get("/", response_model=List[BankAccountResponse])
def get_user_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all bank accounts for the current user
    """
    return crud_bank.get_by_user_id(db, user_id=current_user.id)

@router.get("/{account_id}", response_model=BankAccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific bank account
    """
    account = crud_bank.get(db, bank_account_id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return account

@router.get("/{account_id}/refresh")
def refresh_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh account information from TrueLayer
    """
    # Get bank account
    account = crud_bank.get(db, bank_account_id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Decrypt access token
    access_token = decrypt(account.encrypted_access_token)
    
    # Get updated account information
    account_info = None
    accounts = truelayer.get_accounts(access_token)
    for acc in accounts:
        if acc.get("account_id") == account.account_id:
            account_info = acc
            break
    
    if not account_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found in TrueLayer"
        )
    
    # Get balance information
    balance_info = truelayer.get_account_balance(access_token, account.account_id)
    
    # Update account information
    if balance_info:
        account.balance = balance_info.get("current", account.balance)
        account.available_balance = balance_info.get("available", account.available_balance)
        account.last_synced = datetime.utcnow()
        
        db.add(account)
        db.commit()
        db.refresh(account)
    
    return {
        "status": "success",
        "message": "Account refreshed successfully",
        "account": account
    }

@router.get("/{account_id}/transactions", response_model=List[TransactionResponse])
def get_account_transactions(
    account_id: int,
    from_date: date = Query(None, description="Start date for transactions"),
    to_date: date = Query(None, description="End date for transactions"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get transactions for a specific bank account
    """
    # Get bank account
    account = crud_bank.get(db, bank_account_id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Set default date range if not specified
    if not from_date:
        from_date = (datetime.now() - timedelta(days=90)).date()
    if not to_date:
        to_date = datetime.now().date()
    
    # Decrypt access token
    access_token = decrypt(account.encrypted_access_token)
    
    # Get transactions from TrueLayer
    transactions_df = truelayer.get_transactions(
        access_token, 
        account.account_id, 
        from_date, 
        to_date
    )
    
    # Convert DataFrame to list of dictionaries
    if transactions_df.empty:
        return []
    
    # Convert to list of TransactionResponse objects
    transactions = transactions_df.to_dict('records')
    
    return transactions

@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a bank account
    """
    # Get bank account
    account = crud_bank.get(db, bank_account_id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete account
    crud_bank.delete(db, bank_account_id=account_id)
    
    return {
        "status": "success",
        "message": "Account deleted successfully"
    }