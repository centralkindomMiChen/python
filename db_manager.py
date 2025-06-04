import mysql.connector
from mysql.connector import errorcode
import datetime

DB_CONFIG = {
    'user': 'root',
    'password': '123',
    'host': '127.0.0.1',
    'charset': 'utf8'
}
DB_NAME = 'michentestdb5'
VACATION_TABLE = 'vacations'
MEETING_TABLE = 'meetings'

class DatabaseManager:
    def __init__(self):
        self.cnx = None
        self.ensure_database_and_table()

    def _connect_server(self):
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as err:
            print(f"数据库服务器连接失败: {err}")
            return None

    def _connect_db(self):
        try:
            db_conn_config = DB_CONFIG.copy()
            db_conn_config['database'] = DB_NAME
            return mysql.connector.connect(**db_conn_config)
        except mysql.connector.Error as err:
            print(f"连接到数据库 {DB_NAME} 失败: {err}")
            return None

    def ensure_database_and_table(self):
        server_cnx = self._connect_server()
        if not server_cnx:
            print("无法连接到MySQL服务器，请检查配置和服务器状态。")
            raise ConnectionError("无法连接到MySQL服务器")

        cursor = server_cnx.cursor()
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8 COLLATE utf8_general_ci")
            print(f"数据库 '{DB_NAME}' 已确保存在。")
        except mysql.connector.Error as err:
            print(f"创建数据库 '{DB_NAME}' 失败: {err}")
            cursor.close()
            server_cnx.close()
            raise
        cursor.close()
        server_cnx.close()

        self.cnx = self._connect_db()
        if not self.cnx:
            print(f"无法连接到数据库 {DB_NAME}，即使它可能已创建。")
            raise ConnectionError(f"无法连接到数据库 {DB_NAME}")

        self.create_table_if_not_exists()

    def _get_connection(self):
        if self.cnx is None or not self.cnx.is_connected():
            self.cnx = self._connect_db()
            if self.cnx is None:
                print("数据库连接丢失且无法重建！")
                raise ConnectionError("数据库连接丢失且无法重建！")
        return self.cnx

    def execute_query(self, query, params=None, fetch=False, multi=False, is_ddl=False):
        cnx = self._get_connection()
        cursor = cnx.cursor()
        try:
            cursor.execute(query, params)
            if is_ddl or query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                cnx.commit()
                if query.strip().upper().startswith("INSERT") and cursor.lastrowid:
                    return cursor.lastrowid
                return True
            if fetch:
                return cursor.fetchall() if multi else cursor.fetchone()
            return True
        except mysql.connector.Error as err:
            print(f"数据库查询错误: {err}")
            try:
                executed_query = cursor.statement if cursor._executed else "无法获取执行的查询语句"
                print(f"查询语句: {executed_query}")
            except Exception as e:
                print(f"无法打印查询语句: {e}")
            cnx.rollback()
            return False
        finally:
            cursor.close()

    def create_table_if_not_exists(self):
        # Create vacations table
        create_vacation_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{VACATION_TABLE}` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vacation_date DATE NOT NULL UNIQUE,
            remarks VARCHAR(255) CHARACTER SET utf8 COLLATE utf8_general_ci,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason_for_deletion VARCHAR(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;
        """
        self.execute_query(create_vacation_table_query, is_ddl=True)

        # Create meetings table
        create_meeting_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{MEETING_TABLE}` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            meeting_date DATE NOT NULL UNIQUE,
            content TEXT CHARACTER SET utf8 COLLATE utf8_general_ci,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;
        """
        self.execute_query(create_meeting_table_query, is_ddl=True)

        # Ensure columns exist (optional for robustness)
        check_remarks_query = f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{DB_NAME}' 
        AND TABLE_NAME = '{VACATION_TABLE}' 
        AND COLUMN_NAME = 'remarks';
        """
        if not self.execute_query(check_remarks_query, fetch=True):
            alter_vacation_query = f"""
            ALTER TABLE `{VACATION_TABLE}` 
            ADD COLUMN remarks VARCHAR(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL AFTER vacation_date;
            """
            self.execute_query(alter_vacation_query, is_ddl=True)

    def add_vacation(self, date_obj, remarks):
        query = f"INSERT INTO `{VACATION_TABLE}` (vacation_date, remarks) VALUES (%s, %s)"
        try:
            if isinstance(date_obj, str):
                date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()
            return self.execute_query(query, (date_obj, remarks))
        except mysql.connector.IntegrityError:
            print(f"日期 {date_obj} 的休假记录已存在。")
            return False
        except ValueError:
            print(f"提供的日期格式不正确: {date_obj}")
            return False

    def get_vacation_by_date(self, date_obj):
        query = f"SELECT remarks FROM `{VACATION_TABLE}` WHERE vacation_date = %s"
        if isinstance(date_obj, str):
            date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()
        return self.execute_query(query, (date_obj,), fetch=True)

    def get_vacations_in_range(self, start_date, end_date):
        query = f"SELECT vacation_date, remarks FROM `{VACATION_TABLE}` WHERE vacation_date BETWEEN %s AND %s ORDER BY vacation_date"
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        return self.execute_query(query, (start_date, end_date), fetch=True, multi=True)

    def get_all_vacations_for_export(self):
        query = f"SELECT vacation_date, remarks, created_at FROM `{VACATION_TABLE}` ORDER BY vacation_date"
        results = self.execute_query(query, fetch=True, multi=True)
        if results:
            return [(r[0].strftime('%Y-%m-%d'), r[1], r[2].strftime('%Y-%m-%d %H:%M:%S') if isinstance(r[2], datetime.datetime) else r[2]) for r in results]
        return []

    def get_recent_vacations(self, days_span=365):
        start_date = (datetime.date.today() - datetime.timedelta(days=days_span))
        query = f"""
        SELECT vacation_date, remarks
        FROM `{VACATION_TABLE}`
        WHERE vacation_date >= %s
        ORDER BY vacation_date DESC
        """
        results = self.execute_query(query, (start_date,), fetch=True, multi=True)
        if results:
            return [(r[0].strftime('%Y-%m-%d'), r[1]) for r in results]
        return []

    def delete_vacation(self, date_obj, reason=""):
        query_update_reason = f"UPDATE `{VACATION_TABLE}` SET reason_for_deletion = %s WHERE vacation_date = %s"
        query_delete = f"DELETE FROM `{VACATION_TABLE}` WHERE vacation_date = %s"
        
        if isinstance(date_obj, str):
            date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()

        # self.execute_query(query_update_reason, (reason, date_obj)) # Optional: log reason
        return self.execute_query(query_delete, (date_obj,))

    def add_meeting(self, date_obj, content):
        query = f"INSERT INTO `{MEETING_TABLE}` (meeting_date, content) VALUES (%s, %s)"
        try:
            if isinstance(date_obj, str):
                date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()
            return self.execute_query(query, (date_obj, content))
        except mysql.connector.IntegrityError:
            print(f"日期 {date_obj} 的会议记录已存在。")
            return False
        except ValueError:
            print(f"提供的日期格式不正确: {date_obj}")
            return False

    def get_meeting_by_date(self, date_obj):
        query = f"SELECT content FROM `{MEETING_TABLE}` WHERE meeting_date = %s"
        if isinstance(date_obj, str):
            date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()
        return self.execute_query(query, (date_obj,), fetch=True)

    def get_meetings_in_range(self, start_date, end_date):
        query = f"SELECT meeting_date, content FROM `{MEETING_TABLE}` WHERE meeting_date BETWEEN %s AND %s ORDER BY meeting_date"
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        return self.execute_query(query, (start_date, end_date), fetch=True, multi=True)

    def get_recent_meetings(self):
        start_date = datetime.date.today() - datetime.timedelta(days=30)  # Past 1 month
        end_date = datetime.date.today() + datetime.timedelta(days=365)   # Next 1 year
        query = f"""
        SELECT meeting_date, content
        FROM `{MEETING_TABLE}`
        WHERE meeting_date BETWEEN %s AND %s
        ORDER BY meeting_date DESC
        """
        results = self.execute_query(query, (start_date, end_date), fetch=True, multi=True)
        if results:
            return [(r[0].strftime('%Y-%m-%d'), r[1]) for r in results]
        return []

    def delete_meeting(self, date_obj):
        query = f"DELETE FROM `{MEETING_TABLE}` WHERE meeting_date = %s"
        if isinstance(date_obj, str):
            date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()
        return self.execute_query(query, (date_obj,))

    def close(self):
        if self.cnx and self.cnx.is_connected():
            self.cnx.close()
            print("数据库连接已关闭。")

    def __del__(self):
        self.close()
