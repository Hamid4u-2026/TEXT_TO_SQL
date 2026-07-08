import streamlit as st
import pandas as pd
import sqlite3
from ai_engine import generate_sql_query

# إعدادات الصفحة
st.set_page_config(page_title="مساعد قواعد البيانات الذكي", page_icon="📊", layout="wide")

st.title("📊 مساعد قواعد البيانات الذكي الفصيح (Text-to-SQL)")
st.markdown("اكتب سؤالك باللغة العربية الفصحى أو الإنجليزية واستجوب قاعدة بيانات الجامعة تلقائياً!")

# الشريط الجانبي لبنية قاعدة البيانات
with st.sidebar:
    st.header("📋 بنية قاعدة بيانات الجامعة")
    st.markdown("يمكنك طرح أسئلة تربط وتستعلم عن الجداول التالية:")
    
    st.subheader("1. جدول الطلاب (Students)")
    st.code("الأعمدة: student_id, student_name, department_id")
    
    st.subheader("2. جدول الأقسام (Departments)")
    st.code("الأقسام المتاحة: AI, Computer Science, Software Engineering")
    
    st.subheader("3. جدول المواد الدراسية (Courses)")
    st.code("المواد المتاحة: Intro to AI, Data Structures, Databases, Systems Analysis")
    
    st.subheader("4. جدول الدرجات (Enrollments)")
    st.code("الأعمدة: enrollment_id, student_id, course_id, grade_numeric, grade_letter")

# حقل المدخلات للمستخدم
user_question = st.text_input(
    "اكتب سؤالك هنا باللغة العربية الفصحى:",
    placeholder="مثال: كم عدد الطلاب في قسم علوم حاسوب؟ أو ما متوسط درجات مادة تحليل النظم؟"
)

if user_question:
    with st.spinner("جاري توليد استعلام SQL وفحص قاعدة البيانات..."):
        try:
            # 1. توليد الاستعلام عبر محرك الذكاء الاصطناعي المطور
            sql_query = generate_sql_query(user_question)
            
            # عرض الاستعلام للمطور لمتابعته وضمان جودته
            st.subheader("🤖 استعلام SQL المُولّد تلقائياً:")
            st.code(sql_query, language="sql")
            
            # 2. الاتصال بقاعدة البيانات وتنفيذ الاستعلام
            conn = sqlite3.connect("university_v2.db")
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            # 3. عرض النتائج للمستخدم في جدول منسق
            st.subheader("📊 نتائج الاستعلام:")
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("تم تنفيذ الاستعلام بنجاح، ولكن لا توجد سجلات مطابقة في قاعدة البيانات.")
                
        except Exception as e:
            st.error("❌ عذراً، تعذر تنفيذ الطلب. يرجى صياغة السؤال باللغة العربية الفصحى بشكل أكثر وضوحاً وتوافقاً مع أسماء المواد والأقسام المتاحة.")
