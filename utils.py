import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

def parse_transaction_description(description):
    """
    Parse transaction descriptions to extract merchant names
    
    Parameters:
    -----------
    description: str
        Transaction description
        
    Returns:
    --------
    str
        Cleaned merchant name
    """
    if not description:
        return "Unknown"
    
    # Remove common prefixes
    prefixes = ['POS PURCHASE ', 'DEBIT PURCHASE ', 'ACH DEBIT ', 'ACH CREDIT ',
                'ONLINE PAYMENT ', 'PAYMENT - THANK YOU ', 'DIRECT DEPOSIT ']
    
    cleaned = description
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    
    # Remove dates and transaction numbers
    cleaned = re.sub(r'\d{2}/\d{2}/\d{2,4}', '', cleaned)
    cleaned = re.sub(r'\d{6,}', '', cleaned)
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def suggest_transaction_category(description, amount, existing_categories=None):
    """
    Suggest a category for a transaction based on description and amount
    
    Parameters:
    -----------
    description: str
        Transaction description
    amount: float
        Transaction amount
    existing_categories: pd.DataFrame, optional
        DataFrame with existing category mappings
        
    Returns:
    --------
    str
        Suggested category
    """
    # Common terms for categories
    category_keywords = {
        'Groceries': ['grocery', 'supermarket', 'food', 'market', 'whole foods', 'trader', 'wegmans', 'kroger', 'albertsons', 'safeway'],
        'Dining': ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'takeout', 'doordash', 'uber eats', 'grubhub', 'mcdonalds'],
        'Utilities': ['electric', 'gas', 'water', 'utility', 'phone', 'mobile', 'internet', 'cable', 'netflix', 'spotify'],
        'Transportation': ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'transit', 'parking', 'toll', 'metro', 'subway'],
        'Entertainment': ['movie', 'theatre', 'theater', 'concert', 'show', 'ticket', 'event', 'streaming', 'game'],
        'Shopping': ['amazon', 'walmart', 'target', 'costco', 'store', 'shop', 'retail', 'outlet', 'mall'],
        'Travel': ['hotel', 'airbnb', 'airline', 'flight', 'booking', 'vacation', 'travel', 'trip', 'rental'],
        'Health': ['doctor', 'pharmacy', 'medical', 'healthcare', 'prescription', 'hospital', 'clinic', 'dental'],
        'Rent': ['rent', 'lease', 'apartment', 'housing', 'landlord', 'property'],
        'Income': ['salary', 'payroll', 'deposit', 'income', 'revenue', 'dividend', 'interest']
    }
    
    # Check if we can match from existing data
    if existing_categories is not None and not existing_categories.empty:
        # Try to find an existing transaction with similar description
        desc_lower = description.lower()
        for _, row in existing_categories.iterrows():
            if row['description'] and row['description'].lower() in desc_lower:
                return row['category']
    
    # Check for keywords in description
    desc_lower = description.lower()
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword.lower() in desc_lower:
                return category
    
    # Use amount-based heuristics
    if amount >= 1000:
        return 'Rent' if amount < 5000 else 'Major Expense'
    elif amount <= 5:
        return 'Coffee' if 'coffee' in desc_lower else 'Small Purchase'
    
    # Default category
    return 'Uncategorized'

def calculate_financial_metrics(transactions_df, accounts=None):
    """
    Calculate various financial metrics
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    accounts: list, optional
        List of account dictionaries
        
    Returns:
    --------
    dict
        Dictionary of financial metrics
    """
    metrics = {}
    
    if transactions_df.empty:
        return metrics
    
    # Ensure date is datetime
    df = transactions_df.copy()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Calculate time-based metrics
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Monthly income and expenses
    if 'date' in df.columns and 'type' in df.columns and 'amount' in df.columns:
        monthly_df = df[(df['date'].dt.month == current_month) & (df['date'].dt.year == current_year)]
        
        # Monthly income
        monthly_income = monthly_df[monthly_df['type'] == 'income']['amount'].sum()
        metrics['monthly_income'] = monthly_income
        
        # Monthly expenses
        monthly_expenses = monthly_df[monthly_df['type'] == 'expense']['amount'].sum()
        metrics['monthly_expenses'] = monthly_expenses
        
        # Monthly savings
        metrics['monthly_savings'] = monthly_income - monthly_expenses
        
        # Savings rate
        metrics['savings_rate'] = (metrics['monthly_savings'] / monthly_income * 100) if monthly_income > 0 else 0
    
    # Net worth calculation
    if accounts:
        total_assets = sum(account.get('balance', 0) for account in accounts if account.get('type') not in ['Credit Card', 'Loan'])
        total_liabilities = sum(account.get('balance', 0) for account in accounts if account.get('type') in ['Credit Card', 'Loan'])
        metrics['net_worth'] = total_assets - total_liabilities
    
    # Spending by category
    if 'category' in df.columns and 'type' in df.columns and 'amount' in df.columns:
        expense_df = df[df['type'] == 'expense']
        category_totals = expense_df.groupby('category')['amount'].sum().reset_index()
        metrics['top_spending_category'] = category_totals.sort_values('amount', ascending=False).iloc[0]['category'] if not category_totals.empty else None
    
    return metrics

