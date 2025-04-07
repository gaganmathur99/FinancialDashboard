import requests
import urllib.parse
import os
import pandas as pd
import json
from datetime import datetime, timedelta
import streamlit as st
from dotenv import load_dotenv
import logging
import uuid

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TrueLayerAPI:
    """
    TrueLayer API integration for bank account access
    
    This class handles all interactions with the TrueLayer API for authentication,
    retrieving account information, and getting transactions.
    """
    
    # API endpoints
    AUTH_URL = "https://auth.truelayer.com/"
    TOKEN_URL = "https://auth.truelayer.com/connect/token"
    API_URL = "https://api.truelayer.com/data/v1/"
    
    # Default providers and scopes
    DEFAULT_PROVIDERS = ["uk-ob-all", "uk-oauth-all"]
    DEFAULT_SCOPES = ["info", "accounts", "balance", "cards", "transactions", "offline_access"]
    
    def __init__(self):
        """Initialize the TrueLayer API client"""
        # Get credentials from environment
        self.client_id = os.getenv("TRUELAYER_CLIENT_ID")
        self.client_secret = os.getenv("TRUELAYER_CLIENT_SECRET")
        
        # Check if credentials are available
        if not self.client_id or not self.client_secret:
            logger.error("TrueLayer API credentials not found in environment")
            self.initialized = False
        else:
            self.initialized = True
            logger.info("TrueLayer API client initialized")
    
    def is_initialized(self):
        """Check if the client is properly initialized"""
        return self.initialized
    
    def create_auth_url(self, redirect_uri, providers=None, scopes=None, state=None):
        """
        Create an authentication URL for TrueLayer
        
        Parameters:
        -----------
        redirect_uri: str
            URI to redirect to after authentication
        providers: list, optional
            List of provider identifiers to include
        scopes: list, optional
            List of scope identifiers to request
        state: str, optional
            State parameter for CSRF protection
            
        Returns:
        --------
        str
            Authentication URL
        """
        if not self.initialized:
            logger.error("TrueLayer API client not initialized")
            return None
        
        # Use defaults if not provided
        if providers is None:
            providers = self.DEFAULT_PROVIDERS
        
        if scopes is None:
            scopes = self.DEFAULT_SCOPES
        
        if state is None:
            state = str(uuid.uuid4())
        
        # Build parameters
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "providers": " ".join(providers),
            "state": state
        }
        
        # Create URL
        auth_url = f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"
        return auth_url
    
    def exchange_code_for_token(self, code, redirect_uri):
        """
        Exchange an authorization code for an access token
        
        Parameters:
        -----------
        code: str
            Authorization code from the redirect
        redirect_uri: str
            Redirect URI used in the initial authorization
            
        Returns:
        --------
        dict
            Access token response with access_token, refresh_token, etc.
        """
        if not self.initialized:
            logger.error("TrueLayer API client not initialized")
            return None
        
        try:
            # Build request data
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "code": code
            }
            
            # Make request
            logger.info(f"Exchanging code for token with TrueLayer API")
            response = requests.post(self.TOKEN_URL, data=data)
            
            # Check response
            if response.status_code == 200:
                logger.info("Successfully exchanged code for token")
                return response.json()
            else:
                logger.error(f"Failed to exchange code for token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            return None
    
    def refresh_access_token(self, refresh_token):
        """
        Refresh an access token using a refresh token
        
        Parameters:
        -----------
        refresh_token: str
            Refresh token to use
            
        Returns:
        --------
        dict
            New access token response
        """
        if not self.initialized:
            logger.error("TrueLayer API client not initialized")
            return None
        
        try:
            # Build request data
            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token
            }
            
            # Make request
            logger.info(f"Refreshing access token with TrueLayer API")
            response = requests.post(self.TOKEN_URL, data=data)
            
            # Check response
            if response.status_code == 200:
                logger.info("Successfully refreshed access token")
                return response.json()
            else:
                logger.error(f"Failed to refresh access token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return None
    
    def get_accounts(self, access_token):
        """
        Get accounts for a user
        
        Parameters:
        -----------
        access_token: str
            Access token for the user
            
        Returns:
        --------
        list
            List of account dictionaries
        """
        if not self.initialized:
            logger.error("TrueLayer API client not initialized")
            return None
        
        try:
            # Build headers
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # Make request
            logger.info(f"Getting accounts from TrueLayer API")
            response = requests.get(f"{self.API_URL}accounts", headers=headers)
            
            # Check response
            if response.status_code == 200:
                logger.info("Successfully retrieved accounts")
                accounts_data = response.json().get("results", [])
                return accounts_data
            else:
                logger.error(f"Failed to get accounts: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            return None
    
    def get_account_balance(self, access_token, account_id):
        """
        Get balance for an account
        
        Parameters:
        -----------
        access_token: str
            Access token for the user
        account_id: str
            Account ID to get balance for
            
        Returns:
        --------
        dict
            Balance information
        """
        if not self.initialized:
            logger.error("TrueLayer API client not initialized")
            return None
        
        try:
            # Build headers
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # Make request
            logger.info(f"Getting balance for account {account_id} from TrueLayer API")
            response = requests.get(f"{self.API_URL}accounts/{account_id}/balance", headers=headers)
            
            # Check response
            if response.status_code == 200:
                logger.info("Successfully retrieved account balance")
                balance_data = response.json().get("results", [])
                return balance_data[0] if balance_data else None
            else:
                logger.error(f"Failed to get account balance: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting account balance: {str(e)}")
            return None
    
    def get_transactions(self, access_token, account_id, from_date=None, to_date=None):
        """
        Get transactions for an account
        
        Parameters:
        -----------
        access_token: str
            Access token for the user
        account_id: str
            Account ID to get transactions for
        from_date: str or datetime, optional
            Start date for transactions
        to_date: str or datetime, optional
            End date for transactions
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with transactions
        """
        if not self.initialized:
            logger.error("TrueLayer API client not initialized")
            return pd.DataFrame()
        
        try:
            # Set default dates if not provided
            if from_date is None:
                from_date = datetime.now() - timedelta(days=90)
            
            if to_date is None:
                to_date = datetime.now()
            
            # Format dates
            if isinstance(from_date, datetime):
                from_date = from_date.date().isoformat()
            
            if isinstance(to_date, datetime):
                to_date = to_date.date().isoformat()
            
            # Build headers and parameters
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            params = {
                "from": from_date,
                "to": to_date
            }
            
            # Make request
            logger.info(f"Getting transactions for account {account_id} from TrueLayer API")
            response = requests.get(
                f"{self.API_URL}accounts/{account_id}/transactions",
                headers=headers,
                params=params
            )
            
            # Check response
            if response.status_code == 200:
                logger.info("Successfully retrieved transactions")
                transactions_data = response.json().get("results", [])
                
                # Convert to DataFrame
                if transactions_data:
                    df = pd.DataFrame(transactions_data)
                    return df
                else:
                    return pd.DataFrame()
            else:
                logger.error(f"Failed to get transactions: {response.status_code} - {response.text}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            return pd.DataFrame()
    
    def get_card_transactions(self, access_token, account_id, from_date=None, to_date=None):
        """
        Get card transactions for an account
        
        Parameters:
        -----------
        access_token: str
            Access token for the user
        account_id: str
            Account ID to get transactions for
        from_date: str or datetime, optional
            Start date for transactions
        to_date: str or datetime, optional
            End date for transactions
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with card transactions
        """
        if not self.initialized:
            logger.error("TrueLayer API client not initialized")
            return pd.DataFrame()
        
        try:
            # Set default dates if not provided
            if from_date is None:
                from_date = datetime.now() - timedelta(days=90)
            
            if to_date is None:
                to_date = datetime.now()
            
            # Format dates
            if isinstance(from_date, datetime):
                from_date = from_date.date().isoformat()
            
            if isinstance(to_date, datetime):
                to_date = to_date.date().isoformat()
            
            # Build headers and parameters
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            params = {
                "from": from_date,
                "to": to_date
            }
            
            # Make request
            logger.info(f"Getting card transactions for account {account_id} from TrueLayer API")
            response = requests.get(
                f"{self.API_URL}cards/{account_id}/transactions",
                headers=headers,
                params=params
            )
            
            # Check response
            if response.status_code == 200:
                logger.info("Successfully retrieved card transactions")
                transactions_data = response.json().get("results", [])
                
                # Convert to DataFrame
                if transactions_data:
                    df = pd.DataFrame(transactions_data)
                    return df
                else:
                    return pd.DataFrame()
            else:
                logger.error(f"Failed to get card transactions: {response.status_code} - {response.text}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting card transactions: {str(e)}")
            return pd.DataFrame()

# Create a global instance for easy access
truelayer_api = TrueLayerAPI()