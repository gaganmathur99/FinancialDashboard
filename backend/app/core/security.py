import base64
import os
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from backend.app.core.config import settings


# Password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key for token 
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

# Encryption key for sensitive data
encryption_key = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY.encode("utf-8"))
fernet = Fernet(base64.urlsafe_b64encode(encryption_key))


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Parameters:
    -----------
    subject: Union[str, Any]
        Token subject
    expires_delta: Optional[timedelta]
        Token expiration time
        
    Returns:
    --------
    str
        JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password.
    
    Parameters:
    -----------
    plain_password: str
        Plain password
    hashed_password: str
        Hashed password
        
    Returns:
    --------
    bool
        True if password is valid, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password.
    
    Parameters:
    -----------
    password: str
        Plain password
        
    Returns:
    --------
    str
        Hashed password
    """
    return pwd_context.hash(password)


def encrypt(data: str) -> bytes:
    """
    Encrypt data.
    
    Parameters:
    -----------
    data: str
        Data to encrypt
        
    Returns:
    --------
    bytes
        Encrypted data
    """
    return fernet.encrypt(data.encode("utf-8"))


def decrypt(data: bytes) -> str:
    """
    Decrypt data.
    
    Parameters:
    -----------
    data: bytes
        Data to decrypt
        
    Returns:
    --------
    str
        Decrypted data
    """
    return fernet.decrypt(data).decode("utf-8")