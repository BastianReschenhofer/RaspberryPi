import pandas as pd
import matplotlib.pyplot as plt


file_map = [
    ('testdata0m', 0.0),
    ('testdata0,5m', 0.5),
    ('testdata1m', 1.0),
    ('testdata1,5m', 1.5),
    ('testdata2m', 2.0),
    ('testdata2,5m', 2.5),
    ('testdata3,5m', 3.5)
]
# ---------------------------------

# DataFrame zur Speicherung der Ergebnisse
results_df = pd.DataFrame(columns=['Max. RSSI', 'Min. RSSI', 'Durchschnitt', 'Median'])

print("Starte Datenverarbeitung...")

for file_name, distance in file_map:
    try:
        # Laden der Datei
        df = pd.read_csv(file_name)

        # Sicherstellen, dass 'RSSI_dBm' eine numerische Spalte ist
        df['RSSI_dBm'] = pd.to_numeric(df['RSSI_dBm'], errors='coerce')
        df.dropna(subset=['RSSI_dBm'], inplace=True)

        # Berechnung der Kennzahlen
        max_rssi = df['RSSI_dBm'].max()
        min_rssi = df['RSSI_dBm'].min()
        mean_rssi = df['RSSI_dBm'].mean()
        median_rssi = df['RSSI_dBm'].median()

        # Speichern der Ergebnisse, wobei die Distanz der Index (Zeilenname) ist
        results_df.loc[distance] = {
            'Max. RSSI': max_rssi,
            'Min. RSSI': min_rssi,
            'Durchschnitt': mean_rssi,
            'Median': median_rssi
        }
        print(f"Datei {file_name} (Distanz {distance}m) erfolgreich verarbeitet.")

    except FileNotFoundError:
        print(f"FEHLER: Datei {file_name} nicht gefunden. Wird übersprungen.")
    except KeyError:
        print(f"FEHLER: Spalte 'RSSI_dBm' nicht gefunden in {file_name}. Wird übersprungen.")
    except Exception as e:
        print(f"Ein unbekannter Fehler ist aufgetreten beim Verarbeiten von {file_name}: {e}")

# Distanz (der Index) aufsteigend sortieren
results_df = results_df.sort_index()

print("\n--- Aggregierte Ergebnisse ---")
print(results_df)
# --- Plot-Generierung ---

plt.figure(figsize=(10, 6))

# Plotten der vier Metriken
# Da der Index des DataFrames die Distanz enthält, wird dieser automatisch als X-Achse verwendet.
plt.plot(results_df.index, results_df['Max. RSSI'], marker='o', label='Max. RSSI', color='blue')
plt.plot(results_df.index, results_df['Min. RSSI'], marker='s', label='Min. RSSI', color='orange')
plt.plot(results_df.index, results_df['Durchschnitt'], marker='^', label='Durchschnitt', color='green')
plt.plot(results_df.index, results_df['Median'], marker='D', label='Median', color='red') # Ich habe 'red' für den Median gewählt, um es vom Beispielbild abzuheben

# Beschriftungen und Titel
plt.title('RSSI-Werte in Abhängigkeit von der Distanz')
plt.xlabel('Distanz (m)')
plt.ylabel('RSSI (dBm)')

# Hinzufügen des Gitters
plt.grid(True, linestyle='--', alpha=0.6)

# Legende hinzufügen
plt.legend(title='RSSI Metrik')

# Y-Achse auf typische RSSI-Werte beschränken (optional, aber empfohlen für Übersichtlichkeit)
# Beispiel: plt.ylim(-90, -30)

plt.show()

