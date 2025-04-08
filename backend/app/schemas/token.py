from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class Token(BaseModel):
    """
    Token schema.
    
    Attributes:
    -----------
    access_token: str
        JWT access token
    token_type: str
        Token type
    """
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """
    Token payload schema.
    
    Attributes:
    -----------
    sub: Optional[int]
        Subject (user ID)
    exp: Optional[float]
        Expiration timestamp
    """
    sub: Optional[int] = None
    exp: Optional[float] = None