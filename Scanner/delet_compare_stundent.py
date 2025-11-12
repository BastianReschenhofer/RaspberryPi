import mysql.connector
from mysql.connector import Error
import sys

DB_CONFIG = {
    'host': "localhost",
    'user': "user",
    'password': "1234",
    'database': "students_db"
}

DELETE_SQL = "DELETE FROM compare_stundent"

def delete_timeline_table():
    conn = None
    
    print(f"Lösche Zeilen aus {DB_CONFIG['database']}...")

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        
        if conn.is_connected():
            cursor = conn.cursor()
            
            cursor.execute(DELETE_SQL)
            
            conn.commit()
            
            print("ERFOLG: Alle Zeilen gelöscht (DELETE FROM).")
            
        else:
            print("FEHLER: Keine DB-Verbindung.")

    except Error as e:
        print(f"FEHLER: {e}")
        if conn:
            conn.rollback()
            
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    try:
        delete_timeline_table()
    except Exception as e:
        print(f"FEHLER: {e}")
        sys.exit(1)