import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

from bank_integration.auth_manager import generate_user_id, get_active_connections, db_manager
from bank_integration.transaction_manager import get_account_transactions, sync_all_account_transactions, categorize_transactions

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transaction_dashboard_component():
    """
    Display the transaction dashboard component with account balances,
    recent transactions, and spending visualizations.
    """
    st.header("Financial Dashboard")
    
    # Check if authenticated
    if not st.session_state.get("authenticated", False):
        st.info("Connect a bank account to see your financial dashboard")
        if st.button("Connect Bank Account"):
            # Switch to connect bank page
            st.session_state.nav = "Accounts & Transactions"
            st.rerun()
        return
    
    # Get user ID
    user_id = generate_user_id()
    
    # Get accounts
    accounts = db_manager.get_bank_accounts(user_id=user_id)
    
    if not accounts:
        st.info("No bank accounts connected yet")
        if st.button("Connect Bank Account"):
            st.session_state.nav = "Accounts & Transactions"
            st.rerun()
        return
    
    # Show auto-sync option
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Account Overview")
    
    with col2:
        if st.button("🔄 Sync Data", help="Refresh your transaction data from the banks"):
            with st.spinner("Syncing transactions..."):
                sync_results = sync_all_account_transactions(force_full_sync=False)
                
                if sync_results["success"]:
                    st.success(f"Synced {sync_results['total_transactions']} transactions")
                else:
                    st.warning("Some accounts failed to sync")
    
    # Show account balances
    show_account_balances(accounts)
    
    # Get transactions for the past 90 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    transactions_df = get_account_transactions(
        start_date=start_date,
        end_date=end_date
    )
    
    # If no transactions, show message
    if transactions_df.empty:
        st.info("No transactions found for the selected time period")
        return
    
    # Make sure we have categories
    transactions_df = categorize_transactions(transactions_df)
    
    # Show financial insights
    st.subheader("Financial Insights")
    
    tab1, tab2, tab3 = st.tabs(["Monthly Overview", "Spending Categories", "Recent Transactions"])
    
    with tab1:
        show_income_vs_expenses(transactions_df)
    
    with tab2:
        show_category_breakdown(transactions_df)
    
    with tab3:
        show_recent_transactions(transactions_df)

def show_account_balances(accounts):
    """
    Show account balances in a card format
    
    Parameters:
    -----------
    accounts: list
        List of account dictionaries
    """
    # Calculate total balance
    total_balance = sum(float(account["balance"]) for account in accounts)
    
    # Show total balance
    st.metric(
        label="Total Balance",
        value=f"£{total_balance:,.2f}"
    )
    
    # Create account cards
    cols = st.columns(min(len(accounts), 3))
    
    for i, account in enumerate(accounts):
        col_idx = i % len(cols)
        
        with cols[col_idx]:
            account_name = account["name"]
            account_type = account["type"].capitalize()
            balance = float(account["balance"])
            currency = account.get("currency", "£")
            
            st.metric(
                label=f"{account_name} ({account_type})",
                value=f"{currency} {balance:,.2f}"
            )

