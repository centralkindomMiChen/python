import mysql.connector
from mysql.connector import errorcode
import datetime

# Database configuration
DB_CONFIG = {
    'user': 'root',
    'password': '123',
    'host': '127.0.0.1',
    'database': 'michentestdb5',
    'raise_on_warnings': False, # Changed to False during development to handle utf8 alias warning
    'charset': 'utf8',
    # 'collation': 'utf8_general_ci', # Removed for broader compatibility, letting MySQL default for utf8
    'use_pure': True
}

# SQL Commands for table creation (UTF-8 compatible)
TABLES = {}
TABLES['vacations'] = (
    "CREATE TABLE IF NOT EXISTS `vacations` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `vacation_date` date NOT NULL,"
    "  `type` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL," # Specific collation for MySQL 5.x compatibility
    "  `remarks` text CHARACTER SET utf8 COLLATE utf8_general_ci,"
    "  `cancelled` tinyint(1) DEFAULT 0,"
    "  `deletion_reason` text CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,"
    "  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`),"
    "  UNIQUE KEY `idx_vacation_date` (`vacation_date`)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci") # Table default for MySQL 5.x

TABLES['meetings'] = (
    "CREATE TABLE IF NOT EXISTS `meetings` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `meeting_date` date NOT NULL,"
    "  `content` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,"
    "  `cancelled` tinyint(1) DEFAULT 0,"
    "  `deletion_reason` text CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,"
    "  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`),"
    "  UNIQUE KEY `idx_meeting_date` (`meeting_date`)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci")

