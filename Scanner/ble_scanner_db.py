import sys
import datetime
import time
import csv 
import os 
import binascii
from bluepy.btle import Scanner, DefaultDelegate
import mysql.connector
from mysql.connector import Error 

# Konfig
DB_CONFIG = {
    'host': "localhost",
    'user': "user",
    'password': "1234",
    'database': "students_db"
}

# SQL
SQL_SELECT_ID = "SELECT id_student FROM compare_student WHERE full_name = %s"
SQL_INSERT_TIMELINE = "INSERT INTO student_timeline (id_student, rssi_dbm, timestamp) VALUES (%s, %s, %s)"

# BLE/CSV
TARGET_MANUFACTURING_DATA = "0011" 
OUTPUT_FILE = "ble_sniffer_data.csv"
CSV_HEADER = ["Timestamp", "RSSI_dBm", "Manufacturing_Data_ASCII", "ID_Name"]

# Delegate
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def _get_db_connection(self):
        # Verbinde
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            if conn and conn.is_connected():
                return conn
            else:
                return None
        except Error:
            print("DB-Fehler")
            return None

    def _handle_database_ops(self, name_for_lookup, rssi, timestamp):
        # DB
        conn = None
        cursor = None
        
        try:
            conn = self._get_db_connection()
            if conn is None:
                return name_for_lookup 

            cursor = conn.cursor()
            
            # ID
            cursor.execute(SQL_SELECT_ID, (name_for_lookup,))
            result = cursor.fetchone()

            if result:
                student_id = result[0] 
                
                # Speichern
                data_to_insert = (student_id, rssi, timestamp)
                cursor.execute(SQL_INSERT_TIMELINE, data_to_insert)
                conn.commit()
                print("DB-OK")
                return student_id 
            else:
                return name_for_lookup 

        except Error:
            print("SQL-Fehler")
            if conn:
                conn.rollback() 
            return name_for_lookup 

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()


    def handleDiscovery(self, dev, isNewDev, isNewData):
        rssi = dev.rssi
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        manuf_data_hex = dev.getValueText(0xFF)

        if manuf_data_hex and manuf_data_hex.startswith(TARGET_MANUFACTURING_DATA):
            
            trimmed_data = manuf_data_hex[4:]
            try:
                byte_data = binascii.unhexlify(trimmed_data)
                ascii_data = byte_data.decode('ascii').strip() 
            except (binascii.Error, UnicodeDecodeError):
                return

            # DB/CSV-Daten
            id_or_name_for_csv = self._handle_database_ops(ascii_data, rssi, timestamp)
            
            data_row = [timestamp, rssi, ascii_data, id_or_name_for_csv]
            
            # CSV
            try:
                file_is_empty = not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0
                
                with open(OUTPUT_FILE, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    
                    if file_is_empty:
                        writer.writerow(CSV_HEADER)
                        
                    writer.writerow(data_row)
                    
                print("CSV-OK")
                
            except Exception:
                print("CSV-Fehler")

# Haupt
def run_sniffer():
    print("Start")
    
    scanner = Scanner().withDelegate(ScanDelegate())
    
    while True:
        try:
            scanner.scan(10.0) 
            
        except Exception:
            print("Scan-Fehler")
            time.sleep(5)

if __name__ == "__main__":
    try:
        run_sniffer()
    except KeyboardInterrupt:
        print("Ende")
        sys.exit(0)
    except Exception:
        print("Fatal")
        sys.exit(1)