def generate_financial_insights(transactions_df, budget_analysis=None):
    """
    Generate insights based on financial data
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    budget_analysis: pd.DataFrame, optional
        DataFrame with budget analysis
        
    Returns:
    --------
    list
        List of insight strings
    """
    insights = []
    
    if transactions_df.empty:
        return ["Not enough data to generate insights."]
    
    # Ensure date is datetime
    df = transactions_df.copy()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Calculate basic metrics
    if 'type' in df.columns and 'amount' in df.columns:
        total_income = df[df['type'] == 'income']['amount'].sum()
        total_expenses = df[df['type'] == 'expense']['amount'].sum()
        
        # Income vs expenses
        if total_income > 0 and total_expenses > 0:
            savings_rate = (total_income - total_expenses) / total_income * 100
            if savings_rate > 20:
                insights.append(f"Great job! Your savings rate is {savings_rate:.1f}%, which is excellent.")
            elif savings_rate > 10:
                insights.append(f"Good work - your savings rate is {savings_rate:.1f}%, which is a healthy rate.")
            elif savings_rate > 0:
                insights.append(f"Your savings rate is {savings_rate:.1f}%. Consider ways to increase your savings.")
            else:
                insights.append("You're spending more than you earn. Consider reviewing your budget.")
    
    # Category insights
    if 'category' in df.columns and 'type' in df.columns and 'amount' in df.columns:
        expense_df = df[df['type'] == 'expense']
        
        if not expense_df.empty:
            # Top spending categories
            category_totals = expense_df.groupby('category')['amount'].sum().reset_index()
            sorted_categories = category_totals.sort_values('amount', ascending=False)
            
            if not sorted_categories.empty:
                top_category = sorted_categories.iloc[0]['category']
                top_amount = sorted_categories.iloc[0]['amount']
                
                insights.append(f"Your highest spending category is {top_category} (${top_amount:.2f}).")
    
    # Budget insights
    if budget_analysis is not None and not budget_analysis.empty:
        # Over budget categories
        over_budget = budget_analysis[budget_analysis['percent_used'] > 100]
        
        if not over_budget.empty:
            over_count = len(over_budget)
            if over_count == 1:
                category = over_budget.iloc[0]['category']
                insights.append(f"You've exceeded your budget for {category}. Consider adjusting your spending or your budget.")
            else:
                insights.append(f"You've exceeded your budget in {over_count} categories. Review your spending in these areas.")
        else:
            insights.append("You're staying within your budgets - great job!")
    
    # Spending trends
    if 'date' in df.columns and 'type' in df.columns and 'amount' in df.columns:
        # Get the last 3 months of data
        three_months_ago = datetime.now() - timedelta(days=90)
        recent_df = df[df['date'] >= three_months_ago]
        
        if not recent_df.empty:
            # Monthly expenses
            monthly_expenses = recent_df[recent_df['type'] == 'expense'].groupby(recent_df['date'].dt.strftime('%Y-%m'))['amount'].sum()
            
            if len(monthly_expenses) >= 2:
                latest_month = monthly_expenses.index[-1]
                previous_month = monthly_expenses.index[-2]
                
                if monthly_expenses[latest_month] > monthly_expenses[previous_month]:
                    increase = (monthly_expenses[latest_month] - monthly_expenses[previous_month]) / monthly_expenses[previous_month] * 100
                    insights.append(f"Your spending increased by {increase:.1f}% compared to last month.")
                else:
                    decrease = (monthly_expenses[previous_month] - monthly_expenses[latest_month]) / monthly_expenses[previous_month] * 100
                    insights.append(f"Good job! Your spending decreased by {decrease:.1f}% compared to last month.")
    
    # Add a generic insight if none were generated
    if not insights:
        insights.append("Import more transaction data to generate personalized insights.")
    
    return insights
