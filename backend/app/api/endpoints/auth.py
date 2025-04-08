from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Any

from backend.app.api.dependencies import get_db, get_current_active_user
from backend.app.core import truelayer
from backend.app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, TRUELAYER_REDIRECT_URI
from backend.app.core.security import create_access_token, verify_password, encrypt, decrypt
from backend.app.api.crud import crud_user, crud_bank
from backend.app.api.schemas.user import UserCreate, UserResponse, Token, UserLogin
from backend.app.api.schemas.bank import AuthCodeExchange, TrueLayerToken
from backend.app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user
    """
    # Check if username exists
    user = crud_user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = crud_user.create(db, obj_in=user_in)
    return user

@router.post("/login", response_model=Token)
def login_user(user_in: UserLogin, db: Session = Depends(get_db)) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Authenticate user
    user = crud_user.authenticate(db, username=user_in.username, password=user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Get current user information
    """
    return current_user

@router.get("/truelayer/auth")
def get_truelayer_auth_url(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Get TrueLayer authentication URL
    """
    # Generate auth URL
    auth_url = truelayer.create_auth_link(redirect_uri=TRUELAYER_REDIRECT_URI)
    
    return {"auth_url": auth_url}

@router.get("/truelayer/callback")
def truelayer_callback(
    request: Request,
    code: str = None,
    error: str = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    Handle TrueLayer authentication callback
    """
    # Check for errors
    if error:
        return {"status": "error", "message": error}
    
    # Check for authorization code
    if not code:
        return {"status": "error", "message": "No authorization code provided"}
    
    # Exchange code for token
    token_response = truelayer.exchange_code_for_token(code, TRUELAYER_REDIRECT_URI)
    if not token_response:
        return {"status": "error", "message": "Failed to exchange code for token"}
    
    # Get user info
    access_token = token_response.get("access_token")
    user_info = truelayer.get_user_info(access_token)
    
    # TODO: Save this in session or return to frontend to complete the flow
    # For now, redirecting to a page with the token information
    return {
        "status": "success", 
        "token": token_response,
        "user_info": user_info
    }

@router.post("/truelayer/exchange", response_model=dict)
def exchange_auth_code(
    auth_data: AuthCodeExchange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Exchange TrueLayer authorization code for access token and save connection
    """
    # Exchange code for token
    token_response = truelayer.exchange_code_for_token(
        auth_data.code, 
        auth_data.redirect_uri or TRUELAYER_REDIRECT_URI
    )
    
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )
    
    # Get account information
    access_token = token_response.get("access_token")
    accounts = truelayer.get_accounts(access_token)
    
    # Save account information to database
    saved_accounts = []
    for account in accounts:
        # Get balance information
        account_id = account.get("account_id")
        balance_info = truelayer.get_account_balance(access_token, account_id)
        account_details = truelayer.get_account_details(access_token, account_id)
        
        # Prepare bank account data
        bank_data = {
            "user_id": current_user.id,
            "account_id": account_id,
            "account_name": account.get("display_name"),
            "account_type": account.get("account_type"),
            "institution": account.get("provider", {}).get("display_name", "Unknown Bank"),
            "account_number": account_details.get("account_number", {}).get("number", ""),
            "sort_code": account_details.get("account_number", {}).get("sort_code", ""),
            "iban": account_details.get("account_number", {}).get("iban", ""),
            "currency": account.get("currency"),
            "balance": balance_info.get("current") if balance_info else 0.0,
            "available_balance": balance_info.get("available") if balance_info else 0.0,
            "encrypted_access_token": encrypt(access_token),
            "encrypted_refresh_token": encrypt(token_response.get("refresh_token", ""))
        }
        
        # Check if account already exists
        existing_account = crud_bank.get_by_account_id(db, account_id)
        if existing_account:
            # Update existing account
            update_data = crud_bank.BankAccountUpdate(**bank_data)
            updated_account = crud_bank.update(db, existing_account, update_data)
            saved_accounts.append(updated_account)
        else:
            # Create new account
            create_data = crud_bank.BankAccountCreate(**bank_data)
            new_account = crud_bank.create(db, create_data)
            saved_accounts.append(new_account)
            
    return {
        "status": "success",
        "message": f"Successfully linked {len(saved_accounts)} accounts",
        "account_count": len(saved_accounts)
    }