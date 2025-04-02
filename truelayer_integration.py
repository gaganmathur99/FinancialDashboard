import os
import requests
import json
from datetime import datetime, timedelta
import pandas as pd

# TrueLayer API endpoints
BASE_URL = "https://auth.truelayer.com"
API_URL = "https://api.truelayer.com"

def create_truelayer_client():
    """
    Create a TrueLayer client config using environment variables.
    
    Returns:
    --------
    dict
        Configuration for making TrueLayer API calls
    """
    # Get TrueLayer API credentials from environment variables
    client_id = os.getenv('TRUELAYER_CLIENT_ID')
    client_secret = os.getenv('TRUELAYER_CLIENT_SECRET')
    
    # Check if we have valid credentials
    if not client_id or not client_secret:
        print("TrueLayer credentials not found. Please set TRUELAYER_CLIENT_ID and TRUELAYER_CLIENT_SECRET environment variables.")
        return {"error": "Missing credentials", "authenticated": False}
    
    try:
        # Get an access token
        token_url = f"{BASE_URL}/connect/token"
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "info accounts balance cards transactions",
            "grant_type": "client_credentials"
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            token_response = response.json()
            access_token = token_response.get("access_token")
            
            return {
                "authenticated": True,
                "access_token": access_token,
                "client_id": client_id,
                "client_secret": client_secret
            }
        else:
            # Return error info if authentication fails
            print(f"TrueLayer authentication failed: {response.status_code} - {response.text}")
            return {
                "authenticated": False, 
                "error": f"Authentication failed: {response.status_code}",
                "error_details": response.text
            }
            
    except Exception as e:
        # Return error info if there's an exception
        print(f"TrueLayer authentication error: {str(e)}")
        return {"authenticated": False, "error": str(e)}

def create_auth_link(client_config, redirect_uri):
    """
    Create a TrueLayer authentication link for the user to connect their bank
    
    Parameters:
    -----------
    client_config: dict
        TrueLayer client configuration
    redirect_uri: str
        URI to redirect to after authentication
        
    Returns:
    --------
    str
        Authentication URL for the user to connect their bank
    """
    try:
        client_id = client_config.get("client_id")
        
        # Construct the authorization URL
        auth_url = f"{BASE_URL}/connect/authorize"
        params = {
            "client_id": client_id,
            "response_type": "code",
            "scope": "info accounts balance cards transactions",
            "redirect_uri": redirect_uri,
            "providers": "uk-oauth-all uk-oauth-ob-all uk-oauth-ob2-all uk-cs-mock"
        }
        
        # Construct URL with query parameters
        auth_link = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return auth_link
    
    except Exception as e:
        # Log error and return empty string
        print(f"Error creating auth link: {str(e)}")
        return ""

def exchange_auth_code(client_config, auth_code, redirect_uri):
    """
    Exchange an authorization code for an access token
    
    Parameters:
    -----------
    client_config: dict
        TrueLayer client configuration
    auth_code: str
        Authorization code from the redirect
    redirect_uri: str
        Redirect URI used in the initial authorization
        
    Returns:
    --------
    dict
        Access token response
    """
    try:
        client_id = client_config.get("client_id")
        client_secret = client_config.get("client_secret")
        
        token_url = f"{BASE_URL}/connect/token"
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Log error and return empty dict
            print(f"Error exchanging auth code: {response.status_code} - {response.text}")
            return {}
            
    except Exception as e:
        # Log error and return empty dict
        print(f"Exception exchanging auth code: {str(e)}")
        return {}

def get_account_info(access_token):
    """
    Get account information using the TrueLayer API
    
    Parameters:
    -----------
    access_token: str
        Access token for the connected user
        
    Returns:
    --------
    list
        List of account dictionaries
    """    
    try:
        accounts_url = f"{API_URL}/data/v1/accounts"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(accounts_url, headers=headers)
        
        if response.status_code == 200:
            accounts_data = response.json().get("results", [])
            
            # Format the account information
            accounts = []
            for account in accounts_data:
                account_info = {
                    "account_id": account.get("account_id"),
                    "name": account.get("display_name"),
                    "type": account.get("account_type"),
                    "balance": 0.0,  # Will get balance separately
                    "currency": account.get("currency"),
                    "account_number": account.get("account_number", {}).get("number", ""),
                    "sort_code": account.get("account_number", {}).get("sort_code", ""),
                    "provider": account.get("provider", {})
                }
                
                # Get balance for this account
                balance_url = f"{API_URL}/data/v1/accounts/{account_info['account_id']}/balance"
                balance_response = requests.get(balance_url, headers=headers)
                
                if balance_response.status_code == 200:
                    balance_data = balance_response.json().get("results", [{}])[0]
                    account_info["balance"] = balance_data.get("current", 0.0)
                
                accounts.append(account_info)
            
            return accounts
        else:
            # Log error and return empty list
            print(f"Error fetching accounts: {response.status_code} - {response.text}")
            return []
    
    except Exception as e:
        # Log error and return empty list
        print(f"Exception fetching accounts: {str(e)}")
        return []

def get_transactions(access_token, account_id, start_date, end_date):
    """
    Get transactions for an account using the TrueLayer API
    
    Parameters:
    -----------
    access_token: str
        Access token for the connected user
    account_id: str
        Account ID to get transactions for
    start_date: datetime.date
        Start date for transactions
    end_date: datetime.date
        End date for transactions
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing transaction data
    """    
    try:
        # Format dates as required by TrueLayer
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        transactions_url = f"{API_URL}/data/v1/accounts/{account_id}/transactions"
        params = {
            "from": from_date,
            "to": to_date
        }
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(transactions_url, params=params, headers=headers)
        
        if response.status_code == 200:
            transactions_data = response.json().get("results", [])
            
            # Format the transaction information
            transactions = []
            for transaction in transactions_data:
                # Determine if it's income or expense
                amount = transaction.get("amount", 0.0)
                if amount < 0:
                    tx_type = "expense"
                    amount = abs(amount)
                else:
                    tx_type = "income"
                
                tx_data = {
                    "date": transaction.get("timestamp", "").split("T")[0],
                    "description": transaction.get("description", ""),
                    "amount": amount,
                    "category": transaction.get("transaction_category", "Uncategorized"),
                    "type": tx_type,
                    "account_id": account_id,
                    "transaction_id": transaction.get("transaction_id", ""),
                    "merchant": transaction.get("merchant_name", transaction.get("description", ""))
                }
                
                transactions.append(tx_data)
            
            # Convert to DataFrame
            if transactions:
                df = pd.DataFrame(transactions)
                df["date"] = pd.to_datetime(df["date"]).dt.date
                return df
            else:
                # Return empty DataFrame if no transactions found
                return pd.DataFrame(columns=["date", "description", "amount", "category", "type", "account_id", "transaction_id", "merchant"])
        else:
            # Log error and return empty DataFrame
            print(f"Error fetching transactions: {response.status_code} - {response.text}")
            return pd.DataFrame(columns=["date", "description", "amount", "category", "type", "account_id", "transaction_id", "merchant"])
    
    except Exception as e:
        # Log error and return empty DataFrame
        print(f"Exception fetching transactions: {str(e)}")
        return pd.DataFrame(columns=["date", "description", "amount", "category", "type", "account_id", "transaction_id", "merchant"])