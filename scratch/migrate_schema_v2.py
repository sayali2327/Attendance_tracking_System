"""
Migration script: adds prof_id to lecture table and creates professor_course table
Run this ONCE against your existing attendance_db database.
"""
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='vit@123$',
    database='attendance_db'
)
cursor = conn.cursor()

steps = [
    # 1. Add prof_id column to lecture table (safe if already exists)
    """
    ALTER TABLE lecture
    ADD COLUMN IF NOT EXISTS prof_id INT,
    ADD CONSTRAINT fk_lecture_prof
        FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE SET NULL
    """,

    # 2. Create professor_course table if it doesn't exist
    """
    CREATE TABLE IF NOT EXISTS professor_course (
        prof_id INT,
        c_id    INT,
        PRIMARY KEY (prof_id, c_id),
        FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE CASCADE,
        FOREIGN KEY (c_id)    REFERENCES course(c_id)      ON DELETE CASCADE
    )
    """,
]

for i, sql in enumerate(steps, 1):
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"[OK] Step {i} applied.")
    except mysql.connector.Error as e:
        # 1060 = Duplicate column, 1061 = Duplicate key — both mean already applied
        if e.errno in (1060, 1061, 1050):
            print(f"[SKIP] Step {i} already applied ({e.msg}).")
        else:
            print(f"[ERROR] Step {i} failed: {e}")

cursor.close()
conn.close()
print("\nMigration complete.")
