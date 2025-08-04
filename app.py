# Import warnings and filter the numpy compatibility warning
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")

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

# Set page configuration
st.set_page_config(
    page_title="RFID Inventory Management System",
    page_icon="📦",
    layout="wide"
)

# User authentication setup
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'users' not in st.session_state:
    # Default admin user
    st.session_state.users = {
        "admin": {
            "password": hashlib.sha256("admin123".encode()).hexdigest(),
            "name": "Admin",
            "role": "admin"
        }
    }

# File path for users
USERS_PATH = 'data/users.json'

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

# Load data from files if they exist
def load_data():
    if os.path.exists(RFID_DATA_PATH):
        with open(RFID_DATA_PATH, 'r') as f:
            st.session_state.rfid_data = json.load(f)
    
    if os.path.exists(PRODUCTS_PATH):
        with open(PRODUCTS_PATH, 'r') as f:
            st.session_state.products = json.load(f)
    
    if os.path.exists(CATEGORIES_PATH):
        with open(CATEGORIES_PATH, 'r') as f:
            st.session_state.categories = json.load(f)
    
    if os.path.exists(TRANSACTIONS_PATH):
        with open(TRANSACTIONS_PATH, 'r') as f:
            st.session_state.transactions = json.load(f)
    
    if os.path.exists(SALES_PATH):
        with open(SALES_PATH, 'r') as f:
            st.session_state.sales = json.load(f)
            
    if os.path.exists(BRANCHES_PATH):
        with open(BRANCHES_PATH, 'r') as f:
            st.session_state.branches = json.load(f)
            
    if os.path.exists(TRANSFERS_PATH):
        with open(TRANSFERS_PATH, 'r') as f:
            st.session_state.transfers = json.load(f)
    
    # Load users
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, 'r') as f:
            st.session_state.users = json.load(f)

# Save data to files
def save_data():
    with open(RFID_DATA_PATH, 'w') as f:
        json.dump(st.session_state.rfid_data, f)
    
    with open(PRODUCTS_PATH, 'w') as f:
        json.dump(st.session_state.products, f)
    
    with open(CATEGORIES_PATH, 'w') as f:
        json.dump(st.session_state.categories, f)
    
    with open(TRANSACTIONS_PATH, 'w') as f:
        json.dump(st.session_state.transactions, f)
        
    with open(SALES_PATH, 'w') as f:
        json.dump(st.session_state.sales, f)
        
    with open(BRANCHES_PATH, 'w') as f:
        json.dump(st.session_state.branches, f)
        
    with open(TRANSFERS_PATH, 'w') as f:
        json.dump(st.session_state.transfers, f)
    
    # Save users
    with open(USERS_PATH, 'w') as f:
        json.dump(st.session_state.users, f)

