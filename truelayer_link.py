import streamlit as st
import streamlit.components.v1 as components
import json
import os
import uuid
from datetime import datetime, timedelta
import pandas as pd
import truelayer_integration as truelayer

def generate_user_id():
    """Generate a unique user ID if none exists in session state"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

def truelayer_component():
    """
    Create a TrueLayer component to connect bank accounts using real authentication
    """
    st.write("**Connect Your Bank Account**")
    
    # Check if we already have a TrueLayer auth link
    if 'truelayer_auth_link' not in st.session_state:
        # Create a link for redirecting to TrueLayer auth page
        client_config = st.session_state.truelayer_client
        
        # For TrueLayer, we need to use a redirect URI that's been registered in your TrueLayer dashboard
        # This URL must match exactly what you've configured in your TrueLayer app settings
        redirect_uri = "https://financial-dashboard.replit.app/callback"
        
        # Generate the authentication link
        auth_link = truelayer.create_auth_link(client_config, redirect_uri)
        st.session_state.truelayer_auth_link = auth_link
    
    # Check for client errors
    if st.session_state.truelayer_client.get("error"):
        error_msg = st.session_state.truelayer_client.get("error")
        st.error(f"Error with TrueLayer configuration: {error_msg}")
        st.info("Please check your TrueLayer API credentials.")
        return
        
    # Real authentication flow with TrueLayer
    st.write("### Connect to Your Bank")
    st.write("You'll be redirected to your bank's website to authorize access.")
    
    # Add important information about TrueLayer configuration
    st.info("""
    **Important**: For TrueLayer to work correctly, you need to configure your TrueLayer application with the following:
    
    1. Register the redirect URL `https://financial-dashboard.replit.app/callback` in your TrueLayer developer dashboard
    2. Ensure your TrueLayer client ID and secret are correctly set in the environment variables
    """)
    
    
    # Display the authentication link
    auth_link = st.session_state.truelayer_auth_link
    st.markdown(f"""
    1. Click the button below to connect your bank account
    2. Select your bank on the TrueLayer page
    3. Log in to your bank account
    4. Authorize the connection
    5. You'll be redirected back to this app
    """)
    
    # Create a button that opens the auth link in a new tab
    if st.button("Connect Bank Account", type="primary"):
        # In a real app, we'd use something like:
        # js = f"""window.open("{auth_link}", "_blank")"""
        # st.components.v1.html(f"<script>{js}</script>", height=0)
        
        # For our implementation, show the link
        st.markdown(f"[Click here to connect your bank]({auth_link})", unsafe_allow_html=True)
        
        # Since we can't handle actual OAuth redirects in this simple app,
        # we'll provide a way to manually enter the auth code
        auth_code = st.text_input("After authorizing, enter the code from the redirect URL:", 
                                  help="Look for the 'code=' parameter in the URL you were redirected to")
        
        if auth_code:
            # Exchange the auth code for an access token
            # Get the redirect URI we used earlier
            redirect_uri = "https://financial-dashboard.replit.app/callback"
            token_response = truelayer.exchange_auth_code(
                st.session_state.truelayer_client,
                auth_code,
                redirect_uri
            )
            
            if token_response:
                # Store the access token in session state
                st.session_state.truelayer_access_token = token_response.get("access_token")
                st.session_state.truelayer_refresh_token = token_response.get("refresh_token")
                
                # To get the bank name, we need to fetch account info
                # For now, just mark as connected
                st.session_state.truelayer_response = {
                    "action": "success",
                    "bank_name": "Your Bank",
                    "auth_success": True
                }
                
                st.success("Successfully connected to your bank!")
                st.rerun()
        
    # Add a debug section
    with st.expander("Debug Information"):
        st.write("Session State Keys:", list(st.session_state.keys()))
        if 'truelayer_client' in st.session_state:
            st.write("TrueLayer Client:", {k: v for k, v in st.session_state.truelayer_client.items() if k != 'client_secret'})
        if 'truelayer_response' in st.session_state:
            st.write("TrueLayer Response:", st.session_state.truelayer_response)
    
    # Check for messages from the component
    if 'truelayer_response' not in st.session_state:
        st.session_state.truelayer_response = None

def initialize_truelayer():
    """
    Initialize TrueLayer connection and handle authentication
    
    Returns:
    --------
    bool
        Whether the TrueLayer flow is complete
    """
    # Generate a user ID for the flow
    user_id = generate_user_id()
    
    # Initialize session state variables
    if 'truelayer_access_token' not in st.session_state:
        st.session_state.truelayer_access_token = None
    if 'truelayer_bank_name' not in st.session_state:
        st.session_state.truelayer_bank_name = None
    
    # Initialize TrueLayer client if not already done
    if 'truelayer_client' not in st.session_state:
        st.session_state.truelayer_client = truelayer.create_truelayer_client()
    
    # Check if we have a connected bank (either via real auth or mock)
    if not st.session_state.truelayer_access_token:
        # Display the TrueLayer component
        st.write("### Connect Your Bank")
        st.write("Link your bank account to automatically import transactions and balances.")
        
        # Call the TrueLayer component
        truelayer_component()
        
        # Check for response from the component
        truelayer_response = st.session_state.get('truelayer_response')
        if truelayer_response and truelayer_response.get('action') == 'success':
            if truelayer_response.get('auth_success', False):
                # This was a real OAuth flow, access token is already set
                # Attempt to get real bank information
                try:
                    if st.session_state.truelayer_access_token:
                        account_info = truelayer.get_account_info(st.session_state.truelayer_access_token)
                        if account_info and len(account_info) > 0:
                            # Get the provider name from the first account
                            bank_name = account_info[0].get('provider', {}).get('display_name', 'Your Bank')
                            st.session_state.truelayer_bank_name = bank_name
                        else:
                            st.session_state.truelayer_bank_name = "Connected Bank"
                except Exception as e:
                    st.error(f"Error fetching account information: {str(e)}")
                    st.session_state.truelayer_bank_name = "Connected Bank"
            else:
                # Store the bank information from the response
                st.session_state.truelayer_bank_name = truelayer_response.get('bank_name', 'Connected Bank')
                if 'account_ids' in truelayer_response:
                    st.session_state.truelayer_account_ids = truelayer_response.get('account_ids', [])
            
            st.success(f"Successfully connected to {st.session_state.truelayer_bank_name}!")
            st.rerun()
        
        return False
    
    return True

def display_connected_accounts():
    """
    Display connected bank accounts from TrueLayer
    """
    if not st.session_state.get('truelayer_bank_name'):
        st.info("No bank accounts connected yet.")
        return
    
    st.subheader("Connected Bank Accounts")
    
    # Create a card-like display for the bank
    bank_name = st.session_state.get('truelayer_bank_name', 'Unknown Bank')
    
    with st.container():
        st.markdown(f"""
        <div style="border:1px solid #ddd; border-radius:5px; padding:15px; margin:10px 0;">
            <h3>{bank_name}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Get account information
        access_token = st.session_state.get('truelayer_access_token')
        
        # Show a loading indicator while fetching accounts
        with st.spinner("Fetching account information..."):
            accounts = truelayer.get_account_info(access_token)
        
        if not accounts:
            st.warning("No accounts were found. This could be due to an invalid token or API limitation.")
            return
        
        st.write(f"Found {len(accounts)} accounts")
        
        for account in accounts:
            with st.container():
                st.markdown(f"""<div style="border:1px solid #eee; border-radius:5px; padding:10px; margin:5px 0;"></div>""", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    account_mask = f"•••{account.get('account_number', '')[-4:]}" if account.get('account_number') else "•••1234"
                    st.write(f"**{account['name']}** {account_mask}")
                    st.caption(f"{account['type']}")
                with col2:
                    st.write(f"Balance")
                    st.caption(f"{account.get('currency', 'GBP')} {account.get('balance', 0):,.2f}")
                with col3:
                    if st.button("Import Data", key=f"import_{account['account_id']}"):
                        with st.spinner("Importing transactions..."):
                            # Get transactions for this account
                            today = datetime.now().date()
                            start_date = today - timedelta(days=90)  # Last 90 days
                            
                            # Show progress information
                            st.info(f"Retrieving transactions from {start_date} to {today}")
                            
                            transactions_df = truelayer.get_transactions(
                                access_token,
                                account['account_id'],
                                start_date,
                                today
                            )
                            
                            if transactions_df.empty:
                                st.warning("No transactions found for this account in the specified date range.")
                            else:
                                # Update session state with the transactions
                                if 'transactions' not in st.session_state or st.session_state.transactions.empty:
                                    st.session_state.transactions = transactions_df
                                else:
                                    # Combine and deduplicate transactions
                                    st.session_state.transactions = pd.concat(
                                        [st.session_state.transactions, transactions_df],
                                        ignore_index=True
                                    )
                                    
                                    # Only deduplicate if transaction_id column exists
                                    if "transaction_id" in st.session_state.transactions.columns:
                                        st.session_state.transactions = st.session_state.transactions.drop_duplicates(subset=["transaction_id"])
                                
                                # Make sure the account is in the accounts list
                                account_exists = False
                                for i, acc in enumerate(st.session_state.accounts):
                                    if acc.get('name') == account['name']:
                                        st.session_state.accounts[i]['balance'] = account['balance']
                                        account_exists = True
                                        break
                                
                                if not account_exists:
                                    new_account = {
                                        "name": account['name'],
                                        "type": account['type'],
                                        "balance": account['balance'],
                                        "currency": account.get('currency', 'GBP'),
                                        "account_id": account.get('account_id', '')
                                    }
                                    st.session_state.accounts.append(new_account)
                                
                                st.success(f"Successfully imported {len(transactions_df)} transactions from {account['name']}!")
                                
                                # Show transaction summary
                                with st.expander("Transaction Summary"):
                                    st.write(f"Date range: {transactions_df['date'].min()} to {transactions_df['date'].max()}")
                                    st.write(f"Total transactions: {len(transactions_df)}")
                                    
                                    # Show category breakdown if available
                                    if 'category' in transactions_df.columns:
                                        category_counts = transactions_df['category'].value_counts()
                                        st.write("Top categories:")
                                        st.write(category_counts.head(5))
                                
                                st.rerun()
    
    # Option to refresh token
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh Account Data", key="refresh_truelayer"):
            st.session_state.pop('truelayer_account_data', None)
            st.rerun()
    
    with col2:
        # Option to disconnect
        if st.button("Disconnect Bank", key="disconnect_truelayer"):
            st.session_state.truelayer_access_token = None
            st.session_state.truelayer_bank_name = None
            st.session_state.truelayer_account_ids = []
            st.success("Bank account disconnected.")
            st.rerun()