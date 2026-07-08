import streamlit as st
import sqlite3
import pandas as pd
from ai_engine import generate_sql_query, initialize_database_if_not_exists

# 1. إعداد واجهة الصفحة وتفعيل دعم الاتجاه العربي (RTL)
st.set_page_config(page_title="نظام استعلام قواعد البيانات الذكي", page_icon="🗂️", layout="wide")

st.markdown("""
    <style>
    body, .main, .block-container, div[data-testid="stChatMessage"], .stTextInput, .stDataFrame {
        direction: RTL;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🗂️ مساعد قواعد البيانات الذكي الفصيح (Text-to-SQL)")
st.subheader("اكتب سؤالك باللغة العربية الفصحى واستجوب قاعدة بيانات الجامعة تلقائياً")

# تهيئة قاعدة البيانات سحابياً بشكل تلقائي وآمن
initialize_database_if_not_exists()

# 2. تصميم اللوحة الجانبية لعرض بنية الجداول للمستخدم لمساعدته في صياغة الأسئلة
st.sidebar.title("📊 بنية قاعدة بيانات الجامعة")
st.sidebar.markdown("""
يمكنك طرح أسئلة تربط وتستعلم عن الجداول التالية:
- **الطلاب (Students):** يضم أسماء 20 طالباً وتخصصاتهم الأكاديمية.
- **الأقسام (Departments):** ذكاء اصطناعي، علوم حاسوب، هندسة برمجيات.
- **المواد الدراسية (Courses):** مقدمة في الذكاء الاصطناعي، هياكل البيانات، قواعد البيانات، تحليل النظم.
- **الدرجات والتسجيل (Enrollments):** الدرجات الرقمية والتقديرات الحرفية (A, B, C, D, F).
""")

# 3. حقل إدخال السؤال الرئيسي ونظام معالجة الأخطاء
user_question = st.text_input("اكتب سؤالك هنا باللغة العربية الفصحى:", placeholder="مثال: من هو الطالب صاحب أعلى درجة في مادة قواعد البيانات؟")

if user_question:
    with st.spinner("جاري تحليل السؤال وتوليد استعلام قواعد البيانات سحابياً..."):
        try:
            # استدعاء دالة توليد الاستعلام من المرحلة الثانية
            generated_sql = generate_sql_query(user_question)
            
            # عرض كود SQL المولد بشكل منظم
            st.markdown("### 💻 استعلام SQL المُولد تلقائياً:")
            st.code(generated_sql, language="sql")
            
            # تنفيذ الاستعلام مباشرة داخل قاعدة البيانات السحابية المؤقتة
            conn = sqlite3.connect("university.db")
            df_result = pd.read_sql_query(generated_sql, conn)
            conn.close()
            
            # عرض النتائج المستخرجة في جدول تفاعلي
            st.markdown("### 📊 نتائج الاستعلام الفعلي من قاعدة البيانات:")
            if not df_result.empty:
                st.dataframe(df_result, use_container_width=True)
                st.success(f"✅ تم استخراج {len(df_result)} سجل من البيانات بنجاح.")
            else:
                st.warning("⚠️ نُفّذ الاستعلام بنجاح، ولكن لا توجد سجلات مطابقة لهذا السؤال في قاعدة البيانات الحالية.")
                
        except Exception as e:
            # اعتراض الأخطاء البرمجية بذكاء وعرض رسالة توجيهية فصيحة بدلاً من انهيار التطبيق
            st.error(f"❌ عذراً، تعذر تنفيذ الطلب. يرجى صياغة السؤال باللغة العربية الفصحى بشكل أكثر وضوحاً وتوافقاً مع أسماء المواد والأقسام المتاحة.")
