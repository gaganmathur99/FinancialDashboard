from datetime import datetime, timedelta
from typing import Optional, Union, Any
import os
import base64
import hashlib
import secrets
import string
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from backend.app.core.config import SECRET_KEY, ALGORITHM, FERNET_KEY

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fernet encryption for tokens
if not FERNET_KEY:
    # Generate a new Fernet key if not available
    key = Fernet.generate_key().decode()
    print(f"WARNING: FERNET_KEY not set. Generated temporary key: {key}")
    print("Set this as an environment variable for production use.")
    fernet = Fernet(key.encode())
else:
    fernet = Fernet(FERNET_KEY.encode())

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        subject: Token subject (typically user ID)
        expires_delta: Token expiration time
        
    Returns:
        str: JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[str]:
    """
    Decode JWT token to get user ID
    
    Args:
        token: JWT token
        
    Returns:
        str: User ID or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hashed version
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

def encrypt(data: str) -> str:
    """
    Encrypt sensitive data
    
    Args:
        data: String data to encrypt
        
    Returns:
        str: Base64 encoded encrypted data
    """
    return fernet.encrypt(data.encode()).decode()

def decrypt(encrypted_data: str) -> str:
    """
    Decrypt sensitive data
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        
    Returns:
        str: Decrypted string
    """
    return fernet.decrypt(encrypted_data.encode()).decode()

def generate_secure_random_string(length: int = 32) -> str:
    """
    Generate a secure random string
    
    Args:
        length: Length of the string to generate
        
    Returns:
        str: Random string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))