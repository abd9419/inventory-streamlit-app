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
    menu_options = ["الرئيسية", "إدارة المنتجات", "إدارة الفئات", "عرض المخزون", "التقارير", "إدارة المبيعات", "رفع بيانات RFID", "إدارة الفروع"]
    if st.session_state.role == 'admin':
        menu_options.append("إدارة المستخدمين")
        
    menu = st.sidebar.radio("اختر الوظيفة:", menu_options)
    
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
    
    # Main Dashboard Page
    if menu == "الرئيسية":
        st.title("نظام إدارة المخازن والمستودعات")
        st.write("مرحباً بك في نظام إدارة المخازن والمستودعات. الرجاء اختيار الوظيفة المطلوبة من القائمة الجانبية.")
        
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
        st.subheader("تنبيهات المخزون المنخفض")
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
    
    # Category Management
    elif menu == "إدارة الفئات":
        st.title("إدارة الفئات")
        
        tab1, tab2, tab3 = st.tabs(["إضافة فئة", "تعديل فئة", "حذف فئة"])
        
        with tab1:
            st.header("إضافة فئة جديدة")
            
            name = st.text_input("اسم الفئة")
            description = st.text_area("وصف الفئة")
            
            if st.button("إضافة الفئة"):
                if name:
                    try:
                        c.execute('''
                            INSERT INTO categories (name, description)
                            VALUES (?, ?)
                        ''', (name, description))
                        conn.commit()
                        st.success(f"تم إضافة الفئة '{name}' بنجاح")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء إضافة الفئة: {e}")
                else:
                    st.warning("الرجاء إدخال اسم الفئة")
        
        with tab2:
            st.header("تعديل فئة")
            
            # Get categories for dropdown
            c.execute("SELECT id, name FROM categories")
            categories = c.fetchall()
            category_dict = {cat[0]: cat[1] for cat in categories}
            
            if category_dict:
                category_id = st.selectbox("اختر الفئة للتعديل", options=list(category_dict.keys()), format_func=lambda x: category_dict[x])
                
                # Get current category data
                c.execute("SELECT name, description FROM categories WHERE id = ?", (category_id,))
                category_data = c.fetchone()
                
                if category_data:
                    updated_name = st.text_input("اسم الفئة", value=category_data[0])
                    updated_description = st.text_area("وصف الفئة", value=category_data[1] or "")
                    
                    if st.button("تحديث الفئة"):
                        try:
                            c.execute('''
                                UPDATE categories
                                SET name = ?, description = ?
                                WHERE id = ?
                            ''', (updated_name, updated_description, category_id))
                            
                            conn.commit()
                            st.success(f"تم تحديث الفئة '{updated_name}' بنجاح")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء تحديث الفئة: {e}")
            else:
                st.info("لا توجد فئات لتعديلها")
        
        with tab3:
            st.header("حذف فئة")
            
            if category_dict:
                category_to_delete = st.selectbox("اختر الفئة للحذف", options=list(category_dict.keys()), format_func=lambda x: category_dict[x], key="delete_category_select")
                
                # Check if category has products
                c.execute("SELECT COUNT(*) FROM products WHERE category_id = ?", (category_to_delete,))
                product_count = c.fetchone()[0]
                
                if product_count > 0:
                    st.warning(f"لا يمكن حذف الفئة لأنها تحتوي على {product_count} منتجات مرتبطة بها")
                
                # Confirmation checkbox
                confirm_delete = st.checkbox("أنا متأكد من حذف هذه الفئة", key="confirm_delete_category")
                
                if st.button("حذف الفئة") and confirm_delete:
                    if product_count == 0:  # Only delete if no products are linked
                        try:
                            c.execute("DELETE FROM categories WHERE id = ?", (category_to_delete,))
                            conn.commit()
                            st.success(f"تم حذف الفئة '{category_dict[category_to_delete]}' بنجاح")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء حذف الفئة: {e}")
                    else:
                        st.error("لا يمكن حذف الفئة لأنها تحتوي على منتجات مرتبطة بها. قم بتغيير تصنيف المنتجات أولاً")
            else:
                st.info("لا توجد فئات لحذفها")
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
            c.execute('''
                SELECT p.id, p.name, p.description, c.name, p.price, p.barcode
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.id DESC
            ''')
            products_data = c.fetchall()
            
            if products_data:
                products_list = []
                for prod in products_data:
                    products_list.append({
                        "المعرف": prod[0],
                        "اسم المنتج": prod[1],
                        "الوصف": prod[2] or "",
                        "الفئة": prod[3] or "غير مصنف",
                        "السعر": f"{prod[4]} ريال" if prod[4] else "0.00 ريال",
                        "الباركود": prod[5] or ""
                    })
                
                df_products = pd.DataFrame(products_list)
                
                # Add search functionality
                search_term = st.text_input("البحث عن منتج")
                
                if search_term:
                    df_filtered = df_products[df_products['اسم المنتج'].str.contains(search_term, case=False, na=False)]
                    st.table(df_filtered)
                else:
                    st.table(df_products)
                
                # Add download button
                st.markdown(convert_df_to_csv_download_link(df_products, "products.csv"), unsafe_allow_html=True)
            else:
                st.info("لا توجد منتجات لعرضها")
    # Inventory Management
    elif menu == "عرض المخزون":
        st.title("عرض وإدارة المخزون")
        
        tab1, tab2 = st.tabs(["عرض المخزون", "تعديل المخزون"])
        
        with tab1:
            st.header(f"المخزون الحالي في {get_branch_name(st.session_state.current_branch)}")
            
            # Get inventory data with product info for current branch
            c.execute('''
                SELECT i.id, p.name, c.name, i.quantity, p.price, (p.price * i.quantity) as total_value, i.last_updated, p.id
                FROM inventory i
                JOIN products p ON i.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE i.branch_id = ?
                ORDER BY c.name, p.name
            ''', (st.session_state.current_branch,))
            inventory_data = c.fetchall()
            
            if inventory_data:
                inventory_list = []
                for inv in inventory_data:
                    inventory_list.append({
                        "معرف المخزون": inv[0],
                        "اسم المنتج": inv[1],
                        "الفئة": inv[2] or "غير مصنف",
                        "الكمية": inv[3],
                        "سعر الوحدة": f"{inv[4]} ريال" if inv[4] else "0.00 ريال",
                        "القيمة الإجمالية": f"{inv[5]} ريال" if inv[5] else "0.00 ريال",
                        "آخر تحديث": inv[6],
                        "معرف المنتج": inv[7]
                    })
                
                df_inventory = pd.DataFrame(inventory_list)
                
                # Add filter by category
                c.execute("SELECT id, name FROM categories")
                categories = c.fetchall()
                category_dict = {0: "جميع الفئات"}
                category_dict.update({cat[0]: cat[1] for cat in categories})
                
                filter_category = st.selectbox("تصفية حسب الفئة", options=list(category_dict.keys()), format_func=lambda x: category_dict[x])
                
                if filter_category != 0:
                    df_filtered = df_inventory[df_inventory['الفئة'] == category_dict[filter_category]]
                else:
                    df_filtered = df_inventory
                
                # Add low stock filter
                show_low_stock_only = st.checkbox("عرض المخزون المنخفض فقط (أقل من 10)")
                
                if show_low_stock_only:
                    df_filtered = df_filtered[df_filtered['الكمية'] < 10]
                
                # Show inventory table
                st.table(df_filtered[["اسم المنتج", "الفئة", "الكمية", "سعر الوحدة", "القيمة الإجمالية", "آخر تحديث"]])
                
                # Add download button
                st.markdown(convert_df_to_csv_download_link(df_filtered, "inventory.csv"), unsafe_allow_html=True)
                
                # Show inventory summary
                st.subheader("ملخص المخزون")
                total_items = df_filtered['الكمية'].sum()
                
                # Extract numeric value from price string and sum
                total_value = 0
                for value in df_filtered['القيمة الإجمالية']:
                    try:
                        if isinstance(value, str) and "ريال" in value:
                            total_value += float(value.replace(" ريال", ""))
                    except:
                        pass
                
                col1, col2 = st.columns(2)
                col1.metric("إجمالي عدد القطع", total_items)
                col2.metric("إجمالي قيمة المخزون", f"{total_value:.2f} ريال")
                
                # Show inventory by category pie chart
                st.subheader("توزيع المخزون حسب الفئات")
                
                category_summary = df_inventory.groupby('الفئة')['الكمية'].sum().reset_index()
                if not category_summary.empty and category_summary['الكمية'].sum() > 0:
                    fig = px.pie(category_summary, values='الكمية', names='الفئة', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات مخزون لعرضها")
        
        with tab2:
            st.header("تعديل المخزون")
            
            # Get products for dropdown
            c.execute("SELECT id, name FROM products")
            products = c.fetchall()
            product_dict = {prod[0]: prod[1] for prod in products}
            
            if product_dict:
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_product = st.selectbox("اختر المنتج", options=list(product_dict.keys()), format_func=lambda x: product_dict[x])
                    
                    # Get current inventory quantity
                    c.execute('''
                        SELECT quantity FROM inventory
                        WHERE product_id = ? AND branch_id = ?
                    ''', (selected_product, st.session_state.current_branch))
                    current_qty = c.fetchone()
                    current_qty = current_qty[0] if current_qty else 0
                    
                    st.metric("الكمية الحالية", current_qty)
                
                with col2:
                    operation = st.radio("نوع العملية", ["إضافة", "خصم", "تعيين قيمة محددة"])
                    quantity = st.number_input("الكمية", min_value=1, value=1)
                
                st.markdown("---")
                
                notes = st.text_area("ملاحظات (اختياري)")
                
                if st.button("تحديث المخزون"):
                    new_quantity = current_qty
                    
                    if operation == "إضافة":
                        new_quantity = current_qty + quantity
                    elif operation == "خصم":
                        new_quantity = max(0, current_qty - quantity)
                    else:  # تعيين قيمة محددة
                        new_quantity = quantity
                    
                    try:
                        c.execute('''
                            UPDATE inventory
                            SET quantity = ?, last_updated = ?
                            WHERE product_id = ? AND branch_id = ?
                        ''', (new_quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), selected_product, st.session_state.current_branch))
                        
                        conn.commit()
                        st.success(f"تم تحديث مخزون المنتج '{product_dict[selected_product]}' بنجاح. الكمية الجديدة: {new_quantity}")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء تحديث المخزون: {e}")
            else:
                st.info("لا توجد منتجات لتعديل مخزونها")
    
    # RFID Data Upload
    elif menu == "رفع بيانات RFID":
        st.title("رفع وإدارة بيانات RFID")
        
        tab1, tab2, tab3 = st.tabs(["رفع بيانات RFID", "ربط التاج RFID بمنتج", "عرض بيانات RFID"])
        
        with tab1:
            st.header("رفع بيانات RFID")
            
            upload_method = st.radio("طريقة الرفع", ["ملف CSV", "إدخال يدوي"])
            
            if upload_method == "ملف CSV":
                st.write("قم بتحميل ملف CSV يحتوي على أعمدة: tag_id, product_id (اختياري), quantity (اختياري)")
                uploaded_file = st.file_uploader("اختر ملف CSV", type=["csv"])
                
                if uploaded_file is not None:
                    try:
                        df = pd.read_csv(uploaded_file)
                        st.write("معاينة البيانات:")
                        st.write(df.head())
                        
                        if "tag_id" not in df.columns:
                            st.error("يجب أن يحتوي الملف على عمود 'tag_id'")
                        else:
                            if st.button("معالجة البيانات"):
                                success_count = 0
                                error_count = 0
                                
                                for i, row in df.iterrows():
                                    tag_id = row["tag_id"]
                                    product_id = row.get("product_id", None)
                                    
                                    # Check if tag already exists
                                    c.execute("SELECT id FROM rfid_tags WHERE tag_id = ?", (tag_id,))
                                    tag_exists = c.fetchone()
                                    
                                    if tag_exists:
                                        # Update existing tag
                                        if product_id:
                                            c.execute('''
                                                UPDATE rfid_tags
                                                SET product_id = ?, assigned_at = ?, status = 'assigned'
                                                WHERE tag_id = ?
                                            ''', (product_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tag_id))
                                        success_count += 1
                                    else:
                                        # Insert new tag
                                        try:
                                            if product_id:
                                                c.execute('''
                                                    INSERT INTO rfid_tags (tag_id, product_id, assigned_at, status)
                                                    VALUES (?, ?, ?, 'assigned')
                                                ''', (tag_id, product_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                            else:
                                                c.execute('''
                                                    INSERT INTO rfid_tags (tag_id, status)
                                                    VALUES (?, 'unassigned')
                                                ''', (tag_id,))
                                            success_count += 1
                                        except Exception:
                                            error_count += 1
                                
                                conn.commit()
                                st.success(f"تم معالجة {success_count} تاج RFID بنجاح. فشل في معالجة {error_count} تاج.")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء معالجة الملف: {e}")
            
            else:  # إدخال يدوي
                st.subheader("إضافة تاج RFID جديد")
                
                manual_tag_id = st.text_input("معرف التاج RFID")
                
                # Get products for dropdown
                c.execute("SELECT id, name FROM products")
                products = c.fetchall()
                product_dict = {0: "اختر منتج (اختياري)"}
                product_dict.update({prod[0]: prod[1] for prod in products})
                
                manual_product_id = st.selectbox("المنتج", options=list(product_dict.keys()), format_func=lambda x: product_dict[x])
                if manual_product_id == 0:
                    manual_product_id = None
                
                if st.button("إضافة تاج RFID"):
                    if manual_tag_id:
                        try:
                            # Check if tag already exists
                            c.execute("SELECT id FROM rfid_tags WHERE tag_id = ?", (manual_tag_id,))
                            tag_exists = c.fetchone()
                            
                            if tag_exists:
                                st.warning(f"التاج {manual_tag_id} موجود بالفعل في قاعدة البيانات")
                            else:
                                if manual_product_id:
                                    c.execute('''
                                        INSERT INTO rfid_tags (tag_id, product_id, assigned_at, status)
                                        VALUES (?, ?, ?, 'assigned')
                                    ''', (manual_tag_id, manual_product_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                else:
                                    c.execute('''
                                        INSERT INTO rfid_tags (tag_id, status)
                                        VALUES (?, 'unassigned')
                                    ''', (manual_tag_id,))
                                
                                conn.commit()
                                st.success(f"تم إضافة التاج {manual_tag_id} بنجاح")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء إضافة التاج: {e}")
                    else:
                        st.warning("الرجاء إدخال معرف التاج RFID")
            
            # Generate random RFID tags for testing
            st.markdown("---")
            st.subheader("توليد تاجات RFID عشوائية للاختبار")
            
            col1, col2 = st.columns(2)
            with col1:
                random_tags_count = st.number_input("عدد التاجات", min_value=1, max_value=100, value=5)
            with col2:
                random_tags_assigned = st.checkbox("ربط بمنتجات عشوائية")
            
            if st.button("توليد تاجات RFID عشوائية"):
                try:
                    # Get product IDs if assigning to random products
                    product_ids = []
                    if random_tags_assigned:
                        c.execute("SELECT id FROM products")
                        product_ids = [p[0] for p in c.fetchall()]
                    
                    generated_tags = []
                    for _ in range(random_tags_count):
                        tag_id = generate_rfid_tag()
                        
                        # Check if product IDs exist for assignment
                        product_id = None
                        if product_ids:
                            product_id = random.choice(product_ids)
                        
                        if product_id:
                            c.execute('''
                                INSERT INTO rfid_tags (tag_id, product_id, assigned_at, status)
                                VALUES (?, ?, ?, 'assigned')
                            ''', (tag_id, product_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        else:
                            c.execute('''
                                INSERT INTO rfid_tags (tag_id, status)
                                VALUES (?, 'unassigned')
                            ''', (tag_id,))
                        
                        generated_tags.append(tag_id)
                    
                    conn.commit()
                    st.success(f"تم توليد {random_tags_count} تاجات RFID عشوائية بنجاح")
                    
                    # Display generated tags
                    st.write("التاجات المولدة:")
                    for tag in generated_tags:
                        st.code(tag)
                except Exception as e:
                    st.error(f"حدث خطأ أثناء توليد التاجات: {e}")
        
        with tab2:
            st.header("ربط تاج RFID بمنتج")
            
            # Get unassigned RFID tags
            c.execute("SELECT id, tag_id FROM rfid_tags WHERE status = 'unassigned' OR product_id IS NULL")
            unassigned_tags = c.fetchall()
            tag_dict = {tag[0]: tag[1] for tag in unassigned_tags}
            
            if tag_dict:
                selected_tag_id = st.selectbox("اختر تاج RFID", options=list(tag_dict.keys()), format_func=lambda x: tag_dict[x])
                
                # Get products for dropdown
                c.execute("SELECT id, name FROM products")
                products = c.fetchall()
                product_dict = {prod[0]: prod[1] for prod in products}
                
                if product_dict:
                    selected_product_id = st.selectbox("اختر المنتج", options=list(product_dict.keys()), format_func=lambda x: product_dict[x])
                    
                    if st.button("ربط التاج بالمنتج"):
                        try:
                            c.execute('''
                                UPDATE rfid_tags
                                SET product_id = ?, assigned_at = ?, status = 'assigned'
                                WHERE id = ?
                            ''', (selected_product_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), selected_tag_id))
                            
                            conn.commit()
                            st.success(f"تم ربط التاج {tag_dict[selected_tag_id]} بالمنتج {product_dict[selected_product_id]} بنجاح")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء ربط التاج بالمنتج: {e}")
                else:
                    st.info("لا توجد منتجات لربط التاجات بها")
            else:
                st.info("لا توجد تاجات RFID غير مرتبطة")
        
        with tab3:
            st.header("عرض بيانات RFID")
            
            # Get RFID tags with product info
            c.execute('''
                SELECT r.id, r.tag_id, p.name, r.status, r.assigned_at
                FROM rfid_tags r
                LEFT JOIN products p ON r.product_id = p.id
                ORDER BY r.id DESC
            ''')
            tags_data = c.fetchall()
            
            if tags_data:
                tags_list = []
                for tag in tags_data:
                    tags_list.append({
                        "المعرف": tag[0],
                        "تاج RFID": tag[1],
                        "المنتج": tag[2] or "غير مرتبط",
                        "الحالة": "مرتبط" if tag[3] == "assigned" else "غير مرتبط",
                        "تاريخ الربط": tag[4] or ""
                    })
                
                df_tags = pd.DataFrame(tags_list)
                
                # Add filter by status
                status_filter = st.radio("تصفية حسب الحالة", ["الكل", "مرتبط", "غير مرتبط"])
                
                if status_filter == "مرتبط":
                    df_filtered = df_tags[df_tags['الحالة'] == "مرتبط"]
                elif status_filter == "غير مرتبط":
                    df_filtered = df_tags[df_tags['الحالة'] == "غير مرتبط"]
                else:
                    df_filtered = df_tags
                
                # Add search functionality
                search_term = st.text_input("البحث عن تاج RFID")
                
                if search_term:
                    df_filtered = df_filtered[df_filtered['تاج RFID'].str.contains(search_term, case=False, na=False)]
                
                # Show tags table
                st.table(df_filtered)
                
                # Add download button
                st.markdown(convert_df_to_csv_download_link(df_filtered, "rfid_tags.csv"), unsafe_allow_html=True)
            else:
                st.info("لا توجد تاجات RFID لعرضها")
    # Sales Management
    elif menu == "إدارة المبيعات":
        st.title("إدارة المبيعات")
        
        tab1, tab2, tab3 = st.tabs(["تسجيل مبيعات", "عرض المبيعات", "تقارير المبيعات"])
        
        with tab1:
            st.header("تسجيل عملية بيع جديدة")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Get products for dropdown
                c.execute("SELECT id, name, price FROM products")
                products = c.fetchall()
                product_dict = {prod[0]: f"{prod[1]} - {prod[2]} ريال" for prod in products}
                
                if product_dict:
                    selected_product = st.selectbox("اختر المنتج", options=list(product_dict.keys()), format_func=lambda x: product_dict[x])
                    
                    # Get current product price
                    c.execute("SELECT price FROM products WHERE id = ?", (selected_product,))
                    product_price = c.fetchone()[0] or 0
                    
                    # Get current inventory quantity
                    c.execute('''
                        SELECT quantity FROM inventory
                        WHERE product_id = ? AND branch_id = ?
                    ''', (selected_product, st.session_state.current_branch))
                    current_qty = c.fetchone()
                    current_qty = current_qty[0] if current_qty else 0
                    
                    st.metric("الكمية المتوفرة في المخزون", current_qty)
                    
                    quantity = st.number_input("الكمية المباعة", min_value=1, max_value=current_qty if current_qty > 0 else 1, value=1)
                    sale_price = st.number_input("سعر البيع للوحدة", min_value=0.0, value=float(product_price), format="%.2f")
                    
                    total_amount = quantity * sale_price
                    st.metric("إجمالي المبلغ", f"{total_amount:.2f} ريال")
                else:
                    st.error("لا توجد منتجات متاحة للبيع. يرجى إضافة منتجات أولاً.")
            
            with col2:
                sale_date = st.date_input("تاريخ البيع", value=datetime.now())
                sale_time = st.time_input("وقت البيع", value=datetime.now().time())
                
                sale_datetime = datetime.combine(sale_date, sale_time).strftime("%Y-%m-%d %H:%M:%S")
                
                reference = st.text_input("رقم المرجع (اختياري)", value=generate_reference_number("SALE"))
                
                notes = st.text_area("ملاحظات")
            
            if product_dict:
                if st.button("تسجيل عملية البيع"):
                    if current_qty >= quantity:
                        try:
                            # Record sale
                            c.execute('''
                                INSERT INTO sales (product_id, branch_id, quantity, sale_date, amount, reference)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (selected_product, st.session_state.current_branch, quantity, sale_datetime, total_amount, reference))
                            
                            # Update inventory
                            new_quantity = current_qty - quantity
                            c.execute('''
                                UPDATE inventory
                                SET quantity = ?, last_updated = ?
                                WHERE product_id = ? AND branch_id = ?
                            ''', (new_quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), selected_product, st.session_state.current_branch))
                            
                            conn.commit()
                            st.success(f"تم تسجيل عملية البيع بنجاح. المرجع: {reference}")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء تسجيل عملية البيع: {e}")
                    else:
                        st.error("الكمية المطلوبة غير متوفرة في المخزون")
        
        with tab2:
            st.header("عرض المبيعات")
            
            # Date range filter
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("من تاريخ", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("إلى تاريخ", value=datetime.now())
            
            # Adjust end date to include the entire day
            end_date_adjusted = datetime.combine(end_date, time.max).strftime("%Y-%m-%d %H:%M:%S")
            
            # Get sales data
            c.execute('''
                SELECT s.id, p.name, s.quantity, s.amount, s.sale_date, s.reference, b.name
                FROM sales s
                JOIN products p ON s.product_id = p.id
                JOIN branches b ON s.branch_id = b.id
                WHERE s.sale_date BETWEEN ? AND ? AND s.branch_id = ?
                ORDER BY s.sale_date DESC
            ''', (start_date, end_date_adjusted, st.session_state.current_branch))
            sales_data = c.fetchall()
            
            if sales_data:
                sales_list = []
                for sale in sales_data:
                    sales_list.append({
                        "المعرف": sale[0],
                        "المنتج": sale[1],
                        "الكمية": sale[2],
                        "المبلغ": f"{sale[3]:.2f} ريال",
                        "التاريخ": sale[4],
                        "رقم المرجع": sale[5],
                        "الفرع": sale[6]
                    })
                
                df_sales = pd.DataFrame(sales_list)
                
                # Show sales table
                st.table(df_sales)
                
                # Add download button
                st.markdown(convert_df_to_csv_download_link(df_sales, "sales.csv"), unsafe_allow_html=True)
                
                # Show sales summary
                st.subheader("ملخص المبيعات")
                total_sales = sum(sale[3] for sale in sales_data)
                total_items_sold = sum(sale[2] for sale in sales_data)
                
                col1, col2 = st.columns(2)
                col1.metric("إجمالي المبيعات", f"{total_sales:.2f} ريال")
                col2.metric("إجمالي القطع المباعة", total_items_sold)
            else:
                st.info("لا توجد مبيعات في الفترة المحددة")
        
        with tab3:
            st.header("تقارير المبيعات")
            
            # Date range filter
            col1, col2 = st.columns(2)
            with col1:
                report_start_date = st.date_input("من تاريخ", value=datetime.now() - timedelta(days=30), key="report_start")
            with col2:
                report_end_date = st.date_input("إلى تاريخ", value=datetime.now(), key="report_end")
            
            # Adjust end date to include the entire day
            report_end_date_adjusted = datetime.combine(report_end_date, time.max).strftime("%Y-%m-%d %H:%M:%S")
            
            report_type = st.selectbox("نوع التقرير", ["مبيعات حسب المنتج", "مبيعات حسب اليوم", "مبيعات حسب الشهر"])
            
            if report_type == "مبيعات حسب المنتج":
                # Get sales by product
                c.execute('''
                    SELECT p.name, SUM(s.quantity) as total_qty, SUM(s.amount) as total_amount
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    WHERE s.sale_date BETWEEN ? AND ? AND s.branch_id = ?
                    GROUP BY p.name
                    ORDER BY total_amount DESC
                ''', (report_start_date, report_end_date_adjusted, st.session_state.current_branch))
                product_sales = c.fetchall()
                
                if product_sales:
                    product_sales_list = []
                    for sale in product_sales:
                        product_sales_list.append({
                            "المنتج": sale[0],
                            "إجمالي الكمية": sale[1],
                            "إجمالي المبلغ": f"{sale[2]:.2f} ريال"
                        })
                    
                    df_product_sales = pd.DataFrame(product_sales_list)
                    
                    # Show product sales table
                    st.subheader("المبيعات حسب المنتج")
                    st.table(df_product_sales)
                    
                    # Add download button
                    st.markdown(convert_df_to_csv_download_link(df_product_sales, "product_sales.csv"), unsafe_allow_html=True)
                    
                    # Show product sales chart
                    st.subheader("رسم بياني للمبيعات حسب المنتج")
                    
                    # Extract amounts without "ريال" for plotting
                    df_for_chart = pd.DataFrame({
                        "المنتج": [sale[0] for sale in product_sales],
                        "إجمالي المبيعات": [sale[2] for sale in product_sales]
                    })
                    
                    if len(product_sales) > 10:
                        df_for_chart = df_for_chart.head(10)
                        st.info("يتم عرض أعلى 10 منتجات فقط في الرسم البياني")
                    
                    fig = px.bar(df_for_chart, x="المنتج", y="إجمالي المبيعات", title="أفضل المنتجات مبيعاً")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("لا توجد مبيعات في الفترة المحددة")
            
            elif report_type == "مبيعات حسب اليوم":
                # Get sales by day
                c.execute('''
                    SELECT date(s.sale_date) as sale_day, SUM(s.quantity) as total_qty, SUM(s.amount) as total_amount
                    FROM sales s
                    WHERE s.sale_date BETWEEN ? AND ? AND s.branch_id = ?
                    GROUP BY sale_day
                    ORDER BY sale_day
                ''', (report_start_date, report_end_date_adjusted, st.session_state.current_branch))
                daily_sales = c.fetchall()
                
                if daily_sales:
                    daily_sales_list = []
                    for sale in daily_sales:
                        daily_sales_list.append({
                            "اليوم": sale[0],
                            "إجمالي الكمية": sale[1],
                            "إجمالي المبلغ": f"{sale[2]:.2f} ريال"
                        })
                    
                    df_daily_sales = pd.DataFrame(daily_sales_list)
                    
                    # Show daily sales table
                    st.subheader("المبيعات اليومية")
                    st.table(df_daily_sales)
                    
                    # Add download button
                    st.markdown(convert_df_to_csv_download_link(df_daily_sales, "daily_sales.csv"), unsafe_allow_html=True)
                    
                    # Show daily sales chart
                    st.subheader("رسم بياني للمبيعات اليومية")
                    
                    # Extract amounts without "ريال" for plotting
                    df_for_chart = pd.DataFrame({
                        "اليوم": [sale[0] for sale in daily_sales],
                        "إجمالي المبيعات": [sale[2] for sale in daily_sales]
                    })
                    
                    fig = px.line(df_for_chart, x="اليوم", y="إجمالي المبيعات", title="المبيعات اليومية")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("لا توجد مبيعات في الفترة المحددة")
            
            else:  # مبيعات حسب الشهر
                # Get sales by month
                c.execute('''
                    SELECT strftime('%Y-%m', s.sale_date) as sale_month, SUM(s.quantity) as total_qty, SUM(s.amount) as total_amount
                    FROM sales s
                    WHERE s.sale_date BETWEEN ? AND ? AND s.branch_id = ?
                    GROUP BY sale_month
                    ORDER BY sale_month
                ''', (report_start_date, report_end_date_adjusted, st.session_state.current_branch))
                monthly_sales = c.fetchall()
                
                if monthly_sales:
                    monthly_sales_list = []
                    for sale in monthly_sales:
                        monthly_sales_list.append({
                            "الشهر": sale[0],
                            "إجمالي الكمية": sale[1],
                            "إجمالي المبلغ": f"{sale[2]:.2f} ريال"
                        })
                    
                    df_monthly_sales = pd.DataFrame(monthly_sales_list)
                    
                    # Show monthly sales table
                    st.subheader("المبيعات الشهرية")
                    st.table(df_monthly_sales)
                    
                    # Add download button
                    st.markdown(convert_df_to_csv_download_link(df_monthly_sales, "monthly_sales.csv"), unsafe_allow_html=True)
                    
                    # Show monthly sales chart
                    st.subheader("رسم بياني للمبيعات الشهرية")
                    
                    # Extract amounts without "ريال" for plotting
                    df_for_chart = pd.DataFrame({
                        "الشهر": [sale[0] for sale in monthly_sales],
                        "إجمالي المبيعات": [sale[2] for sale in monthly_sales]
                    })
                    
                    fig = px.bar(df_for_chart, x="الشهر", y="إجمالي المبيعات", title="المبيعات الشهرية")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("لا توجد مبيعات في الفترة المحددة")
    # Reports
    elif menu == "التقارير":
        st.title("تقارير المخزون والمبيعات")
        
        report_type = st.selectbox("نوع التقرير", [
            "تقرير المخزون الحالي", 
            "تقرير المخزون المنخفض",
            "تقرير المبيعات", 
            "تقرير أداء المنتجات"
        ])
        
        if report_type == "تقرير المخزون الحالي":
            st.header(f"تقرير المخزون الحالي في {get_branch_name(st.session_state.current_branch)}")
            
            # Get inventory data with product info for current branch
            c.execute('''
                SELECT p.name, c.name, i.quantity, p.price, (p.price * i.quantity) as total_value
                FROM inventory i
                JOIN products p ON i.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE i.branch_id = ? AND i.quantity > 0
                ORDER BY p.name
            ''', (st.session_state.current_branch,))
            inventory_data = c.fetchall()
            
            if inventory_data:
                inventory_list = []
                for inv in inventory_data:
                    inventory_list.append({
                        "المنتج": inv[0],
                        "الفئة": inv[1] or "غير مصنف",
                        "الكمية": inv[2],
                        "سعر الوحدة": f"{inv[3]} ريال" if inv[3] else "0.00 ريال",
                        "القيمة الإجمالية": f"{inv[4]} ريال" if inv[4] else "0.00 ريال"
                    })
                
                df_inventory = pd.DataFrame(inventory_list)
                
                # Calculate totals
                total_items = sum(inv[2] for inv in inventory_data)
                total_value = sum(inv[4] or 0 for inv in inventory_data)
                
                # Show summary metrics
                col1, col2 = st.columns(2)
                col1.metric("إجمالي عدد القطع", total_items)
                col2.metric("إجمالي قيمة المخزون", f"{total_value:.2f} ريال")
                
                # Show inventory table
                st.subheader("تفاصيل المخزون")
                st.table(df_inventory)
                
                # Add download button
                st.markdown(convert_df_to_csv_download_link(df_inventory, "inventory_report.csv"), unsafe_allow_html=True)
                
                # Show inventory by category pie chart
                st.subheader("توزيع المخزون حسب الفئات")
                
                category_summary = df_inventory.groupby('الفئة')['الكمية'].sum().reset_index()
                if not category_summary.empty and category_summary['الكمية'].sum() > 0:
                    fig = px.pie(category_summary, values='الكمية', names='الفئة', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات مخزون لعرضها")
        
        elif report_type == "تقرير المخزون المنخفض":
            st.header("تقرير المخزون المنخفض")
            
            # Get low inventory items
            threshold = st.slider("حد المخزون المنخفض", min_value=1, max_value=50, value=10)
            
            c.execute('''
                SELECT p.name, c.name, i.quantity, p.price, b.name
                FROM inventory i
                JOIN products p ON i.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                JOIN branches b ON i.branch_id = b.id
                WHERE i.quantity <= ? 
                ORDER BY i.quantity
            ''', (threshold,))
            low_inventory_data = c.fetchall()
            
            if low_inventory_data:
                low_inventory_list = []
                for inv in low_inventory_data:
                    low_inventory_list.append({
                        "المنتج": inv[0],
                        "الفئة": inv[1] or "غير مصنف",
                        "الكمية المتبقية": inv[2],
                        "سعر الوحدة": f"{inv[3]} ريال" if inv[3] else "0.00 ريال",
                        "الفرع": inv[4]
                    })
                
                df_low_inventory = pd.DataFrame(low_inventory_list)
                
                # Show low inventory table
                st.markdown('<div class="warning-box">تنبيه: المنتجات التالية منخفضة المخزون!</div>', unsafe_allow_html=True)
                st.table(df_low_inventory)
                
                # Add download button
                st.markdown(convert_df_to_csv_download_link(df_low_inventory, "low_inventory_report.csv"), unsafe_allow_html=True)
            else:
                st.success("لا توجد منتجات منخفضة المخزون حالياً.")
        
        elif report_type == "تقرير المبيعات":
            st.header("تقرير المبيعات")
            
            # Date range filter
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("من تاريخ", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("إلى تاريخ", value=datetime.now())
            
            # Branch filter
            all_branches = st.checkbox("جميع الفروع")
            
            if all_branches:
                branch_filter = ""
                branch_params = (start_date, end_date)
            else:
                branch_filter = "AND s.branch_id = ?"
                branch_params = (start_date, end_date, st.session_state.current_branch)
            
            # Adjust end date to include the entire day
            end_date_adjusted = datetime.combine(end_date, time.max).strftime("%Y-%m-%d %H:%M:%S")
            
            # Get sales data
            c.execute(f'''
                SELECT p.name, SUM(s.quantity) as total_quantity, SUM(s.amount) as total_amount, b.name
                FROM sales s
                JOIN products p ON s.product_id = p.id
                JOIN branches b ON s.branch_id = b.id
                WHERE s.sale_date BETWEEN ? AND ? {branch_filter}
                GROUP BY p.name, b.name
                ORDER BY total_amount DESC
            ''', branch_params)
            sales_data = c.fetchall()
            
            if sales_data:
                sales_list = []
                for sale in sales_data:
                    sales_list.append({
                        "المنتج": sale[0],
                        "الكمية المباعة": sale[1],
                        "إجمالي المبيعات": f"{sale[2]:.2f} ريال",
                        "الفرع": sale[3]
                    })
                
                df_sales = pd.DataFrame(sales_list)
                
                # Calculate totals
                total_quantity = sum(sale[1] for sale in sales_data)
                total_amount = sum(sale[2] for sale in sales_data)
                
                # Show summary metrics
                col1, col2 = st.columns(2)
                col1.metric("إجمالي القطع المباعة", total_quantity)
                col2.metric("إجمالي المبيعات", f"{total_amount:.2f} ريال")
                
                # Show sales table
                st.subheader("تفاصيل المبيعات")
                st.table(df_sales)
                
                # Add download button
                st.markdown(convert_df_to_csv_download_link(df_sales, "sales_report.csv"), unsafe_allow_html=True)
                
                # Show sales by branch pie chart
                st.subheader("توزيع المبيعات حسب الفروع")
                
                branch_summary = df_sales.groupby('الفرع')['إجمالي المبيعات'].sum().reset_index()
                branch_summary['إجمالي المبيعات'] = branch_summary['إجمالي المبيعات'].str.replace(' ريال', '').astype(float)
                
                if not branch_summary.empty and branch_summary['إجمالي المبيعات'].sum() > 0:
                    fig = px.pie(branch_summary, values='إجمالي المبيعات', names='الفرع', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات مبيعات في الفترة المحددة")
        
        elif report_type == "تقرير أداء المنتجات":
            st.header("تقرير أداء المنتجات")
            
            # Date range filter
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("من تاريخ", value=datetime.now() - timedelta(days=90))
            with col2:
                end_date = st.date_input("إلى تاريخ", value=datetime.now())
            
            # Adjust end date to include the entire day
            end_date_adjusted = datetime.combine(end_date, time.max).strftime("%Y-%m-%d %H:%M:%S")
            
            # Get product performance data
            c.execute('''
                SELECT 
                    p.name,
                    c.name,
                    SUM(s.quantity) as total_sold,
                    SUM(s.amount) as total_revenue,
                    AVG(s.amount / s.quantity) as avg_unit_price,
                    COUNT(DISTINCT s.id) as sale_count
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN sales s ON p.id = s.product_id AND s.sale_date BETWEEN ? AND ?
                GROUP BY p.id
                ORDER BY total_revenue DESC NULLS LAST
            ''', (start_date, end_date_adjusted))
            performance_data = c.fetchall()
            
            if performance_data:
                performance_list = []
                for perf in performance_data:
                    # Handle NULL values
                    total_sold = perf[2] if perf[2] else 0
                    total_revenue = perf[3] if perf[3] else 0
                    avg_unit_price = perf[4] if perf[4] else 0
                    sale_count = perf[5] if perf[5] else 0
                    
                    performance_list.append({
                        "المنتج": perf[0],
                        "الفئة": perf[1] or "غير مصنف",
                        "الكمية المباعة": total_sold,
                        "إجمالي الإيرادات": f"{total_revenue:.2f} ريال",
                        "متوسط سعر البيع": f"{avg_unit_price:.2f} ريال",
                        "عدد عمليات البيع": sale_count
                    })
                
                df_performance = pd.DataFrame(performance_list)
                
                # Show performance table
                st.subheader("تفاصيل أداء المنتجات")
                st.table(df_performance)
                
                # Add download button
                st.markdown(convert_df_to_csv_download_link(df_performance, "product_performance_report.csv"), unsafe_allow_html=True)
                
                # Show top products chart
                st.subheader("أفضل 10 منتجات مبيعاً")
                
                # Filter out products with no sales
                top_products = [(p[0], p[3] or 0) for p in performance_data if p[3]]
                top_products.sort(key=lambda x: x[1], reverse=True)
                top_products = top_products[:10]  # Take only top 10
                
                if top_products:
                    df_top = pd.DataFrame(top_products, columns=["المنتج", "المبيعات"])
                    fig = px.bar(df_top, x="المنتج", y="المبيعات", title="أفضل 10 منتجات من حيث المبيعات")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("لا توجد بيانات مبيعات كافية للعرض في رسم بياني")
            else:
                st.info("لا توجد بيانات لعرضها")
    
    # Branch Management
    elif menu == "إدارة الفروع":
        st.title("إدارة الفروع")
        
        tab1, tab2, tab3, tab4 = st.tabs(["إضافة فرع", "تعديل فرع", "حذف فرع", "عرض الفروع"])
        
        with tab1:
            st.header("إضافة فرع جديد")
            
            name = st.text_input("اسم الفرع")
            address = st.text_input("عنوان الفرع")
            description = st.text_area("وصف الفرع")
            
            if st.button("إضافة الفرع"):
                if name:
                    try:
                        c.execute('''
                            INSERT INTO branches (name, address, description)
                            VALUES (?, ?, ?)
                        ''', (name, address, description))
                        
                        # Get the new branch id
                        branch_id = c.lastrowid
                        
                        # Add initial inventory entries for all products with 0 quantity
                        c.execute('SELECT id FROM products')
                        products = c.fetchall()
                        
                        for product_id in [p[0] for p in products]:
                            c.execute('''
                                INSERT INTO inventory (product_id, branch_id, quantity, last_updated)
                                VALUES (?, ?, ?, ?)
                            ''', (product_id, branch_id, 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
                        conn.commit()
                        st.success(f"تم إضافة الفرع '{name}' بنجاح")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء إضافة الفرع: {e}")
                else:
                    st.warning("الرجاء إدخال اسم الفرع")
        
        with tab2:
            st.header("تعديل فرع")
            
            # Get branches for dropdown
            c.execute("SELECT id, name FROM branches")
            branches = c.fetchall()
            branch_dict = {branch[0]: branch[1] for branch in branches}
            
            if branch_dict:
                branch_id = st.selectbox("اختر الفرع للتعديل", options=list(branch_dict.keys()), format_func=lambda x: branch_dict[x])
                
                # Get current branch data
                c.execute("SELECT name, address, description FROM branches WHERE id = ?", (branch_id,))
                branch_data = c.fetchone()
                
                if branch_data:
                    updated_name = st.text_input("اسم الفرع", value=branch_data[0])
                    updated_address = st.text_input("عنوان الفرع", value=branch_data[1] or "")
                    updated_description = st.text_area("وصف الفرع", value=branch_data[2] or "")
                    
                    if st.button("تحديث الفرع"):
                        try:
                            c.execute('''
                                UPDATE branches
                                SET name = ?, address = ?, description = ?
                                WHERE id = ?
                            ''', (updated_name, updated_address, updated_description, branch_id))
                            
                            conn.commit()
                            st.success(f"تم تحديث الفرع '{updated_name}' بنجاح")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء تحديث الفرع: {e}")
            else:
                st.info("لا توجد فروع لتعديلها")
        
        with tab3:
            st.header("حذف فرع")
            
            if branch_dict:
                branch_to_delete = st.selectbox("اختر الفرع للحذف", options=list(branch_dict.keys()), format_func=lambda x: branch_dict[x], key="delete_branch_select")
                
                # Check if branch has inventory or sales
                c.execute("SELECT SUM(quantity) FROM inventory WHERE branch_id = ?", (branch_to_delete,))
                inventory_count = c.fetchone()[0] or 0
                
                c.execute("SELECT COUNT(*) FROM sales WHERE branch_id = ?", (branch_to_delete,))
                sales_count = c.fetchone()[0]
                
                # Prevent deleting the main branch or last remaining branch
                is_main_branch = branch_to_delete == 1
                is_last_branch = len(branch_dict) == 1
                
                if is_main_branch:
                    st.error("لا يمكن حذف الفرع الرئيسي")
                elif is_last_branch:
                    st.error("لا يمكن حذف الفرع الأخير. يجب أن يكون هناك فرع واحد على الأقل")
                else:
                    st.write(f"الفرع: {branch_dict[branch_to_delete]}")
                    
                    if inventory_count > 0:
                        st.warning(f"هذا الفرع لديه {inventory_count} قطعة في المخزون. تأكد من نقل المخزون أو تصفيره قبل الحذف.")
                    
                    if sales_count > 0:
                        st.warning(f"هذا الفرع مرتبط بـ {sales_count} عمليات بيع سابقة.")
                    
                    # Confirmation checkbox
                    confirm_delete = st.checkbox("أنا متأكد من حذف هذا الفرع وأتفهم أن هذا الإجراء لا يمكن التراجع عنه", key="confirm_delete_branch")
                    
                    if st.button("حذف الفرع") and confirm_delete:
                        try:
                            # Delete related inventory records
                            c.execute("DELETE FROM inventory WHERE branch_id = ?", (branch_to_delete,))
                            # Delete branch
                            c.execute("DELETE FROM branches WHERE id = ?", (branch_to_delete,))
                            
                            conn.commit()
                            st.success(f"تم حذف الفرع '{branch_dict[branch_to_delete]}' بنجاح")
                            
                            # Reset current_branch if it was deleted
                            if st.session_state.current_branch == branch_to_delete:
                                st.session_state.current_branch = 1  # Set to main branch
                                st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء حذف الفرع: {e}")
            else:
                st.info("لا توجد فروع لحذفها")
        
        with tab4:
            st.header("عرض الفروع")
            
            # Get all branches
            c.execute('''
                SELECT b.id, b.name, b.address, b.description,
                       (SELECT COUNT(*) FROM inventory i WHERE i.branch_id = b.id) as inventory_count,
                       (SELECT SUM(i.quantity) FROM inventory i WHERE i.branch_id = b.id) as total_items
                FROM branches b
                ORDER BY b.id
            ''')
            branches_data = c.fetchall()
            
            if branches_data:
                branches_list = []
                for branch in branches_data:
                    branches_list.append({
                        "المعرف": branch[0],
                        "اسم الفرع": branch[1],
                        "العنوان": branch[2] or "",
                        "الوصف": branch[3] or "",
                        "عدد المنتجات": branch[4],
                        "إجمالي القطع": branch[5] or 0
                    })
                
                df_branches = pd.DataFrame(branches_list)
                st.table(df_branches)
            else:
                st.info("لا توجد فروع لعرضها")
    # User Management (admin only)
    elif menu == "إدارة المستخدمين" and st.session_state.role == 'admin':
        st.title("إدارة المستخدمين")
        
        tab1, tab2, tab3 = st.tabs(["إضافة مستخدم", "تعديل مستخدم", "عرض المستخدمين"])
        
        with tab1:
            st.header("إضافة مستخدم جديد")
            
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("اسم المستخدم")
                password = st.text_input("كلمة المرور", type="password")
                confirm_password = st.text_input("تأكيد كلمة المرور", type="password")
            
            with col2:
                role = st.selectbox("الدور", ["مستخدم", "مشرف", "admin"])
                active = st.checkbox("نشط", value=True)
                
                permissions_options = ["view", "add", "edit", "delete", "manage_users"]
                permissions = st.multiselect("الصلاحيات", options=permissions_options, default=["view"])
            
            if st.button("إضافة المستخدم"):
                if not username:
                    st.error("الرجاء إدخال اسم المستخدم")
                elif not password:
                    st.error("الرجاء إدخال كلمة المرور")
                elif password != confirm_password:
                    st.error("كلمة المرور وتأكيدها غير متطابقين")
                else:
                    try:
                        # Check if username already exists
                        c.execute("SELECT id FROM users WHERE username = ?", (username,))
                        if c.fetchone():
                            st.error("اسم المستخدم موجود بالفعل. الرجاء اختيار اسم مستخدم آخر.")
                        else:
                            # Insert new user
                            hashed_password = hash_password(password)
                            permissions_str = ",".join(permissions)
                            
                            c.execute('''
                                INSERT INTO users (username, password, role, permissions, active)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (username, hashed_password, role, permissions_str, 1 if active else 0))
                            
                            conn.commit()
                            st.success(f"تم إضافة المستخدم '{username}' بنجاح")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء إضافة المستخدم: {e}")
        
        with tab2:
            st.header("تعديل مستخدم")
            
            # Get users for dropdown
            c.execute("SELECT id, username FROM users")
            users = c.fetchall()
            user_dict = {user[0]: user[1] for user in users}
            
            if user_dict:
                user_id = st.selectbox("اختر المستخدم للتعديل", options=list(user_dict.keys()), format_func=lambda x: user_dict[x])
                
                # Get current user data
                c.execute("SELECT username, role, permissions, active FROM users WHERE id = ?", (user_id,))
                user_data = c.fetchone()
                
                if user_data:
                    username = user_data[0]
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        updated_username = st.text_input("اسم المستخدم", value=username)
                        update_password = st.checkbox("تحديث كلمة المرور")
                        updated_password = st.text_input("كلمة المرور الجديدة", type="password") if update_password else None
                        confirm_updated_password = st.text_input("تأكيد كلمة المرور الجديدة", type="password") if update_password else None
                    
                    with col2:
                        updated_role = st.selectbox("الدور", ["مستخدم", "مشرف", "admin"], index=["مستخدم", "مشرف", "admin"].index(user_data[1]))
                        updated_active = st.checkbox("نشط", value=user_data[3])
                        
                        current_permissions = user_data[2].split(",") if user_data[2] else []
                        permissions_options = ["view", "add", "edit", "delete", "manage_users"]
                        updated_permissions = st.multiselect("الصلاحيات", options=permissions_options, default=current_permissions)
                    
                    # Prevent changing admin user status if it's the admin user
                    is_admin_user = username == "admin"
                    if is_admin_user:
                        st.warning("المستخدم 'admin' هو مستخدم النظام الرئيسي. بعض الإعدادات لا يمكن تغييرها.")
                        updated_role = "admin"
                        updated_active = True
                    
                    if st.button("تحديث المستخدم"):
                        try:
                            # Validate data
                            error = None
                            
                            if update_password and not updated_password:
                                error = "الرجاء إدخال كلمة المرور الجديدة"
                            elif update_password and updated_password != confirm_updated_password:
                                error = "كلمة المرور الجديدة وتأكيدها غير متطابقين"
                            
                            if error:
                                st.error(error)
                            else:
                                # Update user
                                updates = []
                                params = []
                                
                                if updated_username != username:
                                    # Check if new username already exists
                                    c.execute("SELECT id FROM users WHERE username = ? AND id != ?", (updated_username, user_id))
                                    if c.fetchone():
                                        st.error("اسم المستخدم موجود بالفعل. الرجاء اختيار اسم مستخدم آخر.")
                                        return
                                    
                                    updates.append("username = ?")
                                    params.append(updated_username)
                                
                                if update_password:
                                    updates.append("password = ?")
                                    params.append(hash_password(updated_password))
                                
                                if not is_admin_user:
                                    updates.append("role = ?")
                                    params.append(updated_role)
                                    
                                    updates.append("active = ?")
                                    params.append(1 if updated_active else 0)
                                
                                updates.append("permissions = ?")
                                params.append(",".join(updated_permissions))
                                
                                # Add user_id to params
                                params.append(user_id)
                                
                                c.execute(f'''
                                    UPDATE users
                                    SET {", ".join(updates)}
                                    WHERE id = ?
                                ''', params)
                                
                                conn.commit()
                                st.success(f"تم تحديث المستخدم '{updated_username}' بنجاح")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء تحديث المستخدم: {e}")
            else:
                st.info("لا يوجد مستخدمين لتعديلهم")
        
        with tab3:
            st.header("عرض المستخدمين")
            
            # Get all users
            c.execute("SELECT id, username, role, permissions, active, created_at FROM users ORDER BY id")
            users_data = c.fetchall()
            
            if users_data:
                users_list = []
                for user in users_data:
                    users_list.append({
                        "المعرف": user[0],
                        "اسم المستخدم": user[1],
                        "الدور": user[2],
                        "الصلاحيات": user[3],
                        "الحالة": "نشط" if user[4] else "غير نشط",
                        "تاريخ الإنشاء": user[5]
                    })
                
                df_users = pd.DataFrame(users_list)
                st.table(df_users)
                
                # Add option to delete users
                st.subheader("حذف مستخدم")
                
                # Cannot delete admin user
                delete_user_dict = {u[0]: u[1] for u in users_data if u[1] != "admin"}
                
                if delete_user_dict:
                    user_to_delete = st.selectbox("اختر المستخدم للحذف", options=list(delete_user_dict.keys()), format_func=lambda x: delete_user_dict[x])
                    
                    # Confirmation checkbox
                    confirm_delete = st.checkbox("أنا متأكد من حذف هذا المستخدم وأتفهم أن هذا الإجراء لا يمكن التراجع عنه", key="confirm_delete_user")
                    
                    if st.button("حذف المستخدم") and confirm_delete:
                        try:
                            c.execute("DELETE FROM users WHERE id = ?", (user_to_delete,))
                            conn.commit()
                            st.success(f"تم حذف المستخدم '{delete_user_dict[user_to_delete]}' بنجاح")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء حذف المستخدم: {e}")
                else:
                    st.info("لا يمكن حذف المستخدم الرئيسي")
            else:
                st.info("لا يوجد مستخدمين لعرضهم")

# Main execution
if __name__ == "__main__":
    if st.session_state.authenticated:
        main_app()
    else:
        show_login()
