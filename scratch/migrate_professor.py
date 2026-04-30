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
        ALTER TABLE professor
        ADD qualification VARCHAR(100),
        ADD experience INT,
        ADD gender VARCHAR(10),
        ADD dob DATE,
        ADD joining_date DATE;
    """)
    conn.commit()
    print("PROFESSOR MIGRATION SUCCESSFUL")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
