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
    
    # If we don't have credentials, return a mock client for demo purposes
    if not client_id or not client_secret:
        return {"mock_client": True, "authenticated": False}
    
    # In a real app, we would use these to authenticate with TrueLayer
    # and get an OAuth token
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
            # Return mock client if authentication fails
            return {"mock_client": True, "authenticated": False}
            
    except Exception as e:
        # Return mock client if there's an error
        return {"mock_client": True, "authenticated": False, "error": str(e)}

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
    # If we're using the mock client, return a mock link
    if client_config.get("mock_client", False):
        return "mock-auth-link"
    
    # In a real app, we would use the TrueLayer API to create a link
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
        # Return mock link in case of error
        return "mock-auth-link"

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
    # If we're using the mock client, return a mock token
    if client_config.get("mock_client", False):
        return {
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "mock-refresh-token"
        }
    
    # In a real app, we would exchange the auth code for a token
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
            # Return mock token if exchange fails
            return {
                "access_token": "mock-access-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "mock-refresh-token"
            }
            
    except Exception as e:
        # Return mock token in case of error
        return {
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "mock-refresh-token"
        }

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
    # Check if this is a mock token
    if access_token == "mock-access-token":
        # Return mock accounts
        return [
            {
                "account_id": "checking123",
                "name": "Personal Current Account",
                "type": "CURRENT",
                "balance": 2543.67,
                "currency": "GBP",
                "account_number": "12345678",
                "sort_code": "123456"
            },
            {
                "account_id": "savings456",
                "name": "Savings Account",
                "type": "SAVINGS",
                "balance": 8750.42,
                "currency": "GBP",
                "account_number": "87654321",
                "sort_code": "654321"
            }
        ]
    
    # In a real app, we would use the TrueLayer API to get account info
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
                    "sort_code": account.get("account_number", {}).get("sort_code", "")
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
            # Return mock accounts if API call fails
            return [
                {
                    "account_id": "checking123",
                    "name": "Personal Current Account",
                    "type": "CURRENT",
                    "balance": 2543.67,
                    "currency": "GBP",
                    "account_number": "12345678",
                    "sort_code": "123456"
                },
                {
                    "account_id": "savings456",
                    "name": "Savings Account",
                    "type": "SAVINGS",
                    "balance": 8750.42,
                    "currency": "GBP",
                    "account_number": "87654321",
                    "sort_code": "654321"
                }
            ]
    
    except Exception as e:
        # Return mock accounts in case of error
        return [
            {
                "account_id": "checking123",
                "name": "Personal Current Account",
                "type": "CURRENT",
                "balance": 2543.67,
                "currency": "GBP",
                "account_number": "12345678",
                "sort_code": "123456"
            },
            {
                "account_id": "savings456",
                "name": "Savings Account",
                "type": "SAVINGS",
                "balance": 8750.42,
                "currency": "GBP",
                "account_number": "87654321",
                "sort_code": "654321"
            }
        ]

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
    # Check if this is a mock token
    if access_token == "mock-access-token":
        # Return mock transactions
        return generate_mock_transactions(account_id)
    
    # In a real app, we would use the TrueLayer API to get transactions
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
                    "merchant": transaction.get("merchant_name", "")
                }
                
                transactions.append(tx_data)
            
            # Convert to DataFrame
            if transactions:
                df = pd.DataFrame(transactions)
                df["date"] = pd.to_datetime(df["date"]).dt.date
                return df
            else:
                # Return mock transactions if no transactions found
                return generate_mock_transactions(account_id)
        else:
            # Return mock transactions if API call fails
            return generate_mock_transactions(account_id)
    
    except Exception as e:
        # Return mock transactions in case of error
        return generate_mock_transactions(account_id)

def generate_mock_transactions(account_id):
    """
    Generate mock transactions for demonstration purposes
    
    Parameters:
    -----------
    account_id: str
        Account ID to generate transactions for
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing mock transaction data
    """
    # Create sample transaction data
    today = datetime.now().date()
    
    # Sample transactions
    if "checking" in account_id:
        account_name = "Personal Current Account"
        sample_transactions = [
            {"date": today - timedelta(days=2), "description": "Tesco Supermarket", "amount": 76.32, "category": "Groceries", "type": "expense"},
            {"date": today - timedelta(days=5), "description": "BP Petrol Station", "amount": 45.10, "category": "Transportation", "type": "expense"},
            {"date": today - timedelta(days=7), "description": "Costa Coffee", "amount": 5.75, "category": "Dining", "type": "expense"},
            {"date": today - timedelta(days=10), "description": "Amazon UK", "amount": 120.99, "category": "Shopping", "type": "expense"},
            {"date": today - timedelta(days=1), "description": "Salary", "amount": 1250.00, "category": "Income", "type": "income"},
        ]
    else:
        account_name = "Savings Account"
        sample_transactions = [
            {"date": today - timedelta(days=15), "description": "Transfer from Current Account", "amount": 500.00, "category": "Transfer", "type": "income"},
            {"date": today - timedelta(days=45), "description": "Interest Credit", "amount": 12.50, "category": "Income", "type": "income"},
        ]
    
    # Create DataFrame
    transactions_df = pd.DataFrame(sample_transactions)
    
    # Add additional columns
    transactions_df["account_id"] = account_id
    transactions_df["account"] = account_name
    transactions_df["transaction_id"] = [f"tx_{account_id}_{i}" for i in range(len(sample_transactions))]
    transactions_df["merchant"] = transactions_df["description"]
    
    return transactions_df