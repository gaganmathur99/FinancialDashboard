import streamlit as st
import pandas as pd
import logging
import os
import uuid
from datetime import datetime, timedelta

from database.db_manager import DatabaseManager
from bank_integration.auth_manager import db_manager, get_active_connections, refresh_connection_token
from bank_integration.truelayer_api import truelayer_api

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_account_transactions(account, force_full_sync=False):
    """
    Sync transactions for a specific account
    
    Parameters:
    -----------
    account: dict
        Account dictionary with account_id, connection_id, etc.
    force_full_sync: bool
        Whether to force a full year sync regardless of last sync time
        
    Returns:
    --------
    tuple
        (success, num_transactions)
    """
    try:
        # Get connection for this account
        connection = db_manager.get_bank_connection(account["connection_id"])
        
        if not connection:
            logger.error(f"No connection found for account {account['account_id']}")
            return False, 0
        
        # Determine date range
        if force_full_sync:
            from_date = datetime.now() - timedelta(days=365)  # 1 year back
        else:
            # Get the last sync time for this connection
            last_sync = connection.get("last_sync")
            if last_sync:
                last_sync_dt = datetime.fromisoformat(last_sync)
                # Go back 7 days from last sync to ensure we don't miss anything
                from_date = last_sync_dt - timedelta(days=7)
            else:
                from_date = datetime.now() - timedelta(days=90)  # 90 days back by default
        
        to_date = datetime.now()
        
        # Check if we need to refresh the token
        access_token = connection["access_token"]
        token_expiry = connection.get("token_expiry")
        
        if token_expiry:
            token_expiry_dt = datetime.fromisoformat(token_expiry)
            if token_expiry_dt <= datetime.now():
                # Token expired, refresh it
                connection = refresh_connection_token(connection["connection_id"])
                if not connection:
                    logger.error(f"Failed to refresh token for connection {connection['connection_id']}")
                    return False, 0
                access_token = connection["access_token"]
        
        # Get transactions from the API
        transactions_df = truelayer_api.get_transactions(
            access_token, 
            account["account_id"],
            from_date,
            to_date
        )
        
        if transactions_df.empty:
            logger.info(f"No transactions found for account {account['account_id']}")
            
            # Update sync time even if no transactions were found
            db_manager.update_connection_sync_time(connection["connection_id"], datetime.now())
            
            return True, 0
        
        # Process transactions
        user_id = account["user_id"]
        transactions_list = []
        
        for _, row in transactions_df.iterrows():
            # Generate unique transaction ID if not provided
            transaction_id = row.get("transaction_id") or str(uuid.uuid4())
            
            # Determine transaction type (expense or income)
            amount = float(row.get("amount", 0))
            transaction_type = "expense" if amount < 0 else "income"
            
            # Absolute amount
            amount_abs = abs(amount)
            
            # Basic category
            category = "uncategorized"
            if "category" in row and row["category"]:
                category = row["category"].lower()
            else:
                # Try to categorize based on description
                description = row.get("description", "").lower()
                
                # Very simple categorization, could be improved
                if any(keyword in description for keyword in ["salary", "payroll", "wage"]):
                    category = "income"
                elif any(keyword in description for keyword in ["grocery", "food", "supermarket"]):
                    category = "groceries"
                elif any(keyword in description for keyword in ["restaurant", "cafe", "takeaway"]):
                    category = "dining"
                elif any(keyword in description for keyword in ["uber", "taxi", "transport", "tube", "train"]):
                    category = "transport"
                elif any(keyword in description for keyword in ["amazon", "ebay", "shopping"]):
                    category = "shopping"
                elif any(keyword in description for keyword in ["rent", "mortgage", "housing"]):
                    category = "housing"
                elif any(keyword in description for keyword in ["utility", "electricity", "gas", "water", "internet"]):
                    category = "utilities"
            
            # Prepare transaction data
            transaction_info = {
                "transaction_id": transaction_id,
                "account_id": account["account_id"],
                "user_id": user_id,
                "date": row.get("timestamp", datetime.now().isoformat()),
                "description": row.get("description", ""),
                "amount": amount_abs,
                "currency": row.get("currency", "GBP"),
                "type": transaction_type,
                "category": category,
                "transaction_data": row.to_dict()
            }
            
            transactions_list.append(transaction_info)
        
        # Save transactions to database
        if transactions_list:
            num_saved = db_manager.save_transactions(transactions_list)
            logger.info(f"Saved {num_saved} transactions for account {account['account_id']}")
            
            # Update sync time
            db_manager.update_connection_sync_time(connection["connection_id"], datetime.now())
            
            return True, num_saved
        
        return True, 0
    except Exception as e:
        logger.error(f"Error syncing account transactions: {str(e)}")
        return False, 0

