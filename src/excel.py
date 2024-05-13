import pandas as pd
from db import add_payment, get_categories
from loguru import logger


def parse_xlsx(filename):
    df = pd.read_excel(filename)
    categories = get_categories()
    logger.info(f"Categories: {categories}")
