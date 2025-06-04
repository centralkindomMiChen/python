import mysql.connector
from mysql.connector import errorcode
import datetime

DB_CONFIG = {
    'user': 'root',
    'password': '123',
    'host': '127.0.0.1', # Assuming localhost
    'database': 'michentestdb5',
    'raise_on_warnings': True,
    'charset': 'utf8', # MODIFIED
    'collation': 'utf8_general_ci', # MODIFIED
    'use_pure': True
}

# SQL Commands for table creation
TABLES = {}
TABLES['vacations'] = (
    "CREATE TABLE `vacations` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `vacation_date` date NOT NULL,"
    "  `type` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL," # MODIFIED
    "  `remarks` text CHARACTER SET utf8 COLLATE utf8_general_ci," # MODIFIED
    "  `cancelled` tinyint(1) DEFAULT 0,"
    "  `deletion_reason` text CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL," # MODIFIED
    "  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`),"
    "  UNIQUE KEY `idx_vacation_date` (`vacation_date`)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci") # MODIFIED

TABLES['meetings'] = (
    "CREATE TABLE `meetings` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `meeting_date` date NOT NULL,"
    "  `content` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL," # MODIFIED
    "  `cancelled` tinyint(1) DEFAULT 0,"
    "  `deletion_reason` text CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL," # MODIFIED
    "  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`),"
    "  UNIQUE KEY `idx_meeting_date` (`meeting_date`)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci") # MODIFIED