def sync_all_account_transactions(force_full_sync=False):
    """
    Sync transactions for all accounts
    
    Parameters:
    -----------
    force_full_sync: bool
        Whether to force a full year sync for all accounts
        
    Returns:
    --------
    dict
        Summary of sync results
    """
    try:
        # Get all active connections
        connections = get_active_connections()
        
        if not connections:
            logger.warning("No active connections found")
            return {"success": False, "message": "No active connections found"}
        
        # Get all accounts for these connections
        all_accounts = []
        for connection in connections:
            accounts = db_manager.get_bank_accounts(connection_id=connection["connection_id"])
            all_accounts.extend(accounts)
        
        if not all_accounts:
            logger.warning("No accounts found")
            return {"success": False, "message": "No accounts found"}
        
        # Sync each account
        results = {
            "success": True,
            "total_accounts": len(all_accounts),
            "successful_syncs": 0,
            "failed_syncs": 0,
            "total_transactions": 0,
            "account_results": {}
        }
        
        for account in all_accounts:
            success, num_transactions = sync_account_transactions(account, force_full_sync)
            
            account_name = account.get("name", account["account_id"])
            results["account_results"][account_name] = {
                "success": success,
                "transactions": num_transactions
            }
            
            if success:
                results["successful_syncs"] += 1
                results["total_transactions"] += num_transactions
            else:
                results["failed_syncs"] += 1
        
        return results
    except Exception as e:
        logger.error(f"Error syncing all account transactions: {str(e)}")
        return {"success": False, "message": str(e)}

def get_account_transactions(account_id=None, start_date=None, end_date=None, force_refresh=False):
    """
    Get transactions for an account or all accounts
    
    Parameters:
    -----------
    account_id: str, optional
        Account ID to get transactions for, or None for all accounts
    start_date: str or datetime, optional
        Start date for filtering
    end_date: str or datetime, optional
        End date for filtering
    force_refresh: bool
        Whether to force a sync before getting transactions
        
    Returns:
    --------
    pd.DataFrame
        DataFrame of transactions
    """
    try:
        # Format dates
        if start_date and isinstance(start_date, datetime):
            start_date = start_date.isoformat()
        
        if end_date and isinstance(end_date, datetime):
            end_date = end_date.isoformat()
        
        user_id = st.session_state.get("user_id")
        
        if not user_id:
            logger.warning("No user ID in session state")
            return pd.DataFrame()
        
        # Force refresh if requested
        if force_refresh:
            if account_id:
                # Sync just this account
                account = db_manager.get_bank_accounts(account_id=account_id)
                if account:
                    sync_account_transactions(account, force_full_sync=True)
            else:
                # Sync all accounts
                sync_all_account_transactions(force_full_sync=True)
        
        # Get transactions from database
        transactions_df = db_manager.get_transactions(
            user_id=user_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return transactions_df
    except Exception as e:
        logger.error(f"Error getting account transactions: {str(e)}")
        return pd.DataFrame()

def categorize_transactions(transactions_df):
    """
    Add or update categories for transactions
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame of transactions
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with updated categories
    """
    if transactions_df.empty:
        return transactions_df
    
    try:
        # Make a copy to avoid modifying the original
        df = transactions_df.copy()
        
        # Ensure category column exists
        if "category" not in df.columns:
            df["category"] = "uncategorized"
        
        # For any uncategorized transactions, attempt to categorize
        for idx, row in df.iterrows():
            if row["category"] == "uncategorized":
                description = str(row.get("description", "")).lower()
                
                # Simple categorization - can be improved
                if any(keyword in description for keyword in ["salary", "payroll", "wage"]):
                    df.at[idx, "category"] = "income"
                elif any(keyword in description for keyword in ["grocery", "food", "supermarket", "tesco", "sainsbury", "asda", "waitrose"]):
                    df.at[idx, "category"] = "groceries"
                elif any(keyword in description for keyword in ["restaurant", "cafe", "takeaway", "mcdonalds", "pizza", "burger"]):
                    df.at[idx, "category"] = "dining"
                elif any(keyword in description for keyword in ["uber", "taxi", "transport", "tube", "train", "bus", "oyster"]):
                    df.at[idx, "category"] = "transport"
                elif any(keyword in description for keyword in ["amazon", "ebay", "shopping", "store", "shop"]):
                    df.at[idx, "category"] = "shopping"
                elif any(keyword in description for keyword in ["rent", "mortgage", "housing", "home"]):
                    df.at[idx, "category"] = "housing"
                elif any(keyword in description for keyword in ["utility", "utilities", "electricity", "gas", "water", "internet", "broadband", "phone"]):
                    df.at[idx, "category"] = "utilities"
                elif any(keyword in description for keyword in ["entertainment", "netflix", "cinema", "movie", "spotify", "apple", "subscription", "membership"]):
                    df.at[idx, "category"] = "entertainment"
                elif any(keyword in description for keyword in ["medical", "health", "doctor", "pharmacy", "hospital", "dental", "dentist"]):
                    df.at[idx, "category"] = "health"
                elif any(keyword in description for keyword in ["education", "school", "university", "college", "course", "training"]):
                    df.at[idx, "category"] = "education"
        
        return df
    except Exception as e:
        logger.error(f"Error categorizing transactions: {str(e)}")
        return transactions_df