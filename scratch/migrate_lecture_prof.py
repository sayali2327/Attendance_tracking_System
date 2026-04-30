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
        ALTER TABLE lecture
        ADD prof_id INT,
        ADD FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE CASCADE;
    """)
    conn.commit()
    print("LECTURE PROF_ID MIGRATION SUCCESSFUL")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