class DatabaseManager:
    """Manages database connections, table creation, and CRUD operations."""
    def __init__(self):
        self.conn = None
        try:
            self.connect()
            if self.conn:
                self.create_tables()
        except mysql.connector.Error as e: # Catch specific connector errors during init
            # Print to console as this is a library module, GUI might not be up.
            print(f"FATAL: Failed to initialize DatabaseManager and connect to DB: {e}")
            raise # Re-raise to signal failure to the calling application

    def connect(self):
        """Establishes a connection to the MySQL database.
        If the database does not exist, it attempts to create it.
        """
        try:
            # Connect to the specified database
            self.conn = mysql.connector.connect(**DB_CONFIG)
            # print(f"Successfully connected to database '{DB_CONFIG['database']}'.") # Informative, can keep for module testing
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                # print(f"Database '{DB_CONFIG['database']}' does not exist. Attempting to create it.") # Informative
                temp_config = DB_CONFIG.copy()
                db_name_to_create = temp_config.pop('database') # Remove db name for initial connection
                try:
                    # Connect to MySQL server without specifying a database
                    self.conn = mysql.connector.connect(**temp_config)
                    # print("Connected to MySQL server (for DB creation).") # Informative
                    cursor = self.conn.cursor()
                    # Create database with default charset utf8; collation will be MySQL's default for utf8
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name_to_create}` DEFAULT CHARACTER SET utf8")
                    cursor.close()
                    # print(f"Database '{db_name_to_create}' created or already exists.") # Informative
                    self.conn.database = db_name_to_create # Switch to the newly created/existing database
                    # print(f"Switched to database '{db_name_to_create}'.") # Informative
                except mysql.connector.Error as e_create:
                    # print(f"Error during database creation or server connection: {e_create}") # Informative
                    if self.conn and self.conn.is_connected(): self.conn.close()
                    self.conn = None
                    raise # Re-raise after cleanup attempt
            else:
                # print(f"Error connecting to database '{DB_CONFIG['database']}': {err}") # Informative
                self.conn = None
                raise # Re-raise

    def create_tables(self):
        """Creates database tables if they do not already exist."""
        if not self.conn or not self.conn.is_connected() or not self.conn.database:
            # print("No valid database connection or database not selected, cannot create tables.") # Informative
            raise mysql.connector.Error("Connection lost or database not selected before table creation.")

        cursor = self.conn.cursor()
        for table_name, table_description in TABLES.items():
            try:
                # print(f"Attempting to create table '{table_name}'... ", end='') # Informative
                cursor.execute(table_description)
                self.conn.commit()
                # print("OK") # Informative
            except mysql.connector.Error as err:
                # print(f"Failed to create table {table_name}: {err.msg}") # Informative
                # Decide if we should raise here or try to continue with other tables
                pass # For now, allow trying other tables
            except Exception as e:
                # print(f"An unexpected error occurred during table creation for {table_name}: {e}") # Informative
                pass
        cursor.close()

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """Executes a given SQL query with optional parameters and commit.
        Handles reconnections if the database connection is lost.
        Returns query result (fetchone, fetchall), lastrowid/rowcount on commit, or None on error.
        """
        if not self.conn or not self.conn.is_connected():
            # print("Database not connected. Attempting to reconnect...") # Informative
            try:
                self.connect()
                if not self.conn or not self.conn.is_connected():
                     # print("Failed to reconnect to the database for query execution.") # Informative
                     return None # Indicate failure
            except mysql.connector.Error as e:
                # print(f"Query execution failed due to connection error: {e}") # Informative
                return None

        cursor = self.conn.cursor(dictionary=True) # Use dictionary cursor for easy column access
        try:
            cursor.execute(query, params or ())
            if commit:
                self.conn.commit()
                return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            return True # For queries like CREATE, or if no fetch/commit needed (though commit usually is)
        except mysql.connector.Error as err:
            # print(f"Database Error: {err}") # Informative
            # print(f"Query: {query}") # Potentially sensitive, remove if not needed for debugging
            # print(f"Params: {params}") # Potentially sensitive
            try:
                self.conn.rollback() # Rollback on error if a transaction was started
            except Exception as rb_err:
                # print(f"Error during rollback: {rb_err}") # Informative
                pass
            return None # Indicate failure
        finally:
            cursor.close()

    def _format_date(self, date_obj):
        """Formats a datetime.date or datetime.datetime object to 'YYYY-MM-DD' string."""
        if isinstance(date_obj, (datetime.date, datetime.datetime)):
            return date_obj.strftime('%Y-%m-%d')
        return date_obj # Return as is if not a date/datetime object

    # --- Vacation Methods ---
    def add_or_update_vacation(self, vacation_date, type, remarks=None):
        """Adds a new vacation or updates an existing one for a given date."""
        date_str = self._format_date(vacation_date)
        query = ("INSERT INTO vacations (vacation_date, type, remarks, cancelled, deletion_reason, created_at) "
                 "VALUES (%s, %s, %s, 0, NULL, CURRENT_TIMESTAMP) "
                 "ON DUPLICATE KEY UPDATE type=%s, remarks=%s, cancelled=0, deletion_reason=NULL, created_at=CURRENT_TIMESTAMP")
        params = (date_str, type, remarks, type, remarks)
        return self._execute_query(query, params, commit=True)

    def get_vacation_by_date(self, vacation_date):
        """Retrieves a vacation record by its date."""
        date_str = self._format_date(vacation_date)
        query = "SELECT id, vacation_date, type, remarks, cancelled, deletion_reason, created_at FROM vacations WHERE vacation_date = %s"
        return self._execute_query(query, (date_str,), fetch_one=True)

    def cancel_vacation(self, vacation_date, reason=""):
        """Marks a vacation as cancelled and records the reason."""
        date_str = self._format_date(vacation_date)
        query = "UPDATE vacations SET cancelled = 1, deletion_reason = %s WHERE vacation_date = %s AND cancelled = 0"
        return self._execute_query(query, (reason if reason else None, date_str), commit=True)

    # --- Meeting Methods ---
    def add_or_update_meeting(self, meeting_date, content):
        """Adds a new meeting or updates an existing one for a given date."""
        date_str = self._format_date(meeting_date)
        query = ("INSERT INTO meetings (meeting_date, content, cancelled, deletion_reason, created_at) "
                 "VALUES (%s, %s, 0, NULL, CURRENT_TIMESTAMP) "
                 "ON DUPLICATE KEY UPDATE content=%s, cancelled=0, deletion_reason=NULL, created_at=CURRENT_TIMESTAMP")
        params = (date_str, content, content)
        return self._execute_query(query, params, commit=True)

    def get_meeting_by_date(self, meeting_date):
        """Retrieves a meeting record by its date."""
        date_str = self._format_date(meeting_date)
        query = "SELECT id, meeting_date, content, cancelled, deletion_reason, created_at FROM meetings WHERE meeting_date = %s"
        return self._execute_query(query, (date_str,), fetch_one=True)

    def cancel_meeting(self, meeting_date, reason=""):
        """Marks a meeting as cancelled and records the reason."""
        date_str = self._format_date(meeting_date)
        query = "UPDATE meetings SET cancelled = 1, deletion_reason = %s WHERE meeting_date = %s AND cancelled = 0"
        return self._execute_query(query, (reason if reason else None, date_str), commit=True)

    # --- Combined Record Methods ---
    def get_records_in_date_range(self, start_date, end_date):
        """Retrieves all vacations and meetings within a given date range."""
        start_str = self._format_date(start_date)
        end_str = self._format_date(end_date)

        records = {'vacations': [], 'meetings': []}

        query_vac = ("SELECT id, vacation_date, type, remarks, cancelled FROM vacations "
                     "WHERE vacation_date BETWEEN %s AND %s ORDER BY vacation_date")
        vacations_data = self._execute_query(query_vac, (start_str, end_str), fetch_all=True)
        if vacations_data is not None: records['vacations'] = vacations_data

        query_meet = ("SELECT id, meeting_date, content, cancelled FROM meetings "
                      "WHERE meeting_date BETWEEN %s AND %s ORDER BY meeting_date")
        meetings_data = self._execute_query(query_meet, (start_str, end_str), fetch_all=True)
        if meetings_data is not None: records['meetings'] = meetings_data

        return records

    def get_all_records_for_export(self):
        """Retrieves all vacation and meeting records for data export purposes."""
        records = {'vacations': [], 'meetings': []}
        query_vac = "SELECT vacation_date, type, remarks, cancelled, deletion_reason, created_at FROM vacations ORDER BY vacation_date"
        vac_data = self._execute_query(query_vac, fetch_all=True)
        if vac_data is not None: records['vacations'] = vac_data

        query_meet = "SELECT meeting_date, content, cancelled, deletion_reason, created_at FROM meetings ORDER BY meeting_date"
        meet_data = self._execute_query(query_meet, fetch_all=True)
        if meet_data is not None: records['meetings'] = meet_data

        return records

    def get_recent_records(self, days_limit=365):
        """Retrieves records from the last N days (default 365)."""
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days_limit)
        return self.get_records_in_date_range(start_date, today)

    def close(self):
        """Closes the database connection."""
        if self.conn and self.conn.is_connected():
            self.conn.close()
            # print("Database connection closed.") # Informative, can keep for module testing

# Example Usage (for testing this module directly)
if __name__ == '__main__':
    print("Attempting to initialize DatabaseManager for testing...")
    db = None
    try:
        db = DatabaseManager() # This will print connection status from connect()
        if db.conn and db.conn.is_connected():
            print("DatabaseManager initialized and connected successfully for testing.")

            # Test data
            today = datetime.date.today()
            test_date_vac = today + datetime.timedelta(days=10)
            test_date_meet = today + datetime.timedelta(days=11)
            test_date_overlap = today + datetime.timedelta(days=12)

            # Clean up potential old test data for these specific dates
            print(f"\nCleaning up test data for {test_date_vac}, {test_date_meet}, {test_date_overlap}...")
            db._execute_query("DELETE FROM vacations WHERE vacation_date IN (%s, %s)", (test_date_vac, test_date_overlap), commit=True)
            db._execute_query("DELETE FROM meetings WHERE meeting_date IN (%s, %s)", (test_date_meet, test_date_overlap), commit=True)
            print("Cleanup done.")

            # Test add_or_update_vacation
            print(f"\nTesting ADD vacation for {test_date_vac}...")
            res_add_vac = db.add_or_update_vacation(test_date_vac, "年休假", "年度测试休假")
            assert res_add_vac is not None, "Add vacation failed."
            vac = db.get_vacation_by_date(test_date_vac)
            assert vac and vac['type'] == "年休假" and not vac['cancelled'], "Vacation data error after add."
            print(f"ADD vacation PASSED. Details: {vac}")

            # Test add_or_update_meeting
            print(f"\nTesting ADD meeting for {test_date_meet}...")
            res_add_meet = db.add_or_update_meeting(test_date_meet, "项目启动会议")
            assert res_add_meet is not None, "Add meeting failed."
            meet = db.get_meeting_by_date(test_date_meet)
            assert meet and meet['content'] == "项目启动会议" and not meet['cancelled'], "Meeting data error after add."
            print(f"ADD meeting PASSED. Details: {meet}")

            # Test overlap (add vacation on a date, then meeting on same date)
            print(f"\nTesting ADD vacation for OVERLAP on {test_date_overlap}...")
            db.add_or_update_vacation(test_date_overlap, "临时休假", "Overlap vacation part")
            assert db.get_vacation_by_date(test_date_overlap) is not None, "Overlap vacation add error."
            print(f"Testing ADD meeting for OVERLAP on {test_date_overlap}...")
            db.add_or_update_meeting(test_date_overlap, "紧急会议") # Should coexist
            assert db.get_meeting_by_date(test_date_overlap) is not None, "Overlap meeting add error."
            print("ADD overlap tests PASSED.")

            # Test cancel_vacation
            print(f"\nTesting CANCEL vacation for {test_date_vac}...")
            res_cancel_vac = db.cancel_vacation(test_date_vac, "计划有变")
            assert res_cancel_vac is not None and res_cancel_vac > 0, "Cancel vacation failed."
            cancelled_vac = db.get_vacation_by_date(test_date_vac)
            assert cancelled_vac and cancelled_vac['cancelled'] == 1 and cancelled_vac['deletion_reason'] == "计划有变", "Vacation cancel error."
            print(f"CANCEL vacation PASSED. Details: {cancelled_vac}")

            # Test re-add (uncancel) vacation
            print(f"\nTesting RE-ADD/UPDATE cancelled vacation for {test_date_vac}...")
            db.add_or_update_vacation(test_date_vac, "年休假", "重新申请通过")
            readded_vac = db.get_vacation_by_date(test_date_vac)
            assert readded_vac and readded_vac['cancelled'] == 0 and readded_vac['remarks'] == "重新申请通过", "Vacation re-add error."
            print(f"RE-ADD/UPDATE cancelled vacation PASSED. Details: {readded_vac}")

            # Test get_records_in_date_range
            print("\nTesting GET records in range...")
            range_start = today + datetime.timedelta(days=5)
            range_end = today + datetime.timedelta(days=15)
            range_recs = db.get_records_in_date_range(range_start, range_end)
            assert range_recs is not None, "Range records fetch error."
            print(f"  Vacations found in range: {len(range_recs.get('vacations', []))}")
            print(f"  Meetings found in range: {len(range_recs.get('meetings', []))}")
            print("GET records in range PASSED.")

            print("\nAll local tests for db_manager.py PASSED.")
        else:
            print("DatabaseManager initialization failed or did not connect. Tests cannot run.")

    except Exception as e:
        # import traceback # Uncomment for full traceback during dev
        # print(traceback.format_exc()) # Uncomment for full traceback during dev
        print(f"An error occurred during db_manager.py self-tests: {e}")
    finally:
        if db:
            db.close()
            print("Database connection closed via finally block in self-test.")
