import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database Configuration (Hardcoded for localhost/root for now)
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='vit@123$',
            database='attendance_db'
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Use this decorator to protect routes that require login
def login_required(roles_required=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login'))
            if roles_required:
                user_role = session.get('role')
                if isinstance(roles_required, list):
                    if user_role not in roles_required:
                        flash("You don't have permission to view that page.", "danger")
                        return redirect(url_for('login'))
                elif user_role != roles_required:
                    flash("You don't have permission to view that page.", "danger")
                    return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'student':
            return redirect(url_for('student_dashboard'))
        elif session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('professor_dashboard'))
    return redirect(url_for('login'))

# --- AUTHENTICATION ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for('login'))
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            cursor.close()
            conn.close()
            
            flash("Logged in successfully!", "success")
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('professor_dashboard'))
        else:
            flash("Invalid username or password", "danger")
            
        cursor.close()
        conn.close()
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        name = request.form['name']
        email = request.form['email']
        contact_no = request.form.get('contact_no', '')
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection failed. Please ensure MySQL is running and the database is created.", "danger")
            return redirect(url_for('register'))
            
        cursor = conn.cursor()
        
        try:
            # Insert into users
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", 
                           (username, hashed_password, role))
            user_id = cursor.lastrowid
            
            # Insert into respective tables based on role
            if role == 'student':
                # Assuming division is empty for now and no dept
                cursor.execute("INSERT INTO student (std_id, name, contact_no, email) VALUES (%s, %s, %s, %s)",
                               (user_id, name, contact_no, email))
            elif role == 'professor':
                cursor.execute("INSERT INTO professor (prof_id, name, contact_no, email) VALUES (%s, %s, %s, %s)",
                               (user_id, name, contact_no, email))
            
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for('login'))
            
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f"Error during registration: {err}", "danger")
        finally:
            cursor.close()
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# --- STUDENT ROUTES ---

@app.route('/student/dashboard')
@login_required(roles_required=['student'])
def student_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get personal data + department + courses
    cursor.execute("""
        SELECT s.*, d.dept_name 
        FROM student s 
        LEFT JOIN department d ON s.dept_id = d.dept_id 
        WHERE s.std_id = %s
    """, (user_id,))
    student_info = cursor.fetchone()
    
    # Enrolled courses
    cursor.execute("""
        SELECT c.course_name 
        FROM course c 
        JOIN student_course sc ON c.c_id = sc.c_id 
        WHERE sc.std_id = %s
    """, (user_id,))
    courses = cursor.fetchall()
    
    # Aggregate attendance percentage using complex JOIN
    # Attendance summary per course
    cursor.execute("""
        SELECT 
            c.course_name,
            COUNT(l.lec_id) AS total_lectures,
            SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as attended_lectures,
            ROUND((SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) / COUNT(l.lec_id)) * 100, 2) as attendance_percentage
        FROM 
            student_course sc
            JOIN course c ON sc.c_id = c.c_id
            LEFT JOIN lecture l ON c.c_id = l.c_id
            LEFT JOIN attendance a ON a.lec_id = l.lec_id AND a.std_id = %s
        WHERE 
            sc.std_id = %s
        GROUP BY 
            c.c_id
    """, (user_id, user_id))
    attendance_summary = cursor.fetchall()
    
    # Detailed attendance history
    cursor.execute("""
        SELECT c.course_name, l.date, l.time, l.type, a.status 
        FROM student_course sc 
        JOIN course c ON sc.c_id = c.c_id 
        JOIN lecture l ON c.c_id = l.c_id 
        LEFT JOIN attendance a ON a.lec_id = l.lec_id AND a.std_id = %s 
        WHERE sc.std_id = %s 
        ORDER BY l.date DESC, l.time DESC
    """, (user_id, user_id))
    detailed_attendance = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('dashboard_student.html', student=student_info, courses=courses, attendance=attendance_summary, detailed_attendance=detailed_attendance)

