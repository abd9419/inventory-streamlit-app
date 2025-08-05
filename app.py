# Import warnings and filter the numpy compatibility warning
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore")

# Import required libraries
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
from PIL import Image
import io
import base64
import hashlib
import uuid

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
            "active": True,
            "name": "Administrator"
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
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

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
        
        # Ensure admin user always has all permissions
        if username == "admin" and user.get('role') == "admin" and 'permissions' not in user:
            user['permissions'] = ["view", "add", "edit", "delete", "manage_users"]
            
        if user.get('active', True) and verify_password(password, user['password']):
            return True, user
    return False, None

def has_permission(permission):
    # Admin always has all permissions
    if st.session_state.user_role == "admin":
        return True
    return permission in st.session_state.user_permissions

def require_permission(permission):
    if not has_permission(permission):
        st.error(f"Access denied. Required permission: {permission}")
        return False
    return True
# User management functions
def add_user(username, password, role, permissions=None, name=None):
    if username in st.session_state.users:
        return False, f"User {username} already exists"
    
    if permissions is None:
        permissions = []
    
    if name is None:
        name = username.capitalize()
    
    st.session_state.users[username] = {
        "password": hash_password(password),
        "role": role,
        "permissions": permissions,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active": True,
        "created_by": st.session_state.current_user,
        "name": name
    }
    save_data()
    return True, f"User {username} created successfully"

def update_user(username, password=None, role=None, permissions=None, active=None, name=None):
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
    if name:
        user['name'] = name
    
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

