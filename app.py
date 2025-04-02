import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# Import modules
import data_handler as dh
import visualizations as viz
import budget_tools as budget
import utils

# Set page configuration
st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data persistence
if 'accounts' not in st.session_state:
    st.session_state.accounts = []
if 'transactions' not in st.session_state:
    st.session_state.transactions = pd.DataFrame()
if 'budgets' not in st.session_state:
    st.session_state.budgets = {}
if 'categories' not in st.session_state:
    st.session_state.categories = pd.read_csv('sample_data/categories.csv') if os.path.exists('sample_data/categories.csv') else pd.DataFrame(columns=['category', 'type'])

# App title and introduction
st.title("Personal Finance Dashboard")
st.markdown("Aggregate all your bank data in one place for comprehensive financial analysis.")

# Sidebar for navigation and settings
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        ["Dashboard", "Accounts", "Transactions", "Budgeting", "Import Data"]
    )
    
    st.header("Settings")
    date_range = st.selectbox(
        "Date Range",
        ["Last 30 days", "Last 3 months", "Last 6 months", "Last year", "All time"],
        index=0
    )
    
    # Convert date range to actual dates
    end_date = datetime.now().date()
    if date_range == "Last 30 days":
        start_date = end_date - timedelta(days=30)
    elif date_range == "Last 3 months":
        start_date = end_date - timedelta(days=90)
    elif date_range == "Last 6 months":
        start_date = end_date - timedelta(days=180)
    elif date_range == "Last year":
        start_date = end_date - timedelta(days=365)
    else:  # All time
        start_date = datetime(2000, 1, 1).date()

# Main content based on page selection
if page == "Dashboard":
    st.header("Financial Overview")
    
    # Show warning if no data is available
    if st.session_state.transactions.empty:
        st.warning("No transaction data available. Please import data first.")
        st.markdown("Go to **Import Data** page to upload your financial data.")
    else:
        # Filter transactions based on date range
        filtered_df = dh.filter_transactions_by_date(
            st.session_state.transactions, 
            start_date, 
            end_date
        )
        
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_balance = dh.calculate_total_balance(st.session_state.accounts)
            st.metric(label="Total Balance", value=f"${total_balance:,.2f}")
        
        with col2:
            income = dh.calculate_total_by_type(filtered_df, "income")
            st.metric(label="Income", value=f"${income:,.2f}")
        
        with col3:
            expenses = dh.calculate_total_by_type(filtered_df, "expense")
            st.metric(label="Expenses", value=f"${expenses:,.2f}")
        
        with col4:
            savings = income - expenses
            savings_rate = (savings / income * 100) if income > 0 else 0
            st.metric(label="Savings Rate", value=f"{savings_rate:.1f}%")
        
        # Spending trends
        st.subheader("Spending Trends")
        spending_trends_fig = viz.plot_spending_trends(filtered_df)
        st.plotly_chart(spending_trends_fig, use_container_width=True)
        
        # Income vs Expenses
        st.subheader("Income vs Expenses")
        income_expense_fig = viz.plot_income_vs_expenses(filtered_df)
        st.plotly_chart(income_expense_fig, use_container_width=True)
        
        # Spending by category
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Spending by Category")
            category_fig = viz.plot_spending_by_category(filtered_df)
            st.plotly_chart(category_fig, use_container_width=True)
        
        with col2:
            st.subheader("Top Merchants")
            merchant_fig = viz.plot_top_merchants(filtered_df)
            st.plotly_chart(merchant_fig, use_container_width=True)
        
        # Budget vs Actual
        st.subheader("Budget vs Actual")
        if st.session_state.budgets:
            budget_fig = viz.plot_budget_vs_actual(filtered_df, st.session_state.budgets)
            st.plotly_chart(budget_fig, use_container_width=True)
        else:
            st.info("No budgets set. Go to the Budgeting page to set up your budgets.")

