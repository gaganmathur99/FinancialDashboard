import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import requests
import os
import base64
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables from .env file
load_dotenv()

# TrueLayer credentials
TRUELAYER_CLIENT_ID = os.getenv("TRUELAYER_CLIENT_ID")
TRUELAYER_CLIENT_SECRET = os.getenv("TRUELAYER_CLIENT_SECRET")
REDIRECT_URI = "https://console.truelayer.com/redirect-page"
AUTH_URL = "https://auth.truelayer.com/"
TOKEN_URL = "https://auth.truelayer.com/connect/token"
SCOPES = "info accounts balance transactions offline_access"

# Setup encryption
# Generate a valid Fernet key
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
encryption_key = SECRET_KEY.encode("utf-8")
# Ensure the key is the right size (32 bytes)
if len(encryption_key) < 32:
    encryption_key = encryption_key.ljust(32, b'=')
elif len(encryption_key) > 32:
    encryption_key = encryption_key[:32]

# Create a valid Fernet key (url-safe base64-encoded)
fernet_key = base64.urlsafe_b64encode(encryption_key)
fernet = Fernet(fernet_key)

# Initialize the SQLite database
conn = sqlite3.connect("finance_dashboard.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_superuser BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS bank_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    account_id TEXT NOT NULL,
    account_name TEXT NOT NULL,
    institution TEXT NOT NULL,
    account_type TEXT,
    currency TEXT NOT NULL,
    balance REAL NOT NULL,
    available_balance REAL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expires_at TIMESTAMP,
    last_synced TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE (user_id, account_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_account_id INTEGER NOT NULL,
    transaction_id TEXT NOT NULL,
    transaction_category TEXT NOT NULL,
    transaction_classification TEXT,
    timestamp TEXT,
    date TIMESTAMP NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    currency TEXT,
    merchant_name TEXT,
    meta TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts (id),
    UNIQUE (bank_account_id, transaction_id)
)
''')

conn.commit()

# Helper functions for encryption/decryption
def encrypt(data: str) -> bytes:
    """Encrypt data using Fernet"""
    return fernet.encrypt(data.encode("utf-8"))

def decrypt(data: bytes) -> str:
    """Decrypt data using Fernet"""
    return fernet.decrypt(data).decode("utf-8")

# TrueLayer API helper functions
def get_auth_url():
    """Generate TrueLayer authentication URL"""
    params = {
        "response_type": "code",
        "client_id": TRUELAYER_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "providers": "uk-ob-all uk-oauth-all",
        "state": "personal-finance-app"
    }
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{AUTH_URL}?{query_string}"

def exchange_code_for_token(code: str):
    """Exchange authorization code for access and refresh tokens"""
    data = {
        "grant_type": "authorization_code",
        "client_id": TRUELAYER_CLIENT_ID,
        "client_secret": TRUELAYER_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code != 200:
        raise Exception(f"Failed to exchange code for token: {response.json()}")
    
    tokens = response.json()
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "expires_in": tokens.get("expires_in", 3600)
    }

# Create FastAPI app
app = FastAPI(
    title="Personal Finance API",
    description="API for managing personal finances",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
def root():
    """Root endpoint that returns a welcome message."""
    return {
        "message": "Welcome to the Personal Finance API",
        "version": "0.1.0",
        "docs_url": "/docs",
    }

@app.get("/health")
def health_check():
    """Health check endpoint to verify the API is running and connected to the database."""
    try:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        return {
            "status": "ok",
            "database": "connected" if result else "disconnected",
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
        }

@app.get("/api/auth/login")
def login():
    """Redirect to TrueLayer authentication URL"""
    auth_url = get_auth_url()
    return RedirectResponse(auth_url)

@app.get("/api/auth/callback")
def callback(request: Request):
    """Handle callback from TrueLayer authentication"""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    try:
        tokens = exchange_code_for_token(code)
        # Here you would normally save the tokens to the database
        # For demo purposes, we'll just return them
        return {"message": "Authentication successful", "tokens": tokens}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accounts")
def get_accounts(access_token: str):
    """Get accounts from TrueLayer API"""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.truelayer.com/data/v1/accounts", headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json().get("results", [])

@app.get("/api/transactions")
def get_transactions(access_token: str, account_id: str, from_date: str, to_date: str):
    """Get transactions from TrueLayer API"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.truelayer.com/data/v1/accounts/{account_id}/transactions?from={from_date}&to={to_date}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json().get("results", [])

# Run the app
if __name__ == "__main__":
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
    )