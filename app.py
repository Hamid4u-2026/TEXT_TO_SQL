import streamlit as st
import pandas as pd
import sqlite3
from ai_engine import generate_sql_query

# Configure Streamlit Page Settings
st.set_page_config(page_title="Text-to-SQL Assistant", page_icon="📊", layout="wide")

st.title("📊 Smart University Database Assistant (Text-to-SQL)")
st.markdown("Ask any question about university students, courses, or grades in plain English, and the AI will query the database for you!")

# Sidebar Schema Information
with st.sidebar:
    st.header("📋 Database Schema")
    st.markdown("You can query data from the following connected tables:")
    
    st.subheader("1. Students Table")
    st.code("Columns: student_id, student_name, department_id")
    
    st.subheader("2. Departments Table")
    st.code("Columns: department_id, department_name\nValues: AI, Computer Science, Software Engineering")
    
    st.subheader("3. Courses Table")
    st.code("Columns: course_id, course_name, credit_hours\nValues: Intro to AI, Data Structures, Databases, Systems Analysis")
    
    st.subheader("4. Enrollments Table")
    st.code("Columns: enrollment_id, student_id, course_id, grade_numeric, grade_letter")

# User Input Layout
user_question = st.text_input(
    "Enter your question here:",
    placeholder="e.g., How many students are in Computer Science department?"
)

if user_question:
    with st.spinner("AI is generating SQL and querying the database..."):
        try:
            # 1. Generate SQL query using the updated AI engine
            sql_query = generate_sql_query(user_question)
            
            # Display the generated SQL code
            st.subheader("🤖 Generated SQL Query:")
            st.code(sql_query, language="sql")
            
            # 2. Execute query against SQLite database
            conn = sqlite3.connect("university.db")
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            # 3. Display Results Table
            st.subheader("📊 Query Results:")
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("The query executed successfully, but returned no matching records.")
                
        except Exception as e:
            st.error("❌ Execution Error: Could not execute the generated query. Please rephrase your question clearly matching table column fields.")