elif page == "Accounts":
    st.header("Account Management")
    
    # Add new account
    with st.expander("Add New Account"):
        col1, col2, col3 = st.columns(3)
        with col1:
            account_name = st.text_input("Account Name", key="new_account_name")
        with col2:
            account_type = st.selectbox(
                "Account Type",
                ["Checking", "Savings", "Credit Card", "Investment", "Other"],
                key="new_account_type"
            )
        with col3:
            account_balance = st.number_input("Current Balance", min_value=0.0, key="new_account_balance")
        
        if st.button("Add Account"):
            if account_name and account_balance is not None:
                new_account = {
                    "name": account_name,
                    "type": account_type,
                    "balance": account_balance
                }
                st.session_state.accounts.append(new_account)
                st.success(f"Account '{account_name}' added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields.")
    
    # Display existing accounts
    if st.session_state.accounts:
        st.subheader("Your Accounts")
        
        accounts_df = pd.DataFrame(st.session_state.accounts)
        edited_df = st.data_editor(
            accounts_df,
            column_config={
                "name": "Account Name",
                "type": st.column_config.SelectboxColumn(
                    "Account Type",
                    options=["Checking", "Savings", "Credit Card", "Investment", "Other"],
                ),
                "balance": st.column_config.NumberColumn(
                    "Balance",
                    format="$%.2f",
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
        )
        
        # Update the accounts in session state
        if not edited_df.equals(accounts_df):
            st.session_state.accounts = edited_df.to_dict('records')
            st.success("Accounts updated successfully!")
        
        # Account balance visualization
        st.subheader("Account Balances")
        account_balance_fig = viz.plot_account_balances(pd.DataFrame(st.session_state.accounts))
        st.plotly_chart(account_balance_fig, use_container_width=True)
    else:
        st.info("No accounts added yet. Use the form above to add your first account.")

elif page == "Transactions":
    st.header("Transaction Management")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        account_filter = st.multiselect(
            "Filter by Account",
            options=[acc["name"] for acc in st.session_state.accounts],
            default=[]
        )
    with col2:
        category_filter = st.multiselect(
            "Filter by Category",
            options=st.session_state.categories["category"].unique().tolist() if 'category' in st.session_state.categories else [],
            default=[]
        )
    with col3:
        date_filter = st.date_input(
            "Date Range",
            value=(start_date, end_date)
        )
    
    # Show warning if no data is available
    if st.session_state.transactions.empty:
        st.warning("No transaction data available. Please import data first.")
        st.markdown("Go to **Import Data** page to upload your financial data.")
    else:
        # Filter transactions based on selected filters
        filtered_df = dh.filter_transactions(
            st.session_state.transactions,
            accounts=account_filter,
            categories=category_filter,
            start_date=date_filter[0] if len(date_filter) > 0 else None,
            end_date=date_filter[1] if len(date_filter) > 1 else None
        )
        
        # Add transaction manually
        with st.expander("Add New Transaction"):
            col1, col2 = st.columns(2)
            with col1:
                tx_date = st.date_input("Date", value=datetime.now())
                tx_account = st.selectbox(
                    "Account",
                    options=[acc["name"] for acc in st.session_state.accounts],
                    index=0 if st.session_state.accounts else None
                )
                tx_type = st.selectbox(
                    "Type",
                    options=["expense", "income", "transfer"],
                    index=0
                )
            
            with col2:
                tx_amount = st.number_input("Amount", min_value=0.01, value=0.01, step=0.01)
                tx_category = st.selectbox(
                    "Category",
                    options=st.session_state.categories["category"].unique().tolist() if 'category' in st.session_state.categories else []
                )
                tx_description = st.text_input("Description")
            
            if st.button("Add Transaction"):
                if tx_account and tx_amount > 0:
                    new_tx = {
                        "date": tx_date,
                        "account": tx_account,
                        "type": tx_type,
                        "amount": tx_amount,
                        "category": tx_category,
                        "description": tx_description
                    }
                    
                    # Convert to DataFrame and append to existing transactions
                    new_tx_df = pd.DataFrame([new_tx])
                    if st.session_state.transactions.empty:
                        st.session_state.transactions = new_tx_df
                    else:
                        st.session_state.transactions = pd.concat([st.session_state.transactions, new_tx_df], ignore_index=True)
                    
                    # Update account balance
                    dh.update_account_balance(st.session_state.accounts, tx_account, tx_amount, tx_type)
                    
                    st.success("Transaction added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields.")
        
        # Display transactions
        if not filtered_df.empty:
            st.subheader(f"Transactions ({len(filtered_df)} records)")
            
            # Create a copy to prevent modifying the original data
            display_df = filtered_df.copy()
            
            # Format the date column for display
            if 'date' in display_df.columns:
                display_df['date'] = pd.to_datetime(display_df['date']).dt.date
            
            # Display transactions in an editable table
            edited_df = st.data_editor(
                display_df,
                column_config={
                    "date": "Date",
                    "account": "Account",
                    "type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["expense", "income", "transfer"],
                    ),
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        format="$%.2f",
                    ),
                    "category": "Category",
                    "description": "Description"
                },
                use_container_width=True,
                hide_index=True,
            )
            
            # Allow bulk categorization for selected rows
            if st.button("Update Selected Transactions"):
                if not edited_df.equals(display_df):
                    # Update the transactions in session state
                    for index, row in edited_df.iterrows():
                        # Find the corresponding row in the original DataFrame
                        match_mask = (st.session_state.transactions['date'] == row['date']) & \
                                    (st.session_state.transactions['account'] == row['account']) & \
                                    (st.session_state.transactions['amount'] == row['amount']) & \
                                    (st.session_state.transactions['description'] == row['description'])
                        
                        if match_mask.any():
                            # Update the row
                            st.session_state.transactions.loc[match_mask, 'category'] = row['category']
                            st.session_state.transactions.loc[match_mask, 'type'] = row['type']
                    
                    st.success("Transactions updated successfully!")
                    st.rerun()
        else:
            st.info("No transactions match the selected filters.")

