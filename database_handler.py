# Prerequisites:
# 1. MySQL server must be running and accessible.
# 2. The 'mysql-connector-python' library must be installed (e.g., pip install mysql-connector-python).
# 3. The MySQL user 'root' (or your configured user) must exist with the specified password ('123' in this script)
#    and have privileges to create databases and tables on the server.

import mysql.connector
from mysql.connector import errorcode
from datetime import date # Added for type hinting and constructing date objects

DB_NAME = 'michentestdb5'

TABLES = {}
TABLES['leave_records'] = (
    "CREATE TABLE IF NOT EXISTS `leave_records` ("
    "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `leave_date` DATE NOT NULL UNIQUE,"
    "  `leave_type` VARCHAR(255) NOT NULL,"
    "  `notes` TEXT,"
    "  `status` VARCHAR(50) DEFAULT 'active'  -- e.g., 'active', 'cancelled'"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci")

TABLES['meeting_records'] = (
    "CREATE TABLE IF NOT EXISTS `meeting_records` ("
    "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `meeting_date` DATE NOT NULL UNIQUE,"
    "  `meeting_details` TEXT NOT NULL,"
    "  `status` VARCHAR(50) DEFAULT 'active' -- e.g., 'active', 'cancelled'"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci")

def connect_db():
    """
    Attempts to connect to the MySQL server.
    If the database DB_NAME does not exist, it attempts to create it.
    Then, connects to the DB_NAME database.
    Returns the connection object or None on failure.
    """
    try:
        # Step 1: Connect to MySQL server (without specifying a database initially)
        # This allows us to create the database if it doesn't exist.
        cnx_server = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123'  # Ensure this matches your MySQL root password
        )
        cursor = cnx_server.cursor()

        # Step 2: Create the database if it doesn't exist
        try:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                f"CHARACTER SET utf8 COLLATE utf8_general_ci"
            )
            print(f"Database '{DB_NAME}' ensured to exist.")
        except mysql.connector.Error as err:
            print(f"Failed to create database '{DB_NAME}': {err}")
            # If DB creation fails, we cannot proceed to connect to it.
            cursor.close()
            cnx_server.close()
            return None
        finally:
            cursor.close() # Close cursor used for DB creation

        # Step 3: Now, connect to the specific database
        cnx_db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123',
            database=DB_NAME
        )
        print(f"Successfully connected to database '{DB_NAME}'.")
        return cnx_db

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Access denied: Check MySQL username or password. Ensure 'root'@'localhost' can connect.")
        elif err.errno == errorcode.ER_CONN_REFUSED:
            print("Connection refused: Ensure MySQL server is running and accessible on localhost.")
        # ER_BAD_DB_ERROR might occur if DB creation failed and we tried to connect anyway,
        # but the logic above tries to prevent this.
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"Database '{DB_NAME}' does not exist and could not be selected (should have been created).")
        else:
            print(f"An error occurred while connecting to MySQL: {err} (Error Code: {err.errno})")
        return None

def create_tables(connection):
    """
    Creates the predefined tables in the database using the provided connection.
    Takes a database connection object as input. Returns True on success, False on failure.
    """
    if not connection or not connection.is_connected():
        print("No valid database connection provided. Cannot create tables.")
        return False

    cursor = connection.cursor()
    all_tables_created = True
    try:
        print(f"\nCreating tables in database '{DB_NAME}':")
        for table_name, table_description in TABLES.items():
            try:
                print(f"  Attempting to create table '{table_name}'... ", end='')
                cursor.execute(table_description)
                print("OK (created or already exists).")
            except mysql.connector.Error as err:
                # ER_TABLE_EXISTS_ERROR is not an issue for "CREATE TABLE IF NOT EXISTS"
                # but other errors should be reported.
                print(f"failed: {err.msg} (Error Code: {err.errno})")
                all_tables_created = False

        if all_tables_created:
            connection.commit()
            print("Table creation process completed successfully.")
        else:
            print("Some tables could not be created. Rolling back changes.")
            connection.rollback()

        return all_tables_created
    except mysql.connector.Error as err:
        print(f"An critical error occurred during table creation: {err}")
        connection.rollback() # Rollback in case of error during transaction
        return False
    finally:
        cursor.close()

