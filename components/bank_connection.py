import streamlit as st
import pandas as pd
import logging
import os
import uuid
from datetime import datetime

from bank_integration.auth_manager import (
    generate_user_id, 
    handle_auth_code, 
    get_active_connections, 
    disconnect_bank,
    db_manager
)
from bank_integration.truelayer_api import truelayer_api

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default redirect URI (would be your app's callback URL in production)
DEFAULT_REDIRECT_URI = "https://console.truelayer.com/redirect-page"

def bank_connection_component():
    """
    Display bank connection component with options to connect to a bank
    and manage existing connections.
    """
    st.header("Connect Your Bank")
    
    # Check for query parameters (for auth code callback)
    query_params = st.query_params.to_dict()
    
    if "code" in query_params:
        auth_code = query_params["code"]
        
        # Success message if we've already processed this code
        if "auth_code_processed" in st.session_state and st.session_state.auth_code_processed == auth_code:
            st.success("✅ Bank connected successfully!")
        else:
            with st.spinner("Connecting to your bank..."):
                # Handle the authorization code
                success = handle_auth_code(
                    auth_code=auth_code,
                    provider="TrueLayer",
                    redirect_uri=DEFAULT_REDIRECT_URI
                )
                
                if success:
                    st.session_state.auth_code_processed = auth_code
                    st.success("✅ Bank connected successfully!")
                    st.rerun()  # Refresh to show the new connection
                else:
                    st.error("❌ Failed to connect bank. Please try again.")
    
    # Get active connections
    connections = get_active_connections()
    
    # Display connected banks
    if connections:
        st.subheader("Connected Banks")
        
        # Get accounts for each connection
        for connection in connections:
            connection_id = connection["connection_id"]
            provider = connection["provider"]
            
            with st.expander(f"{provider} Connection", expanded=True):
                # Get accounts for this connection
                accounts = db_manager.get_bank_accounts(connection_id=connection_id)
                
                if accounts:
                    accounts_df = pd.DataFrame([
                        {
                            "Account": account["name"],
                            "Type": account["type"].capitalize(),
                            "Balance": f"{account.get('currency', '£')} {float(account['balance']):,.2f}"
                        }
                        for account in accounts
                    ])
                    
                    st.dataframe(
                        accounts_df,
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("No accounts found for this connection.")
                
                # Disconnect button
                if st.button("Disconnect", key=f"disconnect_{connection_id}"):
                    with st.spinner("Disconnecting bank..."):
                        success = disconnect_bank(connection_id)
                        if success:
                            st.success("Bank disconnected successfully.")
                            st.rerun()  # Refresh to show updated connections
                        else:
                            st.error("Failed to disconnect bank. Please try again.")
    
    # Connect new bank section
    st.subheader("Connect a New Bank")
    
    # Check if TrueLayer API is initialized
    if not truelayer_api.is_initialized():
        st.warning("⚠️ TrueLayer API credentials not configured.")
        st.info("Please set the TRUELAYER_CLIENT_ID and TRUELAYER_CLIENT_SECRET environment variables.")
        return
    
    # Generate auth URL
    auth_url = truelayer_api.create_auth_url(
        redirect_uri=DEFAULT_REDIRECT_URI,
        state=generate_user_id()  # Use user ID as state for additional security
    )
    
    if auth_url:
        st.markdown("""
        **Connect your bank account securely using TrueLayer:**
        
        1. Click the button below to start the connection process
        2. Select your bank from the list
        3. Log in with your bank credentials
        4. Authorize the connection
        5. You'll be redirected back to this app
        
        Your credentials are never stored in this application.
        """)
        
        st.link_button("Connect Bank Account", auth_url, use_container_width=True)
    else:
        st.error("Failed to create authorization URL. Please check API credentials.")
    
    # Information about bank connections
    with st.expander("About Bank Connections"):
        st.markdown("""
        ### How Your Data is Protected
        
        * **Secure Authentication**: We use OAuth 2.0 via TrueLayer for bank connections
        * **Read-Only Access**: This app has read-only access to your transaction data
        * **Bank-Level Security**: Your bank credentials are never shared with this application
        * **Encryption**: All sensitive data is encrypted before being stored
        * **User Control**: You can disconnect your bank account at any time
        
        ### About TrueLayer
        
        [TrueLayer](https://truelayer.com/) is a regulated financial API provider that enables secure 
        access to banking data using open banking standards. They comply with all relevant financial 
        regulations including PSD2 and GDPR.
        """)