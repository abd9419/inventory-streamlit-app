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

# Set page configuration
st.set_page_config(
    page_title="RFID Inventory Management System",
    page_icon="📦",
    layout="wide"
)

# Example of corrected image saving logic in add_product()
def add_product(product_id, name, description, category, image=None):
    if product_id in st.session_state.products:
        return False, f"Product ID {product_id} already exists"

    image_path = None
    if image is not None:
        # Create unique filename and safe path
        image_filename = f"product_{product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        image_path = os.path.join("data", "images", image_filename)
        image.save(image_path)

    st.session_state.products[product_id] = {
        'name': name,
        'description': description,
        'category': category,
        'image': image_path
    }

    save_data()
    return True, f"Product {name} added successfully"

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
</style>
""", unsafe_allow_html=True)

# Application header
st.markdown('<div class="main-header">RFID Inventory Management System</div>', unsafe_allow_html=True)

# Navigation tabs
tabs = ["Upload", "Products", "Categories", "Inventory", "Reports", "Sales", "Branches"]
cols = st.columns(len(tabs))

for i, tab in enumerate(tabs):
    if cols[i].button(tab, key=f"tab_{tab}", use_container_width=True):
        st.session_state.active_tab = tab

st.markdown("---")

# Branch selector (show in all tabs except Branches)
if st.session_state.active_tab != "Branches" and len(st.session_state.branches) > 0:
    col1, col2 = st.columns([3, 1])
    with col1:
        branch_options = {bid: f"{data['name']}" for bid, data in st.session_state.branches.items()}
        selected_branch = st.selectbox("Select Branch", list(branch_options.values()), key="branch_selector")
        selected_branch_id = list(branch_options.keys())[list(branch_options.values()).index(selected_branch)]
        st.session_state.current_branch = selected_branch_id
    with col2:
        st.markdown(f"<div style='padding-top: 2rem;'>Current Branch: <b>{branch_options[selected_branch_id]}</b></div>", unsafe_allow_html=True)
    
    st.markdown("---")

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

# Upload RFID Tags Tab
if st.session_state.active_tab == "Upload":
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
elif st.session_state.active_tab == "Products":
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

# Categories Tab
elif st.session_state.active_tab == "Categories":
    st.markdown('<div class="subheader">Manage Categories</div>', unsafe_allow_html=True)
    
    # Add new category
    with st.expander("Add New Category", expanded=True):
        category_name = st.text_input("Category Name")
        
        if st.button("Add Category"):
            if not category_name:
                st.error("Category name is required")
            else:
                success, message = add_category(category_name)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # List existing categories
    st.markdown('<div class="subheader">Existing Categories</div>', unsafe_allow_html=True)
    
    if len(st.session_state.categories) == 0:
        st.info("No categories added yet")
    else:
        # Display categories with product counts
        category_data = []
        for category in st.session_state.categories:
            product_count = sum(1 for data in st.session_state.products.values() if data['category'] == category)
            rfid_count = sum(1 for data in st.session_state.rfid_data.values() if data['category'] == category)
            category_data.append({
                "Category": category,
                "Products": product_count,
                "RFID Tags": rfid_count
            })
        
        category_df = pd.DataFrame(category_data)
        st.dataframe(category_df)
        
        # Category visualization
        if len(category_data) > 0:
            st.markdown('<div class="subheader">Category Distribution</div>', unsafe_allow_html=True)
            
            # Products by category
            fig1 = px.pie(category_df, values='Products', names='Category', title='Products by Category')
            st.plotly_chart(fig1)
            
            # RFID tags by category
            fig2 = px.pie(category_df, values='RFID Tags', names='Category', title='RFID Tags by Category')
            st.plotly_chart(fig2)

# Inventory Tab
elif st.session_state.active_tab == "Inventory":
    st.markdown('<div class="subheader">Inventory Management</div>', unsafe_allow_html=True)
    
    # Summary metrics
    total_products = len(st.session_state.products)
    total_rfid_tags = len(st.session_state.rfid_data)
    total_categories = len(st.session_state.categories)
    
    # Count products in current branch
    branch_rfid_tags = sum(1 for data in st.session_state.rfid_data.values() if data.get('branch_id') == st.session_state.current_branch)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", total_products)
    col2.metric("Total RFID Tags", total_rfid_tags)
    col3.metric("Branch RFID Tags", branch_rfid_tags)
    col4.metric("Total Categories", total_categories)
    
    # RFID tag search
    st.markdown('<div class="subheader">Search RFID Tags</div>', unsafe_allow_html=True)
    search_rfid = st.text_input("Enter RFID Tag")
    
    if search_rfid:
        if search_rfid in st.session_state.rfid_data:
            tag_data = st.session_state.rfid_data[search_rfid]
            product_id = tag_data['product_id']
            
            if product_id in st.session_state.products:
                product = st.session_state.products[product_id]
                
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                st.markdown(f"**RFID Tag:** {search_rfid}")
                st.markdown(f"**Product:** {product['name']}")
                st.markdown(f"**Product ID:** {product_id}")
                st.markdown(f"**Category:** {tag_data['category']}")
                st.markdown(f"**Added at:** {tag_data['added_at']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Display product image if available
                if product['image'] and os.path.exists(product['image']):
                    img = Image.open(product['image'])
                    st.image(img, width=200)
            else:
                st.warning(f"Product ID {product_id} not found")
        else:
            st.warning(f"RFID Tag {search_rfid} not found")
    
    # RFID tag management
    st.markdown('<div class="subheader">Manual RFID Tag Entry</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        manual_rfid = st.text_input("RFID Tag")
    
    with col2:
        if len(st.session_state.products) > 0:
            product_options = {pid: f"{data['name']} ({pid})" for pid, data in st.session_state.products.items()}
            selected_product = st.selectbox("Assign to Product", list(product_options.values()))
            selected_product_id = list(product_options.keys())[list(product_options.values()).index(selected_product)]
            product_category = st.session_state.products[selected_product_id]['category']
        else:
            st.warning("No products available")
            selected_product_id = None
            product_category = None
    
    if st.button("Add RFID Tag"):
        if not manual_rfid or not selected_product_id:
            st.error("RFID Tag and Product selection are required")
        else:
            success, message = add_rfid_tag(manual_rfid, selected_product_id, product_category)
            
            if success:
                st.success(message)
            else:
                st.error(message)

# Sales Tab
elif st.session_state.active_tab == "Sales":
    st.markdown('<div class="subheader">Process Sales</div>', unsafe_allow_html=True)
    
    with st.expander("Instructions", expanded=False):
        st.info("""
        1. Upload an Excel file containing RFID tags for items being sold.
        2. The Excel file must have a column named 'rfid'.
        3. Optional columns include 'sale_price' and 'sale_date'.
        4. If sale_date is not provided, current date/time will be used.
        5. The system will mark these items as sold and remove them from inventory.
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Upload Excel file with sales data
        uploaded_sales_file = st.file_uploader("Upload Excel file with sold RFID tags", type=["xlsx", "xls"])
        
        if uploaded_sales_file is not None:
            try:
                df = pd.read_excel(uploaded_sales_file)
                
                if 'rfid' not in df.columns:
                    st.error("The Excel file must contain a column named 'rfid'")
                else:
                    # Process the uploaded sales file
                    if st.button("Process Sales"):
                        results = process_sales_excel(df)
                        
                        # Display results
                        st.markdown('<div class="subheader">Sales Processing Results</div>', unsafe_allow_html=True)
                        
                        # Count statuses
                        sold_count = sum(1 for r in results if r['status'] == 'sold')
                        error_count = sum(1 for r in results if r['status'] == 'error')
                        
                        # Display summary
                        col1a, col2a = st.columns(2)
                        col1a.metric("Successfully Sold", sold_count)
                        col2a.metric("Errors", error_count)
                        
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
                st.error(f"Error processing sales file: {str(e)}")
    
    with col2:
        # Manual sale entry
        st.markdown('<div class="subheader">Manual Sale Entry</div>', unsafe_allow_html=True)
        
        manual_sale_rfid = st.text_input("RFID Tag to Sell")
        manual_sale_price = st.number_input("Sale Price (Optional)", min_value=0.0, step=0.01)
        
        if st.button("Process Single Sale"):
            if not manual_sale_rfid:
                st.error("RFID Tag is required")
            else:
                sale_price = manual_sale_price if manual_sale_price > 0 else None
                success, message = process_sale(manual_sale_rfid, sale_price)
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # Recent sales history
    st.markdown('<div class="subheader">Recent Sales</div>', unsafe_allow_html=True)
    
    if len(st.session_state.sales) > 0:
        # Get last 10 sales
        recent_sales = sorted(st.session_state.sales, key=lambda x: x['sale_date'], reverse=True)[:10]
        recent_sales_df = pd.DataFrame(recent_sales)
        st.dataframe(recent_sales_df)
        
        # Show total sales
        total_sales = sum(sale.get('sale_price', 0) for sale in st.session_state.sales if sale.get('sale_price') is not None)
        st.metric("Total Sales Revenue", f"${total_sales:.2f}")
    else:
        st.info("No sales recorded yet")

