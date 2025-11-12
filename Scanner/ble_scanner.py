import sys
import datetime
import time
import csv 
import os 
import binascii
from bluepy.btle import Scanner, DefaultDelegate

# Präfix
TARGET_MANUFACTURING_DATA = "0011" 

# Datei
OUTPUT_FILE = "ble_sniffer_data.csv"

# Header
CSV_HEADER = ["Timestamp", "RSSI_dBm", "Manufacturing_Data", "Name"]

# Delegate
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        # RSSI
        rssi = dev.rssi
        
        # Name
        name = dev.getValueText(0x09)
        if name is None:
            name = dev.getValueText(0x08) 
            if name is None:
                name = "Unbekannt"
        
        # Daten
        manuf_data_hex = dev.getValueText(0xFF)

        # Filter
        if manuf_data_hex and manuf_data_hex.startswith(TARGET_MANUFACTURING_DATA):
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Trim
            trimmed_data = manuf_data_hex[4:]
            
            # Bytes
            try:
                byte_data = binascii.unhexlify(trimmed_data)
                
                # ASCII
                ascii_data = byte_data.decode('ascii')
            except (binascii.Error, UnicodeDecodeError):
                return # Abbruch

            data_row = [timestamp, rssi, ascii_data, name]
            
            # Speichern
            try:
                # Prüfen
                file_is_empty = not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0
                
                # Öffnen
                with open(OUTPUT_FILE, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Header
                    if file_is_empty:
                        writer.writerow(CSV_HEADER)
                        
                    writer.writerow(data_row)
                    
                # Ausgabe
                log_entry = f"[{timestamp}], Manuf. Data: {manuf_data_hex}, RSSI: {rssi} dBm"
                print(f"Gespeichert: {log_entry}")
                
            except Exception:
                print("CSV-Fehler")

# Haupt
def run_sniffer():
    print("Start")
    
    scanner = Scanner().withDelegate(ScanDelegate())
    
    while True:
        try:
            # Scan
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