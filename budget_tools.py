import pandas as pd
import numpy as np

def calculate_budget_vs_actual(transactions_df, budgets):
    """
    Calculate budget vs actual spending for each category
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    budgets: dict
        Dictionary mapping categories to budget amounts
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with budget analysis
    """
    if transactions_df.empty or not budgets:
        return pd.DataFrame()
    
    # Filter for expenses only
    expenses_df = transactions_df[transactions_df['type'] == 'expense']
    
    if expenses_df.empty:
        return pd.DataFrame(columns=['category', 'budget', 'spent', 'remaining', 'percent_used'])
    
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
    comparison_df.rename(columns={'amount': 'spent'}, inplace=True)
    
    # Calculate remaining budget and percent used
    comparison_df['remaining'] = comparison_df['budget'] - comparison_df['spent']
    comparison_df['percent_used'] = (comparison_df['spent'] / comparison_df['budget']) * 100
    
    # Handle division by zero
    comparison_df['percent_used'] = comparison_df['percent_used'].replace([np.inf, -np.inf], 0)
    
    # Sort by percent used in descending order
    comparison_df = comparison_df.sort_values('percent_used', ascending=False)
    
    return comparison_df

def forecast_monthly_expenses(transactions_df, months=3):
    """
    Forecast monthly expenses based on historical data
    
    Parameters:
    -----------
    transactions_df: pd.DataFrame
        DataFrame containing transaction data
    months: int
        Number of months to use for calculation
        
    Returns:
    --------
    dict
        Dictionary mapping categories to forecasted amounts
    """
    if transactions_df.empty or 'date' not in transactions_df.columns:
        return {}
    
    # Ensure date is datetime
    df = transactions_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Add month column
    df['month'] = df['date'].dt.strftime('%Y-%m')
    
    # Filter for expenses only
    expenses_df = df[df['type'] == 'expense']
    
    if expenses_df.empty:
        return {}
    
    # Get unique months in descending order
    unique_months = sorted(expenses_df['month'].unique(), reverse=True)
    
    # Use only the most recent months
    recent_months = unique_months[:months] if len(unique_months) >= months else unique_months
    
    # Filter for recent months
    recent_df = expenses_df[expenses_df['month'].isin(recent_months)]
    
    # Group by category and calculate average
    monthly_avg = recent_df.groupby(['category', 'month'])['amount'].sum().reset_index()
    forecast = monthly_avg.groupby('category')['amount'].mean().reset_index()
    
    # Convert to dictionary
    forecast_dict = dict(zip(forecast['category'], forecast['amount']))
    
    return forecast_dict

def suggest_budget_adjustments(budget_analysis, threshold=90):
    """
    Suggest budget adjustments based on spending patterns
    
    Parameters:
    -----------
    budget_analysis: pd.DataFrame
        DataFrame with budget analysis
    threshold: float
        Percentage threshold for suggesting adjustments
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with suggested adjustments
    """
    if budget_analysis.empty:
        return pd.DataFrame()
    
    # Copy to avoid modifying original
    analysis = budget_analysis.copy()
    
    # Define conditions for adjustments
    over_budget = analysis['percent_used'] > 100
    near_limit = (analysis['percent_used'] > threshold) & (analysis['percent_used'] <= 100)
    under_budget = analysis['percent_used'] < (threshold / 2)
    
    # Create adjustment suggestions
    analysis['suggestion'] = ''
    analysis.loc[over_budget, 'suggestion'] = 'Increase budget'
    analysis.loc[near_limit, 'suggestion'] = 'Monitor closely'
    analysis.loc[under_budget, 'suggestion'] = 'Consider decreasing'
    
    # Calculate suggested amounts
    analysis['suggested_adjustment'] = 0.0
    
    # For over budget categories, suggest increasing by the deficit plus 10%
    analysis.loc[over_budget, 'suggested_adjustment'] = (analysis['spent'] - analysis['budget']) * 1.1
    
    # For under budget categories, suggest decreasing by half the unused portion
    analysis.loc[under_budget, 'suggested_adjustment'] = (analysis['budget'] - analysis['spent']) * -0.5
    
    # Return only categories with suggestions
    suggestions = analysis[analysis['suggestion'] != '']
    
    return suggestions
