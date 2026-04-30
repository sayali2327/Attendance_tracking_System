import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='vit@123$',
        database='attendance_db'
    )
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin', 'student', 'professor') NOT NULL;")
    conn.commit()
    print("MIGRATION SUCCESSFUL")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
