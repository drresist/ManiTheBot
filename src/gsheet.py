import gspread
from datetime import datetime
from dotenv import load_dotenv
import os
from loguru import logger

load_dotenv()


def authenticate_gspread():
    service_file = os.getenv("GOOGLE_SHEETS_KEY_FILE")
    if service_file is None:
        raise RuntimeError("GOOGLE_SHEETS_KEY_FILE is not set")

    gc = gspread.service_account(filename=service_file)
    return gc


def open_spreadsheet():
    gc = authenticate_gspread()
    sheet_id = os.getenv("SHEET_ID")
    sh = gc.open_by_key(sheet_id)
    return sh


def add_payment(category_type, category, amount):
    sh = open_spreadsheet()
    worksheet = sh.sheet1
    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime(
        "%d.%m.%Y"
    )  # Customize the date format as needed
    if category_type == "Expense":
        amount = -1 * int(amount)
    row_data = [formatted_date, category_type, category, int(amount)]
    worksheet.append_row(row_data)
    logger.info(f"Added payment: {category} - {amount}")


def get_categories(category_type):
    sh = open_spreadsheet()
    worksheet = sh.get_worksheet(2)
    logger.info(f"Getting categories: {category_type}")

    if category_type is None:
        return []
    if category_type == "Income":
        return worksheet.col_values(1)
    if category_type == "Expense":
        return worksheet.col_values(2)


def get_summary():
    sh = open_spreadsheet()
    worksheet = sh.get_worksheet(0)
    logger.info("Getting summary")
    values = worksheet.get("D2:D10000")
    values = [int(value[0]) for value in values]
    summary = sum(values)
    logger.info(f"Summary: {summary}")
    return summary


def get_all_vals():
    sh = open_spreadsheet()
    worksheet = sh.get_worksheet(0)
    logger.info("Getting all values")
    values = worksheet.get_all_values()
    return values