# Reports Tab
elif st.session_state.active_tab == "Reports":
    st.markdown('<div class="subheader">Inventory and Sales Reports</div>', unsafe_allow_html=True)
    
    report_type = st.radio("Report Type", ["Inventory Transactions", "Sales Analysis"])
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")
    
    # Convert to string format for comparison
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    if report_type == "Inventory Transactions":
        # Filter transactions by date
        filtered_transactions = [
            t for t in st.session_state.transactions 
            if start_date_str <= t['timestamp'].split()[0] <= end_date_str
        ]
        
        if len(filtered_transactions) > 0:
            # Prepare data for visualization
            transaction_df = pd.DataFrame(filtered_transactions)
            
            # Daily activity chart
            if len(transaction_df) > 0:
                transaction_df['date'] = transaction_df['timestamp'].apply(lambda x: x.split()[0])
                daily_counts = transaction_df.groupby(['date', 'action']).size().reset_index(name='count')
                
                fig = px.line(daily_counts, x='date', y='count', color='action', 
                             title='Daily Inventory Activity',
                             labels={'count': 'Number of Transactions', 'date': 'Date'})
                st.plotly_chart(fig)
            
            # Transaction table
            st.markdown('<div class="subheader">Transaction Log</div>', unsafe_allow_html=True)
            
            if len(filtered_transactions) > 0:
                # Enhance transaction data with product info
                for t in filtered_transactions:
                    product_id = t['product_id']
                    if product_id in st.session_state.products:
                        t['product_name'] = st.session_state.products[product_id]['name']
                    else:
                        t['product_name'] = "Unknown"
                
                transaction_df = pd.DataFrame(filtered_transactions)
                st.dataframe(transaction_df)
                
                # Export option
                if st.button("Export Transactions to Excel"):
                    # Convert DataFrame to Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        transaction_df.to_excel(writer, index=False)
                    
                    # Create a download link
                    excel_data = output.getvalue()
                    b64 = base64.b64encode(excel_data).decode()
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="inventory_report.xlsx">Download Excel Report</a>'
                    st.markdown(href, unsafe_allow_html=True)
            else:
                st.info(f"No transactions found between {start_date_str} and {end_date_str}")
        else:
            st.info("No transaction data available for the selected date range")
            
    else:  # Sales Analysis
        # Filter sales by date
        filtered_sales = [
            s for s in st.session_state.sales 
            if start_date_str <= s['sale_date'].split()[0] <= end_date_str
        ]
        
        if len(filtered_sales) > 0:
            # Prepare sales data for visualization
            sales_df = pd.DataFrame(filtered_sales)
            
            # Summary metrics
            total_sales = sum(s.get('sale_price', 0) for s in filtered_sales if s.get('sale_price') is not None)
            total_items = len(filtered_sales)
            avg_price = total_sales / total_items if total_items > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Sales", f"${total_sales:.2f}")
            col2.metric("Items Sold", total_items)
            col3.metric("Average Price", f"${avg_price:.2f}")
            
            # Sales by category
            if len(sales_df) > 0:
                sales_df['date'] = sales_df['sale_date'].apply(lambda x: x.split()[0])
                
                # Create date for daily sales chart
                if 'sale_price' in sales_df.columns:
                    daily_sales = sales_df.groupby('date')['sale_price'].sum().reset_index()
                    
                    fig1 = px.line(daily_sales, x='date', y='sale_price', 
                                  title='Daily Sales Revenue',
                                  labels={'sale_price': 'Revenue ($)', 'date': 'Date'})
                    st.plotly_chart(fig1)
                
                # Category pie chart
                category_sales = sales_df.groupby('category').size().reset_index(name='count')
                fig2 = px.pie(category_sales, values='count', names='category', 
                             title='Sales by Product Category')
                st.plotly_chart(fig2)
                
                # Sales table
                st.markdown('<div class="subheader">Sales Details</div>', unsafe_allow_html=True)
                st.dataframe(sales_df)
                
                # Export option
                if st.button("Export Sales to Excel"):
                    # Convert DataFrame to Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        sales_df.to_excel(writer, index=False)
                    
                    # Create a download link
                    excel_data = output.getvalue()
                    b64 = base64.b64encode(excel_data).decode()
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="sales_report.xlsx">Download Sales Report</a>'
                    st.markdown(href, unsafe_allow_html=True)
            
        else:
            st.info(f"No sales data available between {start_date_str} and {end_date_str}")

