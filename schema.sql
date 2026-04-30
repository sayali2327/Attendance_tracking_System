CREATE DATABASE IF NOT EXISTS attendance_db;
USE attendance_db;

-- Users table for Authentication
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'student', 'professor') NOT NULL
);

-- Department table
CREATE TABLE IF NOT EXISTS department (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
    hod_name VARCHAR(100) NOT NULL
);

-- Professor table
CREATE TABLE IF NOT EXISTS professor (
    prof_id INT PRIMARY KEY, -- matches user_id
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
CREATE TABLE IF NOT EXISTS student (
    std_id INT PRIMARY KEY, -- matches user_id
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
CREATE TABLE IF NOT EXISTS course (
    c_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES department(dept_id) ON DELETE CASCADE
);

-- Student_Course table (M:N relationship) composite PK
CREATE TABLE IF NOT EXISTS student_course (
    std_id INT,
    c_id INT,
    PRIMARY KEY (std_id, c_id),
    FOREIGN KEY (std_id) REFERENCES student(std_id) ON DELETE CASCADE,
    FOREIGN KEY (c_id) REFERENCES course(c_id) ON DELETE CASCADE
);

-- Lecture table
CREATE TABLE IF NOT EXISTS lecture (
    lec_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    time TIME NOT NULL,
    location VARCHAR(100),
    type VARCHAR(50), -- e.g., Theory, Practical
    c_id INT,
    prof_id INT,
    FOREIGN KEY (c_id) REFERENCES course(c_id) ON DELETE CASCADE,
    FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE SET NULL,
    UNIQUE KEY unique_lecture_slot (date, time, location)
);

-- Professor_Course table (M:N relationship)
CREATE TABLE IF NOT EXISTS professor_course (
    prof_id INT,
    c_id INT,
    PRIMARY KEY (prof_id, c_id),
    FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE CASCADE,
    FOREIGN KEY (c_id) REFERENCES course(c_id) ON DELETE CASCADE
);

-- Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    std_id INT,
    lec_id INT,
    status ENUM('present', 'absent') NOT NULL,
    FOREIGN KEY (lec_id) REFERENCES lecture(lec_id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (std_id, lec_id) -- A student can only have 1 attendance record per lecture
);

-- Professor Attendance table
CREATE TABLE IF NOT EXISTS professor_attendance (
    pa_id INT AUTO_INCREMENT PRIMARY KEY,
    prof_id INT,
    date DATE,
    status VARCHAR(10),
    FOREIGN KEY (prof_id) REFERENCES professor(prof_id) ON DELETE CASCADE,
    UNIQUE KEY unique_prof_attendance (prof_id, date)
);