@app.route('/student_profile')
@login_required(roles_required=['student'])
def student_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, d.dept_name
        FROM student s
        LEFT JOIN department d ON s.dept_id = d.dept_id
        WHERE s.std_id = %s
    """, (session['user_id'],))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('student_profile.html', student=student)

@app.route('/edit_student_profile')
@login_required(roles_required=['student'])
def edit_student_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student WHERE std_id = %s", (session['user_id'],))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_student_profile.html', student=student)

@app.route('/update_student_profile', methods=['POST'])
@login_required(roles_required=['student'])
def update_student_profile():
    name = request.form['name']
    contact = request.form['contact']
    address = request.form['address']
    division = request.form['division']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE student
            SET name=%s, contact_no=%s, address=%s, division=%s
            WHERE std_id=%s
        """, (name, contact, address, division, session['user_id']))
        conn.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error updating profile: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('student_profile'))

# --- PROFESSOR ROUTES ---

@app.route('/professor/dashboard')
@login_required(roles_required=['professor'])
def professor_dashboard():
    # Simple dashboard with stats or direct links
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM student")
    student_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM course")
    course_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM lecture")
    lecture_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return render_template('dashboard_professor.html', students_count=student_count, courses_count=course_count, lectures_count=lecture_count)

@app.route('/professor_profile')
@login_required(roles_required=['professor'])
def professor_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.*, d.dept_name
        FROM professor p
        LEFT JOIN department d ON p.dept_id = d.dept_id
        WHERE p.prof_id = %s
    """, (session['user_id'],))
    
    prof_info = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('professor_profile.html', professor=prof_info)

@app.route('/edit_professor_profile')
@login_required(roles_required=['professor'])
def edit_professor_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM professor WHERE prof_id = %s", (session['user_id'],))
    data = cursor.fetchone()
    
    # Fetch departments for the dropdown
    cursor.execute("SELECT * FROM department")
    departments = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('edit_professor_profile.html', professor=data, departments=departments)

@app.route('/update_professor_profile', methods=['POST'])
@login_required(roles_required=['professor'])
def update_professor_profile():
    name = request.form['name']
    contact = request.form['contact']
    address = request.form['address']
    qualification = request.form['qualification']
    experience = request.form['experience']
    gender = request.form.get('gender')
    dob = request.form.get('dob')
    joining_date = request.form.get('joining_date')
    dept_id = request.form.get('dept_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE professor
            SET name=%s, contact_no=%s, address=%s,
                qualification=%s, experience=%s, gender=%s,
                dob=%s, joining_date=%s, dept_id=%s
            WHERE prof_id=%s
        """, (name, contact, address, qualification, experience, gender, dob, joining_date, dept_id, session['user_id']))

        conn.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error updating profile: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('professor_profile'))

# --- CRUD for Departments ---
@app.route('/departments', methods=['GET', 'POST'])
@login_required(roles_required=['admin'])
def departments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        dept_name = request.form['dept_name']
        hod_name = request.form['hod_name']
        try:
            cursor.execute("INSERT INTO department (dept_name, hod_name) VALUES (%s, %s)", (dept_name, hod_name))
            conn.commit()
            flash('Department added successfully', 'success')
        except Exception as e:
            flash(f'Error adding department: {e}', 'danger')
        return redirect(url_for('departments'))
        
    cursor.execute("SELECT * FROM department")
    depts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('departments.html', departments=depts)

# --- CRUD for Courses (Subjects) ---
@app.route('/courses', methods=['GET', 'POST'])
@login_required(roles_required=['admin'])
def courses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        course_name = request.form['course_name']
        dept_id = request.form['dept_id']
        try:
            cursor.execute("INSERT INTO course (course_name, dept_id) VALUES (%s, %s)", (course_name, dept_id))
            conn.commit()
            flash('Course added successfully', 'success')
        except Exception as e:
            flash(f'Error adding course: {e}', 'danger')
        return redirect(url_for('courses'))
        
    cursor.execute("SELECT c.*, d.dept_name FROM course c LEFT JOIN department d ON c.dept_id = d.dept_id")
    all_courses = cursor.fetchall()
    cursor.execute("SELECT * FROM department")
    depts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('courses.html', courses=all_courses, departments=depts)

