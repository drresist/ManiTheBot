import datetime
from typing import List, Dict

import psycopg2
from psycopg2 import pool
from config import Config
from loguru import logger

config = Config()

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=config.PG_HOST,
    database=config.PG_DB,
    user=config.PG_USER,
    password=config.PG_PASS
)

def get_connection():
    logger.debug("Getting database connection from the pool")
    return connection_pool.getconn()

def release_connection(conn):
    logger.debug("Releasing database connection back to the pool")
    connection_pool.putconn(conn)

def get_transactions() -> List[Dict]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            logger.debug("Executing query to fetch transactions")
            cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
            transactions = cursor.fetchall()
            logger.debug(f"Fetched {len(transactions)} transactions from the database")
        return [{"id": transaction[0],
                 "category_id": transaction[1],
                 "amount": transaction[2],
                 "date": transaction[3].strftime('%d.%m.%Y'),
                 "user_id": transaction[4]} for transaction in transactions]
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while fetching transactions: {error}")
    finally:
        if conn:
            release_connection(conn)

def add_payment(user_id: str, category_id: str, amount: str) -> None:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            logger.debug(f"Adding payment: user_id={user_id}, category_id={category_id}, amount={amount}")
            cursor.execute("INSERT INTO transactions (user_id, category_id, amount) VALUES (%s, %s, %s)",
                           (user_id, category_id, amount))
        conn.commit()
        logger.debug("Payment added successfully")
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while adding payment: {error}")
    finally:
        if conn:
            release_connection(conn)

def get_categories() -> List[Dict]:
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            logger.debug("Executing query to fetch categories")
            cursor.execute("SELECT * FROM categories")
            categories = cursor.fetchall()
            logger.debug(f"Fetched {len(categories)} categories from the database")
        return [{"id": category[0], "type": category[1], "category": category[2]} for category in categories]
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while fetching categories: {error}")
        return []  # Return an empty list in case of an error
