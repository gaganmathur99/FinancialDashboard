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

# Helper functions for encryption/decryption
def encrypt(data: str) -> bytes:
    """Encrypt data using Fernet"""
    return fernet.encrypt(data.encode("utf-8"))

def decrypt(data: bytes) -> str:
    """Decrypt data using Fernet"""
    return fernet.decrypt(data).decode("utf-8")

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

# Create a test user for demo purposes
cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'test_user'")
count = cursor.fetchone()[0]
if count == 0:
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
        ("test_user", "test@example.com", "password")
    )
    conn.commit()
    print("Test user created: test_user")
    
    # Create a demo bank account for the test user
    cursor.execute("SELECT id FROM users WHERE username = 'test_user'")
    user_id = cursor.fetchone()[0]
    cursor.execute(
        """
        INSERT INTO bank_accounts 
        (user_id, account_id, account_name, institution, account_type, currency, balance, 
        available_balance, access_token, refresh_token)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            "acc_12345",
            "Test Checking Account",
            "Demo Bank",
            "checking",
            "GBP",
            1250.45,
            1250.45,
            encrypt("demo_access_token").decode('utf-8'),
            encrypt("demo_refresh_token").decode('utf-8')
        )
    )
    conn.commit()
    print("Demo bank account created for test_user")
    
    # Add some transactions for the demo account
    cursor.execute("SELECT id FROM bank_accounts WHERE user_id = ? AND account_id = ?", (user_id, "acc_12345"))
    bank_account_id = cursor.fetchone()[0]
    
    demo_transactions = [
        {
            "transaction_id": "tx_001",
            "transaction_category": "groceries",
            "timestamp": "2025-03-15T10:30:00Z",
            "date": "2025-03-15",
            "description": "Tesco Supermarket",
            "amount": -45.67,
            "currency": "GBP",
            "merchant_name": "Tesco"
        },
        {
            "transaction_id": "tx_002",
            "transaction_category": "salary",
            "timestamp": "2025-03-01T09:00:00Z",
            "date": "2025-03-01",
            "description": "March Salary",
            "amount": 2500.00,
            "currency": "GBP",
            "merchant_name": "Employer Inc"
        },
        {
            "transaction_id": "tx_003",
            "transaction_category": "dining",
            "timestamp": "2025-03-10T19:15:00Z",
            "date": "2025-03-10",
            "description": "Restaurant Payment",
            "amount": -78.50,
            "currency": "GBP",
            "merchant_name": "The Local Restaurant"
        }
    ]
    
    for tx in demo_transactions:
        cursor.execute(
            """
            INSERT INTO transactions 
            (bank_account_id, transaction_id, transaction_category, timestamp, date, 
            description, amount, currency, merchant_name, meta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bank_account_id,
                tx["transaction_id"],
                tx["transaction_category"],
                tx["timestamp"],
                tx["date"],
                tx["description"],
                tx["amount"],
                tx["currency"],
                tx["merchant_name"],
                "{}"
            )
        )
    conn.commit()
    print("Demo transactions created for test_user")

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
        # Exchange code for tokens
        tokens = exchange_code_for_token(code)
        
        # In a real application, you would:
        # 1. Authenticate the user (create if new)
        # 2. Store encrypted tokens in the database
        # 3. Link to user's account
        
        # We'll just create a dummy user ID for now
        user_id = "user_1"
        
        # Store the tokens in the database
        # First check if we already have accounts for this user
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
        user_record = cursor.fetchone()
        
        if not user_record:
            # Create a dummy user if it doesn't exist
            cursor.execute(
                "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
                (user_id, f"{user_id}@example.com", "hashed_password")
            )
            conn.commit()
            cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
            user_record = cursor.fetchone()
        
        # Encrypt tokens for storage
        encrypted_access_token = encrypt(tokens["access_token"])
        encrypted_refresh_token = encrypt(tokens["refresh_token"])
        
        # Return the response
        return {
            "message": "Authentication successful", 
            "tokens": {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "expires_in": tokens["expires_in"]
            },
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accounts")
def get_accounts(access_token: str):
    """Get accounts from TrueLayer API"""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.truelayer.com/data/v1/accounts", headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    accounts_data = response.json().get("results", [])
    
    # In a real application, we would save these accounts to the database
    # and associate them with the user's record
    for account in accounts_data:
        # Get account information
        account_id = account.get("account_id")
        if not account_id:
            continue
        
        # For simplicity, we'll use a dummy user ID
        user_id = 1  # This would normally come from the authenticated user
        
        # Check if we already have this account in the database
        cursor.execute(
            "SELECT id FROM bank_accounts WHERE user_id = ? AND account_id = ?",
            (user_id, account_id)
        )
        existing_account = cursor.fetchone()
        
        if not existing_account:
            # If not, insert it
            cursor.execute(
                """
                INSERT INTO bank_accounts 
                (user_id, account_id, account_name, institution, account_type, currency, balance, 
                available_balance, access_token, refresh_token)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    account_id,
                    account.get("display_name", "Unknown Account"),
                    account.get("provider", {}).get("display_name", "Unknown Bank"),
                    account.get("account_type", "Unknown"),
                    account.get("currency", "GBP"),
                    account.get("balance", 0.0),
                    account.get("available_balance", 0.0),
                    encrypt(access_token).decode('utf-8'),  # Encrypt and store tokens
                    encrypt(access_token).decode('utf-8')  # Using same token for demo
                )
            )
            conn.commit()
        else:
            # If it exists, update it
            cursor.execute(
                """
                UPDATE bank_accounts
                SET account_name = ?, institution = ?, account_type = ?, currency = ?, 
                balance = ?, available_balance = ?, access_token = ?, refresh_token = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND account_id = ?
                """,
                (
                    account.get("display_name", "Unknown Account"),
                    account.get("provider", {}).get("display_name", "Unknown Bank"),
                    account.get("account_type", "Unknown"),
                    account.get("currency", "GBP"),
                    account.get("balance", 0.0),
                    account.get("available_balance", 0.0),
                    encrypt(access_token).decode('utf-8'),  # Encrypt and store tokens
                    encrypt(access_token).decode('utf-8'),  # Using same token for demo
                    user_id,
                    account_id
                )
            )
            conn.commit()
    
    return accounts_data

@app.get("/api/transactions")
def get_transactions(access_token: str, account_id: str, from_date: str, to_date: str):
    """Get transactions from TrueLayer API"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.truelayer.com/data/v1/accounts/{account_id}/transactions?from={from_date}&to={to_date}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    transactions_data = response.json().get("results", [])
    
    # In a real application, we would store these transactions in the database
    # For this example, we'll simply demonstrate how to do it
    
    # Get the bank account ID from the database
    user_id = 1  # This would normally come from the authenticated user
    
    # Find the bank_account record ID
    cursor.execute(
        "SELECT id FROM bank_accounts WHERE user_id = ? AND account_id = ?",
        (user_id, account_id)
    )
    bank_account_record = cursor.fetchone()
    
    if bank_account_record:
        bank_account_id = bank_account_record[0]
        
        # Update last_synced timestamp
        cursor.execute(
            "UPDATE bank_accounts SET last_synced = CURRENT_TIMESTAMP WHERE id = ?",
            (bank_account_id,)
        )
        conn.commit()
        
        # Store each transaction
        for transaction in transactions_data:
            transaction_id = transaction.get("transaction_id")
            if not transaction_id:
                continue
                
            # Check if transaction exists
            cursor.execute(
                "SELECT id FROM transactions WHERE bank_account_id = ? AND transaction_id = ?",
                (bank_account_id, transaction_id)
            )
            existing_transaction = cursor.fetchone()
            
            if not existing_transaction:
                # Insert new transaction
                cursor.execute(
                    """
                    INSERT INTO transactions 
                    (bank_account_id, transaction_id, transaction_category, timestamp, date, 
                    description, amount, currency, merchant_name, meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bank_account_id,
                        transaction_id,
                        transaction.get("transaction_category", "uncategorized"),
                        transaction.get("timestamp", ""),
                        transaction.get("timestamp", "").split("T")[0],  # Just the date part
                        transaction.get("description", ""),
                        transaction.get("amount", 0.0),
                        transaction.get("currency", "GBP"),
                        transaction.get("merchant_name", ""),
                        str(transaction.get("meta", {}))
                    )
                )
                conn.commit()
    
    return transactions_data

@app.get("/api/user/{user_id}")
def get_user_info(user_id: str):
    """Get user's account information and basic stats"""
    try:
        # First check if the user exists
        cursor.execute("SELECT id, username, email FROM users WHERE username = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Get the user's accounts
        cursor.execute("""
        SELECT id, account_id, account_name, institution, account_type, currency, 
               balance, available_balance, last_synced
        FROM bank_accounts
        WHERE user_id = ? AND is_active = 1
        """, (user[0],))
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                "id": row[0],
                "account_id": row[1],
                "account_name": row[2],
                "institution": row[3],
                "account_type": row[4],
                "currency": row[5],
                "balance": row[6],
                "available_balance": row[7],
                "last_synced": row[8]
            })
            
        # Get some basic transaction stats
        total_transactions = 0
        accounts_with_transactions = []
        
        for account in accounts:
            cursor.execute(
                "SELECT COUNT(*) FROM transactions WHERE bank_account_id = ?", 
                (account["id"],)
            )
            count = cursor.fetchone()[0]
            total_transactions += count
            
            if count > 0:
                accounts_with_transactions.append(account["account_name"])
        
        return {
            "user_id": user[1],
            "email": user[2],
            "accounts": accounts,
            "accounts_count": len(accounts),
            "accounts_with_transactions": accounts_with_transactions,
            "total_transactions": total_transactions
        }
    except Exception as e:
        print(f"Error in get_user_info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/accounts")
def get_user_accounts(user_id: str):
    """Get all bank accounts for a user"""
    try:
        # First check if the user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Get the user's accounts
        cursor.execute("""
        SELECT id, account_id, account_name, institution, account_type, currency, 
               balance, available_balance, last_synced
        FROM bank_accounts
        WHERE user_id = ? AND is_active = 1
        """, (user[0],))
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                "id": row[0],
                "account_id": row[1],
                "account_name": row[2],
                "institution": row[3],
                "account_type": row[4],
                "currency": row[5],
                "balance": row[6],
                "available_balance": row[7],
                "last_synced": row[8]
            })
            
        return accounts
    except Exception as e:
        print(f"Error in get_user_accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/transactions")
