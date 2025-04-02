import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

def plot_account_balances(accounts_df):
    """
    Create a bar chart of account balances
    
    Parameters:
    -----------
    accounts_df: pd.DataFrame
        DataFrame containing account information
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A bar chart of account balances
    """
    if accounts_df.empty:
        return go.Figure()
    
    # Sort accounts by balance in descending order
    sorted_df = accounts_df.sort_values('balance', ascending=False)
    
    # Set colors based on account type
    colors = {
        'Checking': '#1f77b4',
        'Savings': '#2ca02c',
        'Credit Card': '#d62728',
        'Investment': '#9467bd',
        'Other': '#8c564b'
    }
    
    color_map = sorted_df['type'].map(colors)
    
    # Create bar chart
    fig = px.bar(
        sorted_df,
        x='name',
        y='balance',
        color='type',
        color_discrete_map=colors,
        title='Account Balances',
        labels={'name': 'Account', 'balance': 'Balance ($)', 'type': 'Account Type'}
    )
    
    # Format y-axis as currency
    fig.update_layout(
        yaxis=dict(
            tickprefix='$',
            tickformat=',.2f'
        ),
        xaxis=dict(
            categoryorder='total descending'
        )
    )
    
    return fig

def plot_spending_trends(transactions_df):
    """
    Create a line chart of spending trends over time
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A line chart of spending trends
    """
    if transactions_df.empty or 'date' not in transactions_df.columns:
        return go.Figure()
    
    # Ensure date is datetime
    df = transactions_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date and transaction type
    daily_totals = df.groupby([pd.Grouper(key='date', freq='D'), 'type'])['amount'].sum().reset_index()
    
    # Create line chart
    fig = px.line(
        daily_totals,
        x='date',
        y='amount',
        color='type',
        title='Daily Spending and Income Trends',
        labels={'date': 'Date', 'amount': 'Amount ($)', 'type': 'Transaction Type'},
        color_discrete_map={'income': '#2ca02c', 'expense': '#d62728', 'transfer': '#1f77b4'}
    )
    
    # Format y-axis as currency
    fig.update_layout(
        yaxis=dict(
            tickprefix='$',
            tickformat=',.2f'
        )
    )
    
    return fig

def plot_spending_by_category(transactions_df):
    """
    Create a pie chart of spending by category
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A pie chart of spending by category
    """
    if transactions_df.empty or 'category' not in transactions_df.columns:
        return go.Figure()
    
    # Filter for expenses only
    expenses_df = transactions_df[transactions_df['type'] == 'expense']
    
    if expenses_df.empty:
        return go.Figure()
    
    # Group by category and sum amounts
    category_totals = expenses_df.groupby('category')['amount'].sum().reset_index()
    
    # Create pie chart
    fig = px.pie(
        category_totals,
        values='amount',
        names='category',
        title='Spending by Category',
        hole=0.4
    )
    
    # Format values as currency
    fig.update_traces(
        textinfo='label+percent',
        hovertemplate='%{label}<br>$%{value:.2f}<br>%{percent}'
    )
    
    return fig

