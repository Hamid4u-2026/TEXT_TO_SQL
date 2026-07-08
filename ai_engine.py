import os
import sqlite3
from importlib import import_module
from langchain_community.llms import HuggingFaceHub
from langchain_core.prompts import PromptTemplate

def initialize_database_if_not_exists():
    """Initializes the SQLite database with English records for 20 students."""
    db_name = "university.db"
    if os.path.exists(db_name):
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create Tables
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

    # Populate English Data
    departments = [("AI",), ("Computer Science",), ("Software Engineering",)]
    cursor.executemany("INSERT INTO Departments (department_name) VALUES (?);", departments)

    courses = [
        ("Intro to AI", 3),
        ("Data Structures", 4),
        ("Databases", 3),
        ("Systems Analysis", 3)
    ]
    cursor.executemany("INSERT INTO Courses (course_name, credit_hours) VALUES (?, ?);", courses)

    students = [
        ("Ahmed Al-Majed", 1), ("Sara Al-Ali", 1), ("Khaled Al-Shammari", 1), ("Reem Al-Qahtani", 1), ("Omar Al-Farooq", 1), ("Fatima Al-Zahra", 1), ("Ziad Al-Harbi", 1),
        ("Mohammed Al-Otaibi", 2), ("Noura Al-Dossari", 2), ("Abdullah Al-Shehri", 2), ("Hind Al-Fahad", 2), ("Sultan Al-Mutairi", 2), ("Mona Al-Tamimi", 2),
        ("Faisal Al-Sudairy", 3), ("Amal Abdullah", 3), ("Saud Al-Meshal", 3), ("Shahad Al-Salem", 3), ("Hassan Al-Youssef", 3), ("Rana Al-Jaber", 3), ("Tarek Al-Eissa", 3)
    ]
    cursor.executemany("INSERT INTO Students (student_name, department_id) VALUES (?, ?);", students)

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
    cursor.executemany("INSERT INTO Enrollments (student_id, course_id, grade_numeric, grade_letter) VALUES (?, ?, ?, ?);", enrollments)
    
    conn.commit()
    conn.close()

def get_llm_engine():
    """Initializes HuggingFaceHub Inference Client."""
    token = os.environ.get("HF_TOKEN")
    if not token:
        try:
            streamlit_mod = import_module("streamlit")
            if hasattr(streamlit_mod, "secrets") and "HF_TOKEN" in streamlit_mod.secrets:
                token = streamlit_mod.secrets["HF_TOKEN"]
        except ImportError:
            pass
        
    if not token:
        raise ValueError("Token HF_TOKEN not found.")

    os.environ["HUGGINGFACEHUB_API_TOKEN"] = token
    return HuggingFaceHub(
        repo_id="Qwen/Qwen2.5-Coder-7B-Instruct",
        model_kwargs={"temperature": 0.1, "max_new_tokens": 100},
        api_key=token
    )

def generate_sql_query(user_question):
    """Generates a strict and clean SQL query from English text input."""
    initialize_database_if_not_exists()
    llm = get_llm_engine()

    prompt_template = """You are a precise text-to-SQL translator. Convert the user's question into a valid, executable SQLite query.
Output ONLY the raw SQL code. No markdown blocks, no commentary, no triple backticks.

Database Tables and Columns:
1. Departments: department_id, department_name
2. Students: student_id, student_name, department_id
3. Courses: course_id, course_name, credit_hours
4. Enrollments: enrollment_id, student_id, course_id, grade_numeric, grade_letter

Question: {question}
SQL:"""

    prompt = PromptTemplate(input_variables=["question"], template=prompt_template)
    raw_response = llm.invoke(prompt.format(question=user_question))
    
    # Clean output strictly
    sql_query = raw_response.strip()
    if "```sql" in sql_query:
        sql_query = sql_query.split("```sql")[-1].split("```")[0].strip()
    elif "```" in sql_query:
        sql_query = sql_query.split("```")[1].strip()

    if "SELECT" in sql_query:
        sql_query = "SELECT" + sql_query.split("SELECT", 1)[1]

    sql_query = sql_query.split("\n")[0].strip()
    
    if sql_query.endswith(";"):
        sql_query = sql_query[:-1].strip()
        
    return sql_query
