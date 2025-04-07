from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("FERNET_KEY").encode()
fernet = Fernet(key)

def encrypt(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt(data: str) -> str:
    return fernet.decrypt(data.encode()).decode()
