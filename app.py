# app.py - Text to SQL Application using Streamlit and Gemini

# Import required libraries
import streamlit as st
import sqlite3
import os
import random
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai

# ====================== Basic Setup ======================

# Load API key from .env file
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Text to SQL Converter",
    page_icon="💬",
    layout="centered"
)

# Initialize Google Gemini API
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"❌ Error initializing Gemini API: {e}")
    st.stop()

# ====================== Database Setup ======================

def init_database():
    """Create database and student table with sample data"""
    conn = sqlite3.connect("student.db")
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS STUDENT (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME TEXT NOT NULL,
            CLASS TEXT NOT NULL,
            SECTION TEXT NOT NULL,
            MARKS INTEGER CHECK(MARKS >= 0 AND MARKS <= 100)
        )
    ''')
    
    # Add sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM STUDENT")
    if cursor.fetchone()[0] == 0:
        students_data = [
            ('Ahmed Mohammed', 'Science', 'A', 85),
            ('Sara Ali', 'Mathematics', 'B', 92),
            ('Mohammed Khalid', 'Science', 'A', 78),
            ('Nora Saad', 'Physics', 'C', 88),
            ('Khalid Omar', 'Mathematics', 'B', 65),
            ('Mona Hassan', 'Science', 'C', 95),
            ('Abdullah Saeed', 'Physics', 'A', 72),
            ('Reem Khaleel', 'Mathematics', 'A', 81)
        ]
        cursor.executemany(
            "INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES (?, ?, ?, ?)",
            students_data
        )
    
    conn.commit()
    conn.close()

# ====================== Helper Functions ======================

def get_gemini_response(question, prompt):
    """Send question to Gemini and get SQL query"""
    try:
        full_prompt = f"{prompt}\n\nUser question: {question}"
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def execute_sql_query(sql_query):
    """Execute SQL query on the database"""
    conn = sqlite3.connect("student.db")
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        # If SELECT query, return results
        if sql_query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            return {"success": True, "columns": columns, "rows": rows}
        else:
            # For INSERT, UPDATE, DELETE commands
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return {"success": True, "message": f"Modified {affected_rows} row(s)"}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

# ====================== UI Design ======================

# Main title
st.title("💬 Text to SQL Converter")
st.markdown("---")

# Define prompt template for the model
PROMPT_TEMPLATE = """
You are an expert in converting English questions to SQL queries!

The database is named STUDENT and contains the STUDENT table with the following columns:
- ID (unique identifier, integer)
- NAME (student name, text)
- CLASS (class name, text)
- SECTION (section, text)
- MARKS (marks, integer from 0 to 100)

Important rules:
1. Use the column names exactly as they are
2. Make sure the query syntax is correct
3. Do not put ``` at the beginning or end
4. Pay attention to case sensitivity in string comparisons

Examples:
Question: "How many students are there?"
SQL: SELECT COUNT(*) FROM STUDENT;

Question: "Show all students in Science class"
SQL: SELECT * FROM STUDENT WHERE CLASS='Science';

Question: "What is the average marks of students in Section A"
SQL: SELECT AVG(MARKS) FROM STUDENT WHERE SECTION='A';

Question: "List students who got more than 80 marks"
SQL: SELECT * FROM STUDENT WHERE MARKS > 80;
"""

# Question input
st.subheader("📝 Enter your question in English")
question = st.text_area(
    "Example: 'Show all students in Science class'",
    height=100,
    placeholder="Type your question here..."
)

# Buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    submit_button = st.button("🚀 Convert to SQL", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)
with col3:
    sample_button = st.button("📋 Random Example", use_container_width=True)

# Random examples
samples = [
    "Show all students in Science class",
    "List students who got more than 80 marks",
    "How many students are in Section B?",
    "What is the average marks of all students?",
    "Show students with their names and marks only",
    "Find students in Mathematics class with marks above 70",
    "Count students in each class",
    "Show all students sorted by marks descending",
    "What is the highest marks in Physics class?",
    "List all students in Section A"
]

# ====================== Application Logic ======================

# Initialize database
init_database()

# Random example button
if sample_button:
    question = random.choice(samples)
    st.session_state['question'] = question
    st.rerun()

# Clear button
if clear_button:
    if 'question' in st.session_state:
        del st.session_state['question']
    st.rerun()

# Use value from session state if exists
if 'question' in st.session_state and not question:
    question = st.session_state['question']

# Convert button
if submit_button and question:
    with st.spinner("⏳ Generating SQL query..."):
        # Get SQL query from Gemini
        sql_query = get_gemini_response(question, PROMPT_TEMPLATE)
        
        # Display the query
        st.subheader("📊 Generated SQL Query")
        st.code(sql_query, language='sql')
        
        # Execute query and show results
        st.subheader("📋 Results")
        result = execute_sql_query(sql_query)
        
        if result["success"]:
            if "columns" in result:  # SELECT query
                if result["rows"]:
                    # Display as table
                    df = pd.DataFrame(result["rows"], columns=result["columns"])
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"✅ Found {len(result['rows'])} row(s)")
                else:
                    st.info("ℹ️ No results found")
            else:  # INSERT/UPDATE/DELETE commands
                st.success(f"✅ {result['message']}")
        else:
            st.error(f"❌ Error executing query: {result['error']}")
            st.info("💡 Try rephrasing your question")

elif submit_button and not question:
    st.warning("⚠️ Please enter a question first")

# ====================== Additional Information ======================

with st.expander("ℹ️ Database Information"):
    st.write("""
    **Table Name:** STUDENT
    
    **Columns:**
    - `ID` - Student ID (auto-generated)
    - `NAME` - Student name
    - `CLASS` - Class name (Science, Mathematics, Physics)
    - `SECTION` - Section (A, B, C)
    - `MARKS` - Marks (0-100)
    
    **Total Records:** 8 students
    """)
    
    # Display table content
    if st.button("Show All Students"):
        result = execute_sql_query("SELECT * FROM STUDENT")
        if result["success"] and "columns" in result:
            df = pd.DataFrame(result["rows"], columns=result["columns"])
            st.dataframe(df, use_container_width=True)

# ====================== Footer ======================

st.markdown("---")
st.caption("🔒 Your API key is stored in .env file | Built with Streamlit + Gemini")
