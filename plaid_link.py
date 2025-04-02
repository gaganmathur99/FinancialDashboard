import streamlit as st
import streamlit.components.v1 as components
import json
import os
import uuid
from datetime import datetime, timedelta
import pandas as pd
import plaid_integration as plaid

def generate_user_id():
    """Generate a unique user ID if none exists in session state"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

def plaid_link_component(link_token):
    """
    Create a Plaid Link component to connect bank accounts
    
    Parameters:
    -----------
    link_token: str
        Link token from Plaid API
    """
    # This is a simplified version of the Plaid Link integration that doesn't require the full Plaid API
    # instead it creates a mockup interface to demonstrate the flow
    
    st.write("**Connect Your Bank Account**")
    
    # In a real implementation, we would use the Plaid Link SDK
    # For demonstration purposes, show a simulated interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        bank_name = st.selectbox(
            "Select your bank:", 
            ["Chase", "Bank of America", "Wells Fargo", "Citi", "Capital One", "Other..."],
            index=None,
            placeholder="Choose your bank"
        )
    
    with col2:
        connect_button = st.button("Connect", type="primary", key="connect_bank_btn")
    
    if connect_button and bank_name:
        # Simulate successful connection
        st.session_state.plaid_response = {
            "action": "success",
            "public_token": "public-sandbox-token",
            "metadata": {
                "institution": {
                    "name": bank_name
                },
                "accounts": [{
                    "id": "mock_account_id_123",
                    "name": f"{bank_name} Checking",
                    "mask": "1234",
                    "type": "depository",
                    "subtype": "checking"
                }]
            }
        }
        
        st.success(f"Mock connection established to {bank_name}!")
        st.info("This is a simulated connection. In a real app with valid Plaid credentials, you would be prompted to log in to your bank.")
        
    # Add a debug section
    with st.expander("Debug Information"):
        st.write("Link Token:", link_token)
        st.write("Session State Keys:", list(st.session_state.keys()))
        if 'plaid_response' in st.session_state:
            st.write("Plaid Response:", st.session_state.plaid_response)
    
    # Check for messages from the HTML component
    if 'plaid_response' not in st.session_state:
        st.session_state.plaid_response = None

def init_plaid_link_handler():
    """
    Set up event handler for Plaid Link messages
    """
    js_code = """
    <script>
    window.addEventListener('message', function(event) {
        if (event.data.type === 'streamlit:plaid') {
            window.parent.postMessage({
                type: 'streamlit:component_message',
                data: {
                    name: 'plaid_response',
                    value: event.data.data
                }
            }, '*');
        }
    });
    </script>
    """
    components.html(js_code, height=0)

def initialize_plaid():
    """
    Initialize Plaid Link and handle token exchange
    
    Returns:
    --------
    bool
        Whether the Plaid Link flow is complete
    """
    # Generate a user ID for the Plaid Link flow
    user_id = generate_user_id()
    
    # Initialize session state variables
    if 'plaid_public_token' not in st.session_state:
        st.session_state.plaid_public_token = None
    if 'plaid_access_token' not in st.session_state:
        st.session_state.plaid_access_token = None
    if 'plaid_accounts' not in st.session_state:
        st.session_state.plaid_accounts = []
    if 'plaid_institution' not in st.session_state:
        st.session_state.plaid_institution = None
    
    # Use a mock link token for our simplified demonstration
    if 'plaid_link_token' not in st.session_state:
        # In a real application, we would get this from the Plaid API
        # For our simplified version, we use a mock token
        st.session_state.plaid_link_token = "mock-link-token"
    
    # Check if we have a connected institution
    if not st.session_state.plaid_institution:
        # Display the mock Plaid Link component
        st.write("### Connect Your Bank")
        st.write("Link your bank account to automatically import transactions and balances.")
        plaid_link_component(st.session_state.plaid_link_token)
        
        # Check for response from the mock component
        plaid_response = st.session_state.get('plaid_response')
        if plaid_response and plaid_response.get('action') == 'success':
            # Store the bank information
            st.session_state.plaid_public_token = "mock-public-token"
            st.session_state.plaid_access_token = "mock-access-token"
            st.session_state.plaid_institution = plaid_response.get('metadata', {}).get('institution', {}).get('name', 'Unknown Bank')
            
            st.success(f"Successfully connected to {st.session_state.plaid_institution}!")
            st.rerun()
        
        return False
    
    return True

def fetch_plaid_transactions():
    """
    Fetch transactions from Plaid API for connected accounts
    
    Returns:
    --------
    pd.DataFrame
        DataFrame containing transaction data
    """
    if not st.session_state.get('plaid_access_token'):
        return None
    
    try:
        # Set date range (last 30 days by default)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Get transactions
        transactions_df = plaid.get_transactions(
            st.session_state.plaid_access_token,
            start_date,
            end_date
        )
        
        return transactions_df
    except Exception as e:
        st.error(f"Error fetching transactions: {str(e)}")
        return None

def display_connected_accounts():
    """
    Display connected bank accounts from Plaid
    """
    if not st.session_state.get('plaid_institution'):
        st.info("No bank accounts connected yet.")
        return
    
    st.subheader("Connected Bank Accounts")
    
    # Create a mock account based on the connected institution
    bank_name = st.session_state.get('plaid_institution', 'Unknown Bank')
    
    # Create card-like display for the account
    with st.container():
        st.markdown(f"""
        <div style="border:1px solid #ddd; border-radius:5px; padding:15px; margin:10px 0;">
            <h3>{bank_name}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Create mock accounts
        accounts = [
            {"name": f"{bank_name} Checking", "type": "Checking", "balance": 2543.67, "account_id": "check123"},
            {"name": f"{bank_name} Savings", "type": "Savings", "balance": 8750.42, "account_id": "save456"}
        ]
        
        for account in accounts:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{account['name']}** •••1234")
                st.caption(f"{account['type']}")
            with col2:
                st.write(f"Balance")
                st.caption(f"USD {account['balance']:,.2f}")
            with col3:
                if st.button("Import Data", key=f"import_{account['account_id']}"):
                    with st.spinner("Importing transactions..."):
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
                        transactions_df["account"] = account["name"]
                        transactions_df["account_id"] = account["account_id"]
                        transactions_df["transaction_id"] = [f"tx_{i}" for i in range(len(sample_transactions))]
                        
                        # Update session state with the sample transactions
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
    if st.button("Disconnect Bank", key="disconnect_plaid"):
        st.session_state.plaid_public_token = None
        st.session_state.plaid_access_token = None
        st.session_state.plaid_accounts = []
        st.session_state.plaid_institution = None
        st.session_state.plaid_link_token = None
        st.success("Bank account disconnected.")
        st.rerun()