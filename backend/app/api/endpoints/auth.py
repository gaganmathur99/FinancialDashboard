import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.base import get_db
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.core.truelayer import (
    create_auth_link,
    exchange_auth_code,
    get_user_info,
    get_accounts,
    get_account_details,
    get_account_balance
)
from backend.app.api.dependencies import get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.token import Token
from backend.app.schemas.user import UserCreate, UserLogin
from backend.app.schemas.bank import BankAccountCreate
from backend.app.crud import (
    authenticate,
    get_user_by_email,
    create_user,
    get_bank_account_by_account_id,
    create_bank_account,
    update_bank_account_tokens
)

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    *,
    db: Session = Depends(get_db),
    user_login: UserLogin,
) -> Dict[str, str]:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    print(f"Received email: {user_login.email}, password: {user_login.password}")
    # Authenticate user
    user = authenticate(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Create refresh token with longer expiry
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(
        subject=user.id, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=Token)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
) -> Dict[str, str]:
    """
    Register a new user and return an access token.
    """
    print(user_in)
    # Check if the user already exists
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Create the user
    user = create_user(db, obj_in=user_in)
    print(f"User created: {user}")
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/truelayer/authorize")
def authorize_truelayer(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    Get a TrueLayer authorization URL for the user to connect their bank account.
    """
    print(f"User: {current_user}")
    # Generate a state parameter to verify the callback
    state = str(uuid.uuid4())
    
    # Create the authorization URL
    auth_url = create_auth_link(state)
    
    return {
        "auth_url": auth_url,
        "state": state
    }


@router.get("/truelayer/callback")
async def truelayer_callback(
    request: Request,
    code: str = Query(None),
    state: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Handle the TrueLayer callback after the user has authorized the application.
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided",
        )
    
    # Exchange the authorization code for an access token
    token_response = exchange_auth_code(code)
    
    # Check if the token exchange was successful
    if "error" in token_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange authorization code: {token_response.get('error')}",
        )
    
    # Extract the access token and refresh token
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    
    if not access_token or not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token or refresh token not provided",
        )
    
    # Get user information from TrueLayer
    user_info = get_user_info(access_token)
    
    # Get the user's bank accounts
    accounts = get_accounts(access_token)
    
    # Save each account to the database
    for account in accounts:
        # Check if the account already exists
        account_id = account.get("account_id")
        existing_account = get_bank_account_by_account_id(db, account_id)
        
        # Get account details and balance
        account_details = get_account_details(access_token, account_id)
        account_balance = get_account_balance(access_token, account_id)
        
        # Prepare account data
        account_name = account.get("display_name", "")
        institution = account_details.get("provider", {}).get("display_name", "")
        currency = account_details.get("currency", "")
        balance = float(account_balance.get("current", 0))
        available_balance = float(account_balance.get("available", 0))
        account_type = account.get("account_type", "")
        
        if existing_account:
            # Update the existing account
            update_bank_account_tokens(
                db=db,
                db_obj=existing_account,
                access_token=access_token,
                refresh_token=refresh_token
            )
        else:
            # Create a new account
            account_in = BankAccountCreate(
                user_id=current_user.id,
                account_id=account_id,
                account_name=account_name,
                institution=institution,
                currency=currency,
                balance=balance,
                available_balance=available_balance,
                account_type=account_type,
                access_token=access_token,
                refresh_token=refresh_token
            )
            create_bank_account(db=db, obj_in=account_in)
    
    # Redirect to the frontend
    frontend_url = "/"  # Replace with the actual frontend URL
    return RedirectResponse(url=frontend_url)


@router.get("/me", response_model=Dict[str, Any])
def read_current_user(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get information about the current user.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }