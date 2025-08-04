import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import seaborn as sns
from PIL import Image
import os
from datetime import datetime, timedelta
import io
import base64
import uuid
import hashlib
import random
import plotly.express as px
import plotly.graph_objects as go
import warnings

# Filter warnings
warnings.filterwarnings("ignore")

# Set page configuration
st.set_page_config(
    page_title="نظام إدارة المخازن والمستودعات",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create a connection to the database
conn = sqlite3.connect('inventory.db', check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category_id INTEGER,
        price REAL,
        barcode TEXT,
        image BLOB,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        branch_id INTEGER,
        quantity INTEGER,
        rfid_tag TEXT,
        last_updated TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (branch_id) REFERENCES branches (id)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        branch_id INTEGER,
        quantity INTEGER,
        sale_date TIMESTAMP,
        amount REAL,
        reference TEXT,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (branch_id) REFERENCES branches (id)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        from_branch_id INTEGER,
        to_branch_id INTEGER,
        quantity INTEGER,
        transfer_date TIMESTAMP,
        status TEXT,
        reference TEXT,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (from_branch_id) REFERENCES branches (id),
        FOREIGN KEY (to_branch_id) REFERENCES branches (id)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS rfid_tags (
        id INTEGER PRIMARY KEY,
        tag_id TEXT NOT NULL UNIQUE,
        product_id INTEGER,
        assigned_at TIMESTAMP,
        status TEXT,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        permissions TEXT,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert admin user if not exists
c.execute('SELECT COUNT(*) FROM users WHERE username = "admin"')
if c.fetchone()[0] == 0:
    admin_password = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute('''
        INSERT INTO users (username, password, role, permissions, active)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', admin_password, 'admin', 'view,add,edit,delete,manage_users', 1))

# Check if there's a main branch, create it if not
c.execute('SELECT COUNT(*) FROM branches')
if c.fetchone()[0] == 0:
    c.execute('''
        INSERT INTO branches (name, address, description)
        VALUES (?, ?, ?)
    ''', ('المستودع الرئيسي', 'العنوان الرئيسي', 'المستودع الرئيسي للمخزون'))

conn.commit()

# Helper functions
def get_branch_name(branch_id):
    c.execute('SELECT name FROM branches WHERE id = ?', (branch_id,))
    result = c.fetchone()
    return result[0] if result else "غير معروف"

def get_product_name(product_id):
    c.execute('SELECT name FROM products WHERE id = ?', (product_id,))
    result = c.fetchone()
    return result[0] if result else "غير معروف"

def get_category_name(category_id):
    c.execute('SELECT name FROM categories WHERE id = ?', (category_id,))
    result = c.fetchone()
    return result[0] if result else "غير معروف"

def convert_df_to_csv_download_link(df, filename="data.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">تحميل البيانات كملف CSV</a>'
    return href

def generate_reference_number(prefix="REF"):
    """Generate a unique reference number with a timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8]
    return f"{prefix}-{timestamp}-{random_suffix}"

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username, password):
    hashed_password = hash_password(password)
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    if result:
        return result[0] == hashed_password
    return False

def get_user_permissions(username):
    c.execute('SELECT permissions FROM users WHERE username = ? AND active = 1', (username,))
    result = c.fetchone()
    if result and result[0]:
        return result[0].split(',')
    return []

def get_user_role(username):
    c.execute('SELECT role FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    return result[0] if result else None

# Generate random RFID tag
def generate_rfid_tag():
    """Generate a random RFID tag"""
    return f"RFID-{uuid.uuid4().hex[:12].upper()}"

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'permissions' not in st.session_state:
    st.session_state.permissions = []
if 'role' not in st.session_state:
    st.session_state.role = None
if 'current_branch' not in st.session_state:
    st.session_state.current_branch = 1

# CSS styles for Arabic RTL support
st.markdown("""
<style>
    body {
        direction: rtl;
    }
    .stButton > button {
        float: right;
    }
    .stTextInput > div > div > input {
        text-align: right;
    }
    .stSelectbox > div > div > div {
        text-align: right;
    }
    div.stMarkdown {
        text-align: right;
    }
    .css-1kyxreq, .css-12w0qpk {
        justify-content: right !important;
    }
    th, td {
        text-align: right !important;
    }
    [data-testid="stSidebar"] {
        direction: rtl;
    }
    h1, h2, h3, h4, h5, h6, label {
        text-align: right;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F0F2F6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 10px;
        padding-right: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E0E0E0;
    }
    .card {
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        background-color: #f8f9fa;
        border: 1px solid #eee;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 4px;
        border-left: 5px solid #ffcb3d;
        margin-bottom: 16px;
    }
    .success-box {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 4px;
        border-left: 5px solid #28a745;
        margin-bottom: 16px;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 10px;
        border-radius: 4px;
        border-left: 5px solid #dc3545;
        margin-bottom: 16px;
    }
    .info-box {
        background-color: #e2f0fb;
        padding: 10px;
        border-radius: 4px;
        border-left: 5px solid #0dcaf0;
        margin-bottom: 16px;
    }
    .highlight {
        background-color: #fff5cc;
        padding: 5px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Login page
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("نظام إدارة المخازن")
        st.subheader("تسجيل الدخول")
        
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        
        if st.button("تسجيل الدخول"):
            if username and password:
                if verify_password(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.permissions = get_user_permissions(username)
                    st.session_state.role = get_user_role(username)
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
            else:
                st.warning("الرجاء إدخال اسم المستخدم وكلمة المرور")
        
        st.info("اسم المستخدم الافتراضي: admin، كلمة المرور: admin123")

# Main application
def main_app():
    # Sidebar for navigation
    st.sidebar.title("القائمة الرئيسية")
    if st.session_state.role == 'admin':
        menu = st.sidebar.radio(
            "اختر الوظيفة:",
            ["الرئيسية", "إدارة المنتجات", "إدارة الفئات", "عرض المخزون", "التقارير", "إدارة المبيعات", "رفع بيانات RFID", "إدارة الفروع", "إدارة المستخدمين"]
        )
    else:
        menu = st.sidebar.radio(
            "اختر الوظيفة:",
            ["الرئيسية", "إدارة المنتجات", "إدارة الفئات", "عرض المخزون", "التقارير", "إدارة المبيعات", "رفع بيانات RFID", "إدارة الفروع"]
        )
    
    # User info and logout in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**المستخدم**: {st.session_state.username}")
    st.sidebar.markdown(f"**الصلاحية**: {st.session_state.role}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.permissions = []
        st.session_state.role = None
        st.rerun()
    
    # Branch selection (except for branch management page)
    if menu != "إدارة الفروع":
        st.sidebar.markdown("---")
        st.sidebar.subheader("اختيار الفرع")
        
        # Get all branches
        c.execute("SELECT id, name FROM branches")
        branches = c.fetchall()
        branch_dict = {b[0]: b[1] for b in branches}
        
        if branch_dict:
            selected_branch = st.sidebar.selectbox(
                "اختر الفرع",
                options=list(branch_dict.keys()),
                format_func=lambda x: branch_dict[x],
                index=list(branch_dict.keys()).index(st.session_state.current_branch) if st.session_state.current_branch in branch_dict else 0
            )
            st.session_state.current_branch = selected_branch

    # Main Dashboard
    if menu == "الرئيسية":
        st.title("نظام إدارة المخازن")
        st.write("مرحباً بك في نظام إدارة المخازن. الرجاء اختيار الوظيفة المطلوبة من القائمة الجانبية.")
        
        # Dashboard summary
        col1, col2, col3 = st.columns(3)
        
        # Total products
        c.execute("SELECT COUNT(*) FROM products")
        total_products = c.fetchone()[0]
        col1.metric("إجمالي المنتجات", total_products)
        
        # Total inventory for current branch
        c.execute("SELECT SUM(quantity) FROM inventory WHERE branch_id = ?", (st.session_state.current_branch,))
        total_inventory = c.fetchone()[0]
        if total_inventory is None:
            total_inventory = 0
        col2.metric("إجمالي المخزون في الفرع", total_inventory)
        
        # Total sales for current branch
        c.execute("SELECT SUM(amount) FROM sales WHERE branch_id = ?", (st.session_state.current_branch,))
        total_sales = c.fetchone()[0]
        if total_sales is None:
            total_sales = 0
        col3.metric("إجمالي المبيعات في الفرع", f"{total_sales:.2f} ريال")
        
        # Recent activities
        st.subheader("أحدث الأنشطة")
        
        # Get recent inventory changes
        c.execute('''
            SELECT p.name, i.quantity, b.name, i.last_updated, 'inventory' as activity_type
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            JOIN branches b ON i.branch_id = b.id
            WHERE i.last_updated IS NOT NULL
            ORDER BY i.last_updated DESC
            LIMIT 5
        ''')
        inventory_activities = c.fetchall()
        
        # Get recent sales
        c.execute('''
            SELECT p.name, s.quantity, b.name, s.sale_date, 'sale' as activity_type
            FROM sales s
            JOIN products p ON s.product_id = p.id
            JOIN branches b ON s.branch_id = b.id
            ORDER BY s.sale_date DESC
            LIMIT 5
        ''')
        sales_activities = c.fetchall()
        
        # Combine and sort activities
        all_activities = inventory_activities + sales_activities
        if all_activities:
            all_activities.sort(key=lambda x: x[3] if x[3] else "", reverse=True)
            all_activities = all_activities[:5]
        
        if all_activities:
            activity_data = []
            for activity in all_activities:
                product, quantity, branch, date, activity_type = activity
                if activity_type == 'inventory':
                    activity_str = f"تحديث مخزون {product} في {branch} ({quantity} قطعة)"
                else:
                    activity_str = f"بيع {product} من {branch} ({quantity} قطعة)"
                activity_data.append({"النشاط": activity_str, "التاريخ": date})
            
            df_activities = pd.DataFrame(activity_data)
            st.table(df_activities)
        else:
            st.info("لا توجد أنشطة حديثة")
        
        # Low stock alert
        st.subheader("تنبيهات المخزون")
        c.execute('''
            SELECT p.name, i.quantity, b.name
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            JOIN branches b ON i.branch_id = b.id
            WHERE i.quantity < 10 AND i.branch_id = ?
        ''', (st.session_state.current_branch,))
        low_stock = c.fetchall()
        
        if low_stock:
            st.markdown('<div class="warning-box">تنبيه: يوجد منتجات منخفضة المخزون!</div>', unsafe_allow_html=True)
            low_stock_data = []
            for product, quantity, branch in low_stock:
                low_stock_data.append({"المنتج": product, "الكمية المتبقية": quantity, "الفرع": branch})
            
            df_low_stock = pd.DataFrame(low_stock_data)
            st.table(df_low_stock)
        else:
            st.markdown('<div class="success-box">لا توجد منتجات منخفضة المخزون حالياً.</div>', unsafe_allow_html=True)
        
        # Products and categories summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("إحصائيات الفئات")
            c.execute('''
                SELECT c.name, COUNT(p.id)
                FROM categories c
                LEFT JOIN products p ON c.id = p.category_id
                GROUP BY c.name
                ORDER BY COUNT(p.id) DESC
                LIMIT 10
            ''')
            categories_data = c.fetchall()
            
            if categories_data:
                df_categories = pd.DataFrame(categories_data, columns=["الفئة", "عدد المنتجات"])
                if not df_categories.empty and df_categories["عدد المنتجات"].sum() > 0:
                    fig = px.pie(df_categories, values="عدد المنتجات", names="الفئة", hole=0.4)
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("لا توجد بيانات كافية للرسم البياني")
            else:
                st.info("لا توجد فئات كافية لعرض الرسم البياني")
        
        with col2:
            st.subheader("إحصائيات المبيعات")
            c.execute('''
                SELECT p.name, SUM(s.amount) as total_sales
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE s.branch_id = ?
                GROUP BY p.name
                ORDER BY total_sales DESC
                LIMIT 10
            ''', (st.session_state.current_branch,))
            sales_data = c.fetchall()
            
            if sales_data:
                df_sales = pd.DataFrame(sales_data, columns=["المنتج", "إجمالي المبيعات"])
                if not df_sales.empty and df_sales["إجمالي المبيعات"].sum() > 0:
                    fig = px.bar(df_sales, x="المنتج", y="إجمالي المبيعات")
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("لا توجد بيانات كافية للرسم البياني")
            else:
                st.info("لا توجد بيانات مبيعات كافية لعرض الرسم البياني")
    
    # Product Management
    elif menu == "إدارة المنتجات":
        st.title("إدارة المنتجات")
        
        tab1, tab2, tab3, tab4 = st.tabs(["إضافة منتج", "تعديل منتج", "حذف منتج", "عرض المنتجات"])
        
        with tab1:
            st.header("إضافة منتج جديد")
            
            # Get categories for dropdown
            c.execute("SELECT id, name FROM categories")
            categories = c.fetchall()
            category_dict = {cat[0]: cat[1] for cat in categories}
            if not category_dict:
                category_dict[0] = "لا توجد فئات"
            else:
                category_dict[0] = "اختر الفئة"
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("اسم المنتج")
                description = st.text_area("وصف المنتج")
                category = st.selectbox("الفئة", options=list(category_dict.keys()), format_func=lambda x: category_dict[x])
            
            with col2:
                price = st.number_input("السعر", min_value=0.0, format="%.2f")
                barcode = st.text_input("الباركود (اختياري)")
                uploaded_file = st.file_uploader("صورة المنتج", type=["jpg", "png", "jpeg"])
            
            image_data = None
            if uploaded_file is not None:
                image_data = uploaded_file.getvalue()
            
            if st.button("إضافة المنتج"):
                if name and category != 0:
                    try:
                        c.execute('''
                            INSERT INTO products (name, description, category_id, price, barcode, image)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (name, description, category, price, barcode, image_data))
                        
                        # Get the new product id
                        product_id = c.lastrowid
                        
                        # Add initial inventory entry with 0 quantity for all branches
                        c.execute('SELECT id FROM branches')
                        branches = c.fetchall()
                        
                        for branch_id in [b[0] for b in branches]:
                            c.execute('''
                                INSERT INTO inventory (product_id, branch_id, quantity, last_updated)
                                VALUES (?, ?, ?, ?)
                            ''', (product_id, branch_id, 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
                        conn.commit()
                        st.success(f"تم إضافة المنتج '{name}' بنجاح")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء إضافة المنتج: {e}")
                else:
                    st.warning("الرجاء إدخال اسم المنتج واختيار الفئة")
        
        with tab2:
            st.header("تعديل منتج")
            
            # Get products for dropdown
            c.execute("SELECT id, name FROM products")
            products = c.fetchall()
            product_dict = {prod[0]: prod[1] for prod in products}
            
            if product_dict:
                product_id = st.selectbox("اختر المنتج للتعديل", options=list(product_dict.keys()), format_func=lambda x: product_dict[x])
                
                # Get current product data
                c.execute("SELECT name, description, category_id, price, barcode FROM products WHERE id = ?", (product_id,))
                product_data = c.fetchone()
                
                if product_data:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        updated_name = st.text_input("اسم المنتج", value=product_data[0])
                        updated_description = st.text_area("وصف المنتج", value=product_data[1] or "")
                        category_index = 0
                        if product_data[2] in category_dict:
                            category_index = list(category_dict.keys()).index(product_data[2])
                        updated_category = st.selectbox("الفئة", options=list(category_dict.keys()), 
                                                      format_func=lambda x: category_dict[x], 
                                                      index=category_index)
                    
                    with col2:
                        updated_price = st.number_input("السعر", value=float(product_data[3]) if product_data[3] else 0.0, format="%.2f")
                        updated_barcode = st.text_input("الباركود", value=product_data[4] or "")
                        updated_image = st.file_uploader("تحديث صورة المنتج (اترك فارغاً للاحتفاظ بالصورة الحالية)", type=["jpg", "png", "jpeg"])
                    
                    if st.button("تحديث المنتج"):
                        try:
                            if updated_image:
                                image_data = updated_image.getvalue()
                                c.execute('''
                                    UPDATE products
                                    SET name = ?, description = ?, category_id = ?, price = ?, barcode = ?, image = ?
                                    WHERE id = ?
                                ''', (updated_name, updated_description, updated_category, updated_price, updated_barcode, image_data, product_id))
                            else:
                                c.execute('''
                                    UPDATE products
                                    SET name = ?, description = ?, category_id = ?, price = ?, barcode = ?
                                    WHERE id = ?
                                ''', (updated_name, updated_description, updated_category, updated_price, updated_barcode, product_id))
                            
                            conn.commit()
                            st.success(f"تم تحديث المنتج '{updated_name}' بنجاح")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء تحديث المنتج: {e}")
            else:
                st.info("لا توجد منتجات لتعديلها")
        
        with tab3:
            st.header("حذف منتج")
            
            if product_dict:
                product_to_delete = st.selectbox("اختر المنتج للحذف", options=list(product_dict.keys()), format_func=lambda x: product_dict[x], key="delete_product_select")
                
                # Display product details for confirmation
                c.execute('''
                    SELECT p.name, p.description, c.name, p.price
                    FROM products p
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE p.id = ?
                ''', (product_to_delete,))
                product_details = c.fetchone()
                
                if product_details:
                    st.markdown("### تفاصيل المنتج المراد حذفه")
                    st.markdown(f"**الاسم:** {product_details[0]}")
                    st.markdown(f"**الوصف:** {product_details[1] or 'لا يوجد'}")
                    st.markdown(f"**الفئة:** {product_details[2] or 'غير مصنف'}")
                    st.markdown(f"**السعر:** {product_details[3]} ريال")
                
                # Check if product is used in inventory or sales
                c.execute("SELECT SUM(quantity) FROM inventory WHERE product_id = ?", (product_to_delete,))
                inventory_count = c.fetchone()[0] or 0
                
                c.execute("SELECT COUNT(*) FROM sales WHERE product_id = ?", (product_to_delete,))
                sales_count = c.fetchone()[0]
                
                if inventory_count > 0:
                    st.warning(f"هذا المنتج لديه {inventory_count} قطعة في المخزون. تأكد من تصفير المخزون قبل الحذف.")
                
                if sales_count > 0:
                    st.warning(f"هذا المنتج مرتبط بـ {sales_count} عمليات بيع سابقة.")
                
                # Confirmation checkbox
                confirm_delete = st.checkbox("أنا متأكد من حذف هذا المنتج وأتفهم أن هذا الإجراء لا يمكن التراجع عنه", key="confirm_delete_product")
                
                if st.button("حذف المنتج", key="delete_product_btn") and confirm_delete:
                    try:
                        # Delete related inventory records
                        c.execute("DELETE FROM inventory WHERE product_id = ?", (product_to_delete,))
                        # Delete related RFID tags
                        c.execute("DELETE FROM rfid_tags WHERE product_id = ?", (product_to_delete,))
                        # Delete product
                        c.execute("DELETE FROM products WHERE id = ?", (product_to_delete,))
                        
                        conn.commit()
                        st.success(f"تم حذف المنتج '{product_dict[product_to_delete]}' بنجاح")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء حذف المنتج: {e}")
            else:
                st.info("لا توجد منتجات لحذفها")
        
        with tab4:
            st.header("عرض المنتجات")
            
            # Get all products with category info
     
