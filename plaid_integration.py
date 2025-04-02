import os
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from datetime import datetime, timedelta
import pandas as pd

def create_plaid_client():
    """
    Create a Plaid API client using environment variables.
    
    Returns:
    --------
    plaid_api.PlaidApi
        Configured Plaid API client
    """
    # Get Plaid API credentials from environment variables
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    
    # Configure Plaid client
    configuration = plaid.Configuration(
        host=plaid.Environment.Sandbox,  # or plaid.Environment.Development or plaid.Environment.Production
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    
    # Create API client
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)

def create_link_token(client_name, user_id):
    """
    Create a Plaid Link token for initializing the Plaid Link flow
    
    Parameters:
    -----------
    client_name: str
        Name of your application
    user_id: str
        Identifier for the user
        
    Returns:
    --------
    str
        Link token for initializing Plaid Link
    """
    client = create_plaid_client()
    
    # Create a Link token for the user
    request = LinkTokenCreateRequest(
        products=[Products('transactions')],
        client_name=client_name,
        country_codes=[CountryCode('US')],
        language='en',
        user=LinkTokenCreateRequestUser(
            client_user_id=user_id
        )
    )
    
    response = client.link_token_create(request)
    return response['link_token']

def exchange_public_token(public_token):
    """
    Exchange a public token for an access token and item ID
    
    Parameters:
    -----------
    public_token: str
        Public token received from Plaid Link
        
    Returns:
    --------
    tuple
        (access_token, item_id)
    """
    client = create_plaid_client()
    
    # Exchange the public token for an access token
    exchange_request = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    exchange_response = client.item_public_token_exchange(exchange_request)
    
    access_token = exchange_response['access_token']
    item_id = exchange_response['item_id']
    
    return access_token, item_id

def get_account_info(access_token):
    """
    Get account information for an Item
    
    Parameters:
    -----------
    access_token: str
        Access token for the Item
        
    Returns:
    --------
    list
        List of account dictionaries
    """
    client = create_plaid_client()
    
    # Get accounts for the Item
    accounts_response = client.accounts_get({"access_token": access_token})
    
    # Extract account information
    accounts = []
    for account in accounts_response['accounts']:
        account_info = {
            "account_id": account['account_id'],
            "name": account['name'],
            "type": account['type'],
            "subtype": account['subtype'],
            "balance": account['balances']['current'],
            "currency": account['balances']['iso_currency_code'],
            "mask": account.get('mask', '')
        }
        accounts.append(account_info)
    
    return accounts

def get_transactions(access_token, start_date, end_date):
    """
    Get transactions for a date range
    
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
        DataFrame containing transaction data
    """
    client = create_plaid_client()
    
    # Configure request
    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions(
            count=500  # Adjust as needed
        )
    )
    
    # Get all transactions (may require pagination for large datasets)
    response = client.transactions_get(request)
    transactions = response['transactions']
    
    # Get account info for reference
    accounts = {account['account_id']: account['name'] for account in response['accounts']}
    
    # Convert transactions to DataFrame
    transactions_data = []
    for transaction in transactions:
        tx_data = {
            "date": transaction['date'],
            "description": transaction['name'],
            "amount": transaction['amount'],
            "account": accounts.get(transaction['account_id'], 'Unknown'),
            "account_id": transaction['account_id'],
            "category": transaction['category'][0] if transaction['category'] else 'Uncategorized',
            "subcategory": transaction['category'][1] if transaction['category'] and len(transaction['category']) > 1 else '',
            "pending": transaction['pending'],
            "transaction_id": transaction['transaction_id']
        }
        
        # Determine transaction type (expense vs income)
        # In Plaid, positive amounts are outflows (expenses), negative are inflows (income)
        if transaction['amount'] >= 0:
            tx_data['type'] = 'expense'
        else:
            tx_data['type'] = 'income'
            tx_data['amount'] = abs(transaction['amount'])  # Make amount positive for consistency
            
        transactions_data.append(tx_data)
    
    # Create DataFrame
    df = pd.DataFrame(transactions_data)
    
    # Convert date strings to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    
    return df