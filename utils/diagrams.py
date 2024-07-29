from datetime import datetime, timedelta
from typing import List, Dict, Union
from decimal import Decimal
from database.operations import get_transactions, get_categories
import plotly.graph_objects as go
from loguru import logger

category_cache = {}


def get_category_name(category_id: int) -> Union[str, None]:
    if category_id in category_cache:
        return category_cache[category_id]

    logger.debug("Getting category name for category_id: {}", category_id)
    categories = get_categories()
    for category in categories:
        if category["id"] == category_id:
            category_cache[category_id] = category["category"]
            logger.debug("Found category name: {}", category["category"])
            return category["category"]
    logger.warning("Category not found for category_id: {}", category_id)
    return None


def filter_data_by_last_30_days(transactions: List[Dict]) -> List[Dict]:
    logger.debug("Filtering data by last 30 days")
    today = datetime.today()
    last_30_days_start = today - timedelta(days=30)
    return [
        row
        for row in transactions
        if datetime.strptime(row["date"], "%d.%m.%Y") >= last_30_days_start
    ]


def group_transactions_by_date_category(
    transactions: List[Dict],
) -> dict[datetime, dict[str, Decimal]]:
    logger.debug("Grouping transactions by date and category")
    transactions_by_date_category = {}
    for row in transactions:
        date_str = row["date"]
        category_id = row["category_id"]
        amount = Decimal(row["amount"])
        date = datetime.strptime(date_str, "%d.%m.%Y")
        if date not in transactions_by_date_category:
            transactions_by_date_category[date] = {}
        category_name = get_category_name(category_id)
        if category_name:
            transactions_by_date_category[date][category_name] = (
                transactions_by_date_category[date].get(category_name, Decimal(0))
                + amount
            )
    logger.debug("Transactions grouped successfully")
    return transactions_by_date_category


def create_income_expense_bar_chart(data: List[Dict]) -> None:
    logger.debug("Creating income/expense bar chart")
    filtered_data = filter_data_by_last_30_days(data)
    transactions_by_date_category = group_transactions_by_date_category(filtered_data)
    dates = list(transactions_by_date_category.keys())
    unique_categories = list(
        set(
            category
            for categories in transactions_by_date_category.values()
            for category in categories
        )
    )

    traces = []
    for i, category in enumerate(unique_categories):
        amounts = [
            transactions_by_date_category[date].get(category, 0) for date in dates
        ]
        trace = go.Bar(
            x=[date.strftime("%d.%m.%Y") for date in dates], y=amounts, name=category
        )
        traces.append(trace)

    fig = go.Figure(data=traces)
    fig.update_layout(
        xaxis=dict(title="Date", tickangle=45),
        yaxis=dict(title="Amount"),
        barmode="relative",
        title="Income/Expense by Date and Category (Last 30 Days)",
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    fig.write_image("income_expense_last_30_days.png")
    logger.debug("Chart created successfully")


def generate_income_expense_summary(transactions: List[Dict]) -> str:
    logger.debug("Generating income/expense summary for the last 30 days")
    total_income = Decimal(0)
    total_expense = Decimal(0)

    for transaction in transactions:
        amount = Decimal(transaction["amount"])
        if amount >= 0:
            total_income += amount
        else:
            total_expense += abs(amount)

    summary = "Income/Expense Summary (Last 30 Days):\n\n"
    summary += f"Total Income: {total_income:.2f}\n"
    summary += f"Total Expense: {total_expense:.2f}\n"
    summary += f"Net Income: {total_income - total_expense:.2f}"

    return summary


def create_income_expense_summary() -> str:
    logger.debug("Creating income/expense summary")
    data = get_transactions()
    filtered_data = filter_data_by_last_30_days(data)
    summary = generate_income_expense_summary(filtered_data)
    logger.debug("Income/expense summary created successfully")
    return summary
