import os
import requests
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, date, timedelta
from urllib.parse import urlencode

from backend.app.core.config import (
    TRUELAYER_CLIENT_ID,
    TRUELAYER_CLIENT_SECRET,
    TRUELAYER_PROVIDERS,
)

# TrueLayer API Endpoints
TRUELAYER_AUTH_URL = "https://auth.truelayer.com"
TRUELAYER_API_URL = "https://api.truelayer.com"
TRUELAYER_DATA_API_URL = f"{TRUELAYER_API_URL}/data/v1"
TRUELAYER_AUTH_API_URL = f"{TRUELAYER_API_URL}/auth"

def create_auth_link(redirect_uri: str, scope: str = "info accounts balance transactions") -> str:
    """
    Create a TrueLayer authentication link for the user to connect their bank
    
    Args:
        redirect_uri: URI to redirect to after authentication
        scope: TrueLayer API scope
        
    Returns:
        str: Authentication URL for the user to connect their bank
    """
    params = {
        "response_type": "code",
        "client_id": TRUELAYER_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "providers": TRUELAYER_PROVIDERS
    }
    
    auth_url = f"{TRUELAYER_AUTH_URL}/?{urlencode(params)}"
    return auth_url

def exchange_code_for_token(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    """
    Exchange an authorization code for an access token
    
    Args:
        code: Authorization code from the redirect
        redirect_uri: Redirect URI used in the initial authorization
        
    Returns:
        dict: Access token response or None if error
    """
    payload = {
        "grant_type": "authorization_code",
        "client_id": TRUELAYER_CLIENT_ID,
        "client_secret": TRUELAYER_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "code": code
    }
    
    try:
        response = requests.post(f"{TRUELAYER_AUTH_API_URL}/token", data=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error exchanging code for token: {e}")
        return None

def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """
    Refresh an access token using a refresh token
    
    Args:
        refresh_token: Refresh token
        
    Returns:
        dict: New access token response or None if error
    """
    payload = {
        "grant_type": "refresh_token",
        "client_id": TRUELAYER_CLIENT_ID,
        "client_secret": TRUELAYER_CLIENT_SECRET,
        "refresh_token": refresh_token
    }
    
    try:
        response = requests.post(f"{TRUELAYER_AUTH_API_URL}/token", data=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error refreshing token: {e}")
        return None

def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Get user information from TrueLayer
    
    Args:
        access_token: Access token for the user
        
    Returns:
        dict: User information or None if error
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{TRUELAYER_DATA_API_URL}/info", headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [{}])[0] if data.get("results") else {}
    except requests.RequestException as e:
        print(f"Error getting user info: {e}")
        return None

def get_accounts(access_token: str) -> List[Dict[str, Any]]:
    """
    Get accounts from TrueLayer
    
    Args:
        access_token: Access token for the user
        
    Returns:
        list: List of account dictionaries
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{TRUELAYER_DATA_API_URL}/accounts", headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.RequestException as e:
        print(f"Error getting accounts: {e}")
        return []

def get_account_balance(access_token: str, account_id: str) -> Optional[Dict[str, Any]]:
    """
    Get account balance from TrueLayer
    
    Args:
        access_token: Access token for the user
        account_id: Account ID
        
    Returns:
        dict: Account balance information or None if error
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{TRUELAYER_DATA_API_URL}/accounts/{account_id}/balance", headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [{}])[0] if data.get("results") else None
    except requests.RequestException as e:
        print(f"Error getting account balance: {e}")
        return None

def get_account_details(access_token: str, account_id: str) -> Optional[Dict[str, Any]]:
    """
    Get account details from TrueLayer
    
    Args:
        access_token: Access token for the user
        account_id: Account ID
        
    Returns:
        dict: Account details or None if error
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{TRUELAYER_DATA_API_URL}/accounts/{account_id}/details", headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [{}])[0] if data.get("results") else None
    except requests.RequestException as e:
        print(f"Error getting account details: {e}")
        return None

def get_transactions(
    access_token: str, 
    account_id: str, 
    from_date: Optional[date] = None, 
    to_date: Optional[date] = None
) -> pd.DataFrame:
    """
    Get transactions from TrueLayer
    
    Args:
        access_token: Access token for the user
        account_id: Account ID
        from_date: Start date for transactions
        to_date: End date for transactions
        
    Returns:
        pd.DataFrame: DataFrame containing transaction data
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Default to last 90 days if no dates provided
    if not from_date:
        from_date = (datetime.now() - timedelta(days=90)).date()
    if not to_date:
        to_date = datetime.now().date()
    
    # Format dates for TrueLayer API
    from_date_str = from_date.isoformat()
    to_date_str = to_date.isoformat()
    
    params = {
        "from": from_date_str,
        "to": to_date_str
    }
    
    try:
        response = requests.get(
            f"{TRUELAYER_DATA_API_URL}/accounts/{account_id}/transactions", 
            headers=headers,
            params=params
        )
        response.raise_for_status()
        data = response.json()
        transactions = data.get("results", [])
        
        if not transactions:
            return pd.DataFrame()
        
        # Convert to DataFrame and process
        df = pd.DataFrame(transactions)
        
        # Convert date strings to datetime
        if "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        
        # Standardize column names
        column_mapping = {
            "transaction_id": "transaction_id",
            "timestamp": "datetime",
            "description": "description",
            "amount": "amount",
            "currency": "currency",
            "transaction_type": "type",
            "transaction_category": "category",
            "merchant_name": "merchant"
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Fill NaN values
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].fillna("")
                
        return df
    
    except requests.RequestException as e:
        print(f"Error getting transactions: {e}")
        return pd.DataFrame()