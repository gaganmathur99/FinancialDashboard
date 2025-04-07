import uuid
import streamlit as st
import logging
import os
from datetime import datetime, timedelta
import json
import requests

from database.db_manager import DatabaseManager
from bank_integration.truelayer_api import truelayer_api
from utils.encryption import encrypt, decrypt

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database manager
db_manager = DatabaseManager()

def generate_user_id():
    """
    Generate a unique user ID or use session state
    
    Returns:
    --------
    str
        User ID for the current session
    """
    if "user_id" not in st.session_state:
        # In a real app, this would come from authentication
        st.session_state.user_id = str(uuid.uuid4())
    
    return st.session_state.user_id

def initialize_auth():
    """
    Initialize authentication state
    
    Returns:
    --------
    bool
        Whether the user is authenticated
    """
    # Check if authentication has already been attempted
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # Get user ID
    user_id = generate_user_id()
    
    # Check for existing connections
    connections = get_active_connections()
    
    if connections:
        st.session_state.authenticated = True
        return True
    
    return False

def handle_auth_code(auth_code, provider="TrueLayer", redirect_uri=None):
    """
    Handle authorization code from OAuth flow
    
    Parameters:
    -----------
    auth_code: str
        Authorization code from OAuth flow
    provider: str
        Provider name (e.g., "TrueLayer")
    redirect_uri: str, optional
        Redirect URI used in the initial authorization
    
    Returns:
    --------
    bool
        Whether authentication was successful
    """
    if not auth_code:
        return False
    
    user_id = generate_user_id()
    
    try:
        # Exchange code for token
        token_response = truelayer_api.exchange_code_for_token(auth_code, redirect_uri)
        
        if not token_response:
            logger.error("Failed to exchange code for token")
            return False
        
        # Create a unique connection ID
        connection_id = f"{provider.lower()}-{str(uuid.uuid4())}"
        
        # Extract tokens
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        
        if not access_token or not refresh_token:
            logger.error("Missing access_token or refresh_token in response")
            return False
        
        # Calculate token expiry
        expires_in = token_response.get("expires_in", 0)
        expiry = datetime.now() + timedelta(seconds=expires_in) if expires_in else None
        
        # Save connection to database
        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        
        success = db_manager.save_bank_connection(user_id, connection_id, provider, tokens, expiry)
        
        if success:
            # Get and save account information
            fetch_and_save_accounts(user_id, connection_id, access_token, provider)
            
            # Set authenticated state
            st.session_state.authenticated = True
            
            # Update last sync time
            db_manager.update_connection_sync_time(connection_id, datetime.now())
            
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error handling auth code: {str(e)}")
        return False

def refresh_connection_token(connection_id):
    """
    Refresh an access token for a connection
    
    Parameters:
    -----------
    connection_id: str
        Connection ID
    
    Returns:
    --------
    dict
        Updated connection with new tokens, or None if refresh failed
    """
    try:
        # Get connection
        connection = db_manager.get_bank_connection(connection_id)
        
        if not connection or not connection.get("refresh_token"):
            logger.error(f"No connection found with ID {connection_id} or missing refresh token")
            return None
        
        # Refresh token
        refresh_token = connection.get("refresh_token")
        token_response = truelayer_api.refresh_access_token(refresh_token)
        
        if not token_response:
            logger.error(f"Failed to refresh token for connection {connection_id}")
            return None
        
        # Extract tokens
        access_token = token_response.get("access_token")
        new_refresh_token = token_response.get("refresh_token", refresh_token)
        
        if not access_token:
            logger.error("Missing access_token in refresh response")
            return None
        
        # Calculate token expiry
        expires_in = token_response.get("expires_in", 0)
        expiry = datetime.now() + timedelta(seconds=expires_in) if expires_in else None
        
        # Save updated tokens
        tokens = {
            "access_token": access_token,
            "refresh_token": new_refresh_token
        }
        
        success = db_manager.save_bank_connection(connection["user_id"], connection_id, 
                                              connection["provider"], tokens, expiry)
        
        if success:
            logger.info(f"Successfully refreshed token for connection {connection_id}")
            connection["access_token"] = access_token
            connection["refresh_token"] = new_refresh_token
            connection["token_expiry"] = expiry.isoformat() if expiry else None
            return connection
        
        return None
    except Exception as e:
        logger.error(f"Error refreshing connection token: {str(e)}")
        return None

def get_active_connections():
    """
    Get all active bank connections for the current user
    
    Returns:
    --------
    list
        List of connection dictionaries
    """
    user_id = generate_user_id()
    connections = db_manager.get_bank_connections(user_id)
    
    # Filter for active connections (you might want to check token expiry)
    return connections

def disconnect_bank(connection_id):
    """
    Disconnect a bank connection
    
    Parameters:
    -----------
    connection_id: str
        Connection ID to disconnect
    
    Returns:
    --------
    bool
        Whether disconnection was successful
    """
    try:
        # Delete connection and related data from database
        success = db_manager.delete_bank_connection(connection_id)
        
        if success:
            logger.info(f"Successfully disconnected bank connection {connection_id}")
            
            # Check if there are any remaining connections
            connections = get_active_connections()
            if not connections:
                st.session_state.authenticated = False
            
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error disconnecting bank: {str(e)}")
        return False

def fetch_and_save_accounts(user_id, connection_id, access_token, provider):
    """
    Fetch accounts from TrueLayer and save to database
    
    Parameters:
    -----------
    user_id: str
        User ID
    connection_id: str
        Connection ID
    access_token: str
        Access token
    provider: str
        Provider name
        
    Returns:
    --------
    list
        List of saved account IDs
    """
    try:
        # Fetch accounts
        accounts = truelayer_api.get_accounts(access_token)
        
        if not accounts:
            logger.warning("No accounts found")
            return []
        
        # Save each account
        account_ids = []
        for account in accounts:
            account_id = account.get("account_id")
            
            if not account_id:
                continue
            
            # Fetch balance
            balance_info = truelayer_api.get_account_balance(access_token, account_id)
            balance = balance_info.get("current") if balance_info else 0
            
            # Prepare account data
            account_info = {
                "account_id": account_id,
                "connection_id": connection_id,
                "user_id": user_id,
                "name": account.get("display_name") or f"Account {account.get('account_number', {}).get('number', '')}",
                "type": account.get("account_type", "unknown").lower(),
                "provider": provider,
                "balance": balance,
                "currency": account.get("currency", "GBP"),
                "last_updated": datetime.now().isoformat(),
                "account_data": account
            }
            
            # Save account
            success = db_manager.save_bank_account(account_info)
            
            if success:
                account_ids.append(account_id)
        
        return account_ids
    except Exception as e:
        logger.error(f"Error fetching and saving accounts: {str(e)}")
        return []