import os
import sqlite3
from langchain_community.llms import HuggingFaceHub
from langchain_core.prompts import PromptTemplate

def initialize_database_if_not_exists():
    """
    تتحقق هذه الدالة من وجود قاعدة البيانات سحابياً، وإذا لم تكن موجودة
    تقوم بإنشائها وتغذيتها ببيانات 20 طالباً تلقائياً لضمان استقرار السيرفر.
    """
    db_name = "university.db"
    if os.path.exists(db_name):
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # إنشاء الجداول الأربعة المترابطة
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

    # ضخ البيانات الأكاديمية (3 أقسام، 4 مواد، و20 طالباً مع درجاتهم بالتفصيل)
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
        ("محمد العتيبي", 2), ("نورة الدوسري", 2), ("عبد الله الشهري", 2), ("هند الفهد", 2), ("sultan المطيري", 2), ("منى التميمي", 2),
        ("فيصل السديري", 3), ("أمل العبد الله", 3), ("سعود المشعل", 3), ("شهد السالم", 3), ("حسن اليوسف", 3), ("رنا الجابر", 3), ("طارق العيسى", 3)
    ]
    cursor.executemany("INSERT INTO Students (student_name, department_id) VALUES (?, ?);", students)

    enrollments = [
        # توزيع الدرجات: درجات متميزة، متوسطة، وحالات رسوب لضمان دقة الاستعلام والبحث
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
    """استدعاء المفتاح الرقمي بأمان وتشغيل نموذج كود كوين السحابي المتخصص."""
    token = os.environ.get("HF_TOKEN")
    if not token:
        import streamlit as st
        token = st.secrets.get("HF_TOKEN")
        
    if not token:
        raise ValueError("⚠️ لم يتم العثور على مفتاح 'HF_TOKEN' في الإعدادات السحابية المحمية.")

    return HuggingFaceHub(
        repo_id="Qwen/Qwen2.5-Coder-7B-Instruct",
        model_kwargs={"temperature": 0.1, "max_new_tokens": 150},
        huggingfacehub_api_token=token
    )

def generate_sql_query(user_question):
    """تحويل السؤال باللغة العربية الفصحى إلى استعلام SQL عبر هندسة الأوامر المتقدمة."""
    initialize_database_if_not_exists()
    llm = get_llm_engine()

    # صياغة قالب الأوامر الصارم (Few-Shot Prompting) باللغة العربية الفصحى
    prompt_template = """Analyse the user question and convert it into a valid SQLite query based on the following database schema. Return only the SQL query, without markdown or formatting.

    Database Schema:
    1. Table "Departments": department_id (INTEGER PRIMARY KEY), department_name (TEXT)
    2. Table "Students": student_id (INTEGER PRIMARY KEY), student_name (TEXT), department_id (INTEGER, FOREIGN KEY)
    3. Table "Courses": course_id (INTEGER PRIMARY KEY), course_name (TEXT), credit_hours (INTEGER)
    4. Table "Enrollments": enrollment_id (INTEGER PRIMARY KEY), student_id (INTEGER, FOREIGN KEY), course_id (INTEGER, FOREIGN KEY), grade_numeric (REAL), grade_letter (TEXT)

    Examples:
    Question: كم عدد الطلاب في قسم علوم حاسوب؟
    SQL: SELECT COUNT(*) FROM Students WHERE department_id = (SELECT department_id FROM Departments WHERE department_name = 'علوم حاسوب');

    Question: أعطني أسماء الطلاب الذين حصلوا على التقدير A في مادة قواعد البيانات.
    SQL: SELECT s.student_name FROM Students s JOIN Enrollments e ON s.student_id = e.student_id JOIN Courses c ON e.course_id = c.course_id WHERE c.course_name = 'قواعد البيانات' AND e.grade_letter = 'A';

    User Question: {question}
    SQL:"""

    prompt = PromptTemplate(input_variables=["question"], template=prompt_template)
    raw_response = llm.invoke(prompt.format(question=user_question))
    
    # تنظيف مخرجات النموذج لضمان كود SQL نقي وجاهز للتنفيذ
    sql_query = raw_response.strip()
    if "```sql" in sql_query:
        sql_query = sql_query.split("```sql")[-1].split("```")[0].strip()
    elif "```" in sql_query:
        sql_query = sql_query.split("```")[1].strip()
    return sql_query
