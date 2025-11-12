## Datenbank und Tables erstellen

cd DB

sudo apt install mariadb-server mariadb-client -y
sudo mysql_secure_installation

sudo mysql -u root -p

CREATE DATABASE students_db; 

CREATE USER 'user'@'localhost' IDENTIFIED BY '1234';

GRANT ALL PRIVILEGES ON ble_tracking_db.* TO 'user'@'localhost';

FLUSH PRIVILEGES;

USE students_db;

CREATE TABLE compare_stundent (
    id_student INT NOT NULL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL UNIQUE COMMENT 'Name, der aus den ASCII-Daten des BLE-Beacons gelesen wird',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE studend_timeline (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    id_student INT NOT NULL COMMENT 'Studenten-ID aus der compare_stundent-Tabelle',
    rssi_dbm INT NOT NULL COMMENT 'Signalstärke des Scans',
    timestamp DATETIME NOT NULL COMMENT 'Zeitpunkt des Scans',
    FOREIGN KEY (id_student) REFERENCES compare_stundent(id_student)
);

EXIT;

# # Installs

pip install Flask
pip install Flask-Sqlalchemy
pip install PyMySQL

## Enter Virtual Environment

source [venv:Name]/bin/activate

## Change Tables

ALTER TABLE [Table] 