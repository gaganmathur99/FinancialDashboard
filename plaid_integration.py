import os
from datetime import datetime, timedelta
import pandas as pd

# This file provides a simplified mock version of the Plaid API integration
# For actual integration, you would use the plaid-python library
# import plaid
# from plaid.api import plaid_api
# from plaid.model.link_token_create_request import LinkTokenCreateRequest
# etc.

def create_plaid_client():
    """
    Mock version of creating a Plaid API client.
    
    Returns:
    --------
    Mock client object
    """
    # Check if we have credentials
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    
    # In a real application, we would verify these and use them
    # For demo purposes, we return a mock client
    return {"mock_client": True}

def create_link_token(client_name, user_id):
    """
    Mock version of creating a Plaid Link token
    
    Parameters:
    -----------
    client_name: str
        Name of your application
    user_id: str
        Identifier for the user
        
    Returns:
    --------
    str
        Dummy link token
    """
    # In a real app, this would call the Plaid API
    return "mock-link-token"

def exchange_public_token(public_token):
    """
    Mock version of exchanging a public token for an access token
    
    Parameters:
    -----------
    public_token: str
        Public token received from Plaid Link
        
    Returns:
    --------
    tuple
        (access_token, item_id)
    """
    # In a real app, this would call the Plaid API
    return "mock-access-token", "mock-item-id"

def get_account_info(access_token):
    """
    Mock version of getting account information
    
    Parameters:
    -----------
    access_token: str
        Access token for the Item
        
    Returns:
    --------
    list
        List of mock account dictionaries
    """
    # Create some mock accounts
    mock_accounts = [
        {
            "account_id": "checking123",
            "name": "Mock Checking",
            "type": "depository",
            "subtype": "checking",
            "balance": 2500.00,
            "currency": "USD",
            "mask": "1234"
        },
        {
            "account_id": "savings456",
            "name": "Mock Savings",
            "type": "depository",
            "subtype": "savings",
            "balance": 10000.00,
            "currency": "USD",
            "mask": "5678"
        }
    ]
    
    return mock_accounts

def get_transactions(access_token, start_date, end_date):
    """
    Mock version of getting transactions
    
    Parameters:
    -----------
    access_token: str
        Access token for the Item
    start_date: datetime.date
        Start date for transactions
    end_date: datetime.date
        End date for transactions
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing mock transaction data
    """
    # Create sample transaction data
    today = datetime.now().date()
    
    # Sample transactions
    sample_transactions = [
        {"date": today - timedelta(days=2), "description": "Grocery Store", "amount": 76.32, "category": "Groceries", "type": "expense"},
        {"date": today - timedelta(days=5), "description": "Gas Station", "amount": 45.10, "category": "Transportation", "type": "expense"},
        {"date": today - timedelta(days=7), "description": "Coffee Shop", "amount": 5.75, "category": "Dining", "type": "expense"},
        {"date": today - timedelta(days=10), "description": "Online Shopping", "amount": 120.99, "category": "Shopping", "type": "expense"},
        {"date": today - timedelta(days=1), "description": "Paycheck", "amount": 1250.00, "category": "Income", "type": "income"},
    ]
    
    # Create DataFrame
    transactions_df = pd.DataFrame(sample_transactions)
    
    # Add additional columns
    accounts = ["checking123", "savings456"]
    account_names = ["Mock Checking", "Mock Savings"]
    
    transactions_df["account_id"] = [accounts[i % len(accounts)] for i in range(len(sample_transactions))]
    transactions_df["account"] = [account_names[i % len(account_names)] for i in range(len(sample_transactions))]
    transactions_df["transaction_id"] = [f"tx_{i}" for i in range(len(sample_transactions))]
    transactions_df["pending"] = False
    
    return transactions_df