import pandas as pd
from db import get_categories
from loguru import logger


def parse_xlsx(filename):
    pd.read_excel(filename)
    categories = get_categories()
    logger.info(f"Categories: {categories}")