class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.connect()
        if self.conn:
            self.create_database_if_not_exists() # Ensure DB exists before creating tables
            self.create_tables()

    def connect(self):
        try:
            # Try connecting to the specific database first
            self.conn = mysql.connector.connect(**DB_CONFIG)
            print("Successfully connected to the database.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                # Database doesn't exist, connect without specifying DB
                # to create it
                temp_config = DB_CONFIG.copy()
                del temp_config['database']
                try:
                    self.conn = mysql.connector.connect(**temp_config)
                    print("Connected to MySQL server (database will be created).")
                except mysql.connector.Error as e:
                    print(f"Error connecting to MySQL server: {e}")
                    self.conn = None # Ensure conn is None if connection failed
                    raise ConnectionError(f"MySQL Server connection failed: {e}") from e
            else:
                print(f"Error connecting to database: {err}")
                self.conn = None # Ensure conn is None
                raise ConnectionError(f"Database connection failed: {err}") from err

    def create_database_if_not_exists(self):
        if not self.conn:
            print("No connection to MySQL server, cannot create database.")
            # This typically means the connect() method itself failed earlier (e.g. server not running)
            # and self.conn would be None. Raising an error here might be more informative.
            raise ConnectionError("Cannot create database: No active MySQL server connection.")

        cursor = None
        db_name = DB_CONFIG['database']
        database_selected_successfully = False
        try:
            cursor = self.conn.cursor()
            try:
                # Attempt to create the database with UTF8
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci")
                print(f"Database '{db_name}' creation attempted/ensured (utf8).")
                # If it gets here, the command executed. It either created it or it already existed.
                # Now, try to select it.
                self.conn.database = db_name
                print(f"Successfully selected database '{db_name}'.")
                database_selected_successfully = True
            except mysql.connector.Error as err_utf8:
                # Check if the error is specifically "database exists"
                if err_utf8.errno == errorcode.ER_DB_CREATE_EXISTS: # Error code 1007
                    print(f"Database '{db_name}' already exists (utf8 check). Selecting it.")
                    try:
                        self.conn.database = db_name # Try to select it
                        print(f"Successfully selected existing database '{db_name}'.")
                        database_selected_successfully = True
                    except mysql.connector.Error as err_select:
                        print(f"Error selecting existing database '{db_name}': {err_select}")
                        raise # Re-raise if selecting the existing DB fails
                else:
                    # Different error occurred during utf8 database creation
                    print(f"Error during utf8 database creation attempt for '{db_name}': {err_utf8}")
                    # At this point, we could try the utf8mb4 fallback if desired for other error types,
                    # but given the user's specific problem, we want to avoid utf8mb4 if utf8 fails for 'Unknown charset'.
                    # For now, if primary utf8 creation fails (not due to 'exists'), we re-raise.
                    raise err_utf8 # Re-raise the original error from utf8 attempt

            # If database_selected_successfully is False here, it means an unhandled case or error.
            if not database_selected_successfully:
                 # This should ideally not be reached if logic above is correct
                raise ConnectionError(f"Failed to ensure and select database '{db_name}' after creation attempts.")

        except mysql.connector.Error as err: # Catch errors from the outer try or re-raised errors
            print(f"Failed to create or select database '{db_name}' due to: {err}")
            # It's possible self.conn is already closed or None if connect() failed before this method was called.
            if self.conn and self.conn.is_connected():
                self.conn.close()
            self.conn = None # Mark connection as unusable
            raise ConnectionError(f"Database setup failed for '{db_name}': {err}") from err
        finally:
            if cursor:
                cursor.close()


    def create_tables(self):
        if not self.conn or not self.conn.is_connected():
            print("No database connection, cannot create tables.")
            # Attempt to reconnect if connection was lost
            try:
                self.connect()
                if not self.conn or not self.conn.is_connected(): # Check again after trying to connect
                    raise ConnectionError("Failed to reconnect to the database.")
            except ConnectionError as e:
                print(f"Error during table creation (reconnect failed): {e}")
                return # Exit if connection cannot be established

        cursor = self.conn.cursor()
        self.conn.database = DB_CONFIG['database'] # Ensure correct DB is selected
        for table_name, table_description in TABLES.items():
            try:
                print(f"Creating table {table_name}: ", end='')
                cursor.execute(table_description)
                print("OK")
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(f"Failed: {err.msg}")
                    # Consider if this should raise an error and stop initialization
            except Exception as e:
                print(f"An unexpected error occurred during table creation for {table_name}: {e}")
        cursor.close()

    def _execute_query(self, query, params=None, multi=False, fetch_one=False, fetch_all=False, commit=False):
        if not self.conn or not self.conn.is_connected():
            print("Database not connected. Attempting to reconnect...")
            try:
                self.connect()
                if not self.conn or not self.conn.is_connected():
                     raise ConnectionError("Failed to reconnect to the database for query execution.")
            except ConnectionError as e:
                print(f"Query execution failed due to connection error: {e}")
                return None # Or raise the error

        cursor = self.conn.cursor(dictionary=True if fetch_one or fetch_all else False)
        try:
            cursor.execute(query, params or ())
            if commit:
                self.conn.commit()
                return cursor.lastrowid or cursor.rowcount
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            return True # For non-SELECT, non-commit operations if needed
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            self.conn.rollback() # Rollback on error
            return None # Indicate failure
        except Exception as e:
            print(f"An unexpected error occurred during query execution: {e}")
            self.conn.rollback()
            return None
        finally:
            cursor.close()

    def add_vacation(self, vacation_date, type, remarks=None):
        query = ("INSERT INTO vacations (vacation_date, type, remarks, cancelled) "
                 "VALUES (%s, %s, %s, 0) "
                 "ON DUPLICATE KEY UPDATE type=%s, remarks=%s, cancelled=0, deletion_reason=NULL")
        # Convert date object to string if it's not already
        date_str = vacation_date.isoformat() if isinstance(vacation_date, (datetime.date, datetime.datetime)) else vacation_date
        params = (date_str, type, remarks, type, remarks)
        return self._execute_query(query, params, commit=True)

    def add_meeting(self, meeting_date, content):
        query = ("INSERT INTO meetings (meeting_date, content, cancelled) "
                 "VALUES (%s, %s, 0) "
                 "ON DUPLICATE KEY UPDATE content=%s, cancelled=0, deletion_reason=NULL")
        date_str = meeting_date.isoformat() if isinstance(meeting_date, (datetime.date, datetime.datetime)) else meeting_date
        params = (date_str, content, content)
        return self._execute_query(query, params, commit=True)

    def get_vacation_by_date(self, vacation_date):
        query = "SELECT type, remarks, cancelled FROM vacations WHERE vacation_date = %s"
        date_str = vacation_date.isoformat() if isinstance(vacation_date, (datetime.date, datetime.datetime)) else vacation_date
        return self._execute_query(query, (date_str,), fetch_one=True)

    def get_meeting_by_date(self, meeting_date):
        query = "SELECT content, cancelled FROM meetings WHERE meeting_date = %s"
        date_str = meeting_date.isoformat() if isinstance(meeting_date, (datetime.date, datetime.datetime)) else meeting_date
        return self._execute_query(query, (date_str,), fetch_one=True)

    def get_records_in_date_range(self, start_date, end_date):
        # Returns a dictionary with 'vacations' and 'meetings' lists
        records = {'vacations': [], 'meetings': []}

        start_str = start_date.isoformat() if isinstance(start_date, (datetime.date, datetime.datetime)) else start_date
        end_str = end_date.isoformat() if isinstance(end_date, (datetime.date, datetime.datetime)) else end_date

        query_vac = "SELECT vacation_date, type, remarks, cancelled FROM vacations WHERE vacation_date BETWEEN %s AND %s ORDER BY vacation_date"
        vacations_data = self._execute_query(query_vac, (start_str, end_str), fetch_all=True)
        if vacations_data:
            records['vacations'] = vacations_data

        query_meet = "SELECT meeting_date, content, cancelled FROM meetings WHERE meeting_date BETWEEN %s AND %s ORDER BY meeting_date"
        meetings_data = self._execute_query(query_meet, (start_str, end_str), fetch_all=True)
        if meetings_data:
            records['meetings'] = meetings_data

        return records

    def delete_vacation(self, vacation_date, reason=""):
        query = "UPDATE vacations SET cancelled = 1, deletion_reason = %s WHERE vacation_date = %s AND cancelled = 0"
        date_str = vacation_date.isoformat() if isinstance(vacation_date, (datetime.date, datetime.datetime)) else vacation_date
        return self._execute_query(query, (reason, date_str), commit=True)

    def delete_meeting(self, meeting_date, reason=""):
        query = "UPDATE meetings SET cancelled = 1, deletion_reason = %s WHERE meeting_date = %s AND cancelled = 0"
        date_str = meeting_date.isoformat() if isinstance(meeting_date, (datetime.date, datetime.datetime)) else meeting_date
        return self._execute_query(query, (reason, date_str), commit=True)

    def get_all_vacations_for_export(self):
        query = "SELECT vacation_date, type, remarks, cancelled, deletion_reason, created_at FROM vacations ORDER BY vacation_date"
        return self._execute_query(query, fetch_all=True)

    def get_all_meetings_for_export(self):
        query = "SELECT meeting_date, content, cancelled, deletion_reason, created_at FROM meetings ORDER BY meeting_date"
        return self._execute_query(query, fetch_all=True)

    def get_recent_records(self, days_limit=365):
        # Returns a dictionary with 'vacations' and 'meetings' lists for the last year
        records = {'vacations': [], 'meetings': []}
        one_year_ago = (datetime.date.today() - datetime.timedelta(days=days_limit)).isoformat()
        today_str = datetime.date.today().isoformat()

        query_vac = ("SELECT vacation_date, type, remarks, cancelled FROM vacations "
                     "WHERE vacation_date BETWEEN %s AND %s ORDER BY vacation_date DESC")
        vacations_data = self._execute_query(query_vac, (one_year_ago, today_str), fetch_all=True)
        if vacations_data:
            records['vacations'] = vacations_data

        query_meet = ("SELECT meeting_date, content, cancelled FROM meetings "
                      "WHERE meeting_date BETWEEN %s AND %s ORDER BY meeting_date DESC")
        meetings_data = self._execute_query(query_meet, (one_year_ago, today_str), fetch_all=True)
        if meetings_data:
            records['meetings'] = meetings_data

        return records

    def close(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print("Database connection closed.")

# Example Usage (for testing this module directly)
if __name__ == '__main__':
    try:
        db_manager = DatabaseManager()
        if not db_manager.conn:
            print("DB Manager connection object is None. Exiting test.")
        else:
            print("DatabaseManager initialized.")

            # Test adding a vacation
            today = datetime.date.today()
            # added_vac = db_manager.add_vacation(today, "年休假", "测试年休 (Test Annual Leave)")
            # if added_vac:
            #     print(f"Vacation added for {today}")
            # else:
            #     print(f"Failed to add vacation for {today} or it already exists and was updated.")

            # # Test adding a meeting
            # tomorrow = today + datetime.timedelta(days=1)
            # added_meet = db_manager.add_meeting(tomorrow, "重要项目会议 (Important Project Meeting)")
            # if added_meet:
            #     print(f"Meeting added for {tomorrow}")
            # else:
            #     print(f"Failed to add meeting for {tomorrow} or it already exists and was updated.")

            # Test retrieving records
            print("\n--- Records for today ---")
            vac_today = db_manager.get_vacation_by_date(today)
            if vac_today: print(f"Vacation on {today}: {vac_today}")
            else: print(f"No vacation on {today} or query failed.")

            meet_today = db_manager.get_meeting_by_date(today)
            if meet_today: print(f"Meeting on {today}: {meet_today}")
            else: print(f"No meeting on {today} or query failed.")

            print("\n--- Records in range (last 7 days) ---")
            last_week = today - datetime.timedelta(days=7)
            range_records = db_manager.get_records_in_date_range(last_week, today)
            print(f"Vacations in range: {range_records['vacations']}")
            print(f"Meetings in range: {range_records['meetings']}")

            # # Test deleting vacation (if it was added)
            # if vac_today and not vac_today['cancelled']:
            #     deleted_vac = db_manager.delete_vacation(today, "测试删除 (Test deletion)")
            #     if deleted_vac:
            #         print(f"Vacation on {today} marked as cancelled.")
            #         updated_vac = db_manager.get_vacation_by_date(today)
            #         print(f"Updated vacation status: {updated_vac}")
            #     else:
            #         print(f"Failed to delete vacation on {today}")


            print("\n--- Recent Records (last 30 days) ---")
            recent = db_manager.get_recent_records(days_limit=30)
            print(f"Recent Vacations: {recent['vacations']}")
            print(f"Recent Meetings: {recent['meetings']}")

            print("\n--- All Vacations for Export ---")
            # all_vac = db_manager.get_all_vacations_for_export()
            # if all_vac: print(f"Found {len(all_vac)} vacations for export.") # Avoid printing all data
            # else: print("No vacations to export or query failed.")

            print("\n--- All Meetings for Export ---")
            # all_meet = db_manager.get_all_meetings_for_export()
            # if all_meet: print(f"Found {len(all_meet)} meetings for export.")
            # else: print("No meetings to export or query failed.")

            db_manager.close()

    except ConnectionError as e:
        print(f"Critical Connection Error during DB Manager setup: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in the test script: {e}")
