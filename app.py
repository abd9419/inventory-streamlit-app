# Import warnings and filter the numpy compatibility warning
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore")

# First import numpy and ensure it's loaded before pandas
try:
    import numpy
except ImportError:
    pass

# Import streamlit first as it's the main dependency
import streamlit as st
import os
import json
from datetime import datetime
import hashlib
import uuid
import io
import base64

# Try to safely import other dependencies
try:
    import pandas as pd
except Exception as e:
    st.error("Error importing pandas. Using simplified functionality.")
    
    # Create a minimal pandas-like implementation for basic functionality
    class MinimalDF:
        def __init__(self, data=None):
            self.data = data or []
            self.columns = []
        
        def iterrows(self):
            for i, row in enumerate(self.data):
                yield i, row
    
    class MinimalPandas:
        def DataFrame(self, data=None):
            return MinimalDF(data)
        
        def read_excel(self, file):
            st.error("Excel functionality not available due to pandas import error")
            return MinimalDF()
        
        def isna(self, val):
            return val is None
    
    pd = MinimalPandas()

try:
    import plotly.express as px
except Exception:
    # Create a minimal plotting replacement
    class MinimalPlotly:
        def pie(self, **kwargs):
            st.warning("Charts not available due to plotly import error")
            return None
        
        def bar(self, **kwargs):
            st.warning("Charts not available due to plotly import error")
            return None
    
    px = MinimalPlotly()

try:
    from PIL import Image
except Exception:
    # Create a minimal Image replacement
    class MinimalImage:
        @staticmethod
        def open(file):
            return None
        
        @staticmethod
        def save(path):
            pass
    
    Image = MinimalImage

# Set page configuration
st.set_page_config(
    page_title="RFID Inventory Management System",
    page_icon="📦",
    layout="wide"
)

# Initialize session state for storing data
if 'rfid_data' not in st.session_state:
    st.session_state.rfid_data = {}
if 'products' not in st.session_state:
    st.session_state.products = {}
if 'categories' not in st.session_state:
    st.session_state.categories = []
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'sales' not in st.session_state:
    st.session_state.sales = []
