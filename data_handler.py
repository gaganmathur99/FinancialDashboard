import pandas as pd
import numpy as np
from datetime import datetime

def process_imported_data(
    df, 
    date_col, 
    description_col, 
    amount_col, 
    account_col=None,
    category_col=None, 
    type_col=None, 
    date_format='%Y-%m-%d',
    amount_multiplier=None
):
    """
    Process imported CSV data and return a standardized DataFrame
    
    Parameters:
    -----------
    df: pd.DataFrame
        The raw imported DataFrame
    date_col: str
        Column name containing transaction dates
    description_col: str
        Column name containing transaction descriptions
    amount_col: str
        Column name containing transaction amounts
    account_col: str, optional
        Column name containing account information
    category_col: str, optional
        Column name containing category information
    type_col: str, optional
        Column name containing transaction type (income/expense)
    date_format: str
        Format string for parsing dates
    amount_multiplier: str
        Convention for amount signs
        
    Returns:
    --------
    pd.DataFrame
        A standardized DataFrame with processed transaction data
    """
    # Create a new DataFrame with standardized format
    processed = pd.DataFrame()
    
    # Process date column
    if date_col:
        processed['date'] = pd.to_datetime(df[date_col], format=date_format).dt.date
    
    # Process description column
    if description_col:
        processed['description'] = df[description_col]
    
    # Process amount column
    if amount_col:
        processed['amount'] = df[amount_col].astype(float)
        
        # Handle amount sign convention
        if amount_multiplier == "Positive for expenses, negative for income":
            # Invert the sign
            processed['amount'] = -processed['amount']
        
    # Process account column
    if account_col and account_col in df.columns:
        processed['account'] = df[account_col]
    else:
        # Use default account name if not provided
        processed['account'] = "Imported Account"
    
    # Process category column
    if category_col and category_col in df.columns:
        processed['category'] = df[category_col]
    else:
        # Assign "Uncategorized" to all entries
        processed['category'] = "Uncategorized"
    
    # Process transaction type column
    if type_col and type_col in df.columns:
        processed['type'] = df[type_col]
    else:
        # Infer type from amount
        if amount_multiplier == "All positive, use type column to distinguish":
            # Default all to expenses if type not provided
            processed['type'] = "expense"
        else:
            # Infer from amount sign: positive = income, negative = expense
            processed['type'] = np.where(processed['amount'] >= 0, 'income', 'expense')
            
            # Make all amounts positive for consistency
            processed['amount'] = processed['amount'].abs()
    
    return processed

def filter_transactions_by_date(df, start_date, end_date):
    """
    Filter transactions DataFrame by date range
    
    Parameters:
    -----------
    df: pd.DataFrame
        DataFrame containing transaction data
    start_date: datetime.date
        Start date for filtering
    end_date: datetime.date
        End date for filtering
        
    Returns:
    --------
    pd.DataFrame
        Filtered DataFrame
    """
    if df.empty:
        return df
    
    # Ensure date column is datetime
    df_copy = df.copy()
    if 'date' in df_copy.columns:
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        
        # Filter by date range
        mask = (df_copy['date'].dt.date >= start_date) & (df_copy['date'].dt.date <= end_date)
        return df_copy[mask]
    
    return df_copy

def filter_transactions(df, accounts=None, categories=None, start_date=None, end_date=None, min_amount=None, max_amount=None):
    """
    Filter transactions by multiple criteria
    
    Parameters:
    -----------
    df: pd.DataFrame
        DataFrame containing transaction data
    accounts: list, optional
        List of account names to include
    categories: list, optional
        List of categories to include
    start_date: datetime.date, optional
        Start date for filtering
    end_date: datetime.date, optional
        End date for filtering
    min_amount: float, optional
        Minimum transaction amount
    max_amount: float, optional
        Maximum transaction amount
        
    Returns:
    --------
    pd.DataFrame
        Filtered DataFrame
    """
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    filtered_df = df.copy()
    
    # Filter by date range
    if start_date is not None and end_date is not None:
        filtered_df = filter_transactions_by_date(filtered_df, start_date, end_date)
    
    # Filter by accounts
    if accounts and len(accounts) > 0 and 'account' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['account'].isin(accounts)]
    
    # Filter by categories
    if categories and len(categories) > 0 and 'category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['category'].isin(categories)]
    
    # Filter by amount range
    if min_amount is not None and 'amount' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['amount'] >= min_amount]
    
    if max_amount is not None and 'amount' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['amount'] <= max_amount]
    
    return filtered_df

def calculate_total_balance(accounts):
    """
    Calculate the total balance across all accounts
    
    Parameters:
    -----------
    accounts: list
        List of account dictionaries
        
    Returns:
    --------
    float
        Total balance
    """
    if not accounts:
        return 0.0
    
    total = sum(account.get('balance', 0) for account in accounts)
    return total

def calculate_total_by_type(df, transaction_type):
    """
    Calculate the total amount for a specific transaction type
    
    Parameters:
    -----------
    df: pd.DataFrame
        DataFrame containing transaction data
    transaction_type: str
        Transaction type to calculate total for (e.g., 'income', 'expense')
        
    Returns:
    --------
    float
        Total amount
    """
    if df.empty or 'type' not in df.columns or 'amount' not in df.columns:
        return 0.0
    
    # Filter by transaction type and sum amounts
    filtered = df[df['type'] == transaction_type]
    return filtered['amount'].sum() if not filtered.empty else 0.0

def update_account_balance(accounts, account_name, amount, transaction_type):
    """
    Update an account balance based on a new transaction
    
    Parameters:
    -----------
    accounts: list
        List of account dictionaries
    account_name: str
        Name of the account to update
    amount: float
        Transaction amount
    transaction_type: str
        Transaction type ('income', 'expense', 'transfer')
        
    Returns:
    --------
    bool
        True if the account was updated, False otherwise
    """
    if not accounts or not account_name:
        return False
    
    # Find the account by name
    for account in accounts:
        if account.get('name') == account_name:
            # Update the balance based on transaction type
            if transaction_type == 'income':
                account['balance'] += amount
            elif transaction_type == 'expense':
                account['balance'] -= amount
            # For transfers, the balance would be updated on both accounts separately
            return True
    
    return False

def aggregate_by_category(df, transaction_type=None):
    """
    Aggregate transactions by category
    
    Parameters:
    -----------
    df: pd.DataFrame
        DataFrame containing transaction data
    transaction_type: str, optional
        Filter by transaction type before aggregating
        
    Returns:
    --------
    pd.DataFrame
        Aggregated DataFrame with category totals
    """
    if df.empty or 'category' not in df.columns or 'amount' not in df.columns:
        return pd.DataFrame()
    
    # Create a copy to avoid modifying the original
    agg_df = df.copy()
    
    # Filter by transaction type if specified
    if transaction_type and 'type' in agg_df.columns:
        agg_df = agg_df[agg_df['type'] == transaction_type]
    
    # Group by category and sum amounts
    result = agg_df.groupby('category')['amount'].sum().reset_index()
    return result
