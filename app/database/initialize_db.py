import os
import sqlite3

def init_db(db_path: str = "./data/enterprise.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    cursor.execute("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            budget FLOAT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            role VARCHAR(50) NOT NULL,
            salary FLOAT NOT NULL,
            department_id INTEGER,
            FOREIGN KEY(department_id) REFERENCES departments(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            credits INTEGER NOT NULL,
            is_online BOOLEAN NOT NULL,
            department_id INTEGER,
            FOREIGN KEY(department_id) REFERENCES departments(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE enrollments (
            student_id INTEGER,
            course_id INTEGER,
            student_count INTEGER NOT NULL,
            enrollment_date DATE,
            PRIMARY KEY(student_id, course_id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            email VARCHAR(50),
            major_dept_id INTEGER,
            FOREIGN KEY(major_dept_id) REFERENCES departments(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            budget FLOAT NOT NULL,
            department_id INTEGER,
            FOREIGN KEY(department_id) REFERENCES departments(id)
        );
    """)

    for i in range(1, 37):
        table_name = f"dummy_table_{i}"
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY,
                dummy_field_1 VARCHAR(50),
                dummy_field_2 INTEGER,
                department_id INTEGER,
                FOREIGN KEY(department_id) REFERENCES departments(id)
            );
        """)

    departments_data = [
        (1, "Engineering", 1200000.0),
        (2, "Human Resources", 250000.0),
        (3, "Sales", 500000.0),
        (4, "Marketing", 300000.0),
        (5, "Finance", 450000.0),
    ]
    cursor.executemany("INSERT INTO departments VALUES (?, ?, ?)", departments_data)

    employees_data = [
        (1, "Alice Smith", "Software Engineer", 110000.0, 1),
        (2, "Bob Jones", "QA Engineer", 85000.0, 1),
        (3, "Charlie Brown", "HR Specialist", 65000.0, 2),
        (4, "Diana Prince", "VP Engineering", 180000.0, 1),
        (5, "Evan Wright", "Sales Executive", 95000.0, 3),
    ]
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", employees_data)

    courses_data = [
        (101, "Introduction to Computer Science", 4, 0, 1),
        (102, "Advanced Software Engineering", 4, 1, 1),
        (103, "Database Systems", 3, 0, 1),
        (104, "Human Resource Management", 3, 1, 2),
        (105, "Sales Strategy", 3, 0, 3),
    ]
    cursor.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?)", courses_data)

    enrollments_data = [
        (1, 101, 120, "2026-01-15"),
        (2, 102, 85, "2026-01-16"),
        (3, 103, 110, "2026-01-17"),
        (4, 104, 45, "2026-01-18"),
        (5, 105, 60, "2026-01-19"),
    ]
    cursor.executemany("INSERT INTO enrollments VALUES (?, ?, ?, ?)", enrollments_data)

    students_data = [
        (1, "John Doe", "john.doe@example.com", 1),
        (2, "Jane Doe", "jane.doe@example.com", 1),
        (3, "Jim Beam", "jim.beam@example.com", 2),
        (4, "Jack Daniels", "jack.daniels@example.com", 3),
        (5, "Johnny Walker", "johnny.walker@example.com", 4),
    ]
    cursor.executemany("INSERT INTO students VALUES (?, ?, ?, ?)", students_data)

    projects_data = [
        (1, "AI Agent Development", 150000.0, 1),
        (2, "CRM Migration", 75000.0, 3),
        (3, "Brand Redesign", 50000.0, 4),
    ]
    cursor.executemany("INSERT INTO projects VALUES (?, ?, ?, ?)", projects_data)

    conn.commit()
    conn.close()
    print("Database initialized with 42 tables.")

if __name__ == "__main__":
    init_db()