# Load data at startup
load_data()
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
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 1rem;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .user-info {
        padding: 0.5rem 1rem;
        background-color: #e3f2fd;
        border-radius: 0.5rem;
        margin-right: 1rem;
        font-weight: bold;
    }
    .logout-btn {
        color: white;
        background-color: #dc3545;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        text-decoration: none;
    }
    .logout-btn:hover {
        background-color: #c82333;
        text-decoration: none;
        color: white;
    }
    .settings-tab {
        margin-top: 2rem;
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Function to add a new user
def add_user(username, password, name, role="user"):
    if username in st.session_state.users:
        return False, f"Username {username} already exists"
    
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    st.session_state.users[username] = {
        "password": hashed_password,
        "name": name,
        "role": role
    }
    
    save_data()
    return True, f"User {username} added successfully"
# Function to add a new RFID tag
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

# Function to add a new branch
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

# Function to transfer product between branches
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
# Function to process sales Excel file
def process_sales_excel(df):
    results = []
    for _, row in df.iterrows():
        try:
            rfid = str(row['rfid']).strip()
            # Check if sale_price column exists
            sale_price = float(row['sale_price']) if 'sale_price' in df.columns else None
            # Check if sale_date column exists
            sale_date = row['sale_date'].strftime("%Y-%m-%d %H:%M:%S") if 'sale_date' in df.columns else None
            
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

# Function to process sales
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

# Function to add a new product
def add_product(product_id, name, description, category, image=None):
    if product_id in st.session_state.products:
        return False, f"Product ID {product_id} already exists"
    
    image_path = None
    if image is not None:
        # Save the image
        image_filename = f"/images/productimage.jpg"
        image.save(image_filename)
        image_path = image_filename
    
    st.session_state.products[product_id] = {
        'name': name,
        'description': description,
        'category': category,
        'image': image_path
    }
    
    save_data()
    return True, f"Product {name} added successfully"

# Function to add a new category
def add_category(category_name):
    if category_name in st.session_state.categories:
        return False, f"Category {category_name} already exists"
    
    st.session_state.categories.append(category_name)
    save_data()
    return True, f"Category {category_name} added successfully"

# Function to process Excel upload
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
# Login page
def login_page():
    st.markdown('<div class="main-header">RFID Inventory Management System</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="subheader" style="text-align: center;">Login</div>', unsafe_allow_html=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Login", use_container_width=True):
                if username in st.session_state.users:
                    hashed_input = hashlib.sha256(password.encode()).hexdigest()
                    if hashed_input == st.session_state.users[username]["password"]:
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.session_state.user_role = st.session_state.users[username]["role"]
                        st.session_state.user_name = st.session_state.users[username]["name"]
                        st.success("Login successful!")
                        st.experimental_rerun()
                    else:
                        st.error("Incorrect password")
                else:
                    st.error("Username not found")
        
        with col2:
            if len(st.session_state.users) == 0:
                # If no users exist, allow creating the first admin
                if st.button("Create Admin Account", use_container_width=True):
                    add_user("admin", "admin123", "Administrator", "admin")
                    st.success("Admin account created! Username: admin, Password: admin123")
                    st.info("Please login with these credentials and change the password immediately.")
        
        st.markdown('</div>', unsafe_allow_html=True)

# User settings tab
def settings_tab():
    st.markdown('<div class="subheader">User Settings</div>', unsafe_allow_html=True)
    
    # Change password section
    with st.expander("Change Password", expanded=True):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.button("Change Password"):
            # Verify current password
            hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
            if hashed_current == st.session_state.users[st.session_state.current_user]["password"]:
                if new_password == confirm_password:
                    if len(new_password) >= 6:
                        # Update password
                        hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
                        st.session_state.users[st.session_state.current_user]["password"] = hashed_new
                        save_data()
                        st.success("Password changed successfully!")
                    else:
                        st.error("New password must be at least 6 characters long")
                else:
                    st.error("New passwords don't match")
            else:
                st.error("Current password is incorrect")

    # User management (admin only)
    if st.session_state.user_role == "admin":
        st.markdown('<div class="subheader">User Management</div>', unsafe_allow_html=True)
        
        # Add new user
        with st.expander("Add New User", expanded=False):
            new_username = st.text_input("Username")
            new_user_password = st.text_input("User Password", type="password")
            new_user_name = st.text_input("Full Name")
            new_user_role = st.selectbox("Role", ["user", "admin"])
            
            if st.button("Add User"):
                if len(new_username) > 0 and len(new_user_password) >= 6 and len(new_user_name) > 0:
                    success, message = add_user(new_username, new_user_password, new_user_name, new_user_role)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("All fields are required. Password must be at least 6 characters.")
        
        # List and manage existing users
        st.markdown("### Existing Users")
        
        users_data = []
        for username, user_data in st.session_state.users.items():
            users_data.append({
                "Username": username,
                "Name": user_data["name"],
                "Role": user_data["role"]
            })
        
        if users_data:
            users_df = pd.DataFrame(users_data)
            st.dataframe(users_df)
            
            # Delete user
            user_to_delete = st.selectbox("Select user to delete", ["-"] + [u for u in st.session_state.users.keys() if u != st.session_state.current_user])
            
            if user_to_delete != "-":
                if st.button("Delete Selected User"):
                    if user_to_delete != st.session_state.current_user:
                        del st.session_state.users[user_to_delete]
                        save_data()
                        st.success(f"User {user_to_delete} deleted successfully")
                        st.experimental_rerun()
                    else:
                        st.error("You cannot delete your own account")
# Upload RFID Tags Tab
def upload_tab():
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
                        
                        # Assign new tags to products
                        st.markdown('<div class="subheader">Assign New Tags to Products</div>', unsafe_allow_html=True)
                        
                        # Check if we have products
                        if len(st.session_state.products) == 0:
                            st.warning("No products available. Please add products first in the Products tab.")
                        else:
                            # Create product selection
                            product_options = {pid: f"{data['name']} ({pid})" for pid, data in st.session_state.products.items()}
                            selected_product = st.selectbox("Select Product", list(product_options.values()))
                            selected_product_id = list(product_options.keys())[list(product_options.values()).index(selected_product)]
                            
                            # Get product category
                            product_category = st.session_state.products[selected_product_id]['category']
                            
                            # Extract new RFIDs for selection
                            new_rfids = [r['rfid'] for r in results if r['status'] == 'new']
                            
                            # Allow selecting specific tags from the list
                            st.markdown("**Choose which tags to assign:**")
                            
                            assign_option = st.radio(
                                "Assignment method", 
                                ["Assign all tags", "Choose specific tags"]
                            )
                            
                            if assign_option == "Assign all tags":
                                # Assign all new tags
                                if st.button("Assign All New Tags to Selected Product"):
                                    assigned_count = 0
                                    for r in results:
                                        if r['status'] == 'new':
                                            rfid = r['rfid']
                                            success, _ = add_rfid_tag(rfid, selected_product_id, product_category)
                                            if success:
                                                assigned_count += 1
                                    
                                    st.success(f"Successfully assigned {assigned_count} new RFID tags to {product_options[selected_product_id]}")
                                    # Trigger a rerun to update the UI
                                    st.experimental_rerun()
                            else:
                                # Create a multiselect for choosing specific tags
                                # Add a checkbox to select all options by default
                                select_all = st.checkbox("Select all tags", value=True)
                                
                                if select_all:
                                    default_selections = new_rfids
                                else:
                                    default_selections = []
                                
                                selected_rfids = st.multiselect(
                                    "Select specific tags to assign",
                                    options=new_rfids,
                                    default=default_selections
                                )
                                
                                if st.button("Assign Selected Tags to Product"):
                                    assigned_count = 0
                                    for rfid in selected_rfids:
                                        success, _ = add_rfid_tag(rfid, selected_product_id, product_category)
                                        if success:
                                            assigned_count += 1
                                    
                                    st.success(f"Successfully assigned {assigned_count} selected RFID tags to {product_options[selected_product_id]}")
                                    # Trigger a rerun to update the UI
                                    st.experimental_rerun()
                
                if error_count > 0:
                    with st.expander("Errors", expanded=True):
                        error_df = pd.DataFrame([r for r in results if r['status'] == 'error'])
                        st.dataframe(error_df)
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

# Products Tab
def products_tab():
    st.markdown('<div class="subheader">Manage Products</div>', unsafe_allow_html=True)
    
    # Add new product
    with st.expander("Add New Product", expanded=False):
        product_id = st.text_input("Product ID")
        product_name = st.text_input("Product Name")
        product_description = st.text_area("Description")
        
        # Category selection
        if len(st.session_state.categories) > 0:
            product_category = st.selectbox("Category", st.session_state.categories)
        else:
            st.warning("No categories available. Please add categories first in the Categories tab.")
            product_category = st.text_input("Category (will be added automatically)")
        
        product_image = st.file_uploader("Product Image (Optional)", type=["jpg", "jpeg", "png"])
        
        if st.button("Add Product"):
            if not product_id or not product_name:
                st.error("Product ID and Name are required")
            else:
                # Add category if it doesn't exist
                if product_category and product_category not in st.session_state.categories:
                    add_category(product_category)
                
                image_obj = None
                if product_image:
                    image_obj = Image.open(product_image)
                
                success, message = add_product(product_id, product_name, product_description, product_category, image_obj)
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # List existing products
    st.markdown('<div class="subheader">Existing Products</div>', unsafe_allow_html=True)
    
    if len(st.session_state.products) == 0:
        st.info("No products added yet")
    else:
        # Filter by category
        categories = ["All"] + st.session_state.categories
        filter_category = st.selectbox("Filter by Category", categories)
        
        # Display products in a grid
        filtered_products = {
            pid: data for pid, data in st.session_state.products.items() 
            if filter_category == "All" or data['category'] == filter_category
        }
        
        if len(filtered_products) == 0:
            st.info(f"No products in category '{filter_category}'")
        else:
            # Create rows with 3 products each
            for i in range(0, len(filtered_products), 3):
                cols = st.columns(3)
                
                for j in range(3):
                    idx = i + j
                    if idx < len(filtered_products):
                        pid = list(filtered_products.keys())[idx]
                        product = filtered_products[pid]
                        
                        with cols[j]:
                            st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                            
                            # Display product image if available
                            if product['image'] and os.path.exists(product['image']):
                                img = Image.open(product['image'])
                                st.image(img, width=150)
                            else:
                                st.markdown("📷 No image")
                            
                            st.markdown(f"**{product['name']}**")
                            st.markdown(f"ID: {pid}")
                            st.markdown(f"Category: {product['category']}")
                            
                            # Count how many RFIDs are assigned to this product
                            rfid_count = sum(1 for data in st.session_state.rfid_data.values() if data['product_id'] == pid)
                            st.markdown(f"RFID Tags: {rfid_count}")
                            
                            # Show details in an expander
                            with st.expander("Details"):
                                st.markdown(f"Description: {product['description'] if product['description'] else 'No description'}")
                                
                                # Show assigned RFID tags
                                if rfid_count > 0:
                                    st.markdown("**Assigned RFID Tags:**")
                                    assigned_rfids = [rfid for rfid, data in st.session_state.rfid_data.items() if data['product_id'] == pid]
                                    for rfid in assigned_rfids:
                                        st.code(rfid)
                            
                            st.markdown("</div>", unsafe_allow_html=True)

# Main application function with authentication handling
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        # Main application layout with user info and logout button
        col1, col2 = st.columns([10, 2])
        
        with col1:
            st.markdown('<div class="main-header">RFID Inventory Management System</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(
                f"""
                <div style="text-align: right; margin-top: 1rem;">
                    <span class="user-info">{st.session_state.user_name} ({st.session_state.user_role})</span>
                    <a href="#" id="logout" class="logout-btn">Logout</a>
                </div>
                
                <script>
                    document.getElementById('logout').addEventListener('click', function(e) {{
                        e.preventDefault();
                        window.parent.postMessage({{
                            type: 'streamlit:setSessionState',
                            state: {{ authenticated: false }}
                        }}, '*');
                        window.location.reload();
                    }});
                </script>
                """,
                unsafe_allow_html=True
            )
        
        # Navigation tabs
        tabs = ["Upload", "Products", "Categories", "Inventory", "Reports", "Sales", "Branches", "Settings"]
        cols = st.columns(len(tabs))
        
        for i, tab in enumerate(tabs):
            if cols[i].button(tab, key=f"tab_{tab}", use_container_width=True):
                st.session_state.active_tab = tab
        
        st.markdown("---")
        
        # Branch selector (show in all tabs except Branches and Settings)
        if st.session_state.active_tab not in ["Branches", "Settings"] and len(st.session_state.branches) > 0:
            col1, col2 = st.columns([3, 1])
            with col1:
                branch_options = {bid: f"{data['name']}" for bid, data in st.session_state.branches.items()}
                selected_branch = st.selectbox("Select Branch", list(branch_options.values()), key="branch_selector")
                selected_branch_id = list(branch_options.keys())[list(branch_options.values()).index(selected_branch)]
                st.session_state.current_branch = selected_branch_id
            with col2:
                st.markdown(f"<div style='padding-top: 2rem;'>Current Branch: <b>{branch_options[selected_branch_id]}</b></div>", unsafe_allow_html=True)
            
            st.markdown("---")
        
        # Handle different tabs
        if st.session_state.active_tab == "Upload":
            upload_tab()
        elif st.session_state.active_tab == "Products":
            products_tab()
        elif st.session_state.active_tab == "Settings":
            settings_tab()
        # Add other tab functions here when needed

# Run the application
if __name__ == "__main__":
    main()