def get_all_records(connection, table_name: str):
    """
    Fetches all records from the specified table.
    Orders by their respective date column.
    Returns a list of dictionaries.
    """
    if not connection or not connection.is_connected():
        print(f"No valid DB connection for get_all_records from {table_name}.")
        return []

    if table_name not in ['leave_records', 'meeting_records']:
        print(f"Invalid table name '{table_name}' for get_all_records.")
        return []

    cursor = connection.cursor(dictionary=True)
    records = []

    query = ""
    date_column = ""
    select_columns = ""

    if table_name == 'leave_records':
        date_column = 'leave_date'
        select_columns = "leave_date, leave_type, notes, status"
        query = f"SELECT {select_columns} FROM leave_records ORDER BY {date_column}"
    elif table_name == 'meeting_records':
        date_column = 'meeting_date'
        select_columns = "meeting_date, meeting_details, status"
        query = f"SELECT {select_columns} FROM meeting_records ORDER BY {date_column}"

    try:
        cursor.execute(query)
        records = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching all records from {table_name}: {err}")
    finally:
        cursor.close()

    return records

def update_record_status(connection, table_name: str, record_date: date, new_status: str):
    """
    Updates the status of a record for the given record_date in table_name.
    Returns True if a row was updated, False otherwise or on error.
    """
    if not connection or not connection.is_connected():
        print(f"No valid DB connection for update_record_status on {table_name}.")
        return False

    if table_name not in ['leave_records', 'meeting_records']:
        print(f"Invalid table name '{table_name}' for update_record_status.")
        return False

    if new_status not in ['active', 'cancelled']: # Enforce valid statuses
        print(f"Invalid new_status '{new_status}' provided.")
        return False

    date_column = 'leave_date' if table_name == 'leave_records' else 'meeting_date'

    query = f"UPDATE `{table_name}` SET status = %s WHERE `{date_column}` = %s AND status != %s"
    # The "AND status != %s" part is to ensure we only update if there's an actual change,
    # and cursor.rowcount reflects a real update.

    cursor = connection.cursor()
    updated_rows = 0
    try:
        cursor.execute(query, (new_status, record_date, new_status))
        connection.commit()
        updated_rows = cursor.rowcount
        if updated_rows > 0:
            print(f"Successfully updated status to '{new_status}' for {record_date} in {table_name}.")
        else:
            # This could mean the record didn't exist, or its status was already new_status.
            # For "delete" (mark as cancelled), if it wasn't 'active', it's fine.
            # If we are marking as 'cancelled', we only care if it was 'active' before.
            # A more precise check could be done with get_record_status before updating.
            # For now, if rowcount is 0, we'll consider it "no effective change needed or record not found for update".
            print(f"No rows updated for {record_date} in {table_name} to status '{new_status}'. Record might not exist or status already matches.")
        return True # Return True if operation was run, even if 0 rows affected (idempotency)
    except mysql.connector.Error as err:
        print(f"Database error in update_record_status for {table_name} on {record_date}: {err}")
        connection.rollback()
        return False
    finally:
        cursor.close()
    # The definition of success here means the operation completed without SQL error.
    # The caller might need to check if any active record was actually changed.

def get_recent_records(connection, table_name: str, days_limit: int = 365):
    """
    Fetches active records from the specified table within the last 'days_limit'.
    Orders by date descending.
    Returns a list of dictionaries, where each dictionary represents a record.
    """
    if not connection or not connection.is_connected():
        print(f"No valid DB connection for get_recent_records on {table_name}.")
        return []

    if table_name not in ['leave_records', 'meeting_records']:
        print(f"Invalid table name '{table_name}' for get_recent_records.")
        return []

    cursor = connection.cursor(dictionary=True) # Fetch results as dictionaries
    records = []

    query = ""
    date_column = ""

    if table_name == 'leave_records':
        date_column = 'leave_date'
        # For leave_records, select leave_date, leave_type, notes.
        query = f"""
            SELECT leave_date, leave_type, notes
            FROM leave_records
            WHERE status = 'active' AND {date_column} >= CURDATE() - INTERVAL %s DAY
            ORDER BY {date_column} DESC
        """
    elif table_name == 'meeting_records':
        date_column = 'meeting_date'
        # For meeting_records, select meeting_date, meeting_details.
        query = f"""
            SELECT meeting_date, meeting_details
            FROM meeting_records
            WHERE status = 'active' AND {date_column} >= CURDATE() - INTERVAL %s DAY
            ORDER BY {date_column} DESC
        """

    try:
        cursor.execute(query, (days_limit,))
        records = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching recent records from {table_name}: {err}")
    finally:
        cursor.close()

    return records

