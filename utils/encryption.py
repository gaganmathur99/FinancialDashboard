import os
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key
import logging

load_dotenv()

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Fernet instance
fernet = None

def generate_key():
    """Generate a new Fernet key and save it to .env file"""
    key = Fernet.generate_key()
    key_str = key.decode()
    logger.info(f"Generated new Fernet key: {key_str}")
    
    # Update the .env file with the new key
    env_path = os.path.join(os.getcwd(), '.env')
    set_key(env_path, 'FERNET_KEY', key_str)
    
    return key

def get_fernet_key():
    """Get the Fernet key from environment or generate a new one"""
    global fernet
    
    # Get key from environment
    key = os.getenv("FERNET_KEY")
    
    # If no key exists, generate one
    if not key:
        key = generate_key()
    
    try:
        # Create Fernet instance with the key
        fernet = Fernet(key if isinstance(key, bytes) else key.encode())
        return key
    except Exception as e:
        logger.error(f"Error initializing Fernet: {str(e)}")
        # If the key is invalid, generate a new one
        key = generate_key()
        fernet = Fernet(key if isinstance(key, bytes) else key.encode())
        return key

def encrypt(data):
    """
    Encrypt the data using Fernet
    
    Parameters:
    -----------
    data: str
        The data to encrypt
        
    Returns:
    --------
    str
        The encrypted data as a string
    """
    global fernet
    
    if not fernet:
        get_fernet_key()
    
    if not isinstance(data, str):
        data = str(data)
    
    try:
        return fernet.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        # Try reinitializing the fernet instance
        get_fernet_key()
        return fernet.encrypt(data.encode()).decode()

def decrypt(data):
    """
    Decrypt the data using Fernet
    
    Parameters:
    -----------
    data: str
        The encrypted data to decrypt
        
    Returns:
    --------
    str
        The decrypted data as a string
    """
    global fernet
    
    if not fernet:
        get_fernet_key()
    
    try:
        return fernet.decrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        raise ValueError(f"Unable to decrypt data: {str(e)}")