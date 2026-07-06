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
__all__ = ['connect_to_db', 'initialize_database', 'close_connection', 'main_menu', 'add_task', 'view_tasks', 'update_task', 'delete_task']

# Task manager
# The main_menu function displays the main menu of the task manager and provides the user with options
# to add, view or delete tasks, or exit the program.
def main_menu():
    load_dotenv()
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "Leopard1!")
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
def add_task(conn, task_name=None, task_description=None):
    if conn is None:
        print("Connection error: Unable to connect to the database.")
        return False

    if task_name is not None:
        if not task_name.strip():
            raise ValueError("Empty name entered")
    else:
        while True:
            task_name = input("Add task name: ").strip()
            if not task_name:
                print("Empty name entered")
                continue
            break

    if task_description is not None:
        if not task_description.strip():
            raise ValueError("Empty description entered")
    else:
        while True:
            task_description = input("Add task description: ").strip()
            if not task_description:
                print("Empty description entered")
                continue
            break

    task_state = "created"

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "INSERT INTO tasks (task_name, task_description, task_state, create_date) VALUES (%s, %s, %s, CURRENT_DATE)",
        (task_name, task_description, task_state),
    )
    conn.commit()
    cursor.close()
    print("Task added successfully.")
    return True


# The function displays the task list and then only the current tasks with the state "created" or "inprogress".
def view_tasks(conn):
    if conn is None:
        print("Connection error: Unable to connect to the database.")
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, task_name, task_description, task_state, create_date FROM tasks"
        )
        tasks = cursor.fetchall()

        if not tasks:
            print("No tasks available.")
            return []

        print("\n=== ALL TASKS ===")
        for task in tasks:
            print(
                f"id: {task['id']} | task_name: {task['task_name']} | task_description: {task['task_description']} | task_state: {task['task_state']} | create_date: {task['create_date']}"
            )
        
        #Filter only tasks which are newly created or ongoing.
        print("\nCurrent tasks:")
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
    finally:
        cursor.close()


# Function update_task allows the user to update the state of a task in the database.
def update_task(conn, input_id=None, input_state=None):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, task_name, task_description, task_state FROM tasks")
    tasks = cursor.fetchall()

    if not tasks:
        print("No tasks available.")
        cursor.close()
        return

    task_ids = {task['id'] for task in tasks}

    if input_id is not None:
        if input_id not in task_ids:
            cursor.close()
            raise ValueError("Task ID not found. Please enter an existing task ID.")
    else:
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

    if input_state is not None:
        input_state = input_state.strip().lower()
        if input_state not in {"inprogress", "finished"}:
            cursor.close()
            raise ValueError("Invalid state. Update cancelled.")
    else:
        input_state = input("Enter the new state for the task ('inprogress' or 'finished'): ").strip().lower()
        if input_state not in {"inprogress", "finished"}:
            print("Invalid state. Update cancelled.")
            cursor.close()
            return

    cursor.execute("UPDATE tasks SET task_state = %s WHERE id = %s", (input_state, input_id))
    conn.commit()
    cursor.close()
    print("Task updated successfully.")


# Function for task deletion, if not existing id is provided, it will print a message and offer new choice.
def delete_task(conn, delete_task_id=None, confirm_deletion=None):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    if not tasks:
        print("No tasks available to delete.")
        cursor.close()
        return

    task_ids = {task['id'] for task in tasks}

    if delete_task_id is not None:
        if delete_task_id not in task_ids:
            cursor.close()
            raise ValueError("Task ID not found. Please enter an existing task ID.")
    else:
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

    if confirm_deletion is not None:
        if str(confirm_deletion).strip().lower() != "y":
            cursor.close()
            raise ValueError("Deletion cancelled.")
    else:
        confirm = input("Confirm deletion? This task will be permanently removed from the database. (y/n): ").strip().lower()
        if confirm != "y":
            print("Deletion cancelled.")
            cursor.close()
            return

    cursor.execute("DELETE FROM tasks WHERE id = %s", (delete_task_id,))
    conn.commit()
    cursor.close()
    print("Task deleted successfully.")


if __name__ == "__main__":
    main_menu()