def get_user_transactions(user_id: str, account_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 50, offset: int = 0):
    """Get transactions for a user, optionally filtered by account and date range"""
    try:
        # First check if the user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build the query
        query = """
        SELECT t.id, t.transaction_id, t.transaction_category, t.timestamp, t.date,
               t.description, t.amount, t.currency, t.merchant_name, 
               ba.account_name, ba.institution
        FROM transactions t
        JOIN bank_accounts ba ON t.bank_account_id = ba.id
        WHERE ba.user_id = ?
        """
        params = [user[0]]
        
        # Add filters if provided
        if account_id:
            query += " AND ba.id = ?"
            params.append(account_id)
            
        if start_date:
            query += " AND t.date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND t.date <= ?"
            params.append(end_date)
            
        # Add order, limit and offset
        query += " ORDER BY t.date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute the query
        cursor.execute(query, params)
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                "id": row[0],
                "transaction_id": row[1],
                "category": row[2],
                "timestamp": row[3],
                "date": row[4],
                "description": row[5],
                "amount": row[6],
                "currency": row[7],
                "merchant": row[8],
                "account_name": row[9],
                "institution": row[10]
            })
            
        return transactions
    except Exception as e:
        print(f"Error in get_user_transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the app
if __name__ == "__main__":
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
    )