def plot_income_vs_expenses(transactions_df):
    """
    Create a bar chart comparing income vs expenses by month
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A bar chart of income vs expenses
    """
    if transactions_df.empty or 'date' not in transactions_df.columns:
        return go.Figure()
    
    # Ensure date is datetime
    df = transactions_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Add month column for grouping
    df['month'] = df['date'].dt.strftime('%Y-%m')
    
    # Group by month and transaction type
    monthly_totals = df.groupby(['month', 'type'])['amount'].sum().reset_index()
    
    # Pivot to get income and expense columns
    pivot_df = monthly_totals.pivot(index='month', columns='type', values='amount').reset_index()
    
    # Fill NaN values with 0
    if 'income' not in pivot_df.columns:
        pivot_df['income'] = 0
    if 'expense' not in pivot_df.columns:
        pivot_df['expense'] = 0
    
    # Calculate net (income - expense)
    pivot_df['net'] = pivot_df['income'] - pivot_df['expense']
    
    # Create grouped bar chart
    fig = go.Figure()
    
    # Add income bars
    fig.add_trace(
        go.Bar(
            x=pivot_df['month'],
            y=pivot_df['income'],
            name='Income',
            marker_color='#2ca02c'
        )
    )
    
    # Add expense bars
    fig.add_trace(
        go.Bar(
            x=pivot_df['month'],
            y=pivot_df['expense'],
            name='Expenses',
            marker_color='#d62728'
        )
    )
    
    # Add net line
    fig.add_trace(
        go.Scatter(
            x=pivot_df['month'],
            y=pivot_df['net'],
            name='Net',
            mode='lines+markers',
            marker_color='#1f77b4',
            line=dict(width=3)
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Monthly Income vs Expenses',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        yaxis=dict(
            tickprefix='$',
            tickformat=',.2f'
        ),
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_budget_vs_actual(transactions_df, budgets):
    """
    Create a bar chart comparing budget vs actual spending
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    budgets: dict
        Dictionary mapping categories to budget amounts
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A bar chart of budget vs actual spending
    """
    if transactions_df.empty or not budgets:
        return go.Figure()
    
    # Filter for expenses only
    expenses_df = transactions_df[transactions_df['type'] == 'expense']
    
    if expenses_df.empty:
        return go.Figure()
    
    # Group by category and sum amounts
    actual_spending = expenses_df.groupby('category')['amount'].sum().reset_index()
    
    # Create DataFrame for budgets
    budget_df = pd.DataFrame({
        'category': list(budgets.keys()),
        'budget': list(budgets.values())
    })
    
    # Merge actual spending with budgets
    comparison_df = pd.merge(budget_df, actual_spending, on='category', how='left')
    comparison_df.fillna(0, inplace=True)
    comparison_df.rename(columns={'amount': 'actual'}, inplace=True)
    
    # Sort by budget amount
    comparison_df = comparison_df.sort_values('budget', ascending=False)
    
    # Create grouped bar chart
    fig = go.Figure()
    
    # Add budget bars
    fig.add_trace(
        go.Bar(
            x=comparison_df['category'],
            y=comparison_df['budget'],
            name='Budget',
            marker_color='#1f77b4'
        )
    )
    
    # Add actual spending bars
    fig.add_trace(
        go.Bar(
            x=comparison_df['category'],
            y=comparison_df['actual'],
            name='Actual',
            marker_color='#ff7f0e'
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Budget vs Actual Spending by Category',
        xaxis_title='Category',
        yaxis_title='Amount ($)',
        yaxis=dict(
            tickprefix='$',
            tickformat=',.2f'
        ),
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_top_merchants(transactions_df, top_n=10):
    """
    Create a bar chart of top merchants by spending
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    top_n: int
        Number of top merchants to display
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A bar chart of top merchants
    """
    if transactions_df.empty or 'description' not in transactions_df.columns:
        return go.Figure()
    
    # Filter for expenses only
    expenses_df = transactions_df[transactions_df['type'] == 'expense']
    
    if expenses_df.empty:
        return go.Figure()
    
    # Group by description and sum amounts
    merchant_totals = expenses_df.groupby('description')['amount'].sum().reset_index()
    
    # Sort by amount and take top N
    top_merchants = merchant_totals.sort_values('amount', ascending=False).head(top_n)
    
    # Create bar chart
    fig = px.bar(
        top_merchants,
        x='amount',
        y='description',
        orientation='h',
        title=f'Top {top_n} Merchants by Spending',
        labels={'description': 'Merchant', 'amount': 'Amount ($)'}
    )
    
    # Format x-axis as currency
    fig.update_layout(
        xaxis=dict(
            tickprefix='$',
            tickformat=',.2f'
        ),
        yaxis=dict(
            categoryorder='total ascending'
        )
    )
    
    return fig

def plot_budget_progress(budget_analysis):
    """
    Create a horizontal bar chart showing budget progress
    
    Parameters:
    -----------
    budget_analysis: pd.DataFrame
        DataFrame containing budget analysis data
        
    Returns:
    --------
    plotly.graph_objects.Figure
        A horizontal bar chart of budget progress
    """
    if budget_analysis.empty:
        return go.Figure()
    
    # Sort by percentage used
    sorted_df = budget_analysis.sort_values('percent_used', ascending=False)
    
    # Create the figure
    fig = go.Figure()
    
    # Add traces for each category
    for i, row in sorted_df.iterrows():
        percentage = row['percent_used']
        color = '#d62728' if percentage > 100 else '#1f77b4'
        
        fig.add_trace(
            go.Bar(
                x=[percentage],
                y=[row['category']],
                orientation='h',
                name=row['category'],
                text=f"{percentage:.1f}%",
                textposition='auto',
                marker_color=color,
                showlegend=False
            )
        )
    
    # Add a vertical line at 100%
    fig.add_shape(
        type="line",
        x0=100,
        x1=100,
        y0=-0.5,
        y1=len(sorted_df) - 0.5,
        line=dict(
            color="black",
            width=2,
            dash="dash"
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Budget Progress (% Used)',
        xaxis_title='Percentage of Budget Used',
        xaxis=dict(
            ticksuffix='%',
            range=[0, max(sorted_df['percent_used'].max() * 1.1, 110)]
        ),
        yaxis=dict(
            categoryorder='array',
            categoryarray=sorted_df['category'].tolist()
        )
    )
    
    return fig
