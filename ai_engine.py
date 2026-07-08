import os
import sqlite3
from importlib import import_module
from huggingface_hub import InferenceClient

def initialize_database_if_not_exists():
    """Initializes the SQLite database with English records if tables do not exist."""
    db_name = "university_v2.db"
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Students';")
        table_exists = cursor.fetchone()
    except sqlite3.Error:
        table_exists = None

    if table_exists:
        conn.close()
        return

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_name TEXT NOT NULL UNIQUE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        department_id INTEGER,
        FOREIGN KEY (department_id) REFERENCES Departments(department_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL UNIQUE,
        credit_hours INTEGER NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        grade_numeric REAL,
        grade_letter TEXT,
        FOREIGN KEY (student_id) REFERENCES Students(student_id),
        FOREIGN KEY (course_id) REFERENCES Courses(course_id),
        UNIQUE(student_id, course_id)
    );
    """)

    departments = [("AI",), ("Computer Science",), ("Software Engineering",)]
    cursor.executemany("INSERT OR IGNORE INTO Departments (department_name) VALUES (?);", departments)

    courses = [
        ("Intro to AI", 3),
        ("Data Structures", 4),
        ("Databases", 3),
        ("Systems Analysis", 3)
    ]
    cursor.executemany("INSERT OR IGNORE INTO Courses (course_name) VALUES (?, ?);", courses)

    students = [
        ("Ahmed Al-Majed", 1), ("Sara Al-Ali", 1), ("Khaled Al-Shammari", 1), ("Reem Al-Qahtani", 1), ("Omar Al-Farooq", 1), ("Fatima Al-Zahra", 1), ("Ziad Al-Harbi", 1),
        ("Mohammed Al-Otaibi", 2), ("Noura Al-Dossari", 2), ("Abdullah Al-Shehri", 2), ("Hind Al-Fahad", 2), ("Sultan Al-Mutairi", 2), ("Mona Al-Tamimi", 2),
        ("Faisal Al-Sudairy", 3), ("Amal Abdullah", 3), ("Saud Al-Meshal", 3), ("Shahad Al-Salem", 3), ("Hassan Al-Youssef", 3), ("Rana Al-Jaber", 3), ("Tarek Al-Eissa", 3)
    ]
    cursor.executemany("INSERT OR IGNORE INTO Students (student_name, department_id) VALUES (?, ?);", students)

    enrollments = [
        (1, 1, 95.5, "A"), (1, 3, 92.0, "A"),
        (2, 1, 98.0, "A"), (2, 2, 94.0, "A"),
        (8, 2, 91.5, "A"), (14, 4, 96.0, "A"),
        (3, 1, 84.0, "B"), (3, 2, 76.5, "C"),
        (4, 1, 88.0, "B"), (5, 3, 81.0, "B"),
        (9, 2, 85.0, "B"), (10, 2, 73.0, "C"),
        (11, 3, 79.5, "C"), (15, 4, 87.0, "B"),
        (16, 4, 82.0, "B"), (17, 3, 75.0, "C"),
        (6, 1, 45.0, "F"), (7, 2, 52.0, "F"),
        (12, 2, 58.0, "D"), (13, 3, 48.0, "F"),
        (18, 4, 61.0, "D"), (19, 3, 50.0, "F"),
        (20, 4, 55.0, "D")
    ]
    cursor.executemany("INSERT OR IGNORE INTO Enrollments (student_id, course_id, grade_numeric, grade_letter) VALUES (?, ?, ?, ?);", enrollments)
    
    conn.commit()
    conn.close()

def generate_sql_query(user_question):
    """Generates a perfectly cleaned SQLite query supporting both Arabic and English inputs."""
    initialize_database_if_not_exists()
    
    token = os.environ.get("HF_TOKEN")
    if not token:
        try:
            streamlit_mod = import_module("streamlit")
            if hasattr(streamlit_mod, "secrets") and "HF_TOKEN" in streamlit_mod.secrets:
                token = streamlit_mod.secrets["HF_TOKEN"]
        except ImportError:
            pass
            
    if not token:
        raise ValueError("Token HF_TOKEN not found in Streamlit Secrets.")

    client = InferenceClient(token=token)
    
    prompt = f"""You are an elite Text-to-SQL translator for an academic SQLite database.
Convert the user question (which could be in Arabic or English) into a valid, executable SQL query.

CRITICAL MAPPING RULE:
- 'AI' or 'ذكاء اصطناعي' -> 'AI'
- 'Computer Science' or 'علوم حاسوب' -> 'Computer Science'
- 'Software Engineering' or 'هندسة برمجيات' -> 'Software Engineering'
- 'Intro to AI' or 'مقدمة في الذكاء الاصطناعي' -> 'Intro to AI'
- 'Data Structures' or 'هياكل البيانات' -> 'Data Structures'
- 'Databases' or 'قواعد البيانات' -> 'Databases'
- 'Systems Analysis' or 'تحليل النظم' -> 'Systems Analysis'

OUTPUT FORMAT:
Output ONLY the raw SQL code string. Do NOT enclose it in markdown blocks (no ```sql), no commentary, no explanations. It must start directly with SELECT.

Database Schema:
- Departments (department_id, department_name)
- Students (student_id, student_name, department_id)
- Courses (course_id, course_name, credit_hours)
- Enrollments (enrollment_id, student_id, course_id, grade_numeric, grade_letter)

Question: {user_question}
SQL:"""

    response = client.text_generation(
        prompt=prompt,
        model="Qwen/Qwen2.5-Coder-7B-Instruct",
        max_new_tokens=100,
        temperature=0.1
    )
    
    # Advanced strict cleaning for query execution safety
    sql_query = response.strip()
    if "```sql" in sql_query:
        sql_query = sql_query.split("```sql")[-1].split("```")[0].strip()
    elif "```" in sql_query:
        sql_query = sql_query.split("```")[1].strip()

    if "SELECT" in sql_query:
        sql_query = "SELECT" + sql_query.split("SELECT", 1)[1]

    sql_query = sql_query.split("\n")[0].strip()
    if "?" in sql_query:
        sql_query = sql_query.split("?")[0].strip()
    if ";" in sql_query:
        sql_query = sql_query.split(";")[0].strip()
        
    return sql_query
