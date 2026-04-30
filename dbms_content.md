# DBMS Content and Queries - Attendance Management System

This document provides a complete overview of the Database Management System (DBMS) implementation for the Attendance Management System, including the schema design and all SQL queries used in the application.

## 1. Database Schema (MySQL)

The system uses a relational database named `attendance_db` with normalized tables to manage users, students, professors, departments, courses, and attendance records.

### Tables Overview

| Table Name | Description | Key Relationships |
| :--- | :--- | :--- |
| `users` | Stores authentication credentials and roles. | Primary Table |
| `department` | Stores department details and HOD names. | |
| `professor` | Stores professor personal and professional info. | `prof_id` -> `users.user_id`, `dept_id` -> `department.dept_id` |
| `student` | Stores student personal details. | `std_id` -> `users.user_id`, `dept_id` -> `department.dept_id` |
| `course` | Stores subject/course names. | `dept_id` -> `department.dept_id` |
| `student_course` | Many-to-Many mapping for course enrollment. | `std_id` -> `student.std_id`, `c_id` -> `course.c_id` |
| `lecture` | Stores scheduled lecture sessions. | `c_id` -> `course.c_id` |
| `attendance` | Records student attendance status per lecture. | `std_id` -> `student.std_id`, `lec_id` -> `lecture.lec_id` |
| `professor_attendance` | Records professor attendance status per date. | `prof_id` -> `professor.prof_id` |

---

## 2. Table Definitions (DDL)

```sql
-- Users table for Authentication
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'student', 'professor') NOT NULL
);

-- Department table
CREATE TABLE department (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
    hod_name VARCHAR(100) NOT NULL
);

-- Professor table
CREATE TABLE professor (
    prof_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contact_no VARCHAR(15),
    address TEXT,
    qualification VARCHAR(100),
    experience INT,
    gender VARCHAR(10),
    dob DATE,
    joining_date DATE,
    dept_id INT,
    FOREIGN KEY (prof_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES department(dept_id) ON DELETE SET NULL
);

-- Student table
CREATE TABLE student (
    std_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_no VARCHAR(15),
    address TEXT,
    division VARCHAR(10),
    email VARCHAR(100) UNIQUE NOT NULL,
    dept_id INT,
    FOREIGN KEY (std_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES department(dept_id) ON DELETE SET NULL
);

-- Course (Subject) table
CREATE TABLE course (
    c_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES department(dept_id) ON DELETE CASCADE
);

-- Student_Course table (M:N relationship)
CREATE TABLE student_course (
    std_id INT,
    c_id INT,
    PRIMARY KEY (std_id, c_id),
    FOREIGN KEY (std_id) REFERENCES student(std_id) ON DELETE CASCADE,
    FOREIGN KEY (c_id) REFERENCES course(c_id) ON DELETE CASCADE
);

-- Lecture table
CREATE TABLE lecture (
    lec_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    time TIME NOT NULL,
    location VARCHAR(100),
    type VARCHAR(50),
    c_id INT,
    FOREIGN KEY (c_id) REFERENCES course(c_id) ON DELETE CASCADE,
    UNIQUE KEY unique_lecture_slot (date, time, location)
);

-- Attendance table
CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    std_id INT,
    lec_id INT,
    status ENUM('present', 'absent') NOT NULL,
    FOREIGN KEY (lec_id) REFERENCES lecture(lec_id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (std_id, lec_id)
);

-- Professor Attendance table
CREATE TABLE professor_attendance (
    pa_id INT AUTO_INCREMENT PRIMARY KEY,
    prof_id INT,
    date DATE,
    status VARCHAR(10),
    FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE CASCADE,
    UNIQUE KEY unique_prof_attendance (prof_id, date)
);
```

---

## 3. SQL Queries (DML & DQL)

### A. Authentication & Registration
1. **User Login**:
   ```sql
   SELECT * FROM users WHERE username = %s;
   ```
2. **Register User**:
   ```sql
   INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s);
   ```
3. **Link Student/Professor Profile**:
   ```sql
   INSERT INTO student (std_id, name, contact_no, email) VALUES (%s, %s, %s, %s);
   INSERT INTO professor (prof_id, name, contact_no, email) VALUES (%s, %s, %s, %s);
   ```

### B. Student Dashboard
1. **Fetch Student Profile**:
   ```sql
   SELECT s.*, d.dept_name 
   FROM student s 
   LEFT JOIN department d ON s.dept_id = d.dept_id 
   WHERE s.std_id = %s;
   ```
2. **Fetch Enrolled Courses**:
   ```sql
   SELECT c.course_name FROM course c 
   JOIN student_course sc ON c.c_id = sc.c_id 
   WHERE sc.std_id = %s;
   ```
3. **Calculate Attendance Percentage (Complex JOIN & Aggregate)**:
   ```sql
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
       c.c_id;
   ```

### C. Attendance Management
1. **Mark Student Attendance (Upsert)**:
   ```sql
   INSERT INTO attendance (std_id, lec_id, status) 
   VALUES (%s, %s, %s)
   ON DUPLICATE KEY UPDATE status = VALUES(status);
   ```
2. **Fetch Students for a Specific Lecture & Department**:
   ```sql
   SELECT s.std_id, s.name, a.status, d.dept_name 
   FROM student s
   JOIN student_course sc ON s.std_id = sc.std_id
   LEFT JOIN department d ON s.dept_id = d.dept_id
   LEFT JOIN attendance a ON s.std_id = a.std_id AND a.lec_id = %s
   WHERE sc.c_id = %s AND s.dept_id = %s
   ORDER BY d.dept_name, s.name;
   ```
3. **Mark Professor Attendance**:
   ```sql
   INSERT INTO professor_attendance (prof_id, date, status) 
   VALUES (%s, %s, %s)
   ON DUPLICATE KEY UPDATE status = VALUES(status);
   ```

### D. Administrative Controls
1. **Add Department/Course**:
   ```sql
   INSERT INTO department (dept_name, hod_name) VALUES (%s, %s);
   INSERT INTO course (course_name, dept_id) VALUES (%s, %s);
   ```
2. **Assign Courses to Students**:
   ```sql
   DELETE FROM student_course WHERE std_id = %s;
   INSERT INTO student_course (std_id, c_id) VALUES (%s, %s);
   ```
3. **Delete Operations (Cascade Logic)**:
   ```sql
   DELETE FROM users WHERE user_id = %s; -- Deletes Student/Professor profile automatically
   DELETE FROM department WHERE dept_id = %s;
   DELETE FROM course WHERE c_id = %s;
   ```

### E. Analytics & Reporting
1. **Count Statistics for Admin**:
   ```sql
   SELECT COUNT(*) FROM student;
   SELECT COUNT(*) FROM course;
   SELECT COUNT(*) FROM department;
   SELECT COUNT(*) FROM professor;
   ```
2. **Attendance History Log**:
   ```sql
   SELECT s.name, l.date, c.course_name as subject, a.status 
   FROM attendance a
   JOIN student s ON a.std_id = s.std_id
   JOIN lecture l ON a.lec_id = l.lec_id
   JOIN course c ON l.c_id = c.c_id
   ORDER BY l.date DESC;
   ```