# Branches Tab
elif st.session_state.active_tab == "Branches":
    st.markdown('<div class="subheader">Manage Branches</div>', unsafe_allow_html=True)
    
    # Add new branch
    with st.expander("Add New Branch", expanded=True):
        branch_id = st.text_input("Branch ID")
        branch_name = st.text_input("Branch Name")
        branch_address = st.text_area("Branch Address")
        
        if st.button("Add Branch"):
            if not branch_id or not branch_name:
                st.error("Branch ID and Name are required")
            else:
                success, message = add_branch(branch_id, branch_name, branch_address)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # List existing branches
    st.markdown('<div class="subheader">Existing Branches</div>', unsafe_allow_html=True)
    
    if len(st.session_state.branches) == 0:
        st.info("No branches added yet")
    else:
        # Display branches in a table
        branches_data = []
        for bid, data in st.session_state.branches.items():
            # Count products in this branch
            product_count = sum(1 for data in st.session_state.rfid_data.values() if data.get('branch_id') == bid)
            branches_data.append({
                "Branch ID": bid,
                "Name": data['name'],
                "Address": data['address'],
                "Products": product_count,
                "Created At": data['created_at']
            })
        
        branches_df = pd.DataFrame(branches_data)
        st.dataframe(branches_df)
    
    # Transfer products between branches
    st.markdown('<div class="subheader">Transfer Products Between Branches</div>', unsafe_allow_html=True)
    
    if len(st.session_state.branches) < 2:
        st.warning("You need at least 2 branches to transfer products")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            from_branch_options = {bid: f"{data['name']}" for bid, data in st.session_state.branches.items()}
            selected_from_branch = st.selectbox("From Branch", list(from_branch_options.values()), key="from_branch")
            selected_from_branch_id = list(from_branch_options.keys())[list(from_branch_options.values()).index(selected_from_branch)]
            
            # List products in the selected branch
            branch_products = {}
            for rfid, data in st.session_state.rfid_data.items():
                if data.get('branch_id') == selected_from_branch_id:
                    product_id = data['product_id']
                    if product_id in st.session_state.products:
                        product_name = st.session_state.products[product_id]['name']
                        branch_products[rfid] = f"{product_name} (RFID: {rfid})"
            
            if not branch_products:
                st.warning(f"No products found in {from_branch_options[selected_from_branch_id]}")
                selected_products = []
            else:
                st.write(f"**Products in {from_branch_options[selected_from_branch_id]}:**")
                
                # Allow selecting multiple products
                select_all_products = st.checkbox("Select all products", key="select_all_from_branch")
                
                if select_all_products:
                    default_selections = list(branch_products.keys())
                else:
                    default_selections = []
                
                selected_products = st.multiselect(
                    "Select products to transfer",
                    options=list(branch_products.keys()),
                    default=default_selections,
                    format_func=lambda x: branch_products[x] if x in branch_products else x
                )
        
        with col2:
            # Only show branches other than the source branch
            to_branch_options = {bid: f"{data['name']}" for bid, data in st.session_state.branches.items() if bid != selected_from_branch_id}
            
            if not to_branch_options:
                st.warning("No other branches available for transfer")
                selected_to_branch_id = None
            else:
                selected_to_branch = st.selectbox("To Branch", list(to_branch_options.values()), key="to_branch")
                selected_to_branch_id = list(to_branch_options.keys())[list(to_branch_options.values()).index(selected_to_branch)]
        
        if selected_products and selected_to_branch_id:
            if st.button("Transfer Selected Products"):
                successful_transfers = 0
                for rfid in selected_products:
                    success, _ = transfer_product(rfid, selected_to_branch_id)
                    if success:
                        successful_transfers += 1
                
                if successful_transfers > 0:
                    st.success(f"Successfully transferred {successful_transfers} products to {to_branch_options[selected_to_branch_id]}")
                    # Trigger a rerun to update the UI
                    st.experimental_rerun()
                else:
                    st.error("No products were transferred")
    
    # Recent transfers
    st.markdown('<div class="subheader">Recent Transfers</div>', unsafe_allow_html=True)
    
    if len(st.session_state.transfers) == 0:
        st.info("No transfers recorded yet")
    else:
        # Get last 10 transfers
        recent_transfers = sorted(st.session_state.transfers, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        # Enhance transfer data with branch names
        for t in recent_transfers:
            from_branch = st.session_state.branches.get(t['from_branch_id'], {}).get('name', 'Unknown')
            to_branch = st.session_state.branches.get(t['to_branch_id'], {}).get('name', 'Unknown')
            t['from_branch'] = from_branch
            t['to_branch'] = to_branch
        
        transfers_df = pd.DataFrame(recent_transfers)
        st.dataframe(transfers_df)

# Add a footer
st.markdown("---")
st.markdown("RFID Inventory Management System © 2025")