elif page == "Budgeting":
    st.header("Budgeting Tools")
    
    # Create tabs for different budgeting views
    budget_tab, analysis_tab = st.tabs(["Budget Setup", "Budget Analysis"])
    
    with budget_tab:
        st.subheader("Set Up Your Budget")
        
        # Get list of expense categories
        if not st.session_state.categories.empty and 'category' in st.session_state.categories.columns:
            expense_categories = st.session_state.categories[
                st.session_state.categories['type'] == 'expense'
            ]['category'].unique().tolist()
        else:
            expense_categories = []
        
        if not expense_categories:
            st.warning("No expense categories found. Import transaction data or add categories first.")
        else:
            # Create a form for budget setup
            budget_period = st.selectbox(
                "Budget Period",
                ["Monthly", "Annual"],
                index=0
            )
            
            # Create budget input fields for each category
            budget_data = {}
            
            for category in expense_categories:
                current_budget = st.session_state.budgets.get(category, 0)
                budget_data[category] = st.number_input(
                    f"Budget for {category} ({budget_period})",
                    min_value=0.0,
                    value=float(current_budget),
                    step=10.0,
                    format="%.2f"
                )
            
            if st.button("Save Budget"):
                st.session_state.budgets = budget_data
                st.success("Budget saved successfully!")
            
            # Option to reset all budgets
            if st.button("Reset All Budgets"):
                st.session_state.budgets = {}
                st.success("All budgets have been reset.")
                st.rerun()
    
    with analysis_tab:
        st.subheader("Budget Analysis")
        
        if not st.session_state.transactions.empty and st.session_state.budgets:
            # Filter transactions to current month for budget analysis
            current_month = datetime.now().month
            current_year = datetime.now().year
            start_of_month = datetime(current_year, current_month, 1).date()
            
            # Get end of month
            if current_month == 12:
                end_of_month = datetime(current_year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_of_month = datetime(current_year, current_month + 1, 1).date() - timedelta(days=1)
            
            # Filter transactions for the current month
            monthly_transactions = dh.filter_transactions_by_date(
                st.session_state.transactions,
                start_of_month,
                end_of_month
            )
            
            # Calculate budget vs actual spending
            budget_analysis = budget.calculate_budget_vs_actual(
                monthly_transactions,
                st.session_state.budgets
            )
            
            # Display budget summary
            if not budget_analysis.empty:
                st.write(f"Budget Analysis for {datetime.now().strftime('%B %Y')}")
                
                # Format the DataFrame for display
                display_df = budget_analysis.copy()
                display_df['budget'] = display_df['budget'].map('${:,.2f}'.format)
                display_df['spent'] = display_df['spent'].map('${:,.2f}'.format)
                display_df['remaining'] = display_df['remaining'].map('${:,.2f}'.format)
                display_df['percent_used'] = display_df['percent_used'].map('{:.1f}%'.format)
                
                st.dataframe(
                    display_df,
                    column_config={
                        "category": "Category",
                        "budget": "Budget",
                        "spent": "Spent",
                        "remaining": "Remaining",
                        "percent_used": "% Used"
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Budget progress visualization
                st.subheader("Budget Progress")
                budget_progress_fig = viz.plot_budget_progress(budget_analysis)
                st.plotly_chart(budget_progress_fig, use_container_width=True)
                
                # Daily spending rate
                days_in_month = (end_of_month - start_of_month).days + 1
                days_passed = (min(datetime.now().date(), end_of_month) - start_of_month).days + 1
                days_remaining = days_in_month - days_passed
                
                st.subheader("Spending Rate")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="Days in Month", 
                        value=days_in_month
                    )
                
                with col2:
                    st.metric(
                        label="Days Passed", 
                        value=days_passed
                    )
                
                with col3:
                    st.metric(
                        label="Days Remaining", 
                        value=days_remaining
                    )
                
                # Calculate daily spending metrics
                total_budget = budget_analysis['budget'].sum()
                total_spent = budget_analysis['spent'].sum()
                ideal_burn_rate = total_budget / days_in_month
                actual_burn_rate = total_spent / days_passed if days_passed > 0 else 0
                projected_total = actual_burn_rate * days_in_month
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="Ideal Daily Spending", 
                        value=f"${ideal_burn_rate:.2f}"
                    )
                
                with col2:
                    st.metric(
                        label="Actual Daily Spending", 
                        value=f"${actual_burn_rate:.2f}",
                        delta=f"{(actual_burn_rate - ideal_burn_rate):.2f}",
                        delta_color="inverse"
                    )
                
                with col3:
                    st.metric(
                        label="Projected Month Total", 
                        value=f"${projected_total:.2f}",
                        delta=f"{(projected_total - total_budget):.2f}",
                        delta_color="inverse"
                    )
            else:
                st.info("No budget data to analyze. Set up your budgets first.")
        elif not st.session_state.budgets:
            st.info("No budgets set. Go to the Budget Setup tab to set up your budgets.")
        else:
            st.warning("No transaction data available. Please import data first.")

elif page == "Import Data":
    st.header("Import Financial Data")
    
    # Tabs for different import methods
    import_tab, manual_tab, category_tab = st.tabs(["Import from CSV", "Manual Entry", "Manage Categories"])
    
    with import_tab:
        st.subheader("Import from CSV File")
        
        # File uploader
        uploaded_file = st.file_uploader("Upload your transaction data in CSV format", type=["csv"])
        
        if uploaded_file is not None:
            # Preview the data
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                # Mapping columns
                st.subheader("Map Columns")
                st.write("Select which columns in your CSV correspond to the required fields")
                
                # Get column names from the uploaded file
                column_options = [""] + df.columns.tolist()
                
                col1, col2 = st.columns(2)
                with col1:
                    date_col = st.selectbox("Date Column", column_options, index=0)
                    description_col = st.selectbox("Description Column", column_options, index=0)
                    amount_col = st.selectbox("Amount Column", column_options, index=0)
                
                with col2:
                    account_col = st.selectbox("Account Column", column_options, index=0)
                    category_col = st.selectbox("Category Column (optional)", column_options, index=0)
                    type_col = st.selectbox("Transaction Type Column (optional)", column_options, index=0)
                
                # Options for date format
                date_format = st.selectbox(
                    "Date Format",
                    [
                        "%Y-%m-%d",  # 2023-01-31
                        "%m/%d/%Y",  # 01/31/2023
                        "%d/%m/%Y",  # 31/01/2023
                        "%m-%d-%Y",  # 01-31-2023
                        "%d-%m-%Y",  # 31-01-2023
                        "%Y/%m/%d"   # 2023/01/31
                    ],
                    index=0
                )
                
                # Amount format handling
                amount_multiplier = st.selectbox(
                    "Amount Sign Convention",
                    [
                        "Positive for income, negative for expenses",
                        "Positive for expenses, negative for income",
                        "All positive, use type column to distinguish"
                    ],
                    index=0
                )
                
                # Process and import the data
                if st.button("Import Data"):
                    if date_col and amount_col and description_col:
                        # Process the data
                        processed_df = dh.process_imported_data(
                            df,
                            date_col=date_col,
                            description_col=description_col,
                            amount_col=amount_col,
                            account_col=account_col,
                            category_col=category_col,
                            type_col=type_col,
                            date_format=date_format,
                            amount_multiplier=amount_multiplier
                        )
                        
                        # Update session state with the imported data
                        if st.session_state.transactions.empty:
                            st.session_state.transactions = processed_df
                        else:
                            # Concat without duplicates
                            st.session_state.transactions = pd.concat(
                                [st.session_state.transactions, processed_df],
                                ignore_index=True
                            ).drop_duplicates()
                        
                        # Extract and store unique categories
                        if 'category' in processed_df.columns:
                            new_categories = processed_df[['category']].drop_duplicates()
                            if not new_categories.empty:
                                new_categories['type'] = new_categories['category'].apply(
                                    lambda x: 'expense' if x.lower() in ['groceries', 'rent', 'utilities', 'dining', 'transportation', 'entertainment', 'shopping'] else 'income'
                                )
                                
                                if st.session_state.categories.empty:
                                    st.session_state.categories = new_categories
                                else:
                                    # Combine categories without duplicates
                                    combined = pd.concat(
                                        [st.session_state.categories, new_categories],
                                        ignore_index=True
                                    ).drop_duplicates(subset=['category'])
                                    st.session_state.categories = combined
                        
                        st.success(f"Successfully imported {len(processed_df)} transactions!")
                        st.rerun()
                    else:
                        st.error("Please map all required columns before importing.")
            except Exception as e:
                st.error(f"Error processing the file: {str(e)}")
        
        # Sample template for download
        st.markdown("### Need a template?")
        st.write("Download a sample CSV template to format your data:")
        
        sample_data = {
            "Date": ["2023-01-15", "2023-01-20", "2023-01-25"],
            "Description": ["Grocery Store", "Salary Deposit", "Electric Bill"],
            "Amount": [-125.45, 2500.00, -85.20],
            "Account": ["Checking", "Checking", "Credit Card"],
            "Category": ["Groceries", "Income", "Utilities"]
        }
        sample_df = pd.DataFrame(sample_data)
        
        csv = sample_df.to_csv(index=False)
        st.download_button(
            label="Download CSV Template",
            data=csv,
            file_name="transaction_template.csv",
            mime="text/csv"
        )
    
    with manual_tab:
        st.subheader("Bulk Transaction Entry")
        
        # Create a dataframe with empty rows for manual entry
        empty_rows = 5
        empty_data = {
            "date": [""] * empty_rows,
            "description": [""] * empty_rows,
            "amount": [0.0] * empty_rows,
            "account": [""] * empty_rows,
            "category": [""] * empty_rows,
            "type": ["expense"] * empty_rows
        }
        empty_df = pd.DataFrame(empty_data)
        
        # Create an editable dataframe
        manual_df = st.data_editor(
            empty_df,
            column_config={
                "date": st.column_config.DateColumn("Date"),
                "description": "Description",
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    min_value=0.01,
                    format="%.2f",
                ),
                "account": st.column_config.SelectboxColumn(
                    "Account",
                    options=[acc["name"] for acc in st.session_state.accounts],
                ),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=st.session_state.categories["category"].unique().tolist() if not st.session_state.categories.empty and 'category' in st.session_state.categories else [],
                ),
                "type": st.column_config.SelectboxColumn(
                    "Type",
                    options=["expense", "income", "transfer"],
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
        )
        
        if st.button("Add Transactions"):
            # Remove empty rows
            valid_df = manual_df.dropna(subset=["date", "amount", "account"])
            
            if not valid_df.empty:
                # Update session state with the manually entered data
                if st.session_state.transactions.empty:
                    st.session_state.transactions = valid_df
                else:
                    st.session_state.transactions = pd.concat(
                        [st.session_state.transactions, valid_df],
                        ignore_index=True
                    )
                
                # Update account balances
                for _, row in valid_df.iterrows():
                    dh.update_account_balance(
                        st.session_state.accounts,
                        row["account"],
                        row["amount"],
                        row["type"]
                    )
                
                st.success(f"Successfully added {len(valid_df)} transactions!")
                st.rerun()
            else:
                st.warning("No valid transactions to add. Please fill in at least date, amount, and account fields.")
    
    with category_tab:
        st.subheader("Manage Transaction Categories")
        
        # Display existing categories
        if not st.session_state.categories.empty:
            # Create a copy to avoid modifying the original
            category_df = st.session_state.categories.copy()
            
            # Create an editable dataframe for categories
            edited_categories = st.data_editor(
                category_df,
                column_config={
                    "category": "Category Name",
                    "type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["income", "expense", "transfer"],
                    )
                },
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
            )
            
            if st.button("Save Categories"):
                # Update categories in session state
                st.session_state.categories = edited_categories
                
                # Write to CSV file for persistence
                if not os.path.exists('sample_data'):
                    os.makedirs('sample_data')
                edited_categories.to_csv('sample_data/categories.csv', index=False)
                
                st.success("Categories saved successfully!")
        else:
            # Create a new categories dataframe
            empty_categories = pd.DataFrame({
                "category": ["Salary", "Groceries", "Rent", "Utilities", "Dining", "Transportation", "Entertainment", "Shopping"],
                "type": ["income", "expense", "expense", "expense", "expense", "expense", "expense", "expense"]
            })
            
            edited_categories = st.data_editor(
                empty_categories,
                column_config={
                    "category": "Category Name",
                    "type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["income", "expense", "transfer"],
                    )
                },
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
            )
            
            if st.button("Save Categories"):
                # Update categories in session state
                st.session_state.categories = edited_categories
                
                # Write to CSV file for persistence
                if not os.path.exists('sample_data'):
                    os.makedirs('sample_data')
                edited_categories.to_csv('sample_data/categories.csv', index=False)
                
                st.success("Categories saved successfully!")