if __name__ == '__main__':
    print("--- Database Handler Script ---")
    print("This script attempts to connect to a MySQL server, create a database, and create tables.")
    print("\nPrerequisites for this script to run successfully:")
    print("1. MySQL server must be running and accessible on 'localhost'.")
    print("2. The 'mysql-connector-python' library must be installed in your Python environment.")
    print("3. A MySQL user 'root' with password '123' must exist and have necessary privileges.")
    print("   (CREATE DATABASE, CREATE TABLE, etc.)")
    print("---------------------------------\n")

    print("Attempting to connect to the database and set up tables...")
    db_connection = connect_db()

    if db_connection:
        if create_tables(db_connection):
            print("\nDatabase and tables configured successfully.")
            print(f"You can now connect to the '{DB_NAME}' database and use the tables: {', '.join(TABLES.keys())}.")
        else:
            print("\nFailed to configure one or more database tables.")

        db_connection.close()
        print("\nDatabase connection closed.")
    else:
        print("\nFailed to connect to the database. Setup aborted.")
        print("Please check your MySQL server, user credentials, and privileges.")

    print("\n--- Database Handler Script Finished ---")


def get_records_for_month(connection, year: int, month: int):
    """
    Fetches all 'active' leave and meeting records for the given year and month.
    Returns a dictionary like:
    {'leave_dates': {date(YYYY,MM,DD), ...}, 'meeting_dates': {date(YYYY,MM,DD), ...}}
    Returns empty sets if no records found or in case of error.
    """
    if not connection or not connection.is_connected():
        print("No valid database connection provided for get_records_for_month.")
        return {'leave_dates': set(), 'meeting_dates': set()}

    cursor = connection.cursor()
    results = {'leave_dates': set(), 'meeting_dates': set()}

    try:
        # Fetch active leave dates
        query_leave = """
            SELECT leave_date FROM leave_records
            WHERE status = 'active' AND YEAR(leave_date) = %s AND MONTH(leave_date) = %s
        """
        cursor.execute(query_leave, (year, month))
        for (leave_date_db,) in cursor:
            if isinstance(leave_date_db, date):
                 results['leave_dates'].add(leave_date_db)
            # Note: mysql.connector usually returns datetime.date objects for DATE SQL type

        # Fetch active meeting dates
        query_meetings = """
            SELECT meeting_date FROM meeting_records
            WHERE status = 'active' AND YEAR(meeting_date) = %s AND MONTH(meeting_date) = %s
        """
        cursor.execute(query_meetings, (year, month))
        for (meeting_date_db,) in cursor:
            if isinstance(meeting_date_db, date):
                results['meeting_dates'].add(meeting_date_db)

    except mysql.connector.Error as err:
        print(f"Error fetching active records for {year}-{month:02d}: {err}")
        # Return empty sets in case of error to avoid breaking the caller
        results['leave_dates'] = set()
        results['meeting_dates'] = set()
    finally:
        cursor.close()

    return results

def get_cancelled_records_for_month(connection, year: int, month: int):
    """
    Fetches all 'cancelled' leave and meeting records for the given year and month.
    Returns a set of dates: {date(YYYY,MM,DD), ...}
    Returns an empty set if no records found or in case of error.
    """
    if not connection or not connection.is_connected():
        print("No valid database connection provided for get_cancelled_records_for_month.")
        return set()

    cursor = connection.cursor()
    cancelled_dates = set()

    try:
        # Fetch cancelled leave dates
        query_cancelled_leave = """
            SELECT leave_date FROM leave_records
            WHERE status = 'cancelled' AND YEAR(leave_date) = %s AND MONTH(leave_date) = %s
        """
        cursor.execute(query_cancelled_leave, (year, month))
        for (leave_date_db,) in cursor:
            if isinstance(leave_date_db, date):
                cancelled_dates.add(leave_date_db)

        # Fetch cancelled meeting dates
        query_cancelled_meetings = """
            SELECT meeting_date FROM meeting_records
            WHERE status = 'cancelled' AND YEAR(meeting_date) = %s AND MONTH(meeting_date) = %s
        """
        cursor.execute(query_cancelled_meetings, (year, month))
        for (meeting_date_db,) in cursor:
            if isinstance(meeting_date_db, date):
                cancelled_dates.add(meeting_date_db)

    except mysql.connector.Error as err:
        print(f"Error fetching cancelled records for {year}-{month:02d}: {err}")
        # Return empty set in case of error
        return set()
    finally:
        cursor.close()

    return cancelled_dates

