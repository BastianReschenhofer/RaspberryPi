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
SQL_SELECT_ID = "SELECT id_student FROM compare_student WHERE hash_code = %s"

SQL_SELECT_STUDENT = "SELECT id_student, full_name FROM compare_student WHERE hash_code = %s"

SQL_INSERT_TIMELINE = "INSERT INTO student_timeline (id_student, rssi_dbm, timestamp) VALUES (%s, %s, %s)"


# BLE/CSV
TARGET_MANUFACTURING_DATA = "0011" 
OUTPUT_FILE = "ble_sniffer_data.csv"
CSV_HEADER = ["Timestamp", "RSSI_dBm", "Manufacturing_Data_ASCII", "ID_Name"]

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.conn = None 

    def _get_db_connection(self):
        try:
            #Überprüft ob bestehende Verbindung 
            if self.conn and self.conn.is_connected(): 
                self.conn.ping(reconnect=True, attempts=3, delay=2)
                return self.conn
            
            #Neu verbinden
            self.conn = mysql.connector.connect(**DB_CONFIG)
            return self.conn
        except Error:
            print("DB-Fehler beim Verbinden")
            return None

    def _handle_database_ops(self, hash_to_lookup, rssi, timestamp):
        conn = self._get_db_connection()
        cursor = None
        
        if conn is None:
            return "Keine DB-Verbindung"

        try:
            cursor = conn.cursor()
            
            # Suche ID und Name basierend auf dem empfangenen Hash
            cursor.execute(SQL_SELECT_STUDENT, (hash_to_lookup,))
            result = cursor.fetchone()

            if result:
                student_id, full_name = result
                
                # Speichere den Scan in der Timeline-Tabelle
                data_to_insert = (student_id, rssi, timestamp)
                cursor.execute(SQL_INSERT_TIMELINE, data_to_insert)
                conn.commit()
                
                print(f"DB-OK: Student {full_name} erkannt")
                return full_name # Rückgabe für die CSV
            else:
                print(f"Hash {hash_to_lookup} unbekannt")
                return "Unbekannter Hash"

        except Error as e:
            print(f"SQL-Fehler: {e}")
            return "Fehler"
        finally:
            if cursor:
                cursor.close()


    def handleDiscovery(self, dev, isNewDev, isNewData):
        rssi = dev.rssi
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        manuf_data_hex = dev.getValueText(0xFF)

        if manuf_data_hex and manuf_data_hex.startswith(TARGET_MANUFACTURING_DATA):

            raw_hex_payload = manuf_data_hex[4:]
    
            try:
                
                byte_data = binascii.unhexlify(raw_hex_payload)
                received_hash = byte_data.decode('ascii').strip().upper()
        
                print(f"Hash (dekodiert): {received_hash}")

                full_name_for_csv = self._handle_database_ops(received_hash, rssi, timestamp)

            except (binascii.Error, UnicodeDecodeError) as e:
                print(f"Dekodierungsfehler: {e}")
            
            
            full_name_for_csv = self._handle_database_ops(received_hash, rssi, timestamp)
            
    
    
            data_row = [timestamp, rssi, received_hash, full_name_for_csv]
            
            # CSV schreiben
            try:
                file_is_empty = not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0
                with open(OUTPUT_FILE, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    if file_is_empty:
                        writer.writerow(CSV_HEADER)
                    writer.writerow(data_row)
                print(f"CSV-OK (Gefunden: {full_name_for_csv})")
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
        print("Faaataaaleesss Probleme")
        sys.exit(1)