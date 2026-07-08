import mysql.connector
from mysql.connector.connection import MySQLConnection

from typing import Optional

def connect_to_db(host, user, password, database) -> Optional[MySQLConnection]:
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Connection error: Unable to connect to the database. Details: {err}")
        return None

def initialize_database(host, user, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cursor.execute(f"USE {database}")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
              id int NOT NULL AUTO_INCREMENT,
              task_name varchar(50) DEFAULT NULL,
              task_description varchar(255) DEFAULT NULL,
              task_state enum('created','finished','inprogress') DEFAULT NULL,
              create_date date NOT NULL DEFAULT (CURRENT_DATE),
              PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Initialization error: {err}")

def close_connection(conn):
    if conn and conn.is_connected():
        conn.close()