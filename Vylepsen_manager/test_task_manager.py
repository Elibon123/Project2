import os
import pytest
import mysql.connector
from dotenv import load_dotenv

from src.main_menu import add_task, update_task, delete_task
from unittest.mock import patch

@pytest.fixture
def db_connection():
    load_dotenv()
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "Leopard1!")
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
              task_name varchar(255) DEFAULT NULL,
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
    add_task(conn, test_name, test_description)

    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM tasks WHERE task_name='{test_name}' AND task_description='{test_description}' AND task_state='created' AND create_date=CURRENT_DATE")
    tasks = cursor.fetchall()
    task = tasks[0] if tasks else None
    print(task)

    assert task is not None, "Task not found"
    assert task['task_name'] == test_name
    assert task['task_description'] == test_description



def test_add_task_empty_name(db_connection):
    conn, cursor = db_connection
    error_message = "Empty name entered"
    
    with pytest.raises(ValueError) as error:
        add_task(conn, "", "Valid_description")
        
    assert str(error.value) == error_message, f"Expected error {error_message}, real message {str(error.value)}"

def test_update_task_valid(db_connection):
    conn, cursor = db_connection
    
    # Pre-condition: Add a task
    add_task(conn, "Task to update", "Update me")
    cursor.execute("SELECT id FROM tasks WHERE task_name='Task to update'")
    task_id = cursor.fetchone()['id']
    
    # Action: update to finished
    update_task(conn, input_id=task_id, input_state="finished")
    
    # Assert
    cursor.execute(f"SELECT task_state FROM tasks WHERE id={task_id}")
    state = cursor.fetchone()['task_state']
    assert state == "finished", f"Expected state 'finished', got '{state}'"

def test_update_task_invalid_id(db_connection):
    conn, cursor = db_connection
    error_message = "Task ID not found. Please enter an existing task ID."
    
    # Pre-condition: Add at least one task so the list is not empty
    add_task(conn, "Dummy task", "Dummy desc")
    
    # Use a non-existent ID
    fake_id = 9999
    
    with pytest.raises(ValueError) as error:
        update_task(conn, input_id=fake_id, input_state="finished")
        
    assert str(error.value) == error_message, f"Expected error {error_message}, real message {str(error.value)}"

def test_delete_task_valid(db_connection):
    conn, cursor = db_connection
    
    # Pre-condition: Add a task
    add_task(conn, "Task to delete", "Delete me")
    cursor.execute("SELECT id FROM tasks WHERE task_name='Task to delete'")
    task_id = cursor.fetchone()['id']
    
    # Action: delete task
    delete_task(conn, delete_task_id=task_id, confirm_deletion="y")
    
    # Assert
    cursor.execute(f"SELECT * FROM tasks WHERE id={task_id}")
    tasks = cursor.fetchall()
    assert len(tasks) == 0

def test_delete_task_cancelled(db_connection):
    conn, cursor = db_connection
    error_message = "Deletion cancelled."
    
    # Pre-condition: Add a task
    add_task(conn, "Task to cancel delete", "Cancel me")
    cursor.execute("SELECT id FROM tasks WHERE task_name='Task to cancel delete'")
    task_id = cursor.fetchone()['id']
    
    with pytest.raises(ValueError) as error:
        delete_task(conn, delete_task_id=task_id, confirm_deletion="n")
        
    assert str(error.value) == error_message, f"Expected error {error_message}, real message {str(error.value)}"
    
    # Verify task was NOT deleted
    cursor.execute(f"SELECT * FROM tasks WHERE id={task_id}")
    tasks = cursor.fetchall()
    assert len(tasks) == 1

if __name__ == "__main__":
    pytest.main()


