"""Simple helpers for talking to MySQL.

Every query uses %s placeholders and a separate params tuple.
User input is never pasted into the SQL text, which prevents SQL injection.
"""
import mysql.connector

from config import Config


def get_connection():
    """Open a new connection to the jobtrack database."""
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        connection_timeout=5,
    )


def fetch_all(sql, params=()):
    """Run a SELECT and return ALL matching rows as a list of dictionaries."""
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        connection.close()  # always close, even if something fails


def fetch_one(sql, params=()):
    """Run a SELECT and return ONE row as a dictionary (or None if nothing matches)."""
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        connection.close()


def execute(sql, params=()):
    """Run an INSERT, UPDATE or DELETE and save (commit) the change."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        connection.commit()  # without commit, MySQL would not keep the change
        cursor.close()
    finally:
        connection.close()