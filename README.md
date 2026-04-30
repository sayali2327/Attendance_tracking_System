# Attendance Tracking System

A comprehensive web-based application designed to streamline attendance management for educational institutions. Built using **Python (Flask)** and **MySQL**, it provides a robust platform for students, professors, and administrators.

## 🚀 Key Features

### 👤 Role-Based Access Control
- **Admin**: Full control over departments, courses, students, and professors. Handles all core assignments.
- **Professor**: Manage personal profiles, schedule lectures, and mark student attendance for assigned courses.
- **Student**: View personalized dashboards with attendance percentages, detailed history, and profile management.

### 📊 Comprehensive Management
- **Department & Course Management**: CRUD operations for departments and subjects.
- **Attendance Analytics**: Automatic calculation of attendance percentages for students across all enrolled courses.
- **Profile Customization**: Detailed profiles for students and professors with professional and personal information.
- **Lecture Scheduling**: Conflict-aware lecture scheduling system.
- **Professor Attendance**: Mechanism for professors to record their daily attendance.

## 🛠️ Tech Stack
- **Backend**: Python 3.x, Flask
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Authentication**: Werkzeug Security (Password Hashing)

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/sayali2327/Attendance_tracking_System.git
cd Attendance_tracking_System
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Configuration
1. Ensure MySQL is installed and running.
2. Create a database named `attendance_db`.
3. Import the `schema.sql` file:
   ```bash
   mysql -u your_username -p attendance_db < schema.sql
   ```
4. Update the database credentials in `app.py`:
   ```python
   # app.py (Line 14-19)
   conn = mysql.connector.connect(
       host='localhost',
       user='your_username',
       password='your_password',
       database='attendance_db'
   )
   ```

### 5. Run the Application
```bash
python app.py
```
Access the application at `http://127.0.0.1:5000`.

## 📁 Project Structure
```text
├── app.py              # Main Flask application logic
├── schema.sql          # Database schema and initial data
├── requirements.txt    # Project dependencies
├── templates/          # HTML templates (Jinja2)
├── .gitignore          # Files to exclude from Git
└── README.md           # Project documentation
```

## 📜 License
This project is for educational purposes. Feel free to use and modify it!
