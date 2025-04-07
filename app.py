import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import time

# Import custom modules
from bank_integration import auth_manager, transaction_manager
from components import bank_connection, transaction_dashboard
from utils.encryption import get_fernet_key

# Configure page
st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check for required env variables
def check_api_keys():
    """Check if API keys are set"""
    truelayer_client_id = os.getenv("TRUELAYER_CLIENT_ID")
    truelayer_client_secret = os.getenv("TRUELAYER_CLIENT_SECRET")
    
    if not truelayer_client_id or not truelayer_client_secret:
        st.sidebar.warning("⚠️ TrueLayer API keys not found")
        st.sidebar.info("Set TRUELAYER_CLIENT_ID and TRUELAYER_CLIENT_SECRET environment variables")
        return False
    
    return True

# Sidebar navigation
def sidebar():
    st.sidebar.title("Personal Finance")
    
    # Show navigation options
    nav_options = [
        "Dashboard",
        "Accounts & Transactions",
        "Budgeting",
        "Settings"
    ]
    
    # Use session state for navigation if available
    if "nav" in st.session_state:
        default_idx = nav_options.index(st.session_state.nav) if st.session_state.nav in nav_options else 0
    else:
        default_idx = 0
    
    selected = st.sidebar.radio("Navigation", nav_options, index=default_idx)
    
    # API key status
    with st.sidebar.expander("API Status", expanded=False):
        if check_api_keys():
            st.success("✅ TrueLayer API keys configured")
        else:
            st.error("❌ TrueLayer API keys missing")
    
    # Show sync status
    if st.session_state.get("authenticated", False):
        with st.sidebar.expander("Sync Status", expanded=False):
            user_id = auth_manager.generate_user_id()
            accounts = auth_manager.db_manager.get_bank_accounts(user_id)
            
            if accounts:
                st.write(f"Connected accounts: {len(accounts)}")
                
                connections = auth_manager.get_active_connections()
                for connection in connections:
                    last_sync = connection.get("last_sync")
                    if last_sync:
                        last_sync_dt = datetime.fromisoformat(last_sync)
                        time_diff = datetime.now() - last_sync_dt
                        
                        if time_diff < timedelta(hours=1):
                            st.success("✅ Synced recently")
                        elif time_diff < timedelta(days=1):
                            st.info("ℹ️ Synced today")
                        else:
                            st.warning(f"⚠️ Last synced {time_diff.days} days ago")
            else:
                st.warning("No accounts connected")
    
    return selected

# Initialize app
def initialize():
    """Initialize the app"""
    # Initialize encryption
    get_fernet_key()
    
    # Initialize database connection
    if "initialized" not in st.session_state:
        auth_manager.initialize_auth()
        st.session_state.initialized = True