# --- Helper function to check record status ---
def get_record_status(connection, table_name: str, record_date: date):
    """
    Checks if a record for record_date exists in table_name and returns its status.
    Returns 'active', 'cancelled', or None if not found or error.
    """
    if not connection or not connection.is_connected():
        print(f"No valid DB connection for get_record_status on {table_name}.")
        return None

    # Ensure table_name is one of the known tables to prevent SQL injection if it were user-supplied
    if table_name not in ['leave_records', 'meeting_records']:
        print(f"Invalid table name '{table_name}' for get_record_status.")
        return None

    # Determine the correct date column name based on the table
    date_column = 'leave_date' if table_name == 'leave_records' else 'meeting_date'

    query = f"SELECT status FROM `{table_name}` WHERE `{date_column}` = %s"
    cursor = connection.cursor()
    status = None
    try:
        cursor.execute(query, (record_date,))
        result = cursor.fetchone()
        if result:
            status = result[0]
    except mysql.connector.Error as err:
        print(f"Error checking status for {record_date} in {table_name}: {err}")
    finally:
        cursor.close()
    return status

# --- Functions to add records ---
def add_leave_record(connection, leave_date: date, leave_type: str, notes: str):
    """
    Adds or updates a leave record.
    - If no record exists for leave_date, inserts a new 'active' record.
    - If a 'cancelled' record exists, updates it to 'active' with new details.
    - If an 'active' record exists, returns False (error, already an active entry).
    Returns True on success, False on failure.
    """
    if not connection or not connection.is_connected():
        print("No valid DB connection for add_leave_record.")
        return False

    current_status = get_record_status(connection, 'leave_records', leave_date)
    cursor = connection.cursor()

    try:
        if current_status is None: # No record, insert new
            query_insert = """
                INSERT INTO leave_records (leave_date, leave_type, notes, status)
                VALUES (%s, %s, %s, 'active')
            """
            cursor.execute(query_insert, (leave_date, leave_type, notes))
            connection.commit()
            print(f"Successfully inserted new leave record for {leave_date}.")
            return True
        elif current_status == 'cancelled': # Cancelled record exists, update it
            query_update = """
                UPDATE leave_records
                SET leave_type = %s, notes = %s, status = 'active'
                WHERE leave_date = %s
            """
            cursor.execute(query_update, (leave_type, notes, leave_date))
            connection.commit()
            print(f"Successfully updated cancelled leave record to active for {leave_date}.")
            return True
        elif current_status == 'active': # Active record already exists
            print(f"Error: An active leave record already exists for {leave_date}.")
            return False
        else: # Should not happen if statuses are only 'active' or 'cancelled'
            print(f"Unknown status '{current_status}' for leave record on {leave_date}.")
            return False

    except mysql.connector.Error as err:
        print(f"Database error in add_leave_record for {leave_date}: {err}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def add_meeting_record(connection, meeting_date: date, details: str):
    """
    Adds or updates a meeting record.
    - If no record exists for meeting_date, inserts a new 'active' record.
    - If a 'cancelled' record exists, updates it to 'active' with new details.
    - If an 'active' record exists, returns False (error, already an active entry).
    Returns True on success, False on failure.
    """
    if not connection or not connection.is_connected():
        print("No valid DB connection for add_meeting_record.")
        return False

    current_status = get_record_status(connection, 'meeting_records', meeting_date)
    cursor = connection.cursor()

    try:
        if current_status is None: # No record, insert new
            query_insert = """
                INSERT INTO meeting_records (meeting_date, meeting_details, status)
                VALUES (%s, %s, 'active')
            """
            cursor.execute(query_insert, (meeting_date, details))
            connection.commit()
            print(f"Successfully inserted new meeting record for {meeting_date}.")
            return True
        elif current_status == 'cancelled': # Cancelled record exists, update it
            query_update = """
                UPDATE meeting_records
                SET meeting_details = %s, status = 'active'
                WHERE meeting_date = %s
            """
            cursor.execute(query_update, (details, meeting_date))
            connection.commit()
            print(f"Successfully updated cancelled meeting record to active for {meeting_date}.")
            return True
        elif current_status == 'active': # Active record already exists
            print(f"Error: An active meeting record already exists for {meeting_date}.")
            return False
        else:
            print(f"Unknown status '{current_status}' for meeting record on {meeting_date}.")
            return False

    except mysql.connector.Error as err:
        print(f"Database error in add_meeting_record for {meeting_date}: {err}")
        connection.rollback()
        return False
    finally:
        cursor.close()
