import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import requests, urllib.parse
from backend.app.core.config import settings

# TrueLayer API endpoints
AUTH_URL = "https://auth.truelayer.com"
API_URL = "https://api.truelayer.com"
DATA_API_URL = f"{API_URL}/data/v1"


def create_auth_link(state: str) -> str:
    """
    Create a TrueLayer authentication link for the user to connect their bank.
    
    Parameters:
    -----------
    state: str
        Random state parameter to verify the callback
        
    Returns:
    --------
    str
        Authentication URL for the user to connect their bank
    """
    params = {
        "response_type": "code",
        "client_id": settings.TRUELAYER_CLIENT_ID,
        "scope": settings.SCOPES,
        "redirect_uri": settings.TRUELAYER_REDIRECT_URI,
        "providers": settings.TRUELAYER_PROVIDERS,
        "state": state
    }
    
    # Create the authentication URL
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    return auth_url


def exchange_auth_code(code: str) -> Dict[str, Any]:
    """
    Exchange an authorization code for an access token.
    
    Parameters:
    -----------
    code: str
        Authorization code from the redirect
        
    Returns:
    --------
    Dict[str, Any]
        Access token response
    """
    data = {
        "client_id": settings.TRUELAYER_CLIENT_ID,
        "client_secret": settings.TRUELAYER_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.TRUELAYER_REDIRECT_URI
    }
    
    response = requests.post(f"{AUTH_URL}/connect/token", data=data)
    
    if response.status_code != 200:
        return {"error": response.text}
    
    return response.json()


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh an access token using a refresh token.
    
    Parameters:
    -----------
    refresh_token: str
        Refresh token
        
    Returns:
    --------
    Dict[str, Any]
        Access token response
    """
    data = {
        "client_id": settings.TRUELAYER_CLIENT_ID,
        "client_secret": settings.TRUELAYER_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    response = requests.post(f"{AUTH_URL}/connect/token", data=data)
    
    if response.status_code != 200:
        return {"error": response.text}
    
    return response.json()


def get_user_info(access_token: str) -> Dict[str, Any]:
    """
    Get user information from TrueLayer.
    
    Parameters:
    -----------
    access_token: str
        Access token
        
    Returns:
    --------
    Dict[str, Any]
        User information
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{DATA_API_URL}/info", headers=headers)
    
    if response.status_code != 200:
        return {"error": response.text}
    
    return response.json().get("results", [])[0] if response.json().get("results") else {}


def get_accounts(access_token: str) -> List[Dict[str, Any]]:
    """
    Get accounts from TrueLayer.
    
    Parameters:
    -----------
    access_token: str
        Access token
        
    Returns:
    --------
    List[Dict[str, Any]]
        List of accounts
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{DATA_API_URL}/accounts", headers=headers)
    
    if response.status_code != 200:
        return []
    
    return response.json().get("results", [])


def get_account_details(access_token: str, account_id: str) -> Dict[str, Any]:
    """
    Get account details from TrueLayer.
    
    Parameters:
    -----------
    access_token: str
        Access token
    account_id: str
        Account ID
        
    Returns:
    --------
    Dict[str, Any]
        Account details
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{DATA_API_URL}/accounts/{account_id}", headers=headers)
    
    if response.status_code != 200:
        return {}
    
    return response.json().get("results", [])[0] if response.json().get("results") else {}


def get_account_balance(access_token: str, account_id: str) -> Dict[str, Any]:
    """
    Get account balance from TrueLayer.
    
    Parameters:
    -----------
    access_token: str
        Access token
    account_id: str
        Account ID
        
    Returns:
    --------
    Dict[str, Any]
        Account balance
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{DATA_API_URL}/accounts/{account_id}/balance", headers=headers)
    
    if response.status_code != 200:
        return {}
    
    return response.json().get("results", [])[0] if response.json().get("results") else {}


def get_transactions(
    access_token: str, 
    account_id: str, 
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get transactions from TrueLayer.
    
    Parameters:
    -----------
    access_token: str
        Access token
    account_id: str
        Account ID
    from_date: Optional[str]
        From date in ISO format (YYYY-MM-DD)
    to_date: Optional[str]
        To date in ISO format (YYYY-MM-DD)
        
    Returns:
    --------
    List[Dict[str, Any]]
        List of transactions
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    url = f"{DATA_API_URL}/accounts/{account_id}/transactions"
    
    params = {}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        return []
    
    transactions = response.json().get("results", [])
    
    # Process transactions to match our database schema
    processed_transactions = []
    for tx in transactions:
        processed_tx = {
            "transaction_id": tx.get("transaction_id", ""),
            "transaction_category": tx.get("transaction_category", ""),
            "transaction_classification": json.dumps(tx.get("transaction_classification", [])),
            "timestamp": tx.get("timestamp", ""),
            "date": datetime.fromisoformat(tx.get("timestamp", "").replace("Z", "+00:00")),
            "description": tx.get("description", ""),
            "amount": float(tx.get("amount", "0")),
            "currency": tx.get("currency", ""),
            "merchant_name": tx.get("merchant_name", ""),
            "meta": json.dumps(tx.get("meta", {}))
        }
        processed_transactions.append(processed_tx)
    
    return processed_transactions


def transactions_to_dataframe(transactions: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of transactions to a pandas DataFrame.
    
    Parameters:
    -----------
    transactions: List[Dict[str, Any]]
        List of transactions
        
    Returns:
    --------
    pd.DataFrame
        Pandas DataFrame
    """
    df = pd.DataFrame(transactions)
    
    # Convert timestamp to datetime
    if "timestamp" in df.columns:
        df["date"] = pd.to_datetime(df["timestamp"])
    
    # Convert amount to float
    if "amount" in df.columns:
        df["amount"] = df["amount"].astype(float)
    
    return df