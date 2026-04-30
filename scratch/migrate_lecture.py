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
        ADD UNIQUE (date, time, location);
    """)
    conn.commit()
    print("LECTURE MIGRATION SUCCESSFUL")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