# RFID and Product Management Functions
def add_rfid_tag(rfid, product_id, category, branch_id=None, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Default to current branch if not specified
    if branch_id is None:
        branch_id = st.session_state.current_branch
    
    if rfid in st.session_state.rfid_data:
        return False, f"RFID tag {rfid} already exists for product {st.session_state.rfid_data[rfid]['product_id']}"
    
    st.session_state.rfid_data[rfid] = {
        'product_id': product_id,
        'category': category,
        'branch_id': branch_id,
        'added_at': timestamp
    }
    
    # Add to transactions
    st.session_state.transactions.append({
        'rfid': rfid,
        'product_id': product_id,
        'branch_id': branch_id,
        'action': 'added',
        'timestamp': timestamp
    })
    
    save_data()
    return True, f"RFID tag {rfid} added successfully"
def process_excel(df):
    results = []
    for _, row in df.iterrows():
        try:
            rfid = str(row['rfid']).strip()
            if rfid in st.session_state.rfid_data:
                product_id = st.session_state.rfid_data[rfid]['product_id']
                product_name = st.session_state.products[product_id]['name'] if product_id in st.session_state.products else "Unknown"
                results.append({
                    'rfid': rfid,
                    'status': 'existing',
                    'message': f"Tag already exists for product {product_name} (ID: {product_id})"
                })
            else:
                results.append({
                    'rfid': rfid,
                    'status': 'new',
                    'message': "New RFID tag"
                })
        except Exception as e:
            results.append({
                'rfid': rfid if 'rfid' in locals() else "Error",
                'status': 'error',
                'message': str(e)
            })
    
    return results

# Product Functions
def add_product(product_id, name, description, category, image=None):
    if product_id in st.session_state.products:
        return False, f"Product ID {product_id} already exists"
    
    image_path = None
    if image is not None:
        try:
            # Create a unique filename with timestamp and product_id
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            image_filename = f"data/images/{product_id}_{timestamp}.jpg"
            # Ensure directory exists
            os.makedirs(os.path.dirname(image_filename), exist_ok=True)
            # Save the image
            image.save(image_filename)
            image_path = image_filename
        except Exception as e:
            return False, f"Failed to save image: {str(e)}"
    
    st.session_state.products[product_id] = {
        'name': name,
        'description': description,
        'category': category,
        'image': image_path
    }
    
    save_data()
    return True, f"Product {name} added successfully"

def delete_product(product_id):
    if product_id not in st.session_state.products:
        return False, f"Product ID {product_id} not found"
    
    # Check if there are RFID tags associated with this product
    associated_rfids = [rfid for rfid, data in st.session_state.rfid_data.items() if data['product_id'] == product_id]
    if associated_rfids:
        return False, f"Cannot delete product with {len(associated_rfids)} associated RFID tags. Remove the tags first."
    
    # Get the image path to delete the file
    image_path = st.session_state.products[product_id].get('image')
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            # Log the error but continue with deletion
            st.warning(f"Error deleting product image: {str(e)}")
    
    del st.session_state.products[product_id]
    save_data()
    return True, f"Product {product_id} deleted successfully"

def update_product(product_id, name=None, description=None, category=None, image=None):
    if product_id not in st.session_state.products:
        return False, f"Product ID {product_id} not found"
    
    product = st.session_state.products[product_id]
    
    if name is not None:
        product['name'] = name
    
    if description is not None:
        product['description'] = description
    
    if category is not None:
        product['category'] = category
    
    if image is not None:
        try:
            # Delete the old image if it exists
            old_image_path = product.get('image')
            if old_image_path and os.path.exists(old_image_path):
                os.remove(old_image_path)
            
            # Save the new image
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            image_filename = f"data/images/{product_id}_{timestamp}.jpg"
            image.save(image_filename)
            product['image'] = image_filename
        except Exception as e:
            return False, f"Failed to update image: {str(e)}"
    
    save_data()
    return True, f"Product {product_id} updated successfully"
# Category Functions
def add_category(category_name):
    if category_name in st.session_state.categories:
        return False, f"Category {category_name} already exists"
    
    st.session_state.categories.append(category_name)
    save_data()
    return True, f"Category {category_name} added successfully"

def delete_category(category_name):
    if category_name not in st.session_state.categories:
        return False, f"Category {category_name} not found"
    
    # Check if there are products in this category
    products_in_category = [pid for pid, data in st.session_state.products.items() if data['category'] == category_name]
    if products_in_category:
        return False, f"Cannot delete category with {len(products_in_category)} associated products. Change their category first."
    
    st.session_state.categories.remove(category_name)
    save_data()
    return True, f"Category {category_name} deleted successfully"

# Branch Functions
def add_branch(branch_id, name, address):
    if branch_id in st.session_state.branches:
        return False, f"Branch ID {branch_id} already exists"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    st.session_state.branches[branch_id] = {
        'name': name,
        'address': address,
        'created_at': timestamp
    }
    
    save_data()
    return True, f"Branch {name} added successfully"

def delete_branch(branch_id):
    if branch_id not in st.session_state.branches:
        return False, f"Branch ID {branch_id} not found"
    
    if branch_id == "main":
        return False, "Cannot delete the main branch"
    
    # Check if there are RFID tags in this branch
    rfids_in_branch = [rfid for rfid, data in st.session_state.rfid_data.items() if data['branch_id'] == branch_id]
    if rfids_in_branch:
        return False, f"Cannot delete branch with {len(rfids_in_branch)} items. Transfer them first."
    
    del st.session_state.branches[branch_id]
    save_data()
    return True, f"Branch {branch_id} deleted successfully"

def update_branch(branch_id, name=None, address=None):
    if branch_id not in st.session_state.branches:
        return False, f"Branch ID {branch_id} not found"
    
    branch = st.session_state.branches[branch_id]
    
    if name is not None:
        branch['name'] = name
    
    if address is not None:
        branch['address'] = address
    
    save_data()
    return True, f"Branch {branch_id} updated successfully"

# Transfer Functions
def transfer_product(rfid, to_branch_id, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if rfid not in st.session_state.rfid_data:
        return False, f"RFID tag {rfid} not found in inventory"
    
    if to_branch_id not in st.session_state.branches:
        return False, f"Branch {to_branch_id} does not exist"
    
    from_branch_id = st.session_state.rfid_data[rfid]['branch_id']
    
    if from_branch_id == to_branch_id:
        return False, f"Item is already in branch {to_branch_id}"
    
    product_id = st.session_state.rfid_data[rfid]['product_id']
    product_name = st.session_state.products[product_id]['name'] if product_id in st.session_state.products else "Unknown"
    
    # Update the product's branch
    st.session_state.rfid_data[rfid]['branch_id'] = to_branch_id
    
    # Record the transfer
    transfer_record = {
        'rfid': rfid,
        'product_id': product_id,
        'product_name': product_name,
        'from_branch_id': from_branch_id,
        'to_branch_id': to_branch_id,
        'timestamp': timestamp
    }
    
    st.session_state.transfers.append(transfer_record)
    
    # Add to transactions
    st.session_state.transactions.append({
        'rfid': rfid,
        'product_id': product_id,
        'from_branch_id': from_branch_id,
        'to_branch_id': to_branch_id,
        'action': 'transferred',
        'timestamp': timestamp
    })
    
    save_data()
    return True, f"Product {product_name} with RFID {rfid} transferred from {st.session_state.branches[from_branch_id]['name']} to {st.session_state.branches[to_branch_id]['name']}"
# Sales Functions
def process_sale(rfid, sale_price=None, sale_date=None):
    if sale_date is None:
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if rfid not in st.session_state.rfid_data:
        return False, f"RFID tag {rfid} not found in inventory"
    
    product_id = st.session_state.rfid_data[rfid]['product_id']
    product_name = st.session_state.products[product_id]['name'] if product_id in st.session_state.products else "Unknown"
    category = st.session_state.rfid_data[rfid]['category']
    branch_id = st.session_state.rfid_data[rfid]['branch_id']
    
    # Add to sales record
    sale_record = {
        'rfid': rfid,
        'product_id': product_id,
        'product_name': product_name,
        'category': category,
        'branch_id': branch_id,
        'sale_date': sale_date,
        'sale_price': sale_price
    }
    
    st.session_state.sales.append(sale_record)
    
    # Add to transactions
    st.session_state.transactions.append({
        'rfid': rfid,
        'product_id': product_id,
        'branch_id': branch_id,
        'action': 'sold',
        'timestamp': sale_date
    })
    
    # Remove from inventory
    del st.session_state.rfid_data[rfid]
    
    save_data()
    return True, f"Product {product_name} with RFID {rfid} marked as sold from {st.session_state.branches[branch_id]['name']}"

def process_sales_excel(df):
    results = []
    for _, row in df.iterrows():
        try:
            # Ensure RFID is converted to string and stripped of whitespace
            if 'rfid' not in row or pd.isna(row['rfid']):
                results.append({
                    'rfid': "Missing",
                    'product_name': "Unknown",
                    'status': 'error',
                    'message': "Missing RFID tag in row"
                })
                continue
                
            rfid = str(row['rfid']).strip()
            
            # Check if sale_price column exists and is valid
            sale_price = None
            if 'sale_price' in df.columns and not pd.isna(row['sale_price']):
                try:
                    sale_price = float(row['sale_price'])
                except (ValueError, TypeError):
                    sale_price = None
            
            # Check if sale_date column exists and is valid
            sale_date = None
            if 'sale_date' in df.columns and not pd.isna(row['sale_date']):
                try:
                    if isinstance(row['sale_date'], str):
                        sale_date = datetime.strptime(row['sale_date'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        sale_date = row['sale_date'].strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    sale_date = None
            
            if rfid in st.session_state.rfid_data:
                product_id = st.session_state.rfid_data[rfid]['product_id']
                product_name = st.session_state.products[product_id]['name'] if product_id in st.session_state.products else "Unknown"
                
                success, message = process_sale(rfid, sale_price, sale_date)
                
                results.append({
                    'rfid': rfid,
                    'product_name': product_name,
                    'status': 'sold' if success else 'error',
                    'message': message
                })
            else:
                results.append({
                    'rfid': rfid,
                    'product_name': "Unknown",
                    'status': 'error',
                    'message': "RFID tag not found in inventory"
                })
        except Exception as e:
            results.append({
                'rfid': rfid if 'rfid' in locals() else "Error",
                'product_name': "Unknown",
                'status': 'error',
                'message': str(e)
            })
    
    return results

# Load data at startup
load_data()

# Custom CSS
def load_css():
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

# Login page
def show_login_page():
    load_css()
    
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
                            # For admin user, always set all permissions
                            if username == "admin" and user.get('role') == "admin":
                                permissions = ["view", "add", "edit", "delete", "manage_users"]
                            else:
                                permissions = user.get('permissions', [])
                                
                            st.session_state.authenticated = True
                            st.session_state.current_user = username
                            st.session_state.user_role = user.get('role', 'user')
                            st.session_state.user_permissions = permissions
                            st.session_state.user_name = user.get('name', username.capitalize())
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
# Tab Functions
def upload_tab():
    if not require_permission("view"):
        return
        
    st.markdown('<div class="subheader">Upload RFID Tags</div>', unsafe_allow_html=True)
    
    with st.expander("Instructions", expanded=False):
        st.info("""
        1. Upload an Excel file containing RFID tags.
        2. The Excel file must have a column named 'rfid'.
        3. The system will check if the tags already exist and show their status.
        4. For new tags, you can assign them to products.
        """)
    
    uploaded_file = st.file_uploader("Upload Excel file with RFID tags", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            
            if 'rfid' not in df.columns:
                st.error("The Excel file must contain a column named 'rfid'")
            else:
                # Process the uploaded file
                results = process_excel(df)
                
                # Display results
                st.markdown('<div class="subheader">Results</div>', unsafe_allow_html=True)
                
                # Count statuses
                existing_count = sum(1 for r in results if r['status'] == 'existing')
                new_count = sum(1 for r in results if r['status'] == 'new')
                error_count = sum(1 for r in results if r['status'] == 'error')
                
                # Display summary
                col1, col2, col3 = st.columns(3)
                col1.metric("Existing Tags", existing_count)
                col2.metric("New Tags", new_count)
                col3.metric("Errors", error_count)
                
                # Display tables by status
                if existing_count > 0:
                    with st.expander("Existing Tags", expanded=True):
                        existing_df = pd.DataFrame([r for r in results if r['status'] == 'existing'])
                        st.dataframe(existing_df)
                
                if new_count > 0:
                    with st.expander("New Tags", expanded=True):
                        new_df = pd.DataFrame([r for r in results if r['status'] == 'new'])
                        st.dataframe(new_df)
                        
                        # Let user assign these new tags to products
                        st.markdown('<div class="subheader">Assign Products to New RFID Tags</div>', unsafe_allow_html=True)
                        
                        # Create a product selection for each new tag
                        new_tags = [r['rfid'] for r in results if r['status'] == 'new']
                        
                        if not st.session_state.products:
                            st.warning("No products available. Please add products first.")
                        elif not st.session_state.categories:
                            st.warning("No categories available. Please add categories first.")
                        else:
                            # Batch assignment
                            col1, col2 = st.columns(2)
                            with col1:
                                selected_product_id = st.selectbox("Select Product for Batch Assignment", 
                                                                 options=list(st.session_state.products.keys()),
                                                                 format_func=lambda x: f"{st.session_state.products[x]['name']} (ID: {x})")
                            with col2:
                                selected_category = st.selectbox("Select Category for Batch Assignment",
                                                               options=st.session_state.categories)
                            
                            if st.button("Batch Assign Selected Product to All New RFID Tags"):
                                if require_permission("add"):
                                    success_count = 0
                                    for rfid in new_tags:
                                        success, _ = add_rfid_tag(rfid, selected_product_id, selected_category)
                                        if success:
                                            success_count += 1
                                    
                                    st.success(f"Successfully assigned product to {success_count} out of {len(new_tags)} RFID tags")
                                    st.rerun()
                            
                            # Individual assignment
                            st.markdown("---")
                            st.markdown("**Individual Assignment**")
                            
                            for rfid in new_tags:
                                st.markdown(f"**RFID: {rfid}**")
                                col1, col2, col3 = st.columns([2, 1, 1])
                                
                                with col1:
                                    product_id = st.selectbox(f"Product for {rfid}", 
                                                            options=list(st.session_state.products.keys()),
                                                            format_func=lambda x: f"{st.session_state.products[x]['name']} (ID: {x})",
                                                            key=f"product_{rfid}")
                                
                                with col2:
                                    category = st.selectbox(f"Category for {rfid}", 
                                                          options=st.session_state.categories,
                                                          key=f"category_{rfid}")
                                
                                with col3:
                                    if st.button("Assign", key=f"assign_{rfid}"):
                                        if require_permission("add"):
                                            success, message = add_rfid_tag(rfid, product_id, category)
                                            if success:
                                                st.success(message)
                                            else:
                                                st.error(message)
                
                if error_count > 0:
                    with st.expander("Errors", expanded=True):
                        error_df = pd.DataFrame([r for r in results if r['status'] == 'error'])
                        st.dataframe(error_df)
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
def product_tab():
    if not require_permission("view"):
        return
    
    st.markdown('<div class="subheader">Product Management</div>', unsafe_allow_html=True)
    
    # Add new product
    with st.expander("Add New Product", expanded=False):
        if not has_permission("add"):
            st.warning("You don't have permission to add products")
        else:
            with st.form("add_product_form"):
                product_id = st.text_input("Product ID")
                name = st.text_input("Product Name")
                description = st.text_area("Description")
                
                if st.session_state.categories:
                    category = st.selectbox("Category", options=st.session_state.categories)
                else:
                    st.warning("No categories available. Please add categories first.")
                    category = None
                
                image = st.file_uploader("Product Image", type=["jpg", "jpeg", "png"])
                
                submit = st.form_submit_button("Add Product")
                
                if submit and product_id and name and category:
                    if image is not None:
                        try:
                            image_data = Image.open(image)
                            success, message = add_product(product_id, name, description, category, image_data)
                        except Exception as e:
                            success = False
                            message = f"Error processing image: {str(e)}"
                    else:
                        success, message = add_product(product_id, name, description, category)
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                elif submit:
                    st.error("Product ID, Name, and Category are required")
    
    # Manage categories
    with st.expander("Manage Categories", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Add Category**")
            if has_permission("add"):
                with st.form("add_category_form"):
                    category_name = st.text_input("Category Name")
                    submit = st.form_submit_button("Add Category")
                    
                    if submit and category_name:
                        success, message = add_category(category_name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    elif submit:
                        st.error("Category name is required")
            else:
                st.warning("You don't have permission to add categories")
        
        with col2:
            st.markdown("**Delete Category**")
            if has_permission("delete"):
                if st.session_state.categories:
                    with st.form("delete_category_form"):
                        category_to_delete = st.selectbox("Select Category", options=st.session_state.categories)
                        submit = st.form_submit_button("Delete Category")
                        
                        if submit and category_to_delete:
                            success, message = delete_category(category_to_delete)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                else:
                    st.info("No categories to delete")
            else:
                st.warning("You don't have permission to delete categories")
    
    # Display products
    st.markdown("### Products")
    
    if not st.session_state.products:
        st.info("No products available")
    else:
        # Search and filter
        search = st.text_input("Search Products", placeholder="Enter product name or ID")
        
        if st.session_state.categories:
            filter_category = st.multiselect("Filter by Category", options=["All"] + st.session_state.categories, default=["All"])
        else:
            filter_category = ["All"]
        
        # Prepare filtered data
        filtered_products = {}
        
        for pid, product in st.session_state.products.items():
            # Apply search filter
            if search and search.lower() not in product['name'].lower() and search.lower() not in pid.lower():
                continue
            
            # Apply category filter
            if "All" not in filter_category and product['category'] not in filter_category:
                continue
            
            filtered_products[pid] = product
        
        if not filtered_products:
            st.info("No products match the search/filter criteria")
        else:
            # Display products in a grid
            cols = st.columns(3)
            
            for i, (pid, product) in enumerate(filtered_products.items()):
                col_index = i % 3
                
                with cols[col_index]:
                    with st.container():
                        st.markdown(f"**{product['name']}**")
                        st.markdown(f"ID: {pid}")
                        st.markdown(f"Category: {product['category']}")
                        
                        # Display image if available
                        if product.get('image') and os.path.exists(product['image']):
                            try:
                                img = Image.open(product['image'])
                                st.image(img, width=200)
                            except Exception as e:
                                st.error(f"Error loading image: {str(e)}")
                        
                        st.markdown(f"Description: {product['description'] if product['description'] else 'No description'}")
                        
                        # Edit/Delete buttons
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if has_permission("edit"):
                                if st.button("Edit", key=f"edit_{pid}"):
                                    st.session_state.edit_product_id = pid
                            else:
                                st.markdown("*Edit*")
                        
                        with col2:
                            if has_permission("delete"):
                                if st.button("Delete", key=f"delete_{pid}"):
                                    success, message = delete_product(pid)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                            else:
                                st.markdown("*Delete*")
                        
                        st.markdown("---")
        
        # Handle product editing
        if hasattr(st.session_state, 'edit_product_id'):
            pid = st.session_state.edit_product_id
            
            if pid in st.session_state.products:
                st.markdown(f"### Edit Product: {st.session_state.products[pid]['name']}")
                
                with st.form("edit_product_form"):
                    name = st.text_input("Product Name", value=st.session_state.products[pid]['name'])
                    description = st.text_area("Description", value=st.session_state.products[pid]['description'])
                    
                    if st.session_state.categories:
                        category = st.selectbox("Category", 
                                            options=st.session_state.categories,
                                            index=st.session_state.categories.index(st.session_state.products[pid]['category']) if st.session_state.products[pid]['category'] in st.session_state.categories else 0)
                    else:
                        category = None
                        st.warning("No categories available")
                    
                    st.markdown("Upload new image (leave empty to keep current image)")
                    image = st.file_uploader("Product Image", type=["jpg", "jpeg", "png"], key="edit_image")
                    
                    cancel_col, submit_col = st.columns(2)
                    
                    with cancel_col:
                        if st.form_submit_button("Cancel"):
                            del st.session_state.edit_product_id
                            st.rerun()
                    
                    with submit_col:
                        submit = st.form_submit_button("Update Product")
                        
                        if submit:
                            if image is not None:
                                try:
                                    image_data = Image.open(image)
                                    success, message = update_product(pid, name, description, category, image_data)
                                except Exception as e:
                                    success = False
                                    message = f"Error processing image: {str(e)}"
                            else:
                                success, message = update_product(pid, name, description, category)
                            
                            if success:
                                st.success(message)
                                del st.session_state.edit_product_id
                                st.rerun()
                            else:
                                st.error(message)
def inventory_tab():
    if not require_permission("view"):
        return
    
    st.markdown('<div class="subheader">Inventory Management</div>', unsafe_allow_html=True)
    
    # Branch selector
    st.markdown("### Branch Selection")
    
    branches = list(st.session_state.branches.keys())
    branch_names = [st.session_state.branches[b]['name'] for b in branches]
    
    selected_branch_index = branches.index(st.session_state.current_branch) if st.session_state.current_branch in branches else 0
    selected_branch = st.selectbox("Select Branch", options=branches, format_func=lambda x: st.session_state.branches[x]['name'], index=selected_branch_index)
    
    if selected_branch != st.session_state.current_branch:
        st.session_state.current_branch = selected_branch
    
    # Branch management
    with st.expander("Branch Management", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Add Branch**")
            if has_permission("add"):
                with st.form("add_branch_form"):
                    branch_id = st.text_input("Branch ID")
                    branch_name = st.text_input("Branch Name")
                    branch_address = st.text_area("Branch Address")
                    
                    submit = st.form_submit_button("Add Branch")
                    
                    if submit and branch_id and branch_name:
                        success, message = add_branch(branch_id, branch_name, branch_address)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    elif submit:
                        st.error("Branch ID and Name are required")
            else:
                st.warning("You don't have permission to add branches")
        
        with col2:
            st.markdown("**Update/Delete Branch**")
            if has_permission("edit") or has_permission("delete"):
                branch_to_manage = st.selectbox("Select Branch to Manage", 
                                             options=branches,
                                             format_func=lambda x: st.session_state.branches[x]['name'])
                
                if branch_to_manage:
                    st.markdown(f"**Branch Details: {st.session_state.branches[branch_to_manage]['name']}**")
                    st.markdown(f"Address: {st.session_state.branches[branch_to_manage]['address']}")
                    
                    if has_permission("edit"):
                        st.markdown("**Update Branch**")
                        with st.form("update_branch_form"):
                            new_name = st.text_input("New Name", value=st.session_state.branches[branch_to_manage]['name'])
                            new_address = st.text_area("New Address", value=st.session_state.branches[branch_to_manage]['address'])
                            
                            submit = st.form_submit_button("Update Branch")
                            
                            if submit:
                                success, message = update_branch(branch_to_manage, new_name, new_address)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                    
                    if has_permission("delete") and branch_to_manage != "main":
                        if st.button("Delete Branch"):
                            success, message = delete_branch(branch_to_manage)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            else:
                st.warning("You don't have permission to edit or delete branches")
    
    # Display inventory for selected branch
    st.markdown(f"### Inventory for {st.session_state.branches[selected_branch]['name']}")
    
    # Filter inventory by branch
    branch_inventory = {rfid: data for rfid, data in st.session_state.rfid_data.items() 
                      if data['branch_id'] == selected_branch}
    
    if not branch_inventory:
        st.info(f"No items in {st.session_state.branches[selected_branch]['name']}")
    else:
        # Convert to DataFrame for display
        inventory_data = []
        for rfid, data in branch_inventory.items():
            product_id = data['product_id']
            product_name = st.session_state.products[product_id]['name'] if product_id in st.session_state.products else "Unknown"
            category = data['category']
            added_at = data['added_at']
            
            inventory_data.append({
                'RFID': rfid,
                'Product ID': product_id,
                'Product Name': product_name,
                'Category': category,
                'Added At': added_at
            })
        
        inventory_df = pd.DataFrame(inventory_data)
        
        # Search and filter
        search = st.text_input("Search Inventory", placeholder="Enter RFID, product name or ID")
        
        if st.session_state.categories:
            filter_category = st.multiselect("Filter by Category", options=["All"] + st.session_state.categories, default=["All"])
        else:
            filter_category = ["All"]
        
        # Apply filters
        filtered_df = inventory_df.copy()
        
        if search:
            filtered_df = filtered_df[
                filtered_df['RFID'].str.contains(search, case=False) |
                filtered_df['Product ID'].str.contains(search, case=False) |
                filtered_df['Product Name'].str.contains(search, case=False)
            ]
        
        if "All" not in filter_category:
            filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]
        
        # Display inventory
        if filtered_df.empty:
            st.info("No items match the search/filter criteria")
        else:
            st.dataframe(filtered_df, use_container_width=True)
            
            # Summary metrics
            st.markdown("### Inventory Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Items", len(filtered_df))
            
            with col2:
                categories_count = filtered_df['Category'].value_counts()
                most_common_category = categories_count.index[0] if not categories_count.empty else "None"
                st.metric("Most Common Category", most_common_category, categories_count[most_common_category] if not categories_count.empty else 0)
            
            with col3:
                products_count = filtered_df['Product Name'].value_counts()
                most_common_product = products_count.index[0] if not products_count.empty else "None"
                st.metric("Most Common Product", most_common_product, products_count[most_common_product] if not products_count.empty else 0)
            
            # Category distribution
            st.markdown("### Category Distribution")
            category_counts = filtered_df['Category'].value_counts().reset_index()
            category_counts.columns = ['Category', 'Count']
            
            if not category_counts.empty:
                fig = px.pie(category_counts, names='Category', values='Count', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
    
    # Transfer items
    st.markdown("### Transfer Items")
    
    if len(st.session_state.branches) <= 1:
        st.info("You need at least two branches to transfer items")
    else:
        with st.expander("Transfer Items Between Branches", expanded=False):
            if has_permission("edit"):
                # Source and destination branches
                col1, col2 = st.columns(2)
                
                with col1:
                    source_branch = st.selectbox("From Branch", 
                                              options=branches,
                                              format_func=lambda x: st.session_state.branches[x]['name'],
                                              key="source_branch")
                
                with col2:
                    # Filter out the source branch
                    dest_branches = [b for b in branches if b != source_branch]
                    destination_branch = st.selectbox("To Branch", 
                                                 options=dest_branches,
                                                 format_func=lambda x: st.session_state.branches[x]['name'],
                                                 key="dest_branch")
                
                # Get items in source branch
                source_inventory = {rfid: data for rfid, data in st.session_state.rfid_data.items() 
                                if data['branch_id'] == source_branch}
                
                if not source_inventory:
                    st.info(f"No items in {st.session_state.branches[source_branch]['name']} to transfer")
                else:
                    # Convert to list for selection
                    source_items = []
                    for rfid, data in source_inventory.items():
                        product_id = data['product_id']
                        product_name = st.session_state.products[product_id]['name'] if product_id in st.session_state.products else "Unknown"
                        source_items.append((rfid, f"{product_name} (RFID: {rfid})"))
                    
                    # Allow selection of items to transfer
                    selected_rfids = st.multiselect("Select Items to Transfer", 
                                                options=[i[0] for i in source_items],
                                                format_func=lambda x: next((i[1] for i in source_items if i[0] == x), x))
                    
                    if selected_rfids:
                        if st.button(f"Transfer {len(selected_rfids)} Items to {st.session_state.branches[destination_branch]['name']}"):
                            results = []
                            for rfid in selected_rfids:
                                success, message = transfer_product(rfid, destination_branch)
                                results.append((rfid, success, message))
                            
                            # Show results
                            success_count = sum(1 for _, success, _ in results if success)
                            if success_count > 0:
                                st.success(f"Successfully transferred {success_count} out of {len(results)} items")
                                
                                # Show failures if any
                                failures = [(rfid, message) for rfid, success, message in results if not success]
                                if failures:
                                    st.error(f"Failed to transfer {len(failures)} items")
                                    for rfid, message in failures:
                                        st.error(f"RFID {rfid}: {message}")
                                
                                st.rerun()
                            else:
                                st.error("Failed to transfer any items")
                                for rfid, _, message in results:
                                    st.error(f"RFID {rfid}: {message}")
            else:
                st.warning("You don't have permission to transfer items")
def sales_tab():
    if not require_permission("view"):
        return
    
    st.markdown('<div class="subheader">Sales Management</div>', unsafe_allow_html=True)
    
    # Process sales
    with st.expander("Process Sales", expanded=False):
        if has_permission("edit"):
            st.markdown("### Single Item Sale")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Select item from inventory
                inventory_items = []
                for rfid, data in st.session_state.rfid_data.items():
                    product_id = data['product_id']
                    product_name = st.session_state.products[product_id]['name'] if product_id in st.session_state.products else "Unknown"
                    branch_name = st.session_state.branches[data['branch_id']]['name']
                    inventory_items.append((rfid, f"{product_name} - {branch_name} (RFID: {rfid})"))
                
                if not inventory_items:
                    st.info("No items in inventory")
                    selected_rfid = None
                else:
                    selected_rfid = st.selectbox("Select Item to Sell", 
                                              options=[i[0] for i in inventory_items],
                                              format_func=lambda x: next((i[1] for i in inventory_items if i[0] == x), x))
            
            with col2:
                sale_price = st.number_input("Sale Price", min_value=0.0, step=0.01)
                sale_date = st.date_input("Sale Date")
                sale_time = st.time_input("Sale Time")
            
            if selected_rfid and st.button("Process Sale"):
                # Combine date and time
                sale_datetime = datetime.combine(sale_date, sale_time).strftime("%Y-%m-%d %H:%M:%S")
                
                success, message = process_sale(selected_rfid, sale_price, sale_datetime)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            
            st.markdown("### Batch Sales Processing")
            st.markdown("Upload an Excel file with sales data")
            
            with st.expander("Instructions", expanded=False):
                st.info("""
                1. Upload an Excel file containing sales data.
                2. The Excel file must have a column named 'rfid'.
                3. Optional columns: 'sale_price' and 'sale_date'.
                4. The system will process each sale and remove items from inventory.
                """)
            
            uploaded_file = st.file_uploader("Upload Excel file with sales data", type=["xlsx", "xls"], key="sales_upload")
            
            if uploaded_file is not None:
                try:
                    df = pd.read_excel(uploaded_file)
                    
                    if 'rfid' not in df.columns:
                        st.error("The Excel file must contain a column named 'rfid'")
                    else:
                        # Process the uploaded file
                        results = process_sales_excel(df)
                        
                        # Display results
                        st.markdown('<div class="subheader">Sales Results</div>', unsafe_allow_html=True)
                        
                        # Count statuses
                        sold_count = sum(1 for r in results if r['status'] == 'sold')
                        error_count = sum(1 for r in results if r['status'] == 'error')
                        
                        # Display summary
                        col1, col2 = st.columns(2)
                        col1.metric("Successfully Sold", sold_count)
                        col2.metric("Errors", error_count)
                        
                        # Display tables by status
                        if sold_count > 0:
                            with st.expander("Sold Items", expanded=True):
                                sold_df = pd.DataFrame([r for r in results if r['status'] == 'sold'])
                                st.dataframe(sold_df)
                        
                        if error_count > 0:
                            with st.expander("Errors", expanded=True):
                                error_df = pd.DataFrame([r for r in results if r['status'] == 'error'])
                                st.dataframe(error_df)
                
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
        else:
            st.warning("You don't have permission to process sales")
    
    # Sales history
    st.markdown("### Sales History")
    
    if not st.session_state.sales:
        st.info("No sales recorded yet")
    else:
        # Convert to DataFrame for display
        sales_data = pd.DataFrame(st.session_state.sales)
        
        # Date range filter
        col1, col2 = st.columns(2)
        
        with col1:
            min_date = datetime.strptime(min(sales_data['sale_date']), "%Y-%m-%d %H:%M:%S").date() if not sales_data.empty else datetime.now().date()
            max_date = datetime.strptime(max(sales_data['sale_date']), "%Y-%m-%d %H:%M:%S").date() if not sales_data.empty else datetime.now().date()
            start_date = st.date_input("From Date", min_date)
        
        with col2:
            end_date = st.date_input("To Date", max_date)
        
        # Branch filter
        branches = list(st.session_state.branches.keys())
        selected_branches = st.multiselect("Filter by Branch", 
                                         options=["All"] + branches,
                                         format_func=lambda x: "All Branches" if x == "All" else st.session_state.branches[x]['name'],
                                         default=["All"])
        
        # Category filter
        if st.session_state.categories:
            selected_categories = st.multiselect("Filter by Category", 
                                              options=["All"] + st.session_state.categories,
                                              default=["All"])
        else:
            selected_categories = ["All"]
        
        # Apply filters
        filtered_sales = sales_data.copy()
        
        # Date filter
        filtered_sales = filtered_sales[
            (pd.to_datetime(filtered_sales['sale_date']).dt.date >= start_date) &
            (pd.to_datetime(filtered_sales['sale_date']).dt.date <= end_date)
        ]
        
        # Branch filter
        if "All" not in selected_branches:
            filtered_sales = filtered_sales[filtered_sales['branch_id'].isin(selected_branches)]
        
        # Category filter
        if "All" not in selected_categories:
            filtered_sales = filtered_sales[filtered_sales['category'].isin(selected_categories)]
        
        # Display filtered sales
        if filtered_sales.empty:
            st.info("No sales match the filter criteria")
        else:
            st.dataframe(filtered_sales, use_container_width=True)
            
            # Summary metrics
            st.markdown("### Sales Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Sales", len(filtered_sales))
            
            with col2:
                # Calculate total revenue if sale_price column has values
                if 'sale_price' in filtered_sales.columns and filtered_sales['sale_price'].notna().any():
                    total_revenue = filtered_sales['sale_price'].sum()
                    st.metric("Total Revenue", f"${total_revenue:.2f}")
                else:
                    st.metric("Total Revenue", "N/A")
            
            with col3:
                categories_count = filtered_sales['category'].value_counts()
                most_common_category = categories_count.index[0] if not categories_count.empty else "None"
                st.metric("Top Category", most_common_category, categories_count[most_common_category] if not categories_count.empty else 0)
            
            # Sales trends
            st.markdown("### Sales Trends")
            
            # Add date column for easier grouping
            filtered_sales['date'] = pd.to_datetime(filtered_sales['sale_date']).dt.date
            
            # Group by date
            daily_sales = filtered_sales.groupby('date').size().reset_index(name='count')
            daily_sales['date'] = pd.to_datetime(daily_sales['date'])
            
            # Line chart for sales over time
            fig = px.line(daily_sales, x='date', y='count', title='Daily Sales')
            st.plotly_chart(fig, use_container_width=True)
            
            # Category distribution
            st.markdown("### Category Distribution")
            category_counts = filtered_sales['category'].value_counts().reset_index()
            category_counts.columns = ['Category', 'Count']
            
            if not category_counts.empty:
                fig = px.pie(category_counts, names='Category', values='Count', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            
            # Branch distribution
            st.markdown("### Branch Distribution")
            branch_counts = filtered_sales['branch_id'].value_counts().reset_index()
            branch_counts.columns = ['Branch', 'Count']
            branch_counts['Branch Name'] = branch_counts['Branch'].apply(lambda x: st.session_state.branches[x]['name'])
            
            if not branch_counts.empty:
                fig = px.bar(branch_counts, x='Branch Name', y='Count', title='Sales by Branch')
                st.plotly_chart(fig, use_container_width=True)
def reports_tab():
    if not require_permission("view"):
        return
    
    st.markdown('<div class="subheader">Reports & Analytics</div>', unsafe_allow_html=True)
    
    # Report types
    report_type = st.radio("Select Report Type", 
                         options=["Inventory Summary", "Sales Analysis", "Transaction History", "Transfer History"],
                         horizontal=True)
    
    if report_type == "Inventory Summary":
        st.markdown("### Inventory Summary Report")
        
        # Calculate inventory statistics
        if not st.session_state.rfid_data:
            st.info("No inventory data available")
            return
        
        # Convert to DataFrame for analysis
        inventory_data = []
        for rfid, data in st.session_state.rfid_data.items():
            product_id = data['product_id']
            product_name = st.session_state.products[product_id]['name'] if product_id in st.session_state.products else "Unknown"
            category = data['category']
            branch_id = data['branch_id']
            branch_name = st.session_state.branches[branch_id]['name'] if branch_id in st.session_state.branches else "Unknown"
            added_at = data['added_at']
            
            inventory_data.append({
                'RFID': rfid,
                'Product ID': product_id,
                'Product Name': product_name,
                'Category': category,
                'Branch ID': branch_id,
                'Branch Name': branch_name,
                'Added At': added_at
            })
        
        inventory_df = pd.DataFrame(inventory_data)
        
        # Summary metrics
        st.markdown("#### Overall Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Items", len(inventory_df))
        
        with col2:
            unique_products = inventory_df['Product ID'].nunique()
            st.metric("Unique Products", unique_products)
        
        with col3:
            unique_categories = inventory_df['Category'].nunique()
            st.metric("Categories", unique_categories)
        
        with col4:
            unique_branches = inventory_df['Branch ID'].nunique()
            st.metric("Branches", unique_branches)
        
        # Category breakdown
        st.markdown("#### Category Breakdown")
        category_counts = inventory_df['Category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        
        if not category_counts.empty:
            fig = px.pie(category_counts, names='Category', values='Count', title='Inventory by Category')
            st.plotly_chart(fig, use_container_width=True)
        
        # Branch breakdown
        st.markdown("#### Branch Breakdown")
        branch_counts = inventory_df['Branch Name'].value_counts().reset_index()
        branch_counts.columns = ['Branch', 'Count']
        
        if not branch_counts.empty:
            fig = px.bar(branch_counts, x='Branch', y='Count', title='Inventory by Branch')
            st.plotly_chart(fig, use_container_width=True)
        
        # Product breakdown
        st.markdown("#### Top Products")
        product_counts = inventory_df['Product Name'].value_counts().reset_index()
        product_counts.columns = ['Product', 'Count']
        
        if not product_counts.empty:
            top_products = product_counts.head(10)  # Top 10 products
            fig = px.bar(top_products, x='Product', y='Count', title='Top 10 Products in Inventory')
            st.plotly_chart(fig, use_container_width=True)
        
        # Raw data table
        with st.expander("View Raw Inventory Data"):
            st.dataframe(inventory_df, use_container_width=True)
    
    elif report_type == "Sales Analysis":
        st.markdown("### Sales Analysis Report")
        
        if not st.session_state.sales:
            st.info("No sales data available")
            return
        
        # Convert to DataFrame for analysis
        sales_df = pd.DataFrame(st.session_state.sales)
        
        # Add datetime column
        sales_df['datetime'] = pd.to_datetime(sales_df['sale_date'])
        sales_df['date'] = sales_df['datetime'].dt.date
        
        # Date range filter
        col1, col2 = st.columns(2)
        
        with col1:
            min_date = sales_df['date'].min() if not sales_df.empty else datetime.now().date()
            start_date = st.date_input("From Date", min_date, key="sales_start_date")
        
        with col2:
            max_date = sales_df['date'].max() if not sales_df.empty else datetime.now().date()
            end_date = st.date_input("To Date", max_date, key="sales_end_date")
        
        # Apply date filter
        filtered_sales = sales_df[
            (sales_df['date'] >= start_date) &
            (sales_df['date'] <= end_date)
        ]
        
        # Summary metrics
        st.markdown("#### Sales Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sales", len(filtered_sales))
        
        with col2:
            if 'sale_price' in filtered_sales.columns and filtered_sales['sale_price'].notna().any():
                total_revenue = filtered_sales['sale_price'].sum()
                st.metric("Total Revenue", f"${total_revenue:.2f}")
            else:
                st.metric("Total Revenue", "N/A")
        
        with col3:
            unique_products = filtered_sales['product_id'].nunique()
            st.metric("Products Sold", unique_products)
        
        with col4:
            unique_categories = filtered_sales['category'].nunique()
            st.metric("Categories Sold", unique_categories)
        
        # Sales over time
        st.markdown("#### Sales Trend")
        daily_sales = filtered_sales.groupby('date').size().reset_index(name='count')
        
        if not daily_sales.empty:
            fig = px.line(daily_sales, x='date', y='count', title='Daily Sales')
            st.plotly_chart(fig, use_container_width=True)
        
        # Category breakdown
        st.markdown("#### Category Sales")
        category_counts = filtered_sales['category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        
        if not category_counts.empty:
            fig = px.pie(category_counts, names='Category', values='Count', title='Sales by Category')
            st.plotly_chart(fig, use_container_width=True)
        
        # Branch breakdown
        st.markdown("#### Branch Sales")
        branch_counts = filtered_sales['branch_id'].value_counts().reset_index()
        branch_counts.columns = ['Branch', 'Count']
        
        # Add branch names
        branch_counts['Branch Name'] = branch_counts['Branch'].apply(
            lambda x: st.session_state.branches[x]['name'] if x in st.session_state.branches else "Unknown")
        
        if not branch_counts.empty:
            fig = px.bar(branch_counts, x='Branch Name', y='Count', title='Sales by Branch')
            st.plotly_chart(fig, use_container_width=True)
        
        # Raw data table
        with st.expander("View Raw Sales Data"):
            st.dataframe(filtered_sales, use_container_width=True)
    
    elif report_type == "Transaction History":
        st.markdown("### Transaction History Report")
        
        if not st.session_state.transactions:
            st.info("No transaction data available")
            return
        
        # Convert to DataFrame for analysis
        transactions_df = pd.DataFrame(st.session_state.transactions)
        
        # Add datetime column
        transactions_df['datetime'] = pd.to_datetime(transactions_df['timestamp'])
        transactions_df['date'] = transactions_df['datetime'].dt.date
        
        # Date range filter
        col1, col2 = st.columns(2)
        
        with col1:
            min_date = transactions_df['date'].min() if not transactions_df.empty else datetime.now().date()
            start_date = st.date_input("From Date", min_date, key="trans_start_date")
        
        with col2:
            max_date = transactions_df['date'].max() if not transactions_df.empty else datetime.now().date()
            end_date = st.date_input("To Date", max_date, key="trans_end_date")
        
        # Action type filter
        actions = transactions_df['action'].unique().tolist()
        selected_actions = st.multiselect("Filter by Action Type", options=["All"] + actions, default=["All"])
        
        # Apply filters
        filtered_trans = transactions_df[
            (transactions_df['date'] >= start_date) &
            (transactions_df['date'] <= end_date)
        ]
        
        if "All" not in selected_actions:
            filtered_trans = filtered_trans[filtered_trans['action'].isin(selected_actions)]
        
        # Summary metrics
        st.markdown("#### Transaction Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Transactions", len(filtered_trans))
        
        with col2:
            action_counts = filtered_trans['action'].value_counts()
            most_common_action = action_counts.index[0] if not action_counts.empty else "None"
            st.metric("Most Common Action", most_common_action, action_counts[most_common_action] if not action_counts.empty else 0)
        
        with col3:
            unique_products = filtered_trans['product_id'].nunique()
            st.metric("Unique Products", unique_products)
        
        # Transactions over time
        st.markdown("#### Transaction Trend")
        daily_trans = filtered_trans.groupby('date').size().reset_index(name='count')
        
        if not daily_trans.empty:
            fig = px.line(daily_trans, x='date', y='count', title='Daily Transactions')
            st.plotly_chart(fig, use_container_width=True)
        
        # Action type breakdown
        st.markdown("#### Action Type Breakdown")
        action_counts = filtered_trans['action'].value_counts().reset_index()
        action_counts.columns = ['Action', 'Count']
        
        if not action_counts.empty:
            fig = px.pie(action_counts, names='Action', values='Count', title='Transactions by Action Type')
            st.plotly_chart(fig, use_container_width=True)
        
        # Raw data table
        with st.expander("View Raw Transaction Data"):
            st.dataframe(filtered_trans, use_container_width=True)
    
    elif report_type == "Transfer History":
        st.markdown("### Transfer History Report")
        
        if not st.session_state.transfers:
            st.info("No transfer data available")
            return
        
        # Convert to DataFrame for analysis
        transfers_df = pd.DataFrame(st.session_state.transfers)
        
        # Add datetime column
        transfers_df['datetime'] = pd.to_datetime(transfers_df['timestamp'])
        transfers_df['date'] = transfers_df['datetime'].dt.date
        
        # Date range filter
        col1, col2 = st.columns(2)
        
        with col1:
            min_date = transfers_df['date'].min() if not transfers_df.empty else datetime.now().date()
            start_date = st.date_input("From Date", min_date, key="transfer_start_date")
        
        with col2:
            max_date = transfers_df['date'].max() if not transfers_df.empty else datetime.now().date()
            end_date = st.date_input("To Date", max_date, key="transfer_end_date")
        
        # Branch filter
        branches = list(st.session_state.branches.keys())
        from_branches = st.multiselect("From Branch", 
                                    options=["All"] + branches,
                                    format_func=lambda x: "All" if x == "All" else st.session_state.branches[x]['name'],
                                    default=["All"])
        
        to_branches = st.multiselect("To Branch", 
                                  options=["All"] + branches,
                                  format_func=lambda x: "All" if x == "All" else st.session_state.branches[x]['name'],
                                  default=["All"])
        
        # Apply filters
        filtered_transfers = transfers_df[
            (transfers_df['date'] >= start_date) &
            (transfers_df['date'] <= end_date)
        ]
        
        if "All" not in from_branches:
            filtered_transfers = filtered_transfers[filtered_transfers['from_branch_id'].isin(from_branches)]
        
        if "All" not in to_branches:
            filtered_transfers = filtered_transfers[filtered_transfers['to_branch_id'].isin(to_branches)]
        
        # Summary metrics
        st.markdown("#### Transfer Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Transfers", len(filtered_transfers))
        
        with col2:
            unique_products = filtered_transfers['product_id'].nunique()
            st.metric("Products Transferred", unique_products)
        
        with col3:
            unique_branches_involved = set(filtered_transfers['from_branch_id'].tolist() + filtered_transfers['to_branch_id'].tolist())
            st.metric("Branches Involved", len(unique_branches_involved))
        
        # Transfers over time
        st.markdown("#### Transfer Trend")
        daily_transfers = filtered_transfers.groupby('date').size().reset_index(name='count')
        
        if not daily_transfers.empty:
            fig = px.line(daily_transfers, x='date', y='count', title='Daily Transfers')
            st.plotly_chart(fig, use_container_width=True)
        
        # Branch flow analysis
        st.markdown("#### Branch Transfer Flow")
        branch_flow = filtered_transfers.groupby(['from_branch_id', 'to_branch_id']).size().reset_index(name='count')
        
        # Add branch names
        branch_flow['From Branch'] = branch_flow['from_branch_id'].apply(
            lambda x: st.session_state.branches[x]['name'] if x in st.session_state.branches else "Unknown")
        branch_flow['To Branch'] = branch_flow['to_branch_id'].apply(
            lambda x: st.session_state.branches[x]['name'] if x in st.session_state.branches else "Unknown")
        
        if not branch_flow.empty:
            fig = px.bar(branch_flow, x='From Branch', y='count', color='To Branch',
                        title='Transfer Flow Between Branches')
            st.plotly_chart(fig, use_container_width=True)
        
        # Raw data table
        with st.expander("View Raw Transfer Data"):
            display_cols = ['rfid', 'product_id', 'product_name', 'from_branch_id', 'to_branch_id', 'timestamp']
            st.dataframe(filtered_transfers[display_cols], use_container_width=True)

def users_tab():
    if not has_permission("manage_users"):
        st.error("You don't have permission to manage users")
        return
    
    st.markdown('<div class="subheader">User Management</div>', unsafe_allow_html=True)
    
    # Add new user
    with st.expander("Add New User", expanded=False):
        with st.form("add_user_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            name = st.text_input("Full Name")
            
            role_options = ["user", "manager", "admin"]
            role = st.selectbox("Role", options=role_options)
            
            permission_options = ["view", "add", "edit", "delete", "manage_users"]
            permissions = st.multiselect("Permissions", options=permission_options)
            
            submit = st.form_submit_button("Add User")
            
            if submit:
                if username and password and confirm_password:
                    if password == confirm_password:
                        if username in st.session_state.users:
                            st.error(f"User {username} already exists")
                        else:
                            success, message = add_user(username, password, role, permissions, name)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Username and password are required")
    
    # Manage existing users
    st.markdown("### Existing Users")
    
    if not st.session_state.users:
        st.info("No users found")
    else:
        users_data = []
        for username, user_data in st.session_state.users.items():
            users_data.append({
                'Username': username,
                'Name': user_data.get('name', username),
                'Role': user_data.get('role', 'user'),
                'Active': user_data.get('active', True),
                'Permissions': ", ".join(user_data.get('permissions', [])),
                'Created': user_data.get('created_at', 'Unknown')
            })
        
        users_df = pd.DataFrame(users_data)
        st.dataframe(users_df, use_container_width=True)
        
        # Edit user
        st.markdown("### Edit User")
        
        user_to_edit = st.selectbox("Select User to Edit", 
                                 options=list(st.session_state.users.keys()),
                                 format_func=lambda x: f"{x} ({st.session_state.users[x].get('name', '')})")
        
        if user_to_edit:
            user_data = st.session_state.users[user_to_edit]
            
            with st.form("edit_user_form"):
                name = st.text_input("Full Name", value=user_data.get('name', ''))
                
                change_password = st.checkbox("Change Password")
                password = st.text_input("New Password", type="password", disabled=not change_password)
                confirm_password = st.text_input("Confirm New Password", type="password", disabled=not change_password)
                
                role_options = ["user", "manager", "admin"]
                role_index = role_options.index(user_data.get('role', 'user')) if user_data.get('role', 'user') in role_options else 0
                role = st.selectbox("Role", options=role_options, index=role_index)
                
                permission_options = ["view", "add", "edit", "delete", "manage_users"]
                permissions = st.multiselect("Permissions", 
                                          options=permission_options, 
                                          default=user_data.get('permissions', []))
                
                active = st.checkbox("Active", value=user_data.get('active', True))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    submit = st.form_submit_button("Update User")
                
                with col2:
                    delete = st.form_submit_button("Delete User", type="primary")
                
                if submit:
                    if change_password:
                        if not password or not confirm_password:
                            st.error("Please enter both password fields")
                        elif password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            success, message = update_user(user_to_edit, password=password, role=role, permissions=permissions, active=active, name=name)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                    else:
                        success, message = update_user(user_to_edit, role=role, permissions=permissions, active=active, name=name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                
                if delete:
                    success, message = delete_user(user_to_edit)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

# Main application
def main():
    load_css()
    
    # Check if user is authenticated
    if not st.session_state.authenticated:
        show_login_page()
    else:
        # Display header with user info
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            st.markdown('<div class="main-header">RFID Inventory Management System</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="user-info">
                Logged in as: <b>{st.session_state.user_name}</b> ({st.session_state.user_role})
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.user_role = None
                st.session_state.user_permissions = []
                st.session_state.user_name = None
                st.rerun()
        
        # Create tabs
        tabs = ["Upload", "Products", "Inventory", "Sales", "Reports"]
        
        # Add Users tab if user has permission
        if has_permission("manage_users"):
            tabs.append("Users")
        
        selected_tab = st.tabs(tabs)
        
        with selected_tab[0]:
            upload_tab()
        
        with selected_tab[1]:
            product_tab()
        
        with selected_tab[2]:
            inventory_tab()
        
        with selected_tab[3]:
            sales_tab()
        
        with selected_tab[4]:
            reports_tab()
        
        if has_permission("manage_users") and len(tabs) > 5:
            with selected_tab[5]:
                users_tab()

# Run the application
if __name__ == "__main__":
    main()
