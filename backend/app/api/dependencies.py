from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime

from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.core.security import decrypt
from backend.app.db.base import get_db
from backend.app.crud import get_user_by_id
from backend.app.models.user import User
from backend.app.models.bank import BankAccount
from backend.app.schemas.token import TokenPayload

# OAuth2 token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current authenticated user based on the JWT token.
    
    Parameters:
    -----------
    db: Session
        Database session
    token: str
        JWT token
        
    Returns:
    --------
    User
        The authenticated user
        
    Raises:
    -------
    HTTPException
        If authentication fails
    """
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token_data = TokenPayload(**payload)
        
        # Check token expiration
        if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user
    user = get_user_by_id(db, token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.
    
    Parameters:
    -----------
    current_user: User
        The current authenticated user
        
    Returns:
    --------
    User
        The authenticated active user
        
    Raises:
    -------
    HTTPException
        If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active superuser.
    
    Parameters:
    -----------
    current_user: User
        The current authenticated user
        
    Returns:
    --------
    User
        The authenticated active superuser
        
    Raises:
    -------
    HTTPException
        If the user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def check_bank_account_owner(
    bank_account: BankAccount,
    current_user: User = Depends(get_current_user),
) -> BankAccount:
    """
    Check if the current user is the owner of the bank account.
    
    Parameters:
    -----------
    bank_account: BankAccount
        The bank account to check
    current_user: User
        The current authenticated user
        
    Returns:
    --------
    BankAccount
        The bank account if the user is the owner
        
    Raises:
    -------
    HTTPException
        If the user is not the owner
    """
    if bank_account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return bank_account