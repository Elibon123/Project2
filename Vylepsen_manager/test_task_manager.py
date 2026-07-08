import os
import pytest
import mysql.connector
from dotenv import load_dotenv

from src.main_menu import add_task_db, update_task_db, delete_task_db

@pytest.fixture
def db_connection():
    load_dotenv()
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")
    TEST_DB_NAME = "test_task_manager"

    # Connect to db server, raise ConnectionError
    try:
        setup_conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS
        )
    except mysql.connector.Error as err:
        raise ConnectionError(f"Database connection error: {err}")

    # Initialize test db and table, raise RuntimeError
    try:
        setup_cursor = setup_conn.cursor()
        setup_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DB_NAME}")
        setup_cursor.execute(f"USE {TEST_DB_NAME}")
        setup_cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
              id int NOT NULL AUTO_INCREMENT,
              task_name varchar(50) DEFAULT NULL,
              task_description varchar(255) DEFAULT NULL,
              task_state enum('created','finished','inprogress') DEFAULT NULL,
              create_date date NOT NULL DEFAULT (CURRENT_DATE),
              PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
        setup_conn.commit()
    except mysql.connector.Error as err:
        raise RuntimeError(f"Database initialization error: {err}")
    finally:
        setup_cursor.close()
        setup_conn.close()

    # Yield test connection
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=TEST_DB_NAME
        )
        cursor = conn.cursor(dictionary=True)
        yield conn, cursor
    finally:
        if 'cursor' in locals() and cursor is not None:
            # clear the test database with drop table
            try:
                cursor.execute("DROP TABLE IF EXISTS tasks")
                conn.commit()
            except mysql.connector.Error:
                pass
            cursor.close()
        if 'conn' in locals() and conn is not None:
            conn.close()

def test_add_task(db_connection):
    conn, cursor = db_connection
    
    test_name = "Test_task"
    test_description = "Test_description"
    add_task_db(conn, test_name, test_description)

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks WHERE task_name=%s AND task_description=%s AND task_state='created' AND create_date=CURRENT_DATE", (test_name, test_description))
    tasks = cursor.fetchall()
    task = tasks[0] if tasks else None
    print(task)

    assert task is not None, "Task not found"
    assert task['task_name'] == test_name
    assert task['task_description'] == test_description



def test_update_task_valid(db_connection):
    conn, cursor = db_connection
    
    # Pre-condition: Add a task
    add_task_db(conn, "Task to update", "Update me")
    cursor.execute("SELECT id FROM tasks WHERE task_name=%s", ("Task to update",))
    task_id = cursor.fetchone()['id']
    
    # Action: update to finished
    update_task_db(conn, task_id=task_id, new_state="finished")
    
    # Assert
    cursor.execute("SELECT task_state FROM tasks WHERE id=%s", (task_id,))
    state = cursor.fetchone()['task_state']
    assert state == "finished", f"Expected state 'finished', got '{state}'"

def test_delete_task_valid(db_connection):
    conn, cursor = db_connection
    
    # Pre-condition: Add a task
    add_task_db(conn, "Task to delete", "Delete me")
    cursor.execute("SELECT id FROM tasks WHERE task_name=%s", ("Task to delete",))
    task_id = cursor.fetchone()['id']
    
    # Action: delete task
    delete_task_db(conn, task_id=task_id)
    
    # Assert
    cursor.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
    tasks = cursor.fetchall()
    assert len(tasks) == 0

def test_update_task_invalid_state(db_connection):
    conn, cursor = db_connection
    add_task_db(conn, "Task invalid state", "Desc")
    cursor.execute("SELECT id FROM tasks WHERE task_name=%s", ("Task invalid state",))
    task_id = cursor.fetchone()['id']
    
    with pytest.raises(mysql.connector.Error):
        update_task_db(conn, task_id=task_id, new_state="invalid_state")

def test_delete_task_nonexistent_id(db_connection):
    conn, cursor = db_connection
    add_task_db(conn, "Task keep", "Desc")
    
    # Ensure there's 1 task
    cursor.execute("SELECT COUNT(*) as count FROM tasks")
    initial_count = cursor.fetchone()['count']
    
    delete_task_db(conn, task_id=9999)
    
    # Ensure there's still 1 task
    cursor.execute("SELECT COUNT(*) as count FROM tasks")
    final_count = cursor.fetchone()['count']
    assert initial_count == final_count

def test_add_task_too_long_name(db_connection):
    conn, cursor = db_connection
    
    # Name longer than 50 characters (varchar limit is 50)
    too_long_name = "A" * 51
    
    # Expected to raise a database error
    with pytest.raises(mysql.connector.Error):
        add_task_db(conn, too_long_name, "Desc")

if __name__ == "__main__":
    pytest.main()
