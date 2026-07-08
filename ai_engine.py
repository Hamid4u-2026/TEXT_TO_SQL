import os
import sqlite3
from importlib import import_module
from langchain_community.llms import HuggingFaceHub
from langchain_core.prompts import PromptTemplate

def initialize_database_if_not_exists():
    """التحقق من وجود قاعدة البيانات وضخ بيانات الطلاب تلقائياً."""
    db_name = "university.db"
    if os.path.exists(db_name):
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
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

    departments = [("ذكاء اصطناعي",), ("علوم حاسوب",), ("هندسة برمجيات",)]
    cursor.executemany("INSERT INTO Departments (department_name) VALUES (?);", departments)

    courses = [
        ("مقدمة في الذكاء الاصطناعي", 3),
        ("هياكل البيانات والخوارزميات", 4),
        ("قواعد البيانات", 3),
        ("تحليل وتصميم النظم", 3)
    ]
    cursor.executemany("INSERT INTO Courses (course_name, credit_hours) VALUES (?, ?);", courses)

    students = [
        ("أحمد الماجد", 1), ("سارة العلي", 1), ("خالد الشمري", 1), ("ريم القحطاني", 1), ("عمر الفاروق", 1), ("فاطمة الزهراء", 1), ("زياد الحربي", 1),
        ("محمد العتيبي", 2), ("نورة الدوسري", 2), ("عبد الله الشهري", 2), ("هند الفهد", 2), ("سلطان المطيري", 2), ("منى التميمي", 2),
        ("فيصل السديري", 3), ("أمل العبد الله", 3), ("سعود المشعل", 3), ("شهد السالم", 3), ("حسن اليوسف", 3), ("رنا الجابر", 3), ("طارق العيسى", 3)
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
    """تأمين قراءة المفتاح المشفر الجديد وتمريره لمحرك الاستدلال."""
    token = os.environ.get("HF_TOKEN")
    if not token:
        try:
            streamlit_mod = import_module("streamlit")
            if hasattr(streamlit_mod, "secrets") and "HF_TOKEN" in streamlit_mod.secrets:
                token = streamlit_mod.secrets["HF_TOKEN"]
        except ImportError:
            pass
        
    if not token:
        raise ValueError("⚠️ لم يتم العثور على مفتاح 'HF_TOKEN' في الإعدادات السحابية.")

    os.environ["HUGGINGFACEHUB_API_TOKEN"] = token
    return HuggingFaceHub(
        repo_id="Qwen/Qwen2.5-Coder-7B-Instruct",
        model_kwargs={"temperature": 0.1, "max_new_tokens": 100},
        api_key=token
    )

def generate_sql_query(user_question):
    """توليد كود SQL نقي ومعالجة نصوص الاستجابة بدقة."""
    initialize_database_if_not_exists()
    llm = get_llm_engine()

    prompt_template = """You are a Text-to-SQL translator. Convert the Arabic question into a single executable SQLite query.
Output ONLY the raw SQL code. No markdown code blocks, no explanation.

Database Tables:
1. Departments: department_id, department_name
2. Students: student_id, student_name, department_id
3. Courses: course_id, course_name, credit_hours
4. Enrollments: enrollment_id, student_id, course_id, grade_numeric, grade_letter

Question: {question}
SQL:"""

    prompt = PromptTemplate(input_variables=["question"], template=prompt_template)
    raw_response = llm.invoke(prompt.format(question=user_question))
    
    # تنظيف النص الراجع بشكل صارم
    cleaned_text = raw_response.strip()
    
    if "```sql" in cleaned_text:
        cleaned_text = cleaned_text.split("```sql")[-1].split("```")[0].strip()
    elif "```" in cleaned_text:
        cleaned_text = cleaned_text.split("```")[1].strip()

    if "SELECT" in cleaned_text:
        cleaned_text = "SELECT" + cleaned_text.split("SELECT", 1)[1]

    sql_query = cleaned_text.split("\n")[0].strip()
    
    if sql_query.endswith(";"):
        sql_query = sql_query[:-1].strip()
        
    return sql_query
