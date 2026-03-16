# db.py — MySQL connection helper using mysql-connector-python
# This file provides a reusable function to connect to the MySQL database.

import mysql.connector  # Import the MySQL connector library

def get_db():
    """
    Creates and returns a new MySQL database connection.
    Every route that needs to talk to the database will call this function.
    """
    conn = mysql.connector.connect(
        host="localhost",       # MySQL server address (localhost = your own machine)
        user="root",            # MySQL username (default is 'root')
        password="15022006",    # MySQL password
        database="skillswap"    # The database we created in schema.sql
    )
    return conn  # Return the connection object so routes can use it
