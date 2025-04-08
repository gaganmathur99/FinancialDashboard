import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# JWT Authentication settings
SECRET_KEY = os.getenv("SECRET_KEY", "temporary_secret_key_replace_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finance_app.db")

# TrueLayer settings
TRUELAYER_CLIENT_ID = os.getenv("TRUELAYER_CLIENT_ID")
TRUELAYER_CLIENT_SECRET = os.getenv("TRUELAYER_CLIENT_SECRET")
TRUELAYER_REDIRECT_URI = os.getenv("TRUELAYER_REDIRECT_URI", "http://localhost:5000/api/v1/auth/truelayer/callback")
TRUELAYER_PROVIDERS = os.getenv("TRUELAYER_PROVIDERS", "uk-ob-all uk-oauth-all")

# Encryption
FERNET_KEY = os.getenv("FERNET_KEY")  # For token encryption

# API settings
API_V1_PREFIX = "/api/v1"
PROJECT_NAME = "Personal Finance Manager"
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# CORS settings
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
    "https://localhost",
    "https://localhost:3000",
    "https://localhost:5000",
    "https://localhost:8000",
]

# Validation
if not TRUELAYER_CLIENT_ID:
    print("WARNING: TRUELAYER_CLIENT_ID not set. TrueLayer integration will not work.")

if not TRUELAYER_CLIENT_SECRET:
    print("WARNING: TRUELAYER_CLIENT_SECRET not set. TrueLayer integration will not work.")