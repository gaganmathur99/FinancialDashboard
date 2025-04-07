from sqlalchemy import Column, Integer, String
from backend.db import Base

class UserAccount(Base):
    __tablename__ = 'user_accounts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    account_id = Column(String)
    account_type = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
