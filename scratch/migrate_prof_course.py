import mysql.connector

def migrate():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='vit@123$',
            database='attendance_db'
        )
        cursor = conn.cursor()
        
        # Create Professor_Course table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professor_course (
                prof_id INT,
                c_id INT,
                PRIMARY KEY (prof_id, c_id),
                FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE CASCADE,
                FOREIGN KEY (c_id) REFERENCES course(c_id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("Table professor_course created successfully.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    migrate()
