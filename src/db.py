from typing import List, Dict

import psycopg2
from psycopg2 import pool
from config import Config
from loguru import logger

config = Config()

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    host=config.PG_HOST,
    database=config.PG_DB,
    user=config.PG_USER,
    password=config.PG_PASS
)


def get_connection():
    """
    Get a database connection from the connection pool.

    Returns:
        conn (psycopg2.extensions.connection): A database connection.

    Raises:
        RuntimeError: If the connection pool is not initialized.
    """
    # Check if the connection pool is initialized
    if connection_pool is None:
        raise RuntimeError("Connection pool is not initialized")

    # Log debug message
    logger.debug("Getting database connection from the pool")

    # Get a connection from the pool
    return connection_pool.getconn()


def release_connection(conn):
    """
    Release a database connection back to the connection pool.

    Args:
        conn (psycopg2.extensions.connection): The database connection to be released.

    Returns:
        None
    """
    logger.debug("Releasing database connection back to the pool")
    connection_pool.putconn(conn)


def get_transactions() -> List[Dict]:
    """
    Retrieves all transactions from the database and returns them as a list of dictionaries.

    Returns:
        List[Dict]: A list of dictionaries representing transactions. Each dictionary has the following keys:
            - "id" (int): The ID of the transaction.
            - "category_id" (int): The ID of the category associated with the transaction.
            - "amount" (float): The amount of the transaction.
            - "date" (str): The date of the transaction in the format '%d.%m.%Y'.
            - "user_id" (int): The ID of the user associated with the transaction.
    """
    conn = None
    try:
        # Get a database connection
        conn = get_connection()

        with conn.cursor() as cursor:
            # Execute a query to fetch all transactions from the database
            logger.debug("Executing query to fetch transactions")
            cursor.execute("SELECT * FROM transactions ORDER BY date DESC")

            # Fetch all transactions from the cursor
            transactions = cursor.fetchall()

            # Log the number of transactions fetched
            logger.debug(f"Fetched {len(transactions)} transactions from the database")

            # Convert each transaction into a dictionary and return as a list
            return [
                {
                    "id": transaction[0],
                    "category_id": transaction[1],
                    "amount": transaction[2],
                    "date": transaction[3].strftime('%d.%m.%Y'),
                    "user_id": transaction[4]
                }
                for transaction in transactions
            ]
    except (Exception, psycopg2.Error) as error:
        # Log and re-raise any errors that occur while fetching transactions
        logger.error(f"Error while fetching transactions: {error}")
        raise
    finally:
        # Release the database connection back to the connection pool
        if conn:
            release_connection(conn)


def add_payment(user_id: str, category_id: str, amount: str) -> None:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                logger.debug(f"Adding payment: user_id={user_id}, category_id={category_id}, amount={amount}")
                cursor.execute("INSERT INTO transactions (user_id, category_id, amount) VALUES (%s, %s, %s)",
                               (user_id, category_id, amount))
                conn.commit()
                logger.debug("Payment added successfully")
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while adding payment: {error}")


def get_categories() -> List[Dict]:
    """
    Retrieve a list of categories from the database.

    Returns:
        List[Dict]: A list of dictionaries representing categories.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute query to fetch categories
                logger.debug("Executing query to fetch categories")
                cursor.execute("SELECT * FROM categories")
                categories = cursor.fetchall()
                # Log the number of categories fetched
                logger.debug(f"Fetched {len(categories)} categories from the database")
        # Prepare category data for return
        return [{"id": category[0], "type": category[1], "category": category[2]} for category in categories]
    except (Exception, psycopg2.Error) as error:
        # Log error if fetching categories fails
        logger.error(f"Error while fetching categories: {error}")
        return []