def show_income_vs_expenses(transactions_df):
    """
    Show income vs expenses over time
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    """
    if transactions_df.empty:
        st.info("No transaction data available")
        return
    
    # Ensure date is datetime
    transactions_df["date"] = pd.to_datetime(transactions_df["date"])
    
    # Group by month and type
    monthly_df = transactions_df.copy()
    monthly_df["month"] = monthly_df["date"].dt.strftime("%Y-%m")
    
    # Group by month and transaction type
    monthly_summary = monthly_df.groupby(["month", "type"])["amount"].sum().reset_index()
    
    # Pivot for plotting
    pivot_df = monthly_summary.pivot(index="month", columns="type", values="amount").reset_index()
    pivot_df = pivot_df.fillna(0)
    
    # Ensure income and expense columns exist
    if "income" not in pivot_df.columns:
        pivot_df["income"] = 0
    
    if "expense" not in pivot_df.columns:
        pivot_df["expense"] = 0
    
    # Calculate net (income - expense)
    pivot_df["net"] = pivot_df["income"] - pivot_df["expense"]
    
    # Sort by month
    pivot_df = pivot_df.sort_values("month")
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add bars for income and expense
    fig.add_trace(
        go.Bar(
            x=pivot_df["month"],
            y=pivot_df["income"],
            name="Income",
            marker_color="green"
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=pivot_df["month"],
            y=pivot_df["expense"],
            name="Expenses",
            marker_color="red"
        )
    )
    
    # Add line for net
    fig.add_trace(
        go.Scatter(
            x=pivot_df["month"],
            y=pivot_df["net"],
            name="Net",
            line=dict(color="blue", width=3),
            mode="lines+markers"
        )
    )
    
    # Update layout
    fig.update_layout(
        title="Monthly Income vs Expenses",
        xaxis_title="Month",
        yaxis_title="Amount (£)",
        legend_title="Type",
        barmode="group",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary of latest month
    if not pivot_df.empty:
        latest_month = pivot_df.iloc[-1]
        
        cols = st.columns(3)
        with cols[0]:
            st.metric("Income", f"£{latest_month['income']:,.2f}")
        
        with cols[1]:
            st.metric("Expenses", f"£{latest_month['expense']:,.2f}")
        
        with cols[2]:
            st.metric("Net", f"£{latest_month['net']:,.2f}")

def show_category_breakdown(transactions_df):
    """
    Show spending breakdown by category
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    """
    if transactions_df.empty:
        st.info("No transaction data available")
        return
    
    # Filter for expenses only
    expenses_df = transactions_df[transactions_df["type"] == "expense"]
    
    if expenses_df.empty:
        st.info("No expense data available")
        return
    
    # Group by category
    category_totals = expenses_df.groupby("category")["amount"].sum().reset_index()
    
    # Sort by amount descending
    category_totals = category_totals.sort_values("amount", ascending=False)
    
    # Create pie chart
    fig = px.pie(
        category_totals,
        values="amount",
        names="category",
        title="Spending by Category",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        hole=0.4
    )
    
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=14
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show top categories as a bar chart
    top_categories = category_totals.head(6)
    
    fig2 = px.bar(
        top_categories,
        x="category",
        y="amount",
        title="Top Spending Categories",
        color="category",
        labels={"amount": "Amount (£)", "category": "Category"}
    )
    
    st.plotly_chart(fig2, use_container_width=True)

def show_recent_transactions(transactions_df, limit=10):
    """
    Show a table of recent transactions
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    limit: int
        Number of transactions to show
    """
    if transactions_df.empty:
        st.info("No transaction data available")
        return
    
    # Ensure date is datetime and sort
    transactions_df["date"] = pd.to_datetime(transactions_df["date"])
    sorted_df = transactions_df.sort_values("date", ascending=False)
    
    # Take top N transactions
    recent_df = sorted_df.head(limit)
    
    # Get account names
    accounts = db_manager.get_bank_accounts(user_id=generate_user_id())
    account_map = {account["account_id"]: account["name"] for account in accounts} if accounts else {}
    
    # Format for display
    display_df = recent_df.copy()
    
    # Format date
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    
    # Add account name
    display_df["account"] = display_df["account_id"].map(account_map)
    
    # Format amount with currency
    display_df["formatted_amount"] = display_df.apply(
        lambda row: f"{row.get('currency', '£')} {float(row['amount']):,.2f}",
        axis=1
    )
    
    # Capitalize type and category
    display_df["type"] = display_df["type"].str.capitalize()
    display_df["category"] = display_df["category"].str.title()
    
    # Select columns for display
    display_cols = ["date", "account", "description", "formatted_amount", "type", "category"]
    
    # Rename columns
    rename_cols = {
        "date": "Date",
        "account": "Account",
        "description": "Description",
        "formatted_amount": "Amount",
        "type": "Type",
        "category": "Category"
    }
    
    # Select and rename
    final_df = display_df[display_cols].rename(columns=rename_cols)
    
    # Show dataframe
    st.dataframe(
        final_df,
        hide_index=True,
        use_container_width=True
    )