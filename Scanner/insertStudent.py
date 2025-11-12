import mysql.connector

# Konfig (ANPASSEN!)
DB_CONFIG = {
    'host': "localhost",
    'user': "user",
    'password': "1234",
    'database': "students_db"
}

# SQL
SQL_INSERT = "INSERT INTO compare_student (id_student, full_name) VALUES (%s, %s)"

def add_student(student_id, student_name):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("Füge ein...")

    data = (student_id, student_name)
    cursor.execute(SQL_INSERT, data)
    conn.commit()
    
    print("OK.")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    
    # Daten
    NEUE_ID = 1
    NEUER_NAME = "Test.test" 
    
    add_student(NEUE_ID, NEUER_NAME)