import os
import sys
from pathlib import Path

# Add project root to sys.path so it can resolve the 'src' module when run directly
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
from src.create_connection import connect_to_db, initialize_database, close_connection

# Re-exporting these so they can be accessed via `db.connect_to_db` etc.
__all__ = ['connect_to_db', 'initialize_database', 'close_connection', 'main_menu', 'add_task', 'view_tasks', 'update_task', 'delete_task', 'add_task_db', 'get_all_tasks_db', 'update_task_db', 'delete_task_db']

# Task manager
# The main_menu function displays the main menu of the task manager and provides the user with options
# to add, view or delete tasks, or exit the program.
def main_menu():
    load_dotenv()
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_NAME = os.getenv("DB_NAME", "task_manager")
    
    initialize_database(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    conn = connect_to_db(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    if not conn:
        print("Failed to initialize database connection.")
        return

    while True:
        print("\nTask Manager - Main Menu")
        print("1. Add new task")
        print("2. View all tasks")
        print("3. Update task")
        print("4. Delete task")
        print("5. Exit program")

        try:
            option = int(input("Choose an option (1-5): ").strip())
        except ValueError:
            print("Invalid option. Choose an option (1-5).")
            continue

        if option == 1:
            add_task(conn)
        elif option == 2:
            view_tasks(conn)
        elif option == 3:
            update_task(conn)
        elif option == 4:
            delete_task(conn)
        elif option == 5:
            print("Exiting program.")
            close_connection(conn)
            break
        else:
            print("Invalid option. Choose an option (1-5).")


# The function adds a new task to the task list,
# if the name or description is empty, it prints the message "Empty name entered"
# or "Empty description entered"
def add_task(conn):
    if conn is None:
        print("Connection error: Unable to connect to the database.")
        return False

    while True:
        task_name = input("Add task name: ").strip()
        if not task_name:
            print("Empty name entered")
            continue
        break

    while True:
        task_description = input("Add task description: ").strip()
        if not task_description:
            print("Empty description entered")
            continue
        break

    add_task_db(conn, task_name, task_description)
    print("Task added successfully.")
    return True

def add_task_db(conn, task_name, task_description):
    task_state = "created"
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "INSERT INTO tasks (task_name, task_description, task_state, create_date) VALUES (%s, %s, %s, CURRENT_DATE)",
        (task_name, task_description, task_state),
    )
    conn.commit()
    cursor.close()

# The function displays the task list and then only the current tasks with the state "created" or "inprogress".
def view_tasks(conn):
    if conn is None:
        print("Connection error: Unable to connect to the database.")
        return None

    tasks = get_all_tasks_db(conn)

    if not tasks:
        print("No tasks available.")
        return []

    print("\n=== CURRENT TASKS ===")
    active_count = 0
    for item in tasks:
        if item['task_state'] in ('created', 'inprogress'):
            active_count += 1
            print(
                f"id: {item['id']} | task_name: {item['task_name']} | task_description: {item['task_description']} | task_state: {item['task_state']} | create_date: {item['create_date']}"
            )
            
    if active_count == 0:
        print("No current tasks.")
        
    return tasks

def get_all_tasks_db(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, task_name, task_description, task_state, create_date FROM tasks"
        )
        return cursor.fetchall()
    finally:
        cursor.close()

# Function update_task allows the user to update the state of a task in the database.
def update_task(conn):
    tasks = get_all_tasks_db(conn)

    if not tasks:
        print("No tasks available.")
        return

    task_ids = {task['id'] for task in tasks}

    print("Current tasks:")
    for task in tasks:
        print(f"{task['id']}: {task['task_name']} - {task['task_state']}")
        
    while True:
        try:
            input_id = int(input("Enter the ID of the task you want to update: ").strip())
        except ValueError:
            print("Invalid ID. Please enter a numeric task ID.")
            continue

        if input_id not in task_ids:
            print("Task ID not found. Please enter an existing task ID.")
            continue
        break

    input_state = input("Enter the new state for the task ('inprogress' or 'finished'): ").strip().lower()
    if input_state not in {"inprogress", "finished"}:
        print("Invalid state. Update cancelled.")
        return

    update_task_db(conn, input_id, input_state)
    print("Task updated successfully.")

def update_task_db(conn, task_id, new_state):
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET task_state = %s WHERE id = %s", (new_state, task_id))
    conn.commit()
    cursor.close()

# Function for task deletion, if not existing id is provided, it will print a message and offer new choice.
def delete_task(conn):
    tasks = get_all_tasks_db(conn)

    if not tasks:
        print("No tasks available to delete.")
        return

    task_ids = {task['id'] for task in tasks}

    print("Current tasks:")
    for task in tasks:
        print(f"{task['id']}: {task['task_name']} - {task['task_state']}")   

    while True:
        try:
            delete_task_id = int(input("Enter the ID of the task you want to delete: ").strip())
        except ValueError:
            print("Invalid ID. Please enter a numeric task ID.")
            continue

        if delete_task_id not in task_ids:
            print("Task ID not found. Please enter an existing task ID.")
            continue
        break

    confirm = input("Confirm deletion? This task will be permanently removed from the database. (y/n): ").strip().lower()
    if confirm != "y":
        print("Deletion cancelled.")
        return

    delete_task_db(conn, delete_task_id)
    print("Task deleted successfully.")

def delete_task_db(conn, task_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cursor.close()


if __name__ == "__main__":
    main_menu()