if 'branches' not in st.session_state:
    # Default main branch
    st.session_state.branches = {
        "main": {"name": "Main Branch", "address": "Main Location", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    }
if 'current_branch' not in st.session_state:
    st.session_state.current_branch = "main"
if 'transfers' not in st.session_state:
    st.session_state.transfers = []
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Upload"

# User management initialization
if 'users' not in st.session_state:
    # Default admin user (password: admin123)
    st.session_state.users = {
        "admin": {
            "password": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "admin",
            "permissions": ["view", "add", "edit", "delete", "manage_users"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "active": True
        }
    }

# Authentication state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_permissions' not in st.session_state:
    st.session_state.user_permissions = []

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)
os.makedirs('data/images', exist_ok=True)

# File paths
RFID_DATA_PATH = 'data/rfid_data.json'
PRODUCTS_PATH = 'data/products.json'
CATEGORIES_PATH = 'data/categories.json'
TRANSACTIONS_PATH = 'data/transactions.json'
SALES_PATH = 'data/sales.json'
BRANCHES_PATH = 'data/branches.json'
TRANSFERS_PATH = 'data/transfers.json'
USERS_PATH = 'data/users.json'

# Load data from files if they exist
def load_data():
    try:
        if os.path.exists(RFID_DATA_PATH):
            with open(RFID_DATA_PATH, 'r', encoding='utf-8') as f:
                st.session_state.rfid_data = json.load(f)
        
        if os.path.exists(PRODUCTS_PATH):
            with open(PRODUCTS_PATH, 'r', encoding='utf-8') as f:
                st.session_state.products = json.load(f)
        
        if os.path.exists(CATEGORIES_PATH):
            with open(CATEGORIES_PATH, 'r', encoding='utf-8') as f:
                st.session_state.categories = json.load(f)
        
        if os.path.exists(TRANSACTIONS_PATH):
            with open(TRANSACTIONS_PATH, 'r', encoding='utf-8') as f:
                st.session_state.transactions = json.load(f)
        
        if os.path.exists(SALES_PATH):
            with open(SALES_PATH, 'r', encoding='utf-8') as f:
                st.session_state.sales = json.load(f)
                
        if os.path.exists(BRANCHES_PATH):
            with open(BRANCHES_PATH, 'r', encoding='utf-8') as f:
                st.session_state.branches = json.load(f)
                
        if os.path.exists(TRANSFERS_PATH):
            with open(TRANSFERS_PATH, 'r', encoding='utf-8') as f:
                st.session_state.transfers = json.load(f)
                
        if os.path.exists(USERS_PATH):
            with open(USERS_PATH, 'r', encoding='utf-8') as f:
                st.session_state.users = json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

# Save data to files
def save_data():
    try:
        with open(RFID_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.rfid_data, f, ensure_ascii=False, indent=2)
        
        with open(PRODUCTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.products, f, ensure_ascii=False, indent=2)
        
        with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.categories, f, ensure_ascii=False, indent=2)
        
        with open(TRANSACTIONS_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.transactions, f, ensure_ascii=False, indent=2)
            
        with open(SALES_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.sales, f, ensure_ascii=False, indent=2)
            
        with open(BRANCHES_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.branches, f, ensure_ascii=False, indent=2)
            
        with open(TRANSFERS_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.transfers, f, ensure_ascii=False, indent=2)
            
        with open(USERS_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    return hash_password(password) == hashed_password

def authenticate_user(username, password):
    if username in st.session_state.users:
        user = st.session_state.users[username]
        if user.get('active', True) and verify_password(password, user['password']):
            return True, user
    return False, None

def has_permission(permission):
    return permission in st.session_state.user_permissions

def require_permission(permission):
    if not has_permission(permission):
        st.error(f"Access denied. Required permission: {permission}")
        return False
    return True

# User management functions
def add_user(username, password, role, permissions):
    if username in st.session_state.users:
        return False, f"User {username} already exists"
    
    st.session_state.users[username] = {
        "password": hash_password(password),
        "role": role,
        "permissions": permissions,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active": True,
        "created_by": st.session_state.current_user
    }
    save_data()
    return True, f"User {username} created successfully"

def update_user(username, password=None, role=None, permissions=None, active=None):
    if username not in st.session_state.users:
        return False, f"User {username} not found"
    
    user = st.session_state.users[username]
    if password:
        user['password'] = hash_password(password)
    if role:
        user['role'] = role
    if permissions is not None:
        user['permissions'] = permissions
    if active is not None:
        user['active'] = active
    
    user['modified_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user['modified_by'] = st.session_state.current_user
    
    save_data()
    return True, f"User {username} updated successfully"

def delete_user(username):
    if username not in st.session_state.users:
        return False, f"User {username} not found"
    
    if username == "admin":
        return False, "Cannot delete admin user"
    
    del st.session_state.users[username]
    save_data()
    return True, f"User {username} deleted successfully"

# Load data at startup
load_data()

# Login page
def show_login_page():
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🔐 RFID Inventory Management System</h1>
        <h3>Admin Login</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login", use_container_width=True):
                    if username and password:
                        success, user = authenticate_user(username, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.current_user = username
                            st.session_state.user_role = user['role']
                            # Ensure 'permissions' key exists, default to empty list if not
                            st.session_state.user_permissions = user.get('permissions', [])
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Please enter both username and password")
    
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; background-color: #f0f2f6; border-radius: 0.5rem;">
        <h4>Default Admin Credentials:</h4>
        <p><strong>Username:</strong> admin</p>
        <p><strong>Password:</strong> admin123</p>
        <p><em>Please change the default password after first login</em></p>
    </div>
    """, unsafe_allow_html=True)

# Main application
def show_main_app():
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
        }
        .subheader {
            font-size: 1.5rem;
            font-weight: bold;
            color: #0D47A1;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        .card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            margin-bottom: 1rem;
        }
        .success-msg {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
        }
        .warning-msg {
            background-color: #fff3cd;
            color: #856404;
            padding: 1rem;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
        }
        .info-box {
            background-color: #e3f2fd;
            padding: 1rem;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
        }
        .user-info {
            background-color: #e8f5e8;
            padding: 0.5rem;
            border-radius: 0.25rem;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Application header with user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="main-header">RFID Inventory Management System</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="user-info">
            <strong>User:</strong> {st.session_state.current_user}<br>
            <strong>Role:</strong> {st.session_state.user_role}
        </div>
        """, unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.user_role = None
            st.session_state.user_permissions = []
            st.rerun()

    # Navigation tabs (filtered by permissions)
    tabs = []
    if has_permission("view"):
        tabs.extend(["Upload", "Products", "Categories", "Inventory", "Reports", "Sales", "Branches"])
    if has_permission("manage_users"):
        tabs.append("User Management")
    
    if not tabs:
        st.error("You don't have permission to access any features.")
        return
    
    cols = st.columns(len(tabs))
    for i, tab in enumerate(tabs):
        if cols[i].button(tab, key=f"tab_{tab}", use_container_width=True):
            st.session_state.active_tab = tab

    st.markdown("---")

    # Branch selector (show in all tabs except Branches and User Management)
    if st.session_state.active_tab not in ["Branches", "User Management"] and len(st.session_state.branches) > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            branch_options = {bid: f"{data['name']}" for bid, data in st.session_state.branches.items()}
            selected_branch = st.selectbox("Select Branch", list(branch_options.values()), key="branch_selector")
            selected_branch_id = list(branch_options.keys())[list(branch_options.values()).index(selected_branch)]
            st.session_state.current_branch = selected_branch_id
        with col2:
            st.markdown(f"<div style='padding-top: 2rem;'>Current Branch: <b>{branch_options[selected_branch_id]}</b></div>", unsafe_allow_html=True)
        
        st.markdown("---")

    # User Management Tab
    if st.session_state.active_tab == "User Management":
        if not require_permission("manage_users"):
            return
            
        st.markdown('<div class="subheader">User Management</div>', unsafe_allow_html=True)
        
        # Add new user
        with st.expander("Add New User", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["user", "manager", "admin"])
            
            with col2:
                st.markdown("**Permissions:**")
                available_permissions = ["view", "add", "edit", "delete", "manage_users"]
                selected_permissions = []
                
                for perm in available_permissions:
                    if st.checkbox(perm.replace("_", " ").title(), key=f"new_perm_{perm}"):
                        selected_permissions.append(perm)
            
            if st.button("Add User"):
                if new_username and new_password:
                    success, message = add_user(new_username, new_password, new_role, selected_permissions)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Username and password are required")
        
        # List existing users
        st.markdown('<div class="subheader">Existing Users</div>', unsafe_allow_html=True)
        
        for username, user_data in st.session_state.users.items():
            with st.expander(f"👤 {username} ({user_data['role']})", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Role:** {user_data['role']}")
                    st.markdown(f"**Active:** {'Yes' if user_data.get('active', True) else 'No'}")
                    st.markdown(f"**Created:** {user_data.get('created_at', 'Unknown')}")
                    if 'created_by' in user_data:
                        st.markdown(f"**Created by:** {user_data['created_by']}")
                
                with col2:
                    st.markdown("**Permissions:**")
                    for perm in user_data.get('permissions', []):
                        st.markdown(f"- {perm.replace('_', ' ').title()}")
                
                # User management actions
                if username != "admin":
                    st.markdown("---")
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button(f"Toggle Status", key=f"toggle_{username}"):
                            current_status = user_data.get('active', True)
                            success, message = update_user(username, active=not current_status)
                            if success:
                                st.success(f"User {username} {'activated' if not current_status else 'deactivated'}")
                                st.rerun()
                    
                    with action_col2:
                        if st.button(f"Reset Password", key=f"reset_{username}"):
                            new_pwd = f"{username}123"
                            success, message = update_user(username, password=new_pwd)
                            if success:
                                st.success(f"Password reset to: {new_pwd}")
                            else:
                                st.error(message)
                    
                    with action_col3:
                        if st.button(f"Delete", key=f"delete_{username}"):
                            success, message = delete_user(username)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

    # Other tabs with basic functionality
    elif st.session_state.active_tab == "Upload":
        if not require_permission("view"):
            return
        st.markdown('<div class="subheader">Upload RFID Tags</div>', unsafe_allow_html=True)
        st.info("Upload functionality requires the full implementation")

    elif st.session_state.active_tab == "Products":
        if not require_permission("view"):
            return
        st.markdown('<div class="subheader">Manage Products</div>', unsafe_allow_html=True)
        st.info("Product management functionality requires the full implementation")

    elif st.session_state.active_tab == "Categories":
        if not require_permission("view"):
            return
        st.markdown('<div class="subheader">Manage Categories</div>', unsafe_allow_html=True)
        st.info("Category management functionality requires the full implementation")

    elif st.session_state.active_tab == "Inventory":
        if not require_permission("view"):
            return
        st.markdown('<div class="subheader">Inventory Overview</div>', unsafe_allow_html=True)
        st.info("Inventory overview functionality requires the full implementation")

    elif st.session_state.active_tab == "Reports":
        if not require_permission("view"):
            return
        st.markdown('<div class="subheader">Reports</div>', unsafe_allow_html=True)
        st.info("Reports functionality requires the full implementation")

    elif st.session_state.active_tab == "Sales":
        if not require_permission("view"):
            return
        st.markdown('<div class="subheader">Sales Management</div>', unsafe_allow_html=True)
        st.info("Sales management functionality requires the full implementation")

    elif st.session_state.active_tab == "Branches":
        if not require_permission("view"):
            return
        st.markdown('<div class="subheader">Manage Branches</div>', unsafe_allow_html=True)
        st.info("Branch management functionality requires the full implementation")

# Main execution
if __name__ == "__main__":
    # Check authentication
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()
