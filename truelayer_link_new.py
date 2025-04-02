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
    Create a TrueLayer component to connect bank accounts using a simplified authentication flow
    that works better with Streamlit's constraints
    """
    st.write("**Connect Your Bank Account**")
    
    # Check for client errors
    if st.session_state.truelayer_client.get("error"):
        error_msg = st.session_state.truelayer_client.get("error")
        st.error(f"Error with TrueLayer configuration: {error_msg}")
        st.info("Please check your TrueLayer API credentials.")
        return
        
    # Show information section
    st.write("### Connect to Your Bank")
    st.write("Follow these steps to connect your bank account:")
    
    # Show configuration information
    with st.expander("TrueLayer Configuration Information", expanded=True):
        st.info("""
        **Important**: TrueLayer authentication requires proper configuration:
        
        1. The redirect URI must be registered in your TrueLayer developer dashboard
        2. Your TrueLayer client ID and secret must be set in the environment
        3. In sandbox mode, you can only connect to TrueLayer test banks
        
        If you're having connection issues, this is likely due to a configuration mismatch.
        """)
    
    # Present the three ways to authenticate
    st.markdown("### Choose a connection method:")
    
    tab1, tab2, tab3 = st.tabs(["Option 1: Direct Token", "Option 2: Test Bank", "Option 3: Developer Mode"])
    
    with tab1:
        st.markdown("#### Enter Access Token Directly")
        st.write("If you already have a TrueLayer access token, enter it below:")
        
        direct_token = st.text_input("TrueLayer access token:", key="direct_access_token")
        
        if st.button("Connect with Token", key="connect_direct"):
            if direct_token:
                st.session_state.truelayer_access_token = direct_token
                st.session_state.truelayer_response = {
                    "action": "success",
                    "bank_name": "Connected Bank",
                    "auth_success": True
                }
                st.success("Connected with access token!")
                st.rerun()
            else:
                st.error("Please enter a valid access token")
    
    with tab2:
        st.markdown("#### Connect Test Bank")
        st.write("For development purposes, you can connect to a test bank:")
        
        test_banks = ["Mock Bank", "Sandbox Bank", "Test Financial Institution"]
        selected_bank = st.selectbox("Select a test bank:", test_banks)
        
        if st.button("Connect to Test Bank", key="connect_test"):
            # Initialize a client for TrueLayer test mode
            client_id = st.session_state.truelayer_client.get("client_id")
            
            # For test banks, we'll simulate a successful connection
            # but provide more detailed information to help debugging
            st.session_state.truelayer_access_token = f"test-access-token-{client_id[-6:]}"
            st.session_state.truelayer_response = {
                "action": "success", 
                "bank_name": selected_bank,
                "auth_success": True
            }
            st.success(f"Connected to test bank: {selected_bank}")
            st.rerun()
            
    with tab3:
        st.markdown("#### Developer OAuth Flow")
        st.write("Use the standard OAuth flow with the preconfigured redirect URI:")
        
        # Use the exact redirect URI from the provided link
        fixed_redirect = "https://console.truelayer.com/redirect-page"
        st.write(f"Using redirect URI: {fixed_redirect}")
        st.info("This redirect URI must match what's configured in your TrueLayer dashboard.")
        
        # Create authentication link on demand
        if st.button("Use Provided Auth Link", key="gen_auth_link"):
            # Use the provided authentication link directly
            auth_link = "https://auth.truelayer.com/?response_type=code&client_id=personalfinance-662298&scope=info%20accounts%20balance%20cards%20transactions%20direct_debits%20standing_orders%20offline_access&redirect_uri=https://console.truelayer.com/redirect-page&providers=uk-ob-all%20uk-oauth-all"
            st.session_state.truelayer_auth_link = auth_link
            st.session_state.truelayer_redirect_uri = fixed_redirect
            
            st.success("Authentication link ready!")
            st.markdown(f"[Click here to connect your bank]({auth_link})", unsafe_allow_html=True)
            
        # Alternative: generate link from parameters
        if st.button("Generate Auth Link (Alternative)", key="gen_alt_auth_link"):
            auth_link = truelayer.create_auth_link(st.session_state.truelayer_client, fixed_redirect)
            st.session_state.truelayer_auth_link = auth_link
            st.session_state.truelayer_redirect_uri = fixed_redirect
            
            if auth_link:
                st.success("Authentication link generated!")
                st.markdown(f"[Click here to connect your bank]({auth_link})", unsafe_allow_html=True)
            else:
                st.error("Failed to generate authentication link. Check your TrueLayer credentials.")
            
        # Show auth code input if we have generated an auth link
        if 'truelayer_auth_link' in st.session_state:
            with st.container():
                st.markdown("---")
                st.write("After authorizing, you'll be redirected. Enter the code from the URL:")
                auth_code = st.text_input(
                    "Authorization code:",
                    help="Look for the 'code=' parameter in the URL you were redirected to"
                )
                
                if st.button("Submit Code", key="submit_auth_code"):
                    if auth_code:
                        # Exchange the auth code for an access token
                        redirect_uri = st.session_state.truelayer_redirect_uri
                        token_response = truelayer.exchange_auth_code(
                            st.session_state.truelayer_client,
                            auth_code,
                            redirect_uri
                        )
                        
                        if token_response and "access_token" in token_response:
                            # Store the access token in session state
                            st.session_state.truelayer_access_token = token_response.get("access_token")
                            st.session_state.truelayer_refresh_token = token_response.get("refresh_token")
                            
                            # Success! Set the response
                            st.session_state.truelayer_response = {
                                "action": "success",
                                "bank_name": "Connected Bank",
                                "auth_success": True
                            }
                            
                            st.success("Successfully connected to your bank!")
                            st.rerun()
                        else:
                            st.error("Failed to exchange authorization code for access token. Please check the code and try again.")
                    else:
                        st.error("Please enter the authorization code from the redirect URL")
   
    # Add a debug section
    with st.expander("Debug Information", expanded=False):
        st.write("Session State Keys:", list(st.session_state.keys()))
        if 'truelayer_client' in st.session_state:
            st.write("TrueLayer Client:", {k: v for k, v in st.session_state.truelayer_client.items() if k != 'client_secret'})
        if 'truelayer_response' in st.session_state:
            st.write("TrueLayer Response:", st.session_state.truelayer_response)
    
    # Initialize response if needed
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