# --- Students assignment to courses/department ---
@app.route('/students', methods=['GET', 'POST'])
@login_required(roles_required=['admin'])
def students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        std_id = request.form['std_id']
        dept_id = request.form['dept_id']
        
        try:
            cursor.execute("UPDATE student SET dept_id = %s WHERE std_id = %s", (dept_id, std_id))
            conn.commit()
            flash('Student updated successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
        return redirect(url_for('students'))

    cursor.execute("""
        SELECT s.std_id, s.name, s.email, d.dept_name 
        FROM student s 
        LEFT JOIN department d ON s.dept_id = d.dept_id
    """)
    students_list = cursor.fetchall()
    
    cursor.execute("SELECT * FROM department")
    depts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('students.html', students=students_list, departments=depts)

# --- Lectures ---
@app.route('/lectures', methods=['GET', 'POST'])
@login_required(roles_required=['admin', 'professor'])
def lectures():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        location = request.form['location']
        type = request.form['type']
        c_id = request.form['c_id']
        
        # Date Validation
        lecture_date = datetime.strptime(date, '%Y-%m-%d').date()
        if lecture_date < datetime.today().date():
            flash('⚠️ Cannot schedule lecture for past date', 'danger')
            return redirect(url_for('lectures'))

        # Check conflict before insertion
        cursor.execute("""
            SELECT * FROM lecture
            WHERE date=%s AND time=%s AND location=%s
        """, (date, time, location))
        existing = cursor.fetchone()

        if existing:
            flash('⚠️ Lecture already scheduled at this location and time', 'danger')
            return redirect(url_for('lectures'))

        try:
            if session.get('role') == 'professor':
                cursor.execute("INSERT INTO lecture (date, time, location, type, c_id, prof_id) VALUES (%s, %s, %s, %s, %s, %s)", 
                               (date, time, location, type, c_id, session['user_id']))
            else:
                cursor.execute("INSERT INTO lecture (date, time, location, type, c_id) VALUES (%s, %s, %s, %s, %s)", 
                               (date, time, location, type, c_id))
            conn.commit()
            flash('Lecture created successfully', 'success')
        except Exception as e:
            flash(f'Error adding lecture: {e}', 'danger')
        return redirect(url_for('lectures'))
        
    if session.get('role') == 'professor':
        cursor.execute("""
            SELECT l.*, c.course_name 
            FROM lecture l 
            JOIN course c ON l.c_id = c.c_id
            WHERE l.prof_id = %s
            ORDER BY l.date DESC, l.time DESC
        """, (session['user_id'],))
    else:
        cursor.execute("""
            SELECT l.*, c.course_name 
            FROM lecture l 
            JOIN course c ON l.c_id = c.c_id
            ORDER BY l.date DESC, l.time DESC
        """)
    all_lectures = cursor.fetchall()
    
    if session.get('role') == 'professor':
        cursor.execute("""
            SELECT c.c_id, c.course_name 
            FROM course c 
            JOIN professor_course pc ON c.c_id = pc.c_id 
            WHERE pc.prof_id = %s
        """, (session['user_id'],))
    else:
        cursor.execute("SELECT * FROM course")
    all_courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('lectures.html', lectures=all_lectures, courses=all_courses)

# --- Record Attendance ---
@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required(roles_required=['admin', 'professor'])
def mark_attendance():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    lec_id = request.args.get('lec_id') or request.form.get('lec_id')
    dept_id = request.args.get('dept_id') or request.form.get('dept_id')
    
    if request.method == 'POST':
        if session.get('role') == 'professor':
            cursor.execute("SELECT prof_id FROM lecture WHERE lec_id = %s", (lec_id,))
            lec_check = cursor.fetchone()
            if not lec_check or lec_check['prof_id'] != session['user_id']:
                flash('Unauthorized access to this lecture.', 'danger')
                return redirect(url_for('mark_attendance'))
                
        # Submit attendance
        statuses = dict(request.form) # std_id -> 'present'/'absent'
        try:
            for key, val in statuses.items():
                if key.startswith('status_'):
                    std_id = key.split('_')[1]
                    # De-duplicate: insert or update existing record logic
                    cursor.execute("""
                        INSERT INTO attendance (std_id, lec_id, status) 
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE status = VALUES(status)
                    """, (std_id, lec_id, val))
            conn.commit()
            flash('Attendance recorded successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
            
        return redirect(url_for('mark_attendance', dept_id=dept_id, lec_id=lec_id))

    cursor.execute("SELECT * FROM department")
    all_departments = cursor.fetchall()
    
    all_lectures = []
    if dept_id:
        if session.get('role') == 'professor':
            cursor.execute("""
                SELECT l.lec_id, l.date, l.time, c.course_name, l.type 
                FROM lecture l 
                JOIN course c ON l.c_id = c.c_id 
                WHERE c.dept_id = %s AND l.prof_id = %s
                ORDER BY l.date DESC
            """, (dept_id, session['user_id']))
        else:
            cursor.execute("""
                SELECT l.lec_id, l.date, l.time, c.course_name, l.type 
                FROM lecture l 
                JOIN course c ON l.c_id = c.c_id 
                WHERE c.dept_id = %s 
                ORDER BY l.date DESC
            """, (dept_id,))
        all_lectures = cursor.fetchall()

    students_for_lecture = []
    lecture_info = None
    if lec_id and dept_id:
        cursor.execute("SELECT * FROM lecture l JOIN course c ON l.c_id = c.c_id WHERE lec_id = %s", (lec_id,))
        lecture_info = cursor.fetchone()
        
        if lecture_info:
            if session.get('role') == 'professor' and lecture_info['prof_id'] != session['user_id']:
                flash('Unauthorized access to this lecture.', 'danger')
                return redirect(url_for('mark_attendance'))
                
            c_id = lecture_info['c_id']
            # Get students enrolled in this course AND belonging to the selected department
            # Refined with professor security check
            cursor.execute("""
                SELECT s.std_id, s.name, a.status, d.dept_name 
                FROM student s
                JOIN student_course sc ON s.std_id = sc.std_id
                JOIN lecture l ON sc.c_id = l.c_id
                LEFT JOIN department d ON s.dept_id = d.dept_id
                LEFT JOIN attendance a ON s.std_id = a.std_id AND a.lec_id = %s
                WHERE l.lec_id = %s AND s.dept_id = %s
                AND l.prof_id = %s
                ORDER BY d.dept_name, s.name
            """, (lec_id, lec_id, dept_id, session['user_id'] if session.get('role') == 'professor' else lecture_info['prof_id']))
            students_for_lecture = cursor.fetchall()
            
    # Fetch historical attendance records unconditionally
    cursor.execute("""
        SELECT s.name, l.date, c.course_name as subject, a.status 
        FROM attendance a
        JOIN student s ON a.std_id = s.std_id
        JOIN lecture l ON a.lec_id = l.lec_id
        JOIN course c ON l.c_id = c.c_id
        ORDER BY l.date DESC
    """)
    attendance_history = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('mark_attendance.html', departments=all_departments, selected_dept_id=str(dept_id) if dept_id else None, lectures=all_lectures, selected_lecture=lecture_info, students=students_for_lecture, history=attendance_history)

# --- Professor Attendance ---
@app.route('/mark_professor_attendance', methods=['GET', 'POST'])
@login_required(roles_required=['admin', 'professor'])
def mark_professor_attendance():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    role = session.get('role')

    # ── PROFESSOR: strict self-only isolation ──────────────────────────────
    if role == 'professor':
        date = request.form.get('date') or request.args.get('date')

        if request.method == 'POST' and 'prof_status_submit' in request.form:
            date_selected = request.form.get('date')
            status = request.form.get(f"status_{session['user_id']}", 'absent')
            # Always use session user_id — never accept prof_id from form
            try:
                cursor.execute("""
                    INSERT INTO professor_attendance (prof_id, date, status)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE status = VALUES(status)
                """, (session['user_id'], date_selected, status))
                conn.commit()
                flash('Your attendance has been recorded.', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error: {e}', 'danger')
            return redirect(url_for('mark_professor_attendance', date=date_selected))

        # Fetch only logged-in professor's info and their existing status for today
        cursor.execute("""
            SELECT p.prof_id, p.name, pa.status
            FROM professor p
            LEFT JOIN professor_attendance pa ON p.prof_id = pa.prof_id AND pa.date = %s
            WHERE p.prof_id = %s
        """, (date, session['user_id']))
        my_record = cursor.fetchone()

        # Fetch only this professor's history
        cursor.execute("""
            SELECT date, status
            FROM professor_attendance
            WHERE prof_id = %s
            ORDER BY date DESC
        """, (session['user_id'],))
        my_history = cursor.fetchall()

        cursor.close()
        conn.close()
        return render_template(
            'mark_professor_attendance.html',
            role='professor',
            my_record=my_record,
            date=date,
            my_history=my_history
        )

    # ── ADMIN: department-level access (unchanged) ─────────────────────────
    dept_id = request.args.get('dept_id') or request.form.get('dept_id')
    date = request.form.get('date') or request.args.get('date')

    if request.method == 'POST' and 'prof_status_submit' in request.form:
        statuses = dict(request.form)
        date_selected = request.form.get('date')
        try:
            for key, val in statuses.items():
                if key.startswith('status_') and key != 'status_submit':
                    prof_id = key.split('_')[1]
                    cursor.execute("""
                        INSERT INTO professor_attendance (prof_id, date, status)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE status = VALUES(status)
                    """, (prof_id, date_selected, val))
            conn.commit()
            flash('Professor attendance recorded successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
        return redirect(url_for('mark_professor_attendance', dept_id=dept_id, date=date_selected))

    cursor.execute("SELECT * FROM department")
    all_departments = cursor.fetchall()

    professors = []
    if dept_id:
        cursor.execute("""
            SELECT p.prof_id, p.name, pa.status
            FROM professor p
            LEFT JOIN professor_attendance pa ON p.prof_id = pa.prof_id AND pa.date = %s
            WHERE p.dept_id = %s
            ORDER BY p.name
        """, (date, dept_id))
        professors = cursor.fetchall()

    cursor.execute("""
        SELECT p.name, pa.date, pa.status
        FROM professor_attendance pa
        JOIN professor p ON pa.prof_id = p.prof_id
        ORDER BY pa.date DESC
    """)
    attendance_history = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template(
        'mark_professor_attendance.html',
        role='admin',
        departments=all_departments,
        selected_dept_id=dept_id,
        date=date,
        professors=professors,
        history=attendance_history
    )

# --- ADMIN ROUTES ---

@app.route('/admin_dashboard')
@login_required(roles_required=['admin'])
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM student")
    student_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM course")
    course_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM department")
    dept_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM professor")
    prof_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return render_template('dashboard_admin.html', students=student_count, courses=course_count, departments=dept_count, professors=prof_count)

@app.route('/assign_course_professor', methods=['GET', 'POST'])
@login_required(roles_required=['admin'])
def assign_course_professor():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM professor")
    professors = cursor.fetchall()
    
    cursor.execute("SELECT * FROM course")
    courses = cursor.fetchall()
    
    # Fetch existing assignments
    cursor.execute("""
        SELECT p.name as prof_name, c.course_name
        FROM professor_course pc
        JOIN professor p ON pc.prof_id = p.prof_id
        JOIN course c ON pc.c_id = c.c_id
        ORDER BY p.name
    """)
    assignments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('assign_course_professor.html', 
                           professors=professors, 
                           courses=courses,
                           assignments=assignments)

@app.route('/save_prof_course', methods=['POST'])
@login_required(roles_required=['admin'])
def save_prof_course():
    prof_id = request.form['prof_id']
    courses = request.form.getlist('courses')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # remove old assignments
        cursor.execute("DELETE FROM professor_course WHERE prof_id=%s", (prof_id,))
        # insert new ones
        for c in courses:
            cursor.execute("""
                INSERT INTO professor_course (prof_id, c_id)
                VALUES (%s, %s)
            """, (prof_id, c))
        conn.commit()
        flash('Professor courses assigned successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('assign_course_professor'))

@app.route('/assign_course', methods=['GET', 'POST'])
@login_required(roles_required=['admin'])
def assign_course():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        std_id = request.form.get('std_id')
        courses = request.form.getlist('courses')
        try:
            cursor.execute("DELETE FROM student_course WHERE std_id = %s", (std_id,))
            for c_id in courses:
                cursor.execute("INSERT INTO student_course (std_id, c_id) VALUES (%s, %s)", (std_id, c_id))
            conn.commit()
            flash('Courses assigned successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error assigning courses: {e}', 'danger')
        return redirect(url_for('assign_course'))
        
    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()
    cursor.execute("SELECT * FROM course")
    all_courses = cursor.fetchall()
    
    # Query provided by user to show student and assigned subjects
    cursor.execute("""
        SELECT s.name, c.course_name
        FROM student s
        JOIN student_course sc ON s.std_id = sc.std_id
        JOIN course c ON sc.c_id = c.c_id
        ORDER BY s.name;
    """)
    assignments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('assign_course.html', students=students, courses=all_courses, assignments=assignments)

@app.route('/professors', methods=['GET', 'POST'])
@login_required(roles_required=['admin'])
def professors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        dept_id = request.form.get('dept_id')
        contact_no = request.form.get('contact_no', '')
        
        # New fields
        address = request.form.get('address')
        qualification = request.form.get('qualification')
        experience = request.form.get('experience')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        joining_date = request.form.get('joining_date')
        
        # validations
        if len(contact_no) > 0 and len(contact_no) < 10:
            flash("Contact number must be at least 10 digits.", "danger")
            return redirect(url_for('professors'))
            
        try:
            exp_val = int(experience) if experience else 0
        except ValueError:
            flash("Experience must be a numeric value.", "danger")
            return redirect(url_for('professors'))
            
        if not "@" in email or "." not in email:
            flash("Invalid email format.", "danger")
            return redirect(url_for('professors'))
        
        hashed_password = generate_password_hash(password)
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", (username, hashed_password, 'professor'))
            user_id = cursor.lastrowid
            
            if not dept_id:
                dept_id = None
                
            cursor.execute("""
                INSERT INTO professor 
                (prof_id, name, email, contact_no, dept_id, address, qualification, experience, gender, dob, joining_date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, name, email, contact_no, dept_id, address, qualification, exp_val, gender, dob, joining_date))
            conn.commit()
            flash('Professor added successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding professor: {e}', 'danger')
        return redirect(url_for('professors'))
        
    cursor.execute("""
        SELECT p.*, d.dept_name 
        FROM professor p 
        LEFT JOIN department d ON p.dept_id = d.dept_id
    """)
    profs = cursor.fetchall()
    
    cursor.execute("SELECT * FROM department")
    departments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('professors.html', professors=profs, departments=departments)

# --- DELETE ROUTES (Admin Only) ---

@app.route('/delete_student/<int:id>')
@login_required(roles_required=['admin'])
def delete_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Note: Foreign keys are SET NULL or CASCADE, so this should work
        # Deleting from users will cascade to student if configured, but let's be explicit if needed.
        # Actually user_id is the PK for student as well.
        cursor.execute("DELETE FROM users WHERE user_id = %s", (id,))
        conn.commit()
        flash('Student deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting student: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('students'))

@app.route('/delete_professor/<int:id>')
@login_required(roles_required=['admin'])
def delete_professor(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (id,))
        conn.commit()
        flash('Professor deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting professor: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('professors'))

@app.route('/delete_department/<int:id>')
@login_required(roles_required=['admin'])
def delete_department(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM department WHERE dept_id = %s", (id,))
        conn.commit()
        flash('Department deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting department: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('departments'))

@app.route('/delete_course/<int:id>')
@login_required(roles_required=['admin'])
def delete_course(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM course WHERE c_id = %s", (id,))
        conn.commit()
        flash('Course deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting course: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('courses'))

@app.route('/delete_lecture/<int:id>')
@login_required(roles_required=['admin'])
def delete_lecture(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM lecture WHERE lec_id = %s", (id,))
        conn.commit()
        flash('Lecture deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting lecture: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('lectures'))

if __name__ == '__main__':
    app.run(debug=True)
