from datetime import datetime, timedelta, date
from typing import List, Dict, Union, Any
from collections import defaultdict

from db import get_transactions, get_categories
import plotly.graph_objects as go
from loguru import logger

category_cache = {}

def get_category_name(category_id: int) -> Union[str, None]:
    if category_id in category_cache:
        return category_cache[category_id]
    
    logger.debug("Getting category name for category_id: {}", category_id)
    categories = get_categories()
    for category in categories:
        if category['id'] == category_id:
            category_cache[category_id] = category['category']
            logger.debug("Found category name: {}", category['category'])
            return category['category']
    logger.warning("Category not found for category_id: {}", category_id)
    return None

def filter_data_by_last_month(transactions: List[Dict]) -> List[Dict]:
    logger.debug("Filtering data by last month")
    today = datetime.today()
    last_month_start = today - timedelta(days=today.day)
    return [row for row in transactions if datetime.strptime(row['date'], '%d.%m.%Y') >= last_month_start]

from decimal import Decimal

def group_expenses_by_date_category(transactions: List[Dict]) -> dict[date, dict[Any, Any]]:
    """
    Group expenses by date and category.
    """
    logger.debug("Grouping expenses by date and category")
    expenses_by_date_category = {}
    for row in transactions:
        date_str = row['date']
        category_id = row['category_id']
        amount = Decimal(row['amount'])  # Convert amount to decimal.Decimal
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
        if date not in expenses_by_date_category:
            expenses_by_date_category[date] = {}
        category_name = get_category_name(category_id)
        if category_name:
            expenses_by_date_category[date][category_name] = expenses_by_date_category[date].get(category_name, Decimal(0)) + amount
    logger.debug("Expenses grouped successfully")
    return expenses_by_date_category

def create_stacked_bar_chart(data: List[Dict], colors: List[str] = None, font: str = None) -> None:
    logger.debug("Creating stacked bar chart")
    filtered_data = filter_data_by_last_month(data)
    expenses_by_date_category = group_expenses_by_date_category(filtered_data)
    dates = list(expenses_by_date_category.keys())
    unique_categories = list(set(category for categories in expenses_by_date_category.values() for category in categories))
    
    traces = []
    for i, category in enumerate(unique_categories):
        amounts = [expenses_by_date_category[date][category] if category in expenses_by_date_category[date] else 0 for date in dates]
        trace = go.Bar(x=[date.strftime('%d.%m.%Y') for date in dates], y=amounts, name=category)
        if colors:
            trace.marker.color = colors[i % len(colors)]
        traces.append(trace)
        
    fig = go.Figure(data=traces)
    fig.update_layout(
        xaxis=dict(title='Date', tickangle=45),
        yaxis=dict(title='Amount'),
        barmode='stack',
        title='Expense by Date and Category (Last Month)'
    )
    if font:
        fig.update_layout(font_family=font)
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    fig.write_image("month_expense.png")
    logger.debug("Chart created successfully")
