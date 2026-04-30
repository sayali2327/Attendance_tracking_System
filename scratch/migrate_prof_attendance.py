import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='vit@123$',
        database='attendance_db'
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_attendance (
            pa_id INT AUTO_INCREMENT PRIMARY KEY,
            prof_id INT,
            date DATE,
            status VARCHAR(10),
            FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE CASCADE,
            UNIQUE KEY unique_prof_attendance (prof_id, date)
        );
    """)
    conn.commit()
    print("PROFESSOR ATTENDANCE TABLE CREATED SUCCESSFULLY")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