# Main application
def main():
    # Initialize
    initialize()
    
    # Sidebar navigation
    selected_page = sidebar()
    
    # Store navigation in session state
    st.session_state.nav = selected_page
    
    # Main content based on navigation
    if selected_page == "Dashboard":
        transaction_dashboard.transaction_dashboard_component()
    
    elif selected_page == "Accounts & Transactions":
        tabs = st.tabs(["Connected Accounts", "Transactions", "Connect Bank"])
        
        with tabs[0]:
            st.header("Bank Accounts")
            user_id = auth_manager.generate_user_id()
            accounts = auth_manager.db_manager.get_bank_accounts(user_id)
            
            if accounts:
                # Create dataframe for display
                accounts_df = pd.DataFrame([
                    {
                        "Account": account["name"],
                        "Type": account["type"],
                        "Balance": f"{account.get('currency', '£')} {float(account['balance']):,.2f}",
                        "Provider": account["provider"],
                        "Last Updated": datetime.fromisoformat(account["last_updated"]).strftime("%Y-%m-%d %H:%M")
                    }
                    for account in accounts
                ])
                
                st.dataframe(
                    accounts_df,
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No bank accounts connected yet. Go to the 'Connect Bank' tab to get started.")
        
        with tabs[1]:
            st.header("Transactions")
            
            user_id = auth_manager.generate_user_id()
            accounts = auth_manager.db_manager.get_bank_accounts(user_id)
            
            if accounts:
                # Account selector
                account_options = ["All Accounts"] + [account["name"] for account in accounts]
                selected_account = st.selectbox("Select Account", account_options)
                
                account_id = None
                if selected_account != "All Accounts":
                    # Find the selected account
                    for account in accounts:
                        if account["name"] == selected_account:
                            account_id = account["account_id"]
                            break
                
                # Date range
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
                with col2:
                    end_date = st.date_input("End Date", value=datetime.now().date())
                
                # Search filters
                search_term = st.text_input("Search Transactions", placeholder="Search by description...")
                
                # Get transactions
                transactions_df = transaction_manager.get_account_transactions(
                    account_id=account_id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not transactions_df.empty:
                    # Apply search filter if provided
                    if search_term:
                        transactions_df = transactions_df[
                            transactions_df["description"].str.contains(search_term, case=False)
                        ]
                    
                    # Format for display
                    display_df = transactions_df.copy()
                    
                    # Ensure date is datetime and format
                    display_df["date"] = pd.to_datetime(display_df["date"])
                    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
                    
                    # Format amount with currency
                    display_df["amount"] = display_df.apply(
                        lambda row: f"{row.get('currency', '£')} {float(row['amount']):,.2f}",
                        axis=1
                    )
                    
                    # Capitalize type and category
                    display_df["type"] = display_df["type"].str.capitalize()
                    display_df["category"] = display_df["category"].str.title()
                    
                    # Add account name column if showing all accounts
                    if account_id is None:
                        account_map = {account["account_id"]: account["name"] for account in accounts}
                        display_df["account"] = display_df["account_id"].map(account_map)
                        columns = ["date", "account", "description", "amount", "type", "category"]
                    else:
                        columns = ["date", "description", "amount", "type", "category"]
                    
                    # Select and rename columns
                    display_df = display_df[columns]
                    display_df.columns = [col.capitalize() for col in columns]
                    
                    # Show dataframe
                    st.dataframe(
                        display_df,
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Show download button
                    csv = display_df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"transactions_{start_date}_to_{end_date}.csv",
                        "text/csv",
                        key="download-csv"
                    )
                    
                    # Show stats
                    st.caption(f"Showing {len(display_df)} transactions from {start_date} to {end_date}")
                else:
                    st.info("No transactions found for the selected criteria")
            else:
                st.info("No bank accounts connected yet. Go to the 'Connect Bank' tab to get started.")
        
        with tabs[2]:
            bank_connection.bank_connection_component()
    
    elif selected_page == "Budgeting":
        st.header("Budgeting")
        
        # Check if authenticated
        if not st.session_state.get("authenticated", False):
            st.info("Connect a bank account to use budgeting features")
            if st.button("Connect Bank Account"):
                # Switch to connect bank page
                st.session_state.nav = "Accounts & Transactions"
                st.rerun()
            return
        
        # Get transactions for category selection
        user_id = auth_manager.generate_user_id()
        transactions_df = transaction_manager.get_account_transactions(
            start_date=datetime.now().date() - timedelta(days=90),
            end_date=datetime.now().date()
        )
        
        if transactions_df.empty:
            st.info("No transaction data available. Sync your accounts to use budgeting features.")
            return
        
        # Make sure we have categories
        transactions_df = transaction_manager.categorize_transactions(transactions_df)
        
        # Get existing budgets
        budgets = auth_manager.db_manager.get_budgets(user_id)
        
        # Tabs for budget view and management
        tab1, tab2 = st.tabs(["Budget Overview", "Manage Budgets"])
        
        with tab1:
            st.subheader("Monthly Budget vs Actual")
            
            if not budgets:
                st.info("No budgets set yet. Go to the 'Manage Budgets' tab to create some.")
            else:
                # Calculate actual spending for the current month
                today = datetime.now().date()
                start_of_month = datetime(today.year, today.month, 1).date()
                
                monthly_spending = transactions_df[
                    (transactions_df["type"] == "expense") &
                    (pd.to_datetime(transactions_df["date"]).dt.date >= start_of_month)
                ]
                
                # Group by category
                if not monthly_spending.empty:
                    category_spending = monthly_spending.groupby("category")["amount"].sum()
                    
                    # Create a dataframe for the budget vs actual
                    budget_vs_actual = []
                    
                    for category, budget_info in budgets.items():
                        budget_amount = budget_info["amount"]
                        actual_amount = category_spending.get(category, 0)
                        
                        # Calculate percentage
                        percent = (actual_amount / budget_amount * 100) if budget_amount > 0 else 0
                        
                        budget_vs_actual.append({
                            "Category": category,
                            "Budget": budget_amount,
                            "Actual": actual_amount,
                            "Percent": percent,
                            "Remaining": budget_amount - actual_amount
                        })
                    
                    budget_df = pd.DataFrame(budget_vs_actual)
                    
                    if not budget_df.empty:
                        # Sort by percent descending
                        budget_df = budget_df.sort_values("Percent", ascending=False)
                        
                        # Create progress bars
                        for _, row in budget_df.iterrows():
                            cat = row["Category"]
                            budget = row["Budget"]
                            actual = row["Actual"]
                            percent = row["Percent"]
                            remaining = row["Remaining"]
                            
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"**{cat}**")
                                progress_color = "normal"
                                if percent > 90:
                                    progress_color = "off"
                                
                                # Cap at 100% for the progress bar
                                bar_value = min(percent / 100, 1.0)
                                st.progress(bar_value, text=f"{percent:.1f}%")
                            
                            with col2:
                                st.write(f"£{actual:,.2f} of £{budget:,.2f}")
                                if remaining >= 0:
                                    st.caption(f"£{remaining:,.2f} remaining")
                                else:
                                    st.caption(f"£{-remaining:,.2f} over budget", unsafe_allow_html=True)
                            
                            st.write("---")
                    else:
                        st.info("No spending in budgeted categories this month.")
                else:
                    st.info("No spending recorded this month.")
        
        with tab2:
            st.subheader("Manage Your Budgets")
            
            # Get all unique categories from transactions
            categories = []
            if not transactions_df.empty and 'category' in transactions_df.columns:
                categories = sorted(transactions_df['category'].unique())
            
            # Show existing budgets
            if budgets:
                st.write("Current Budgets:")
                
                for category, budget in budgets.items():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**{category}**")
                    
                    with col2:
                        st.write(f"£{budget['amount']:,.2f} / {budget['period']}")
                    
                    with col3:
                        if st.button("Edit", key=f"edit_{category}"):
                            st.session_state.edit_budget = category
                            st.session_state.edit_amount = budget['amount']
            
            # Add or edit budget form
            st.write("---")
            
            if hasattr(st.session_state, 'edit_budget'):
                st.subheader(f"Edit Budget: {st.session_state.edit_budget}")
                category = st.session_state.edit_budget
                default_amount = st.session_state.edit_amount
                is_edit = True
            else:
                st.subheader("Add New Budget")
                if categories:
                    category = st.selectbox("Category", categories)
                else:
                    category = st.text_input("Category")
                default_amount = 0.0
                is_edit = False
            
            with st.form(key="budget_form"):
                amount = st.number_input("Budget Amount (£)", min_value=0.0, value=default_amount, step=10.0)
                period = st.selectbox("Period", ["monthly", "weekly", "yearly"], index=0)
                
                submit = st.form_submit_button("Save Budget")
                
                if submit and category and amount > 0:
                    # Save budget
                    auth_manager.db_manager.save_budget(user_id, category, amount, period)
                    
                    if is_edit:
                        st.success(f"Updated budget for {category}")
                        # Clear edit state
                        if hasattr(st.session_state, 'edit_budget'):
                            delattr(st.session_state, 'edit_budget')
                        if hasattr(st.session_state, 'edit_amount'):
                            delattr(st.session_state, 'edit_amount')
                    else:
                        st.success(f"Added new budget for {category}")
                    
                    # Refresh the page
                    time.sleep(1)
                    st.rerun()
    
    elif selected_page == "Settings":
        st.header("Settings")
        
        # User information
        user_id = auth_manager.generate_user_id()
        
        st.subheader("User Information")
        st.info(f"User ID: {user_id}")
        st.caption("This is a demo user ID. In a real app, this would be tied to your account.")
        
        # Bank account information
        st.subheader("Connected Banks")
        accounts = auth_manager.db_manager.get_bank_accounts(user_id)
        
        if accounts:
            st.write(f"You have {len(accounts)} connected accounts")
            
            # Show connection details
            connections = auth_manager.get_active_connections()
            for connection in connections:
                with st.expander(f"Connection: {connection['provider']}"):
                    st.write(f"Provider: {connection['provider']}")
                    if "last_sync" in connection and connection["last_sync"]:
                        st.write(f"Last Sync: {datetime.fromisoformat(connection['last_sync']).strftime('%Y-%m-%d %H:%M')}")
                    
                    # Show accounts for this connection
                    connection_accounts = [a for a in accounts if a["connection_id"] == connection["connection_id"]]
                    for account in connection_accounts:
                        st.write(f"• {account['name']} ({account['type']}): {account.get('currency', '£')} {float(account['balance']):,.2f}")
        else:
            st.info("No bank accounts connected.")
            if st.button("Connect Bank Account"):
                st.session_state.nav = "Accounts & Transactions"
                st.rerun()
        
        # Data management
        st.subheader("Data Management")
        
        # Sync data
        if st.button("Sync All Transactions"):
            with st.spinner("Syncing transactions..."):
                results = transaction_manager.sync_all_account_transactions(force_full_sync=True)
                
                if results["success"]:
                    st.success(f"Successfully synced {results['total_transactions']} transactions")
                else:
                    st.warning("Some accounts failed to sync")
                
                with st.expander("Sync Details"):
                    st.json(results)
        
        # About section
        st.subheader("About")
        st.write("""
        This is a personal finance dashboard demo using TrueLayer for bank integration.
        
        The application allows you to:
        - Connect to your bank accounts securely via TrueLayer API
        - View transactions and account balances 
        - Create and track budgets
        - Visualize your spending patterns
        
        This is a demonstration only and should not be used for production purposes.
        """)

if __name__ == "__main__":
    main()