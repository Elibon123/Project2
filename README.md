# Task Manager

Task manager communicating with a MySQL database.

## Requirements
- Python 3.8+
- MySQL Server

## Installation and Setup

1. **Install dependencies**
   Install required libraries from`requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database access**
   Copy the `.env.example` template and create a `.env` file.
   Fill in the correct password for your MySQL database (and adjust the user if it is not `root`):
   ```ini
   DB_HOST=localhost
   DB_USER=root
   DB_PASS=your_secret_password
   DB_NAME=task_manager
   ```

3. **Run the application**
   Run the application from the project root directory (`Vylepsen_manager`) using the following command:
   ```bash
   python -m src.main_menu
   ```
   *(On some Windows systems, you may need to use `py -m src.main_menu`)*

## Testing
The project includes tests that create a temporary test database (`test_task_manager`) and clean it up afterwards.
Run the tests using the `pytest` package:
```bash
python -m pytest test_task_manager.py
```
*(Or `py -m pytest test_task_manager.py` on Windows)*
