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
    # HTML and JavaScript for the Plaid Link component
    plaid_link_html = f"""
    <html>
    <head>
        <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
        <script>
            function sendMessageToStreamlit(data) {{
                window.parent.postMessage(
                    {{
                        type: "streamlit:plaid",
                        data: data
                    }},
                    "*"
                );
            }}
            
            function handleOnSuccess(public_token, metadata) {{
                sendMessageToStreamlit({{
                    action: "success",
                    public_token: public_token,
                    metadata: metadata
                }});
            }}
            
            function handleOnExit(err, metadata) {{
                if (err != null) {{
                    sendMessageToStreamlit({{
                        action: "error",
                        error: err
                    }});
                }} else {{
                    sendMessageToStreamlit({{
                        action: "exit",
                        metadata: metadata
                    }});
                }}
            }}
            
            function initializePlaidLink() {{
                const handler = Plaid.create({{
                    token: '{link_token}',
                    onSuccess: handleOnSuccess,
                    onExit: handleOnExit,
                    receivedRedirectUri: window.location.href
                }});
                
                handler.open();
            }}
        </script>
    </head>
    <body>
        <button id="link-button" onclick="initializePlaidLink()" style="
            background-color: #1E88E5;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 0;
        ">
            Connect Bank Account
        </button>
        
        <div id="status"></div>
    </body>
    </html>
    """
    
    # Render the HTML component
    components.html(plaid_link_html, height=100)
    
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
    if 'plaid_link_token' not in st.session_state:
        try:
            # Create a new Link token
            st.session_state.plaid_link_token = plaid.create_link_token(
                client_name="Personal Finance Dashboard", 
                user_id=user_id
            )
        except Exception as e:
            st.error(f"Error creating Plaid Link token: {str(e)}")
            return False
    
    # Add the event handler for Plaid Link messages
    init_plaid_link_handler()
    
    # Check if we have a public token from Plaid Link
    if st.session_state.plaid_public_token is None:
        # Display the Plaid Link button
        plaid_link_component(st.session_state.plaid_link_token)
        
        # Check for response from the Plaid Link component
        plaid_response = st.session_state.get('plaid_response')
        if plaid_response and plaid_response.get('action') == 'success':
            # Store the public token
            st.session_state.plaid_public_token = plaid_response.get('public_token')
            st.session_state.plaid_institution = plaid_response.get('metadata', {}).get('institution', {}).get('name', 'Unknown')
            
            # Exchange the public token for an access token
            try:
                access_token, item_id = plaid.exchange_public_token(st.session_state.plaid_public_token)
                st.session_state.plaid_access_token = access_token
                st.session_state.plaid_item_id = item_id
                
                # Fetch account information
                accounts = plaid.get_account_info(access_token)
                st.session_state.plaid_accounts = accounts
                
                st.success(f"Successfully connected to {st.session_state.plaid_institution}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error exchanging public token: {str(e)}")
        
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
    if not st.session_state.get('plaid_accounts'):
        st.info("No bank accounts connected yet.")
        return
    
    st.subheader("Connected Bank Accounts")
    
    accounts = st.session_state.plaid_accounts
    for account in accounts:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"**{account['name']}** {'•••' + account['mask'] if account['mask'] else ''}")
            st.caption(f"{account['type'].capitalize()} - {account['subtype'].capitalize()}")
        with col2:
            st.write(f"Balance")
            st.caption(f"{account['currency']} {account['balance']:,.2f}")
        with col3:
            if st.button("Import Data", key=f"import_{account['account_id']}"):
                with st.spinner("Importing transactions..."):
                    transactions_df = fetch_plaid_transactions()
                    if transactions_df is not None:
                        # Filter for just this account
                        account_df = transactions_df[transactions_df['account_id'] == account['account_id']]
                        
                        # Update session state with the new transactions
                        if not account_df.empty:
                            if st.session_state.transactions.empty:
                                st.session_state.transactions = account_df
                            else:
                                # Check for duplicates using transaction_id
                                existing_ids = []
                                if 'transaction_id' in st.session_state.transactions.columns:
                                    existing_ids = st.session_state.transactions['transaction_id'].tolist()
                                
                                new_transactions = account_df[~account_df['transaction_id'].isin(existing_ids)]
                                if not new_transactions.empty:
                                    st.session_state.transactions = pd.concat([st.session_state.transactions, new_transactions], ignore_index=True)
                            
                            # Update account in session state
                            account_exists = False
                            for i, acc in enumerate(st.session_state.accounts):
                                if acc.get('name') == account['name']:
                                    st.session_state.accounts[i]['balance'] = account['balance']
                                    account_exists = True
                                    break
                            
                            if not account_exists:
                                new_account = {
                                    "name": account['name'],
                                    "type": account['type'].capitalize(),
                                    "balance": account['balance']
                                }
                                st.session_state.accounts.append(new_account)
                            
                            st.success(f"Successfully imported {len(account_df)} transactions from {account['name']}!")
                            st.rerun()
                        else:
                            st.warning("No transactions found for this account in the last 30 days.")
    
    # Option to disconnect
    if st.button("Disconnect Bank", key="disconnect_plaid"):
        st.session_state.plaid_public_token = None
        st.session_state.plaid_access_token = None
        st.session_state.plaid_accounts = []
        st.session_state.plaid_link_token = None
        st.success("Bank account disconnected.")
        st.rerun()