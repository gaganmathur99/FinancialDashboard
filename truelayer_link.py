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
    Create a TrueLayer component to connect bank accounts
    """
    st.write("**Connect Your Bank Account**")
    
    # Create columns for bank selection and connect button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        bank_name = st.selectbox(
            "Select your bank:", 
            ["Barclays", "HSBC", "Lloyds", "Monzo", "Revolut", "Starling", "Other..."],
            index=None,
            placeholder="Choose your bank"
        )
    
    with col2:
        connect_button = st.button("Connect", type="primary", key="connect_bank_btn")
    
    if connect_button and bank_name:
        # In a real implementation, we would redirect to the bank's website via TrueLayer
        # For demonstration purposes, show a simulated connection
        st.session_state.truelayer_response = {
            "action": "success",
            "bank_name": bank_name,
            "account_ids": ["checking123", "savings456"]
        }
        
        st.success(f"Mock connection established to {bank_name}!")
        st.info("This is a simulated connection. In a real app with valid TrueLayer credentials, you would be redirected to your bank's login page.")
        
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
    
    # Check if we have a connected bank
    if not st.session_state.truelayer_bank_name:
        # Display the TrueLayer component
        st.write("### Connect Your Bank")
        st.write("Link your bank account to automatically import transactions and balances.")
        
        # Call the TrueLayer component
        truelayer_component()
        
        # Check for response from the component
        truelayer_response = st.session_state.get('truelayer_response')
        if truelayer_response and truelayer_response.get('action') == 'success':
            # Store the bank information
            st.session_state.truelayer_access_token = "mock-access-token"
            st.session_state.truelayer_bank_name = truelayer_response.get('bank_name', 'Unknown Bank')
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
        accounts = truelayer.get_account_info(access_token)
        
        for account in accounts:
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
                        
                        transactions_df = truelayer.get_transactions(
                            access_token,
                            account['account_id'],
                            start_date,
                            today
                        )
                        
                        # Update session state with the transactions
                        if st.session_state.transactions.empty:
                            st.session_state.transactions = transactions_df
                        else:
                            st.session_state.transactions = pd.concat(
                                [st.session_state.transactions, transactions_df],
                                ignore_index=True
                            ).drop_duplicates(subset=["transaction_id"])
                        
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
                                "balance": account['balance']
                            }
                            st.session_state.accounts.append(new_account)
                        
                        st.success(f"Successfully imported {len(transactions_df)} transactions from {account['name']}!")
                        st.rerun()
    
    # Option to disconnect
    if st.button("Disconnect Bank", key="disconnect_truelayer"):
        st.session_state.truelayer_access_token = None
        st.session_state.truelayer_bank_name = None
        st.session_state.truelayer_account_ids = []
        st.success("Bank account disconnected.")
        st.rerun()