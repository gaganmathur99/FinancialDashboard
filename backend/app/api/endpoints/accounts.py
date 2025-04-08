from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from backend.app.db.base import get_db
from backend.app.core.truelayer import (
    get_transactions,
    transactions_to_dataframe,
    refresh_access_token
)
from backend.app.api.dependencies import (
    get_current_active_user,
    check_bank_account_owner
)
from backend.app.models.user import User
from backend.app.models.bank import BankAccount
from backend.app.schemas.bank import (
    BankAccount as BankAccountSchema,
    Transaction as TransactionSchema
)
from backend.app.crud import (
    get_bank_account_by_id,
    get_bank_accounts_by_user_id,
    get_active_bank_accounts_by_user_id,
    get_decrypted_access_token,
    get_decrypted_refresh_token,
    update_bank_account_tokens,
    update_last_synced,
    get_transactions_by_bank_account_id,
    create_transaction
)

router = APIRouter()


@router.get("/", response_model=List[BankAccountSchema])
def read_bank_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all bank accounts for the current user.
    """
    bank_accounts = get_bank_accounts_by_user_id(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return bank_accounts


@router.get("/{account_id}", response_model=BankAccountSchema)
def read_bank_account(
    *,
    db: Session = Depends(get_db),
    account_id: int = Path(...),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific bank account by ID.
    """
    bank_account = get_bank_account_by_id(db=db, account_id=account_id)
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )
    
    # Check if the user is the owner of the bank account
    check_bank_account_owner(bank_account=bank_account, current_user=current_user)
    
    return bank_account


@router.get("/{account_id}/transactions", response_model=List[TransactionSchema])
def read_transactions(
    *,
    db: Session = Depends(get_db),
    account_id: int = Path(...),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    sync: bool = Query(False)
) -> Any:
    """
    Get transactions for a specific bank account.
    
    If sync=True, it will fetch the latest transactions from TrueLayer.
    """
    # Get the bank account
    bank_account = get_bank_account_by_id(db=db, account_id=account_id)
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )
    
    # Check if the user is the owner of the bank account
    check_bank_account_owner(bank_account=bank_account, current_user=current_user)
    
    # Fetch the latest transactions if requested
    if sync:
        # Check if the access token is still valid
        if bank_account.token_expires_at and bank_account.token_expires_at < datetime.utcnow():
            # Refresh the access token
            refresh_token = get_decrypted_refresh_token(bank_account)
            token_response = refresh_access_token(refresh_token)
            
            # Check if the token refresh was successful
            if "error" in token_response:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to refresh access token: {token_response.get('error')}",
                )
            
            # Update the access token and refresh token
            access_token = token_response.get("access_token")
            refresh_token = token_response.get("refresh_token")
            expires_in = token_response.get("expires_in")
            
            update_bank_account_tokens(
                db=db,
                db_obj=bank_account,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in
            )
        else:
            # Use the existing access token
            access_token = get_decrypted_access_token(bank_account)
        
        # Get transactions from TrueLayer
        from_date = None
        if bank_account.last_synced:
            # Get transactions since the last sync
            from_date = bank_account.last_synced.date().isoformat()
        
        # Get transactions
        transactions = get_transactions(
            access_token=access_token,
            account_id=bank_account.account_id,
            from_date=from_date
        )
        
        # Save transactions to the database
        for transaction in transactions:
            # Check if the transaction already exists
            existing_transaction = db.query(bank_account.transactions).filter(
                bank_account.transactions.c.transaction_id == transaction["transaction_id"]
            ).first()
            
            if not existing_transaction:
                # Create the transaction
                transaction_in = {
                    "bank_account_id": bank_account.id,
                    **transaction
                }
                create_transaction(db=db, obj_in=transaction_in)
        
        # Update the last synced timestamp
        update_last_synced(db=db, db_obj=bank_account)
    
    # Get transactions from the database
    return get_transactions_by_bank_account_id(
        db=db, bank_account_id=bank_account.id, skip=skip, limit=limit
    )


@router.get("/{account_id}/balance")
def read_bank_account_balance(
    *,
    db: Session = Depends(get_db),
    account_id: int = Path(...),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get the balance for a specific bank account.
    """
    # Get the bank account
    bank_account = get_bank_account_by_id(db=db, account_id=account_id)
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )
    
    # Check if the user is the owner of the bank account
    check_bank_account_owner(bank_account=bank_account, current_user=current_user)
    
    return {
        "balance": bank_account.balance,
        "available_balance": bank_account.available_balance,
        "currency": bank_account.currency,
        "last_synced": bank_account.last_synced
    }